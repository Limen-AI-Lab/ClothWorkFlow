#!/usr/bin/env python3
"""ClothWorkFlow Web UI — Gradio 前端（整合版）"""

import json
from pathlib import Path

import gradio as gr

from clothworkflow.core.config import (
    PROJECT_ROOT, PACKAGE_ROOT, CONFIG_FILE,
    DEFAULT_ANALYSIS_MODEL, DEFAULT_BEDROCK_MODEL,
    BGE_M3_PATH, RERANKER_PATH,
    DEFAULT_ANALYSIS_DIR, DEFAULT_DOWNLOAD_DIR,
    RECOMMEND_TOP_N, RECOMMEND_BM25_K, RECOMMEND_VECTOR_K, RECOMMEND_RERANK_K, RECOMMEND_RRF_K,
    SCRAPE_MAX_STEPS, SCRAPE_MIN_IMAGE_SIZE,
    ANALYZE_TIMEOUT, ANALYZE_DELAY, ANALYZE_TEMPERATURE,
)
from clothworkflow.core.indexer import load_index, index_is_stale, build_index, load_analysis_results

# ============ 全局状态 ============
_retriever = None
_meta_list = None
_analysis_dir = None
_all_analysis_data = {}  # {filename: analysis_json} 缓存


# ============ 加载 CSS 主题 ============
_CSS_PATH = Path(__file__).parent / "static" / "theme.css"
CUSTOM_CSS = _CSS_PATH.read_text(encoding="utf-8") if _CSS_PATH.exists() else ""


# ============ 工具函数 ============

def get_analysis_dirs() -> list[str]:
    """扫描可用的分析目录"""
    dirs = []
    full = PACKAGE_ROOT / "analysis"
    if full.exists():
        dirs.append(str(full))
        for d in sorted(full.iterdir()):
            if d.is_dir() and any(d.glob("*.json")):
                dirs.append(str(d))
    testbed = PACKAGE_ROOT / "testbed" / "analysis"
    if testbed.exists():
        dirs.append(str(testbed))
    return dirs


def resolve_image_path(img_path_str: str) -> str | None:
    """多层 fallback 解析图片路径"""
    img_path = Path(img_path_str)

    # 1. 绝对路径
    if img_path.is_absolute() and img_path.exists():
        return str(img_path)

    # 2. 相对于项目根目录
    candidate = PROJECT_ROOT / img_path
    if candidate.exists():
        return str(candidate)

    # 3. 在下载目录按文件名查找
    candidate = DEFAULT_DOWNLOAD_DIR / img_path.name
    if candidate.exists():
        return str(candidate)

    # 4. 递归查找下载目录子目录
    if DEFAULT_DOWNLOAD_DIR.exists():
        for subdir in DEFAULT_DOWNLOAD_DIR.iterdir():
            if subdir.is_dir():
                candidate = subdir / img_path.name
                if candidate.exists():
                    return str(candidate)

    # 5. 按路径中的目录结构查找
    if len(img_path.parts) >= 2:
        candidate = DEFAULT_DOWNLOAD_DIR / img_path.parts[-2] / img_path.name
        if candidate.exists():
            return str(candidate)

    return None


# ============ 核心功能 ============

def load_retriever(analysis_dir: str) -> str:
    """加载或切换检索器"""
    global _retriever, _meta_list, _analysis_dir, _all_analysis_data

    analysis_path = Path(analysis_dir)
    if not analysis_path.exists():
        return f"目录不存在: {analysis_dir}"

    if index_is_stale(analysis_path):
        build_index(analysis_path)

    try:
        embeddings, meta_list, bm25_corpus = load_index(analysis_path)
        from clothworkflow.core.retriever import HybridRetriever
        _retriever = HybridRetriever(embeddings, meta_list, bm25_corpus)
        _meta_list = meta_list
        _analysis_dir = analysis_dir

        # 缓存分析数据用于详情展示
        _all_analysis_data = {}
        items = load_analysis_results(analysis_path)
        for item in items:
            source = item.get("_source_file", "")
            if source:
                _all_analysis_data[Path(source).stem] = item

        return f"已加载 {len(meta_list)} 件商品 (向量维度: {embeddings.shape[1]})"
    except Exception as e:
        return f"加载失败: {e}"


