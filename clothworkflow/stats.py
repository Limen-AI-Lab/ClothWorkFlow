#!/usr/bin/env python3
"""
数据统计和可视化模块
为 ClothWorkFlow 提供丰富的数据分布统计和 HTML 可视化
"""

import json
from pathlib import Path
from collections import Counter
from typing import Dict, Any

from clothworkflow.core.config import PACKAGE_ROOT


def get_category_distribution(analysis_dir: Path | str) -> Dict[str, Any]:
    """
    遍历分析目录下所有 JSON 文件，统计各维度分布

    Args:
        analysis_dir: 分析目录路径（可能包含子目录）

    Returns:
        统计结果字典，包含：
        - category: 品类分布
        - gender: 性别分布
        - style: 风格分布
        - color: 颜色分布
        - price: 价格分布
        - season: 季节分布
        - total: 总商品数
        - shops: 店铺数（如果有子目录）
    """
    analysis_path = Path(analysis_dir)
    if not analysis_path.exists():
        return {"total": 0, "error": f"目录不存在: {analysis_dir}"}

    # 统计计数器
    categories = Counter()
    genders = Counter()
    styles = Counter()
    colors = Counter()
    prices = Counter()
    seasons = Counter()

    # 店铺集合
    shops = set()

    total_count = 0

    # 递归扫描所有 JSON 文件
    for json_file in analysis_path.rglob("*.json"):
        # 跳过以 _ 开头的元数据文件
        if json_file.name.startswith("_"):
            continue

        # 记录店铺（如果是子目录结构）
        if json_file.parent != analysis_path:
            shops.add(json_file.parent.name)

        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # 提取各维度数据
            # 品类
            if "basic_info" in data and "category" in data["basic_info"]:
                category = data["basic_info"]["category"]
                if category:
                    categories[category] += 1

            # 性别
            if "basic_info" in data and "gender" in data["basic_info"]:
                gender = data["basic_info"]["gender"]
                if gender:
                    genders[gender] += 1

            # 风格
            if "style" in data and "primary_style" in data["style"]:
                style = data["style"]["primary_style"]
                if style:
                    styles[style] += 1

            # 颜色
            if "colors" in data and "primary_color" in data["colors"]:
                color = data["colors"]["primary_color"]
                if color:
                    colors[color] += 1

            # 价格
            if "commercial" in data and "price_tier" in data["commercial"]:
                price = data["commercial"]["price_tier"]
                if price:
                    prices[price] += 1

            # 季节（列表类型，需要展开）
            if "basic_info" in data and "season" in data["basic_info"]:
                season_list = data["basic_info"]["season"]
                if isinstance(season_list, list):
                    for s in season_list:
                        if s:
                            seasons[s] += 1

            total_count += 1

        except (json.JSONDecodeError, KeyError, IOError) as e:
            # 跳过损坏的文件
            continue

    return {
        "category": dict(categories.most_common()),
        "gender": dict(genders.most_common()),
        "style": dict(styles.most_common()),
        "color": dict(colors.most_common()),
        "price": dict(prices.most_common()),
        "season": dict(seasons.most_common()),
        "total": total_count,
        "shops": len(shops) if shops else 0,
    }


