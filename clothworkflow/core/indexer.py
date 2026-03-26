"""向量索引 + BM25 语料构建"""

import json
import time
from pathlib import Path

import numpy as np

from .config import INDEX_VECTOR_FILE, INDEX_META_FILE, INDEX_BM25_FILE, INDEX_VERSION_FILE
from .model_manager import ensure_bge_m3
from .text_builder import analysis_to_semantic_text, analysis_to_bm25_tokens


def load_analysis_results(analysis_dir: Path) -> list[dict]:
    """加载所有分析结果 JSON（跳过以 _ 开头的元文件）"""
    results = []
    for f in sorted(analysis_dir.rglob("*.json")):
        if f.name.startswith("_"):
            continue
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            if data.get("_parse_error"):
                continue
            data["_source_file"] = str(f)
            results.append(data)
        except (json.JSONDecodeError, KeyError):
            continue
    return results


def get_analysis_fingerprint(analysis_dir: Path) -> str:
    """基于文件数量和最新修改时间生成指纹"""
    files = sorted(f for f in analysis_dir.rglob("*.json") if not f.name.startswith("_"))
    if not files:
        return ""
    return f"{len(files)}_{max(f.stat().st_mtime for f in files):.0f}"


def index_is_stale(analysis_dir: Path) -> bool:
    """检查索引是否需要重建"""
    version_path = analysis_dir / INDEX_VERSION_FILE
    if not version_path.exists():
        return True
    try:
        saved = json.loads(version_path.read_text())
        return saved.get("fingerprint") != get_analysis_fingerprint(analysis_dir)
    except Exception:
        return True


def build_index(analysis_dir: Path):
    """构建向量索引 + BM25 语料"""
    items = load_analysis_results(analysis_dir)
    if not items:
        raise SystemExit("未找到分析结果")

    print(f"共 {len(items)} 件商品\n")

    semantic_texts = []
    keyword_corpus = []
    meta_list = []

    for item in items:
        sem_text = analysis_to_semantic_text(item)
        kw_tokens = analysis_to_bm25_tokens(item)
        semantic_texts.append(sem_text)
        keyword_corpus.append(kw_tokens)
        meta_list.append({
            "image": item.get("_meta", {}).get("image", ""),
            "source_file": item.get("_source_file", ""),
            "title": item.get("ecommerce", {}).get("title", ""),
            "category": item.get("basic_info", {}).get("category", ""),
            "primary_color": item.get("colors", {}).get("primary_color", ""),
            "primary_style": item.get("style", {}).get("primary_style", ""),
            "gender": item.get("basic_info", {}).get("gender", ""),
            "semantic_text": sem_text,
        })

    # BGE-M3 Embedding
    from sentence_transformers import SentenceTransformer
    print(f"加载 BGE-M3...")
    embed_model = SentenceTransformer(ensure_bge_m3())
    print("生成 embedding...")
    embeddings = embed_model.encode(semantic_texts, show_progress_bar=True, normalize_embeddings=True)

    # 保存
    np.savez_compressed(analysis_dir / INDEX_VECTOR_FILE, embeddings=embeddings)
    (analysis_dir / INDEX_META_FILE).write_text(
        json.dumps(meta_list, ensure_ascii=False, indent=2), encoding="utf-8")
    (analysis_dir / INDEX_BM25_FILE).write_text(
        json.dumps(keyword_corpus, ensure_ascii=False), encoding="utf-8")
    (analysis_dir / INDEX_VERSION_FILE).write_text(
        json.dumps({"fingerprint": get_analysis_fingerprint(analysis_dir),
                     "items": len(items), "built_at": time.strftime("%Y-%m-%d %H:%M:%S")}),
        encoding="utf-8")

    print(f"\n索引构建完成:")
    print(f"  向量: {embeddings.shape} (BGE-M3, 1024维)")
    print(f"  BM25: {len(keyword_corpus)} 篇文档 (jieba 分词)")
    print(f"  元数据: {len(meta_list)} 条")


def load_index(analysis_dir: Path):
    """加载已构建的索引"""
    for name in [INDEX_VECTOR_FILE, INDEX_META_FILE, INDEX_BM25_FILE]:
        p = analysis_dir / name
        if not p.exists():
            raise SystemExit(
                f"索引不存在: {p}\n请先运行: .venv/bin/python recommend_clothes.py --analysis-dir {analysis_dir} --build-index"
            )

    embeddings = np.load(analysis_dir / INDEX_VECTOR_FILE)["embeddings"]
    meta_list = json.loads((analysis_dir / INDEX_META_FILE).read_text(encoding="utf-8"))
    bm25_corpus = json.loads((analysis_dir / INDEX_BM25_FILE).read_text(encoding="utf-8"))
    return embeddings, meta_list, bm25_corpus