def search_clothes(query: str, top_n: int) -> tuple[list, str]:
    """执行搜索并返回图片 gallery + 详情 HTML"""
    if _retriever is None:
        return [], '<div class="result-card" style="text-align:center;padding:40px;color:#e94560;">请先在「数据总览」标签页加载分析数据</div>'

    if not query.strip():
        return [], '<div class="result-card" style="text-align:center;padding:40px;color:#e94560;">请输入搜索描述</div>'

    result = _retriever.search(query.strip(), top_n=int(top_n))

    gallery_items = []
    t = result["timing"]

    # 搜索信息头部
    html_parts = [f"""
    <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
                color: white; padding: 24px; border-radius: 16px; margin-bottom: 24px;
                box-shadow: 0 8px 24px rgba(26,26,46,0.3);">
        <div style="font-size: 20px; font-weight: 700; margin-bottom: 12px;">
            🔍 {result['query']}
        </div>
        <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 10px;">
            {' '.join(f'<span style="background:rgba(233,69,96,0.3); padding:4px 12px; border-radius:20px; font-size:13px;">{tok}</span>' for tok in result.get('query_tokens', []))}
        </div>
        <div style="font-size: 13px; opacity: 0.85; display: flex; gap: 20px; flex-wrap: wrap;">
            <span>📦 {result['total_items']} 件商品</span>
            <span>🎯 {result['candidates_before_rerank']} 件候选</span>
            <span>⚡ {t['total_ms']}ms (BM25 {t['bm25_ms']} + 向量 {t['vector_ms']} + Rerank {t['rerank_ms']})</span>
        </div>
    </div>
    """]

    # 颜色映射
    color_map = {
        "黑色": "#2c3e50", "白色": "#bdc3c7", "灰色": "#95a5a6", "深灰": "#555",
        "红色": "#e74c3c", "酒红": "#722F37", "玫红": "#e91e63", "砖红": "#b33939",
        "蓝色": "#3498db", "藏青": "#003153", "天蓝": "#87CEEB", "雾蓝": "#6c8ebf",
        "绿色": "#27ae60", "墨绿": "#004225",
        "黄色": "#f1c40f", "亮黄色": "#f39c12",
        "粉色": "#e91e63", "裸粉": "#d4a0a0",
        "紫色": "#9b59b6", "棕色": "#795548", "深棕": "#5d4037",
        "橙色": "#ff6b35", "焦糖": "#a0522d", "卡其": "#c3b091",
        "米白": "#f5f5dc", "米色": "#f5f5dc", "驼色": "#c19a6b",
        "炭灰": "#36454f",
    }

    for r in result["results"]:
        s = r["scores"]

        # 解析图片路径
        resolved = resolve_image_path(r["image"])
        caption = f"#{r['rank']} {r['title'][:30]}\n{r['category']} | {r['primary_color']}"
        if resolved:
            gallery_items.append((resolved, caption))

        # 颜色标签背景
        pc = color_map.get(r['primary_color'], '#7f8c8d')
        # 确保白色/浅色标签文字可读
        text_color = "#333" if r['primary_color'] in ("白色", "米白", "米色", "亮黄色", "裸粉") else "#fff"

        source_colors = {"bm25": "#e67e22", "vector": "#3498db"}
        sc = source_colors.get(s['source'], '#9b59b6')

        html_parts.append(f"""
        <div class="result-card" style="background:#fff; border-radius:16px; padding:24px; margin-bottom:16px;
                    box-shadow: 0 2px 12px rgba(0,0,0,0.06); border: 1px solid #eee;
                    transition: all 0.3s; position:relative;">

            <div style="display:flex; align-items:flex-start; gap:16px; margin-bottom:16px;">
                <span style="background: linear-gradient(135deg, #e94560, #c23152); color:#fff;
                             font-size:18px; font-weight:800; padding:8px 14px; border-radius:12px;
                             min-width:36px; text-align:center; box-shadow: 0 4px 12px rgba(233,69,96,0.3);">
                    {r['rank']}
                </span>
                <div style="flex:1;">
                    <div style="font-size:17px; font-weight:600; color:#1a1a2e; line-height:1.4; margin-bottom:8px;">
                        {r['title']}
                    </div>
                    <div style="display:flex; flex-wrap:wrap; gap:6px;">
                        <span class="tag" style="background:#0f3460; color:#fff; padding:4px 12px; border-radius:20px; font-size:12px;">
                            {r['category']}
                        </span>
                        <span class="tag" style="background:{pc}; color:{text_color}; padding:4px 12px; border-radius:20px; font-size:12px;
                                     {f'border:1px solid #ccc;' if text_color == '#333' else ''}">
                            {r['primary_color']}
                        </span>
                        <span class="tag" style="background:#9b59b6; color:#fff; padding:4px 12px; border-radius:20px; font-size:12px;">
                            {r['primary_style']}
                        </span>
                        <span class="tag" style="background:#16a085; color:#fff; padding:4px 12px; border-radius:20px; font-size:12px;">
                            {r['gender']}
                        </span>
                    </div>
                </div>
                <span style="background:{sc}; color:#fff; font-size:11px; padding:4px 10px; border-radius:8px; font-weight:600;">
                    {s['source'].upper()}
                </span>
            </div>

            <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px;">
                {"".join(f'''
                <div style="display:flex; align-items:center; gap:8px;">
                    <span style="font-size:12px; color:#888; width:70px; text-align:right;">{label}</span>
                    <div style="flex:1; background:#f0f0f0; border-radius:8px; height:18px; overflow:hidden; position:relative;">
                        <div style="background:linear-gradient(90deg, {c1}, {c2}); width:{w:.0f}%; height:100%; border-radius:8px;"></div>
                        <span style="position:absolute; right:8px; top:50%; transform:translateY(-50%); font-size:11px; font-weight:600; color:#555;">{val}</span>
                    </div>
                </div>
                ''' for label, val, w, c1, c2 in [
                    ("Reranker", f"{s['reranker']:.3f}", min(s['reranker']*100, 100), "#e94560", "#c23152"),
                    ("向量", f"{s['vector_sim']:.3f}", min(s['vector_sim']*100, 100), "#0f3460", "#3498db"),
                    ("BM25", f"{s['bm25']:.2f}", min(s['bm25']/10*100, 100), "#e67e22", "#f39c12"),
                    ("RRF", f"{s['rrf']:.4f}", min(s['rrf']*3000, 100), "#16a085", "#1abc9c"),
                ])}
            </div>
        </div>
        """)

    return gallery_items, "\n".join(html_parts)


