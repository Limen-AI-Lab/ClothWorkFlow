"""FastAPI 后端 — 为 React 前端提供 REST API"""

import asyncio
import json
import os
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

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


def _auto_load_if_enabled() -> None:
    """在后台线程执行，避免阻塞 Uvicorn 监听端口（否则建索引期间浏览器会 connection refused）"""
    auto = os.getenv("CLOTHWORKFLOW_AUTO_LOAD", "1").strip().lower()
    skip_auto = auto in ("0", "false", "no", "off")
    dirs_resp = get_analysis_dirs()
    if skip_auto and dirs_resp["dirs"]:
        print("已跳过自动加载（CLOTHWORKFLOW_AUTO_LOAD=0），请在界面选择并加载数据集。")
        return
    if not dirs_resp["dirs"]:
        return
    first = dirs_resp["dirs"][0]["path"]
    print(f"自动加载（后台）: {first}")
    try:
        load_data(LoadRequest(analysis_dir=first))
        print("自动加载完成。")
    except Exception as e:
        print(f"自动加载失败（可在页面选择数据集后重试）: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    async def _bg():
        await asyncio.to_thread(_auto_load_if_enabled)

    asyncio.create_task(_bg())
    yield


app = FastAPI(title="ClothWorkFlow API", version="0.3.0", lifespan=lifespan)

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
_bucket_indices: dict[str, frozenset[int]] | None = None


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
    llm_route: bool = Field(
        False,
        description="为 True 时用 Gemini 判断单品/搭配；搭配则按上装/下装等分桶各检索一次。",
    )
    per_slot_top_n: int | None = Field(
        None,
        description="搭配模式下每个 slot 的返回条数；默认按 top_n 与 slot 数自动分配。",
    )


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
    global _retriever, _meta_list, _analysis_dir, _all_analysis_data, _bucket_indices

    analysis_path = Path(req.analysis_dir)
    if not analysis_path.exists():
        raise HTTPException(404, f"目录不存在: {req.analysis_dir}")

    try:
        if index_is_stale(analysis_path):
            build_index(analysis_path)

        embeddings, meta_list, bm25_corpus = load_index(analysis_path)
        from clothworkflow.core.retriever import HybridRetriever
        _retriever = HybridRetriever(embeddings, meta_list, bm25_corpus)
        _meta_list = meta_list
        _analysis_dir = req.analysis_dir
        from clothworkflow.core.search_intent import build_bucket_index

        _bucket_indices = build_bucket_index(meta_list)

        _all_analysis_data = {}
        for item in load_analysis_results(analysis_path):
            source = item.get("_source_file", "")
            if source:
                _all_analysis_data[Path(source).stem] = item

        return {"status": "ok", "count": len(meta_list), "dim": embeddings.shape[1]}
    except HTTPException:
        raise
    except SystemExit as e:
        raise HTTPException(400, str(e) or "索引构建或加载失败") from e
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=(
                f"加载失败: {e}。若本地 models/bge-m3 不完整，可删除该文件夹后重试以下载完整模型；"
                "Python 3.14 下 HuggingFace 下载可能崩溃，建议改用 3.12/3.13 虚拟环境。"
            ),
        ) from e


def _search_results_to_items(raw_results: list[dict]) -> list[dict]:
    items = []
    for r in raw_results:
        resolved = resolve_image_path(r["image"])
        row = {
            **r,
            "image_url": f"/api/image?path={resolved}" if resolved else None,
        }
        items.append(row)
    return items


