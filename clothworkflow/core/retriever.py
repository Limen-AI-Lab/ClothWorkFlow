"""混合检索器：BM25 + BGE-M3 向量 + BGE-Reranker 精排"""

import time

import numpy as np

from .config import RECOMMEND_BM25_K, RECOMMEND_VECTOR_K, RECOMMEND_RERANK_K, RECOMMEND_RRF_K
from .model_manager import ensure_bge_m3, ensure_reranker
from .text_builder import tokenize_chinese


class HybridRetriever:
    """BM25(jieba) + BGE-M3 语义向量 + RRF 融合 + BGE-Reranker 精排"""

    def __init__(self, embeddings: np.ndarray, meta_list: list[dict], bm25_corpus: list[list[str]]):
        from rank_bm25 import BM25Okapi
        from sentence_transformers import SentenceTransformer, CrossEncoder

        self.embeddings = embeddings
        self.meta_list = meta_list
        self.n = len(meta_list)

        print("  初始化 BM25 (jieba 分词)...")
        self.bm25 = BM25Okapi(bm25_corpus)

        print("  加载 BGE-M3 (embedding)...")
        self.embed_model = SentenceTransformer(ensure_bge_m3())

        print("  加载 BGE-Reranker-v2-M3...")
        self.reranker = CrossEncoder(ensure_reranker())
        print("  模型加载完成\n")

    def search(self, query: str, top_n: int = 5,
               bm25_k: int = RECOMMEND_BM25_K,
               vector_k: int = RECOMMEND_VECTOR_K,
               rerank_k: int = RECOMMEND_RERANK_K) -> dict:
        """混合检索 + Reranker 精排"""
        t0 = time.time()

        # Step 1: BM25
        query_tokens = tokenize_chinese(query)
        bm25_scores = self.bm25.get_scores(query_tokens)
        t1 = time.time()

        # Step 2: 向量语义
        query_vec = self.embed_model.encode([query], normalize_embeddings=True)
        vec_scores = (query_vec @ self.embeddings.T)[0]
        t2 = time.time()

        # Step 3: RRF 融合
        rrf_k = RECOMMEND_RRF_K
        rrf_scores = {}

        bm25_ranking = np.argsort(bm25_scores)[::-1]
        for rank, idx in enumerate(bm25_ranking):
            rrf_scores[int(idx)] = rrf_scores.get(int(idx), 0) + 1.0 / (rrf_k + rank + 1)

        vec_ranking = np.argsort(vec_scores)[::-1]
        for rank, idx in enumerate(vec_ranking):
            rrf_scores[int(idx)] = rrf_scores.get(int(idx), 0) + 1.0 / (rrf_k + rank + 1)

        rrf_sorted = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:rerank_k]
        candidates = [(idx, float(bm25_scores[idx]), float(vec_scores[idx]), rrf) for idx, rrf in rrf_sorted]
        t3 = time.time()

        # Step 4: Reranker 精排（完整文本）
        pairs = [(query, self.meta_list[idx]["semantic_text"]) for idx, *_ in candidates]
        rerank_scores = self.reranker.predict(pairs)
        t4 = time.time()

        # 组装结果
        ranked = sorted(zip(candidates, rerank_scores), key=lambda x: x[1], reverse=True)

        results = []
        for i, ((idx, bm25_s, vec_s, rrf_s), rerank_s) in enumerate(ranked[:top_n]):
            meta = self.meta_list[idx]
            bm25_rank = int(np.where(bm25_ranking == idx)[0][0]) + 1
            vec_rank = int(np.where(vec_ranking == idx)[0][0]) + 1
            source = "bm25" if bm25_rank < vec_rank else "vector"

            results.append({
                "rank": i + 1,
                "image": meta.get("image", ""),
                "title": meta.get("title", ""),
                "category": meta.get("category", ""),
                "primary_color": meta.get("primary_color", ""),
                "primary_style": meta.get("primary_style", ""),
                "gender": meta.get("gender", ""),
                "scores": {
                    "reranker": round(float(rerank_s), 4),
                    "vector_sim": round(vec_s, 4),
                    "bm25": round(bm25_s, 4),
                    "rrf": round(rrf_s, 4),
                    "source": source,
                },
            })

        return {
            "query": query,
            "query_tokens": query_tokens,
            "total_items": self.n,
            "candidates_before_rerank": len(candidates),
            "timing": {
                "bm25_ms": round((t1 - t0) * 1000),
                "vector_ms": round((t2 - t1) * 1000),
                "merge_ms": round((t3 - t2) * 1000),
                "rerank_ms": round((t4 - t3) * 1000),
                "total_ms": round((t4 - t0) * 1000),
            },
            "results": results,
        }
