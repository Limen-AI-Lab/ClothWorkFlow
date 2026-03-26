#!/usr/bin/env python3
"""CLI: 一键运行完整工作流（分析 → 建索引 → 推荐）"""

import argparse
import subprocess
import sys
from pathlib import Path

from clothworkflow.core.config import DEFAULT_ANALYSIS_DIR, DEFAULT_DOWNLOAD_DIR

PYTHON = sys.executable


def run_cmd(args: list[str], check: bool = True):
    print(f"\n{'─'*60}")
    print(f"$ {' '.join(args)}")
    print(f"{'─'*60}\n")
    result = subprocess.run(args)
    if check and result.returncode != 0:
        sys.exit(result.returncode)


def main():
    parser = argparse.ArgumentParser(description="ClothWorkFlow 一键运行")
    parser.add_argument("--images", type=Path, default=DEFAULT_DOWNLOAD_DIR, help="图片目录")
    parser.add_argument("--analysis", type=Path, default=DEFAULT_ANALYSIS_DIR, help="分析结果目录")
    parser.add_argument("--skip-analyze", action="store_true", help="跳过分析")
    parser.add_argument("--no-recommend", action="store_true", help="不进入推荐")
    parser.add_argument("--query", type=str, default=None, help="直接查询")
    parser.add_argument("--top", type=int, default=5, help="推荐数量")
    args = parser.parse_args()

    print("=" * 60)
    print("  ClothWorkFlow 服装智能工作流")
    print("=" * 60)

    if not args.skip_analyze:
        print("\n[Step 1/3] 分析服装图片特征")
        run_cmd([PYTHON, "-m", "clothworkflow.cli.analyze",
                 "--dir", str(args.images), "--recursive", "--outdir", str(args.analysis)])
    else:
        print("\n[Step 1/3] 跳过分析")

    print("\n[Step 2/3] 构建检索索引")
    run_cmd([PYTHON, "-m", "clothworkflow.cli.recommend",
             "--analysis-dir", str(args.analysis), "--build-index"])

    if not args.no_recommend:
        print("\n[Step 3/3] 智能推荐")
        cmd = [PYTHON, "-m", "clothworkflow.cli.recommend",
               "--analysis-dir", str(args.analysis), "--top", str(args.top)]
        if args.query:
            cmd.extend(["--query", args.query])
        run_cmd(cmd, check=False)
    else:
        print("\n[Step 3/3] 跳过推荐")

    print("\n完成！")


if __name__ == "__main__":
    main()