@app.post("/api/search")
def search(req: SearchRequest):
    if _retriever is None:
        raise HTTPException(400, "请先加载分析数据")

    q = req.query.strip()
    if not q:
        raise HTTPException(400, "query 不能为空")

    if not req.llm_route:
        result = _retriever.search(q, top_n=req.top_n)
        items = _search_results_to_items(result["results"])
        return {
            "query": result["query"],
            "query_tokens": result.get("query_tokens", []),
            "total_items": result["total_items"],
            "candidates": result["candidates_before_rerank"],
            "timing": result["timing"],
            "results": items,
            "llm_route": None,
        }

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise HTTPException(
            400,
            "已开启智能理解（llm_route），请设置环境变量 GEMINI_API_KEY（Google AI Studio API Key）",
        )

    from clothworkflow.core.search_intent import (
        gemini_classify_search_intent,
        ROLE_TO_BUCKET,
        SLOT_LABEL_ZH,
    )

    try:
        plan, gemini_ms = gemini_classify_search_intent(q, api_key)
    except httpx.HTTPStatusError as e:
        detail = e.response.text[:500] if e.response is not None else str(e)
        raise HTTPException(502, f"Gemini API 请求失败: {detail}") from e
    except Exception as e:
        raise HTTPException(502, f"Gemini 意图解析失败: {e}") from e

    if plan["mode"] == "single":
        result = _retriever.search(plan["single_query"], top_n=req.top_n)
        items = _search_results_to_items(result["results"])
        timing = dict(result["timing"])
        timing["gemini_ms"] = gemini_ms
        timing["total_ms"] = timing.get("total_ms", 0) + gemini_ms
        return {
            "query": q,
            "query_tokens": result.get("query_tokens", []),
            "total_items": result["total_items"],
            "candidates": result["candidates_before_rerank"],
            "timing": timing,
            "results": items,
            "llm_route": {
                "mode": "single",
                "reason": plan["reason"],
                "plan": plan,
                "used_queries": [{"slot": None, "query": plan["single_query"]}],
                "gemini_ms": gemini_ms,
            },
        }

    slots = plan["slots"]
    n_slots = len(slots)
    per = req.per_slot_top_n
    if per is None or per < 1:
        per = max(3, min(15, req.top_n // max(1, n_slots)))

    assert _bucket_indices is not None
    acc_timing = {"bm25_ms": 0, "vector_ms": 0, "merge_ms": 0, "rerank_ms": 0, "total_ms": 0}
    candidates_sum = 0
    items: list[dict] = []
    used_queries: list[dict] = []
    rank = 1

    for slot in slots:
        role = slot["role"]
        sq = slot["query"]
        bucket = ROLE_TO_BUCKET[role]
        allowed = _bucket_indices.get(bucket) or frozenset()
        used_queries.append({"slot": role, "query": sq})
        sub = _retriever.search(sq, top_n=per, allowed_indices=allowed)
        candidates_sum += sub["candidates_before_rerank"]
        for k in acc_timing:
            if k in sub["timing"]:
                acc_timing[k] += sub["timing"][k]
        for r in sub["results"]:
            row = {**r, "rank": rank}
            rank += 1
            row["slot"] = role
            row["slot_label"] = SLOT_LABEL_ZH.get(role, role)
            resolved = resolve_image_path(row["image"])
            row["image_url"] = f"/api/image?path={resolved}" if resolved else None
            items.append(row)

    acc_timing["gemini_ms"] = gemini_ms
    acc_timing["total_ms"] = acc_timing.get("total_ms", 0) + gemini_ms

    return {
        "query": q,
        "query_tokens": [],
        "total_items": _retriever.n,
        "candidates": candidates_sum,
        "timing": acc_timing,
        "results": items,
        "llm_route": {
            "mode": "outfit",
            "reason": plan["reason"],
            "plan": plan,
            "used_queries": used_queries,
            "gemini_ms": gemini_ms,
            "per_slot_top_n": per,
        },
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
        "gemini_configured": bool(os.getenv("GEMINI_API_KEY", "").strip()),
    }


# ============ 启动入口 ============

def main():
    import uvicorn

    # 自动加载在 lifespan 后台线程中进行，此处不再阻塞

    # 如果有前端构建产物则 serve
    frontend_dist = PACKAGE_ROOT / "web" / "dist"
    if frontend_dist.exists():
        app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")

    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