def get_product_detail(evt: gr.SelectData) -> str:
    """Gallery 点击时显示商品详情"""
    if not _meta_list or evt.index >= len(_meta_list):
        return ""

    # 从搜索结果中找到对应的分析数据
    meta = _meta_list[evt.index] if evt.index < len(_meta_list) else None
    if not meta:
        return ""

    # 尝试从缓存获取完整分析数据
    source_file = meta.get("source_file", "")
    stem = Path(source_file).stem if source_file else ""
    analysis = _all_analysis_data.get(stem)

    if analysis:
        from clothworkflow.detail_view import render_product_detail
        return render_product_detail(analysis)
    return ""


def get_stats_html() -> str:
    """获取数据统计 HTML"""
    analysis_full = PACKAGE_ROOT / "analysis"
    if analysis_full.exists():
        from clothworkflow.stats import get_category_distribution, create_distribution_html
        dist = get_category_distribution(str(analysis_full))
        return create_distribution_html(dist)

    # fallback: testbed
    testbed = PACKAGE_ROOT / "testbed" / "analysis"
    if testbed.exists():
        from clothworkflow.stats import get_category_distribution, create_distribution_html
        dist = get_category_distribution(str(testbed))
        return create_distribution_html(dist)

    return "<p style='text-align:center; color:#888; padding:40px;'>暂无分析数据</p>"


