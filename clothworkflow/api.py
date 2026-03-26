"""FastAPI 后端 — 为 React 前端提供 REST API"""

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from clothworkflow.core.config import (
    PROJECT_ROOT, PACKAGE_ROOT, CONFIG_FILE,
    DEFAULT_ANALYSIS_DIR, DEFAULT_DOWNLOAD_DIR,
    DEFAULT_ANALYSIS_MODEL, DEFAULT_BEDROCK_MODEL,
    BGE_M3_PATH, RERANKER_PATH,
    RECOMMEND_TOP_N, RECOMMEND_BM25_K, RECOMMEND_VECTOR_K, RECOMMEND_RERANK_K, RECOMMEND_RRF_K,
    SCRAPE_MAX_STEPS, SCRAPE_MIN_IMAGE_SIZE,
    ANALYZE_TIMEOUT, ANALYZE_DELAY, ANALYZE_TEMPERATURE,
)
from clothworkflow.core.indexer import load_index, index_is_stale, build_index, load_analysis_results

app = FastAPI(title="ClothWorkFlow API", version="0.3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ 全局状态 ============
_retriever = None
_meta_list = None
_analysis_dir = None
_all_analysis_data = {}


# ============ 路径解析 ============

def resolve_image_path(img_path_str: str) -> str | None:
    img_path = Path(img_path_str)
    for candidate in [
        img_path if img_path.is_absolute() else None,
        PROJECT_ROOT / img_path,
        DEFAULT_DOWNLOAD_DIR / img_path.name,
    ]:
        if candidate and candidate.exists():
            return str(candidate)

    if DEFAULT_DOWNLOAD_DIR.exists():
        for subdir in DEFAULT_DOWNLOAD_DIR.iterdir():
            if subdir.is_dir():
                c = subdir / img_path.name
                if c.exists():
                    return str(c)

    if len(img_path.parts) >= 2:
        c = DEFAULT_DOWNLOAD_DIR / img_path.parts[-2] / img_path.name
        if c.exists():
            return str(c)
    return None


# ============ Pydantic Models ============

class SearchRequest(BaseModel):
    query: str
    top_n: int = 5


class LoadRequest(BaseModel):
    analysis_dir: str


# ============ API 端点 ============

@app.get("/api/analysis-dirs")
def get_analysis_dirs():
    dirs = []
    full = PACKAGE_ROOT / "analysis"
    if full.exists():
        dirs.append({"path": str(full), "label": "全量数据", "type": "full"})
        for d in sorted(full.iterdir()):
            if d.is_dir() and any(d.glob("*.json")):
                dirs.append({"path": str(d), "label": d.name, "type": "shop"})
    testbed = PACKAGE_ROOT / "testbed" / "analysis"
    if testbed.exists():
        dirs.append({"path": str(testbed), "label": "测试床", "type": "testbed"})
    return {"dirs": dirs}


@app.post("/api/load")
def load_data(req: LoadRequest):
    global _retriever, _meta_list, _analysis_dir, _all_analysis_data

    analysis_path = Path(req.analysis_dir)
    if not analysis_path.exists():
        raise HTTPException(404, f"目录不存在: {req.analysis_dir}")

    if index_is_stale(analysis_path):
        build_index(analysis_path)

    embeddings, meta_list, bm25_corpus = load_index(analysis_path)
    from clothworkflow.core.retriever import HybridRetriever
    _retriever = HybridRetriever(embeddings, meta_list, bm25_corpus)
    _meta_list = meta_list
    _analysis_dir = req.analysis_dir

    _all_analysis_data = {}
    for item in load_analysis_results(analysis_path):
        source = item.get("_source_file", "")
        if source:
            _all_analysis_data[Path(source).stem] = item

    return {"status": "ok", "count": len(meta_list), "dim": embeddings.shape[1]}


@app.post("/api/search")
def search(req: SearchRequest):
    if _retriever is None:
        raise HTTPException(400, "请先加载分析数据")

    result = _retriever.search(req.query.strip(), top_n=req.top_n)

    items = []
    for r in result["results"]:
        resolved = resolve_image_path(r["image"])
        items.append({
            **r,
            "image_url": f"/api/image?path={resolved}" if resolved else None,
        })

    return {
        "query": result["query"],
        "query_tokens": result.get("query_tokens", []),
        "total_items": result["total_items"],
        "candidates": result["candidates_before_rerank"],
        "timing": result["timing"],
        "results": items,
    }


@app.get("/api/image")
def get_image(path: str = Query(...)):
    p = Path(path)
    if not p.exists():
        raise HTTPException(404, "图片不存在")
    return FileResponse(p, media_type="image/jpeg")


@app.get("/api/product/{stem}")
def get_product_detail(stem: str):
    data = _all_analysis_data.get(stem)
    if not data:
        raise HTTPException(404, f"未找到商品: {stem}")
    return data


@app.get("/api/stats")
def get_stats():
    from clothworkflow.stats import get_category_distribution
    analysis_full = PACKAGE_ROOT / "analysis"
    if analysis_full.exists():
        return get_category_distribution(str(analysis_full))
    testbed = PACKAGE_ROOT / "testbed" / "analysis"
    if testbed.exists():
        return get_category_distribution(str(testbed))
    return {"total": 0, "shops": 0}


@app.get("/api/config")
def get_config():
    return {
        "yaml": CONFIG_FILE.read_text("utf-8") if CONFIG_FILE.exists() else "",
        "current": {
            "analysis_model": DEFAULT_ANALYSIS_MODEL,
            "bedrock_model": DEFAULT_BEDROCK_MODEL,
            "bge_m3_path": BGE_M3_PATH,
            "reranker_path": RERANKER_PATH,
            "recommend_top_n": RECOMMEND_TOP_N,
            "recommend_bm25_k": RECOMMEND_BM25_K,
            "recommend_vector_k": RECOMMEND_VECTOR_K,
            "recommend_rerank_k": RECOMMEND_RERANK_K,
            "recommend_rrf_k": RECOMMEND_RRF_K,
            "scrape_max_steps": SCRAPE_MAX_STEPS,
            "scrape_min_image_size": SCRAPE_MIN_IMAGE_SIZE,
            "analyze_timeout": ANALYZE_TIMEOUT,
            "analyze_delay": ANALYZE_DELAY,
            "analyze_temperature": ANALYZE_TEMPERATURE,
        },
    }


@app.put("/api/config")
def save_config(data: dict):
    yaml_text = data.get("yaml", "")
    CONFIG_FILE.write_text(yaml_text, encoding="utf-8")
    return {"status": "ok", "message": "配置已保存，重启后生效"}


@app.get("/api/status")
def get_status():
    return {
        "loaded": _retriever is not None,
        "count": _retriever.n if _retriever else 0,
        "analysis_dir": _analysis_dir,
    }


# ============ 启动入口 ============

def main():
    import uvicorn

    # 自动加载数据
    dirs_resp = get_analysis_dirs()
    if dirs_resp["dirs"]:
        first = dirs_resp["dirs"][0]["path"]
        print(f"自动加载: {first}")
        load_data(LoadRequest(analysis_dir=first))

    # 如果有前端构建产物则 serve
    frontend_dist = PACKAGE_ROOT / "web" / "dist"
    if frontend_dist.exists():
        app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")

    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
