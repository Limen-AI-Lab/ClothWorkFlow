#!/usr/bin/env python3
"""CLI: Gemini 多模态服装特征分析"""

import argparse
import json
import os
import time
from pathlib import Path

from clothworkflow.core import analyze_single_image, collect_images
from clothworkflow.core.config import DEFAULT_ANALYSIS_MODEL, DEFAULT_ANALYSIS_DIR


def parse_args():
    parser = argparse.ArgumentParser(description="Gemini 多模态服装特征分析")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--image", type=Path, help="分析单张图片")
    group.add_argument("--dir", type=Path, help="批量分析目录")
    parser.add_argument("--recursive", action="store_true", help="递归扫描子目录")
    parser.add_argument("--outdir", type=Path, default=DEFAULT_ANALYSIS_DIR, help="输出目录")
    parser.add_argument("--model", default=DEFAULT_ANALYSIS_MODEL, help="OpenRouter 模型")
    parser.add_argument("--api-key", default=os.getenv("OPENROUTER_API_KEY", ""), help="OpenRouter API Key")
    parser.add_argument("--timeout", type=int, default=120, help="超时秒数")
    parser.add_argument("--delay", type=float, default=1.0, help="请求间隔秒数")
    parser.add_argument("--limit", type=int, default=0, help="最多处理数量")
    parser.add_argument("--force", action="store_true", help="强制重新分析")
    return parser.parse_args()


def main():
    args = parse_args()

    if not args.api_key:
        raise SystemExit("缺少 API Key。请设置环境变量 OPENROUTER_API_KEY。")

    source = args.image or args.dir
    images = collect_images(source, recursive=args.recursive)
    if not images:
        raise SystemExit(f"未找到图片: {source}")

    if args.limit > 0:
        images = images[:args.limit]

    args.outdir.mkdir(parents=True, exist_ok=True)

    # 增量模式
    if not args.force:
        original = len(images)
        images = [img for img in images if not (args.outdir / f"{img.stem}.json").exists()]
        skipped = original - len(images)
        if skipped > 0:
            print(f"增量模式: 跳过 {skipped} 张已分析图片（--force 强制重跑）")
        if not images:
            print("所有图片均已分析。")
            return

    print(f"共 {len(images)} 张图片待分析\n")

    results = []
    success = fail = 0

    for i, img_path in enumerate(images, 1):
        print(f"[{i}/{len(images)}] {img_path.name} ... ", end="", flush=True)
        try:
            result = analyze_single_image(img_path, args.api_key, model=args.model, timeout=args.timeout)
            if result.get("_parse_error"):
                print("JSON 解析失败")
                fail += 1
            else:
                title = result.get("ecommerce", {}).get("title", "")
                category = result.get("basic_info", {}).get("category", "?")
                print(f"{category} | {title}")
                success += 1
            results.append(result)

            with open(args.outdir / f"{img_path.stem}.json", "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"失败: {e}")
            results.append({"_meta": {"image": str(img_path), "error": str(e)}})
            fail += 1

        if i < len(images) and args.delay > 0:
            time.sleep(args.delay)

    summary = {"total": len(images), "success": success, "fail": fail, "model": args.model, "items": results}
    with open(args.outdir / "_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"\n分析完成: 成功 {success}, 失败 {fail}, 共 {len(images)} 张")
    print(f"结果: {args.outdir}")


if __name__ == "__main__":
    main()