def get_config_text() -> str:
    if CONFIG_FILE.exists():
        return CONFIG_FILE.read_text(encoding="utf-8")
    return "# config.yaml 不存在"


def save_config_text(text: str) -> str:
    try:
        CONFIG_FILE.write_text(text, encoding="utf-8")
        return "配置已保存。重启应用后生效。"
    except Exception as e:
        return f"保存失败: {e}"


def get_current_config_summary() -> str:
    return f"""
<div style="display:grid; grid-template-columns:repeat(auto-fill, minmax(300px, 1fr)); gap:12px; padding:16px 0;">
    {"".join(f'''
    <div style="background:#fff; border-radius:12px; padding:16px; border:1px solid #eee;">
        <div style="font-size:12px; color:#888; margin-bottom:4px;">{label}</div>
        <div style="font-size:14px; font-weight:600; color:#1a1a2e; word-break:break-all;">{val}</div>
    </div>
    ''' for label, val in [
        ("分析模型", DEFAULT_ANALYSIS_MODEL),
        ("Bedrock 模型", DEFAULT_BEDROCK_MODEL),
        ("BGE-M3", f"...{BGE_M3_PATH[-45:]}"),
        ("Reranker", f"...{RERANKER_PATH[-45:]}"),
        ("推荐 Top-N / BM25-K / Vec-K", f"{RECOMMEND_TOP_N} / {RECOMMEND_BM25_K} / {RECOMMEND_VECTOR_K}"),
        ("Rerank-K / RRF-K", f"{RECOMMEND_RERANK_K} / {RECOMMEND_RRF_K}"),
        ("分析超时 / 间隔 / 温度", f"{ANALYZE_TIMEOUT}s / {ANALYZE_DELAY}s / {ANALYZE_TEMPERATURE}"),
        ("爬取步数 / 最小图片", f"{SCRAPE_MAX_STEPS} / {SCRAPE_MIN_IMAGE_SIZE}B"),
    ])}
</div>"""


# ============ 构建 UI ============