def create_distribution_html(dist: Dict[str, Any]) -> str:
    """
    将统计结果转为美观的 HTML 可视化

    Args:
        dist: get_category_distribution 返回的统计字典

    Returns:
        完整的 HTML 字符串，包含样式和图表
    """

    total = dist.get("total", 0)
    shops = dist.get("shops", 0)

    if total == 0:
        return """
        <div style="padding: 40px; text-align: center; color: #666;">
            <h3>暂无数据</h3>
            <p>请先加载分析数据或执行商品分析</p>
        </div>
        """

    # 计算品类数
    num_categories = len(dist.get("category", {}))

    # 样式定义
    css = """
    <style>
        .stats-container {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 12px;
            margin-bottom: 30px;
        }

        .stats-cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .stat-card {
            background: white;
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            text-align: center;
            transition: transform 0.2s, box-shadow 0.2s;
        }

        .stat-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 8px 12px rgba(0, 0, 0, 0.15);
        }

        .stat-number {
            font-size: 48px;
            font-weight: bold;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin: 10px 0;
        }

        .stat-label {
            font-size: 14px;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 500;
        }

        .chart-section {
            background: white;
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
        }

        .chart-title {
            font-size: 18px;
            font-weight: 600;
            color: #333;
            margin-bottom: 20px;
            padding-bottom: 12px;
            border-bottom: 2px solid #f0f0f0;
        }

        .bar-chart {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .bar-item {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .bar-label {
            min-width: 100px;
            font-size: 14px;
            color: #555;
            font-weight: 500;
        }

        .bar-container {
            flex: 1;
            height: 32px;
            background: #f5f5f5;
            border-radius: 16px;
            overflow: hidden;
            position: relative;
        }

        .bar-fill {
            height: 100%;
            border-radius: 16px;
            display: flex;
            align-items: center;
            justify-content: flex-end;
            padding-right: 12px;
            color: white;
            font-size: 12px;
            font-weight: 600;
            transition: width 0.5s ease;
            box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.1);
        }

        .bar-value {
            min-width: 60px;
            text-align: right;
            font-size: 14px;
            color: #666;
            font-weight: 500;
        }

        /* 不同维度的配色 */
        .category-bar { background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%); }
        .gender-bar { background: linear-gradient(90deg, #43e97b 0%, #38f9d7 100%); }
        .style-bar { background: linear-gradient(90deg, #fa709a 0%, #fee140 100%); }
        .color-bar { background: linear-gradient(90deg, #30cfd0 0%, #330867 100%); }
        .price-bar { background: linear-gradient(90deg, #a8edea 0%, #fed6e3 100%); }
        .season-bar { background: linear-gradient(90deg, #ff9a9e 0%, #fecfef 100%); }
    </style>
    """

    # 顶部统计卡片
    cards_html = f"""
    <div class="stats-container">
        <div class="stats-cards">
            <div class="stat-card">
                <div class="stat-label">总商品数</div>
                <div class="stat-number">{total}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">品类数</div>
                <div class="stat-number">{num_categories}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">店铺数</div>
                <div class="stat-number">{shops if shops > 0 else '1'}</div>
            </div>
        </div>
    </div>
    """

    # 生成图表的辅助函数
    def create_bar_chart(data: Dict[str, int], title: str, color_class: str, max_items: int = 10) -> str:
        if not data:
            return ""

        # 取前 max_items 项
        items = list(data.items())[:max_items]
        if not items:
            return ""

        max_value = max(v for _, v in items)

        bars_html = []
        for label, value in items:
            width_percent = (value / max_value * 100) if max_value > 0 else 0
            percent = (value / total * 100) if total > 0 else 0

            bars_html.append(f"""
            <div class="bar-item">
                <div class="bar-label">{label}</div>
                <div class="bar-container">
                    <div class="bar-fill {color_class}" style="width: {width_percent}%;">
                        {value}
                    </div>
                </div>
                <div class="bar-value">{percent:.1f}%</div>
            </div>
            """)

        return f"""
        <div class="chart-section">
            <div class="chart-title">{title}</div>
            <div class="bar-chart">
                {''.join(bars_html)}
            </div>
        </div>
        """

    # 生成各维度图表
    charts = []

    # 品类分布
    if dist.get("category"):
        charts.append(create_bar_chart(
            dist["category"],
            "品类分布 (Category Distribution)",
            "category-bar",
            max_items=12
        ))

    # 性别分布
    if dist.get("gender"):
        charts.append(create_bar_chart(
            dist["gender"],
            "性别分布 (Gender Distribution)",
            "gender-bar"
        ))

    # 风格分布
    if dist.get("style"):
        charts.append(create_bar_chart(
            dist["style"],
            "风格分布 (Style Distribution)",
            "style-bar",
            max_items=10
        ))

    # 颜色分布
    if dist.get("color"):
        charts.append(create_bar_chart(
            dist["color"],
            "颜色分布 (Color Distribution)",
            "color-bar",
            max_items=12
        ))

    # 价格分布
    if dist.get("price"):
        # 价格排序（按价格区间排序）
        price_order = {
            "奢侈1000+": 4,
            "中高端500-1000": 3,
            "中端150-500": 2,
            "平价50-150": 1,
            "低价<50": 0,
        }
        sorted_prices = dict(sorted(
            dist["price"].items(),
            key=lambda x: price_order.get(x[0], 99),
            reverse=True
        ))
        charts.append(create_bar_chart(
            sorted_prices,
            "价格分布 (Price Tier Distribution)",
            "price-bar"
        ))

    # 季节分布
    if dist.get("season"):
        # 季节排序
        season_order = {"春": 0, "夏": 1, "秋": 2, "冬": 3, "四季": 4}
        sorted_seasons = dict(sorted(
            dist["season"].items(),
            key=lambda x: season_order.get(x[0], 99)
        ))
        charts.append(create_bar_chart(
            sorted_seasons,
            "季节分布 (Season Distribution)",
            "season-bar"
        ))

    # 组合最终 HTML
    html = css + cards_html + ''.join(charts)

    return html


def get_default_analysis_dir() -> Path:
    """获取默认的分析目录"""
    # 优先使用 clothworkflow/analysis（全量数据）
    full_analysis = PACKAGE_ROOT / "analysis"
    if full_analysis.exists():
        json_files = [f for f in full_analysis.rglob("*.json") if not f.name.startswith("_")]
        if json_files:
            return full_analysis

    # 否则使用 testbed
    testbed_analysis = PACKAGE_ROOT / "testbed" / "analysis"
    if testbed_analysis.exists():
        return testbed_analysis

    return full_analysis  # 返回默认路径，即使不存在


def generate_stats_html(analysis_dir: Path | str | None = None) -> str:
    """
    一站式生成统计报告 HTML

    Args:
        analysis_dir: 分析目录路径，为 None 时自动检测

    Returns:
        完整的 HTML 统计报告
    """
    if analysis_dir is None:
        analysis_dir = get_default_analysis_dir()

    dist = get_category_distribution(analysis_dir)
    html = create_distribution_html(dist)

    return html


if __name__ == "__main__":
    # 测试代码
    test_dir = PACKAGE_ROOT / "testbed" / "analysis"
    if test_dir.exists():
        print(f"测试目录: {test_dir}")
        dist = get_category_distribution(test_dir)
        print(f"\n统计结果:")
        print(f"总商品数: {dist['total']}")
        print(f"品类: {dist['category']}")
        print(f"性别: {dist['gender']}")
        print(f"风格: {dist['style']}")
        print(f"颜色: {dist['color']}")
        print(f"价格: {dist['price']}")
        print(f"季节: {dist['season']}")

        html = create_distribution_html(dist)
        output_file = PACKAGE_ROOT / "testbed" / "stats_preview.html"
        output_file.write_text(html, encoding="utf-8")
        print(f"\n✓ HTML 预览已保存到: {output_file}")
    else:
        print(f"测试目录不存在: {test_dir}")
