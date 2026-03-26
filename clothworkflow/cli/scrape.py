#!/usr/bin/env python3
"""CLI: browser-use 爬取 1688 店铺商品图片"""

import argparse
import asyncio
import re
from pathlib import Path

from clothworkflow.core.config import (
    DEFAULT_DOWNLOAD_DIR, DEFAULT_BEDROCK_MODEL,
    SCRAPE_MAX_STEPS, SCRAPE_MIN_IMAGE_SIZE,
)

# 延迟导入 browser-use 相关（可选依赖）
DATA_DIR = Path(__file__).parent.parent / "data"
DEFAULT_URL_FILE = DATA_DIR / "taget_url.txt"


def parse_args():
    parser = argparse.ArgumentParser(description="1688 服装图片爬取工具")
    parser.add_argument("-f", "--url-file", type=Path, default=DEFAULT_URL_FILE, help="URL 文件路径")
    parser.add_argument("-o", "--output", type=Path, default=DEFAULT_DOWNLOAD_DIR, help="图片保存目录")
    parser.add_argument("--model", default=DEFAULT_BEDROCK_MODEL, help="Bedrock 模型 ID")
    parser.add_argument("--max-steps", type=int, default=SCRAPE_MAX_STEPS, help="Agent 最大步数")
    parser.add_argument("--headless", action="store_true", help="无头模式")
    parser.add_argument("--min-size", type=int, default=SCRAPE_MIN_IMAGE_SIZE, help="最小图片大小(字节)")
    return parser.parse_args()


def read_urls(file_path: Path) -> list[str]:
    text = file_path.read_text(encoding="utf-8")
    return [line.strip() for line in text.splitlines() if line.strip()]


def get_shop_name(url: str) -> str:
    match = re.search(r"//([^/]+)\.1688\.com", url)
    if match:
        return match.group(1)
    return re.sub(r"[^\w]", "_", url)[:50]


async def scrape_shop(url: str, shop_dir: Path, llm, *, headless: bool, max_steps: int, min_image_size: int):
    from browser_use import Agent, Browser, BrowserProfile

    shop_dir.mkdir(parents=True, exist_ok=True)
    browser = Browser(
        browser_profile=BrowserProfile(
            headless=headless,
            downloads_path=str(shop_dir),
            accept_downloads=True,
            window_size={"width": 1280, "height": 800},
            device_scale_factor=1,
        )
    )

    task = f"""
你是一个图片采集助手。请完成以下任务：

1. 打开网页: {url}
2. 这是一个 1688 服装店铺页面，请找到商品列表区域
3. 如果页面有弹窗或登录提示，请关闭它们
4. 慢慢向下滚动页面，确保所有商品图片都加载出来
5. 找到页面中所有服装商品的主图（通常是商品列表中的大图），提取它们的图片 URL
6. 图片 URL 通常以 .jpg 或 .png 结尾，可能包含 cbu01.alicdn.com 等域名
7. 请把所有找到的商品图片 URL 汇总输出，每行一个 URL

注意：
- 只需要商品主图，不需要 logo、banner、广告图等
- 如果有分页，只需要采集第一页的商品图片
- 输出所有图片 URL 即可，后续下载由程序处理
"""

    agent = Agent(
        task=task, llm=llm, browser=browser,
        max_actions_per_step=3, use_vision=True, vision_detail_level="low",
    )

    try:
        result = await agent.run(max_steps=max_steps)
        image_urls = extract_image_urls(result)
        print(f"\n[{get_shop_name(url)}] 找到 {len(image_urls)} 张商品图片")
        if image_urls:
            await download_images(image_urls, shop_dir, min_image_size=min_image_size)
        return image_urls
    finally:
        await browser.stop()


def extract_image_urls(result) -> list[str]:
    urls = set()
    text = str(result)
    patterns = [
        r'https?://cbu\d+\.alicdn\.com/[^\s"\'<>]+\.(?:jpg|jpeg|png|webp)(?:\?[^\s"\'<>]*)?',
        r'https?://img\.alicdn\.com/[^\s"\'<>]+\.(?:jpg|jpeg|png|webp)(?:\?[^\s"\'<>]*)?',
        r'https?://[^\s"\'<>]+\.alicdn\.com/[^\s"\'<>]+\.(?:jpg|jpeg|png|webp)(?:\?[^\s"\'<>]*)?',
    ]
    for pattern in patterns:
        urls.update(re.findall(pattern, text, re.IGNORECASE))
    return [u.rstrip(".,;)]}>'\"") for u in urls]


async def download_images(urls: list[str], save_dir: Path, *, min_image_size: int = 10240):
    import httpx
    save_dir.mkdir(parents=True, exist_ok=True)
    async with httpx.AsyncClient(
        timeout=30, follow_redirects=True,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Referer": "https://www.1688.com/",
        },
    ) as client:
        saved = 0
        for i, url in enumerate(urls, 1):
            try:
                resp = await client.get(url)
                if resp.status_code == 200:
                    if len(resp.content) < min_image_size:
                        continue
                    ct = resp.headers.get("content-type", "")
                    ext = ".png" if "png" in ct else ".webp" if "webp" in ct else ".jpg"
                    saved += 1
                    (save_dir / f"product_{saved:03d}{ext}").write_bytes(resp.content)
                    print(f"  [{saved}/{len(urls)}] 已保存: product_{saved:03d}{ext}")
            except Exception as e:
                print(f"  [{i}/{len(urls)}] 下载出错: {e}")
        print(f"  实际保存: {saved} 张 (过滤了 {len(urls) - saved} 张小图)")


async def async_main():
    from clothworkflow.core.llm_bedrock import ChatLiteLLMBedrock
    args = parse_args()
    urls = read_urls(args.url_file)
    print(f"读取到 {len(urls)} 个店铺 URL\n")

    llm = ChatLiteLLMBedrock(model=args.model)
    all_results = {}

    for url in urls:
        shop_name = get_shop_name(url)
        shop_dir = args.output / shop_name
        print(f"\n{'='*60}\n开始爬取: {shop_name}\nURL: {url}\n{'='*60}\n")
        try:
            image_urls = await scrape_shop(
                url, shop_dir, llm,
                headless=args.headless, max_steps=args.max_steps, min_image_size=args.min_size,
            )
            all_results[shop_name] = image_urls or []
        except Exception as e:
            print(f"爬取失败: {e}")
            all_results[shop_name] = []

    print(f"\n{'='*60}\n爬取完成:")
    total = sum(len(v) for v in all_results.values())
    for shop, imgs in all_results.items():
        print(f"  {shop}: {len(imgs)} 张")
    print(f"  总计: {total} 张 | 保存位置: {args.output}")


def main():
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
