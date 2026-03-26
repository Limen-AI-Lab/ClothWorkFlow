#!/usr/bin/env python3
"""CLI: 混合检索智能推荐（BM25 + BGE-M3 + Reranker）"""

import argparse
import json
from pathlib import Path

from clothworkflow.core import build_index, load_index, index_is_stale, HybridRetriever
from clothworkflow.core.config import DEFAULT_ANALYSIS_DIR


def print_results(data: dict):
    print(f"\n{'='*60}")
    print(f"搜索: {data['query']}")
    print(f"分词: {' / '.join(data.get('query_tokens', []))}")
    print(f"范围: {data['total_items']} 件 | 候选: {data['candidates_before_rerank']} 件")
    t = data["timing"]
    print(f"耗时: BM25 {t['bm25_ms']}ms + 向量 {t['vector_ms']}ms + Rerank {t['rerank_ms']}ms = {t['total_ms']}ms")
    print(f"{'='*60}\n")

    for r in data["results"]:
        s = r["scores"]
        print(f"  #{r['rank']}  Reranker: {s['reranker']:.3f} | 向量: {s['vector_sim']:.3f} | BM25: {s['bm25']:.2f} | RRF: {s['rrf']:.4f} | 来源: {s['source']}")
        print(f"      {r['title']}")
        print(f"      {r['category']} | {r['primary_color']} | {r['primary_style']} | {r['gender']}")
        print(f"      图片: {r['image']}")
        print()


def parse_args():
    parser = argparse.ArgumentParser(description="混合检索推荐：BM25 + BGE-M3 + Reranker")
    parser.add_argument("--analysis-dir", type=Path, default=DEFAULT_ANALYSIS_DIR, help="分析结果目录")
    parser.add_argument("--build-index", action="store_true", help="构建/重建索引")
    parser.add_argument("--query", type=str, default=None, help="搜索描述")
    parser.add_argument("--top", type=int, default=5, help="推荐数量")
    parser.add_argument("--save", type=Path, default=None, help="保存结果到 JSON")
    return parser.parse_args()


def main():
    args = parse_args()

    if args.build_index:
        build_index(args.analysis_dir)
        return

    if index_is_stale(args.analysis_dir):
        print("检测到分析结果变更，自动重建索引...\n")
        build_index(args.analysis_dir)
        print()

    print(f"加载索引: {args.analysis_dir}")
    embeddings, meta_list, bm25_corpus = load_index(args.analysis_dir)
    print(f"已加载 {len(meta_list)} 件商品 (向量维度: {embeddings.shape[1]})\n")

    print("初始化检索模型:")
    retriever = HybridRetriever(embeddings, meta_list, bm25_corpus)

    if args.query:
        result = retriever.search(args.query, top_n=args.top)
        print_results(result)
        if args.save:
            args.save.parent.mkdir(parents=True, exist_ok=True)
            args.save.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        print("进入交互推荐模式（输入 q 退出）\n")
        while True:
            try:
                query = input("描述你想要的服装 > ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if not query or query.lower() == "q":
                break
            try:
                result = retriever.search(query, top_n=args.top)
                print_results(result)
            except Exception as e:
                print(f"检索失败: {e}\n")
        print("再见！")


if __name__ == "__main__":
    main()