def create_app() -> gr.Blocks:
    with gr.Blocks(
        title="ClothWorkFlow - 服装智能推荐",
        theme=gr.themes.Soft(
            primary_hue=gr.themes.Color(c50="#f0f4ff", c100="#d9e4ff", c200="#b3c9ff",
                c300="#8daeff", c400="#6693ff", c500="#4078ff", c600="#1a1a2e",
                c700="#16213e", c800="#0f3460", c900="#0a1628", c950="#050b14"),
            secondary_hue="gray",
            font=gr.themes.GoogleFont("Inter"),
        ),
        css=CUSTOM_CSS,
    ) as app:

        # Header
        gr.HTML("""
        <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 40%, #0f3460 100%);
                    padding: 32px; border-radius: 20px; margin-bottom: 8px; text-align:center;
                    box-shadow: 0 8px 32px rgba(26,26,46,0.4);">
            <h1 style="color:#fff; font-size:36px; font-weight:800; margin:0 0 8px 0; letter-spacing:2px;">
                ClothWorkFlow
            </h1>
            <p style="color:rgba(255,255,255,0.7); font-size:16px; margin:0;">
                服装图片爬取 · AI 特征分析 · 混合检索智能推荐
            </p>
        </div>
        """)

        with gr.Tabs() as tabs:

            # ============ Tab 1: 智能推荐 ============
            with gr.Tab("🔍 智能推荐", id="search"):
                with gr.Row(equal_height=True):
                    with gr.Column(scale=4):
                        query_input = gr.Textbox(
                            placeholder="描述你想要的服装... 例如：显瘦的夏天裙子、街头风男装、参加婚礼穿的礼服",
                            label="搜索描述",
                            lines=2,
                            elem_classes=["search-box"],
                        )
                    with gr.Column(scale=1, min_width=160):
                        top_n_slider = gr.Slider(minimum=1, maximum=20, value=5, step=1, label="推荐数量")
                        search_btn = gr.Button("🔍 搜索推荐", variant="primary", size="lg")

                gallery = gr.Gallery(
                    label="推荐结果",
                    columns=5,
                    height=350,
                    object_fit="cover",
                    show_label=False,
                    allow_preview=True,
                )

                with gr.Row():
                    with gr.Column(scale=3):
                        details_html = gr.HTML(label="搜索结果")
                    with gr.Column(scale=2):
                        detail_panel = gr.HTML(label="商品详情", value="<div style='text-align:center;color:#aaa;padding:60px;'>点击图片查看商品详情</div>")

                gr.Examples(
                    examples=[
                        ["显瘦的夏天连衣裙"],
                        ["街头风男生T恤，水洗做旧"],
                        ["参加派对的正式优雅礼服"],
                        ["透气凉快便宜的衣服"],
                        ["冬天保暖的厚卫衣"],
                        ["上班穿的商务衬衫"],
                        ["去海边度假拍照好看的"],
                        ["宽松oversize潮牌"],
                    ],
                    inputs=query_input,
                    label="💡 试试这些查询",
                )

                search_btn.click(
                    fn=search_clothes,
                    inputs=[query_input, top_n_slider],
                    outputs=[gallery, details_html],
                    show_progress="minimal",
                )
                query_input.submit(
                    fn=search_clothes,
                    inputs=[query_input, top_n_slider],
                    outputs=[gallery, details_html],
                    show_progress="minimal",
                )

            # ============ Tab 2: 数据总览 ============
            with gr.Tab("📊 数据总览", id="stats"):
                gr.Markdown("### 数据源管理")
                with gr.Row():
                    analysis_dir_dropdown = gr.Dropdown(
                        choices=get_analysis_dirs(),
                        label="选择分析数据目录",
                        interactive=True,
                        scale=3,
                    )
                    load_btn = gr.Button("📥 加载数据", variant="primary", scale=1)
                load_status = gr.Textbox(label="状态", interactive=False, max_lines=1)

                load_btn.click(fn=load_retriever, inputs=analysis_dir_dropdown, outputs=load_status)

                gr.Markdown("---")
                stats_html = gr.HTML()
                refresh_btn = gr.Button("🔄 刷新统计", variant="secondary")
                refresh_btn.click(fn=get_stats_html, outputs=stats_html)
                app.load(fn=get_stats_html, outputs=stats_html)

            # ============ Tab 3: 配置管理 ============
            with gr.Tab("⚙️ 配置管理", id="config"):
                gr.Markdown("### 当前生效配置")
                config_summary = gr.HTML(get_current_config_summary())

                gr.Markdown("### 编辑 config.yaml")
                gr.Markdown("*修改后点击保存，重启应用生效。优先级：环境变量 > config.yaml > 默认值*")
                config_editor = gr.Code(
                    value=get_config_text(),
                    language="yaml",
                    label="config.yaml",
                    lines=25,
                )
                with gr.Row():
                    save_config_btn = gr.Button("💾 保存配置", variant="primary")
                    save_status = gr.Textbox(label="", interactive=False, show_label=False, max_lines=1)
                save_config_btn.click(fn=save_config_text, inputs=config_editor, outputs=save_status)

            # ============ Tab 4: 项目介绍 ============
            with gr.Tab("📖 项目介绍", id="about"):
                gr.HTML("""
                <div style="max-width:900px; margin:0 auto; padding:20px;">

                <h2 style="text-align:center; color:#1a1a2e; margin-bottom:32px;">ClothWorkFlow — 服装智能工作流</h2>

                <div style="display:grid; grid-template-columns:repeat(3, 1fr); gap:16px; margin-bottom:32px;">
                    <div style="background:linear-gradient(135deg,#667eea,#764ba2); color:#fff; padding:24px; border-radius:16px; text-align:center;">
                        <div style="font-size:32px; margin-bottom:8px;">🕷️</div>
                        <div style="font-size:18px; font-weight:700; margin-bottom:4px;">Step 1: 爬取</div>
                        <div style="font-size:13px; opacity:0.9;">browser-use + Bedrock Claude<br>自动化浏览器爬取 1688</div>
                    </div>
                    <div style="background:linear-gradient(135deg,#f093fb,#f5576c); color:#fff; padding:24px; border-radius:16px; text-align:center;">
                        <div style="font-size:32px; margin-bottom:8px;">🧠</div>
                        <div style="font-size:18px; font-weight:700; margin-bottom:4px;">Step 2: 分析</div>
                        <div style="font-size:13px; opacity:0.9;">Gemini 多模态模型<br>50+ 维度特征提取</div>
                    </div>
                    <div style="background:linear-gradient(135deg,#4facfe,#00f2fe); color:#fff; padding:24px; border-radius:16px; text-align:center;">
                        <div style="font-size:32px; margin-bottom:8px;">🔍</div>
                        <div style="font-size:18px; font-weight:700; margin-bottom:4px;">Step 3: 推荐</div>
                        <div style="font-size:13px; opacity:0.9;">BM25 + BGE-M3 + Reranker<br>混合检索精排</div>
                    </div>
                </div>

                <div style="background:#f8f9fa; border-radius:16px; padding:24px; margin-bottom:24px;">
                    <h3 style="color:#1a1a2e; margin-top:0;">推荐检索原理</h3>
                    <pre style="background:#1a1a2e; color:#4facfe; padding:20px; border-radius:12px; font-size:14px; line-height:1.6; overflow-x:auto;">
用户: "显瘦的夏天裙子"
  ├─ jieba 分词: 显瘦 / 夏天 / 裙子
  ├─ BM25 关键词 → 精确命中"显瘦""裙子"
  ├─ BGE-M3 语义 → 理解 显瘦≈修身/A型/高腰/深色
  ├─ RRF 融合排序
  └─ BGE-Reranker 精排 → Top N</pre>
                </div>

                <div style="background:#f8f9fa; border-radius:16px; padding:24px; margin-bottom:24px;">
                    <h3 style="color:#1a1a2e; margin-top:0;">分析维度 (50+)</h3>
                    <div style="display:grid; grid-template-columns:repeat(2, 1fr); gap:8px;">
                        <div>• <strong>基础信息</strong>: 品类、性别、年龄段、季节、场合</div>
                        <div>• <strong>风格美学</strong>: 主风格、美学调性、潮流相关度</div>
                        <div>• <strong>颜色体系</strong>: 主辅色、配色方案、色温、饱和度</div>
                        <div>• <strong>面料材质</strong>: 面料、克重、质感、垂坠、弹性</div>
                        <div>• <strong>版型结构</strong>: 廓形、版型、领袖腰型</div>
                        <div>• <strong>设计细节</strong>: 图案、装饰、工艺、功能</div>
                        <div>• <strong>体型适配</strong>: 适合体型、修饰效果</div>
                        <div>• <strong>商业信息</strong>: 价格、卖点、搭配建议</div>
                        <div>• <strong>电商文案</strong>: 标题、关键词、描述</div>
                        <div>• <strong>图片信息</strong>: 类型、颜色展示、品牌</div>
                    </div>
                </div>

                <div style="text-align:center; color:#888; font-size:13px; padding-top:16px; border-top:1px solid #eee;">
                    Python 3.13 · Gradio · sentence-transformers · jieba · rank-bm25 · BGE-M3 · BGE-Reranker
                </div>

                </div>
                """)

    return app


def main():
    dirs = get_analysis_dirs()
    if dirs:
        print(f"自动加载分析数据: {dirs[0]}")
        status = load_retriever(dirs[0])
        print(status)

    app = create_app()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
    )


if __name__ == "__main__":
    main()
