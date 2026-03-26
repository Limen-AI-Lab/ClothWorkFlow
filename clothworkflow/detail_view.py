"""
商品详情展示组件

提供 render_product_detail 函数，将分析 JSON 转换为美观的 HTML 展示页面。
"""

from typing import Dict, List, Any, Optional


# 颜色映射字典
COLOR_MAP = {
    "黑色": "#000000",
    "白色": "#FFFFFF",
    "米白": "#F5F5DC",
    "酒红": "#722F37",
    "粉色": "#FFB6C1",
    "亮黄色": "#FFD700",
    "藏青": "#003153",
    "深灰": "#555555",
    "炭灰": "#36454F",
    "墨绿": "#004225",
    "天蓝": "#87CEEB",
    "米色": "#F5F5DC",
    "深棕": "#654321",
    "卡其": "#C3B091",
    "焦糖": "#A0522D",
    "红色": "#FF0000",
    "蓝色": "#0000FF",
    "绿色": "#008000",
    "紫色": "#800080",
    "橙色": "#FFA500",
    "灰色": "#808080",
    "棕色": "#A52A2A",
}


def get_color_hex(color_name: str) -> str:
    """获取颜色对应的十六进制值"""
    return COLOR_MAP.get(color_name, "#CCCCCC")


def render_pill(text: str, bg_color: str = "#E0E7FF", text_color: str = "#4338CA") -> str:
    """渲染 pill 标签"""
    return f'<span style="display: inline-block; padding: 4px 12px; margin: 4px; background-color: {bg_color}; color: {text_color}; border-radius: 16px; font-size: 13px; font-weight: 500;">{text}</span>'


def render_color_block(color_name: str) -> str:
    """渲染颜色名称和色块"""
    hex_color = get_color_hex(color_name)
    border = "1px solid #ddd" if color_name in ["白色", "米白", "米色"] else "none"
    return f'''
    <div style="display: flex; align-items: center; gap: 8px;">
        <div style="width: 24px; height: 24px; background-color: {hex_color}; border-radius: 4px; border: {border};"></div>
        <span style="font-weight: 500;">{color_name}</span>
    </div>
    '''


def render_section_title(title: str, icon: str = "●") -> str:
    """渲染章节标题"""
    return f'''
    <div style="margin-top: 24px; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 2px solid #E5E7EB; display: flex; align-items: center; gap: 8px;">
        <span style="color: #6366F1; font-size: 18px;">{icon}</span>
        <h3 style="margin: 0; font-size: 18px; font-weight: 600; color: #1F2937;">{title}</h3>
    </div>
    '''


def render_info_item(label: str, value: Any) -> str:
    """渲染信息项"""
    if value is None or value == "" or value == []:
        return ""

    if isinstance(value, list):
        value = "、".join(str(v) for v in value)

    return f'''
    <div style="margin-bottom: 12px;">
        <span style="color: #6B7280; font-size: 13px; font-weight: 500;">{label}：</span>
        <span style="color: #1F2937; font-size: 14px;">{value}</span>
    </div>
    '''


def render_highlight_card(content: str, bg_color: str = "#FEF3C7") -> str:
    """渲染高亮卡片"""
    return f'''
    <div style="background-color: {bg_color}; padding: 16px; border-radius: 8px; margin: 12px 0; border-left: 4px solid #F59E0B;">
        <p style="margin: 0; font-size: 14px; color: #92400E; line-height: 1.6;">{content}</p>
    </div>
    '''


def render_quote_card(content: str) -> str:
    """渲染引用样式卡片"""
    return f'''
    <div style="background-color: #F3F4F6; padding: 16px; border-radius: 8px; margin: 12px 0; border-left: 4px solid #6366F1; font-style: italic;">
        <p style="margin: 0; font-size: 15px; color: #374151; line-height: 1.6;">"{content}"</p>
    </div>
    '''


def render_tag_cloud(tags: List[str]) -> str:
    """渲染标签云"""
    if not tags:
        return ""

    colors = [
        ("#DBEAFE", "#1E40AF"),
        ("#FCE7F3", "#9F1239"),
        ("#D1FAE5", "#065F46"),
        ("#FEF3C7", "#92400E"),
        ("#E0E7FF", "#4338CA"),
    ]

    html = '<div style="display: flex; flex-wrap: wrap; gap: 6px; margin: 12px 0;">'
    for i, tag in enumerate(tags):
        bg_color, text_color = colors[i % len(colors)]
        html += render_pill(tag, bg_color, text_color)
    html += '</div>'
    return html


def render_numbered_list(items: List[str]) -> str:
    """渲染编号列表卡片"""
    if not items:
        return ""

    html = '<div style="display: flex; flex-direction: column; gap: 12px; margin: 12px 0;">'
    for i, item in enumerate(items, 1):
        html += f'''
        <div style="display: flex; gap: 12px; padding: 12px; background-color: #F9FAFB; border-radius: 8px; border: 1px solid #E5E7EB;">
            <div style="flex-shrink: 0; width: 24px; height: 24px; background-color: #6366F1; color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 600;">{i}</div>
            <div style="flex: 1; color: #374151; font-size: 14px; line-height: 1.5;">{item}</div>
        </div>
        '''
    html += '</div>'
    return html


def render_bar_chart(label: str, value: float, max_value: float = 1.0, color: str = "#6366F1") -> str:
    """渲染条形图"""
    percentage = min(100, (value / max_value) * 100)
    return f'''
    <div style="margin-bottom: 16px;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
            <span style="font-size: 13px; color: #6B7280; font-weight: 500;">{label}</span>
            <span style="font-size: 13px; color: #1F2937; font-weight: 600;">{value:.3f}</span>
        </div>
        <div style="width: 100%; height: 8px; background-color: #E5E7EB; border-radius: 4px; overflow: hidden;">
            <div style="width: {percentage}%; height: 100%; background-color: {color}; transition: width 0.3s ease;"></div>
        </div>
    </div>
    '''


def render_body_type_icons(body_types: List[str]) -> str:
    """渲染体型图标展示"""
    if not body_types:
        return ""

    body_type_icons = {
        "梨形": "🍐",
        "苹果形": "🍎",
        "沙漏形": "⏳",
        "直筒型": "📏",
        "倒三角": "🔻",
    }

    html = '<div style="display: flex; flex-wrap: wrap; gap: 12px; margin: 12px 0;">'
    for body_type in body_types:
        icon = body_type_icons.get(body_type, "👤")
        html += f'''
        <div style="display: flex; flex-direction: column; align-items: center; padding: 12px 16px; background-color: #F0FDF4; border: 2px solid #86EFAC; border-radius: 8px; min-width: 80px;">
            <div style="font-size: 28px; margin-bottom: 4px;">{icon}</div>
            <div style="font-size: 13px; color: #166534; font-weight: 600;">{body_type}</div>
        </div>
        '''
    html += '</div>'
    return html


def render_product_detail(analysis_json: Dict[str, Any]) -> str:
    """
    将分析 JSON 渲染为美观的 HTML 展示页面

    Args:
        analysis_json: 商品分析结果 JSON

    Returns:
        HTML 字符串
    """
    basic_info = analysis_json.get("basic_info", {})
    style = analysis_json.get("style", {})
    colors = analysis_json.get("colors", {})
    material = analysis_json.get("material", {})
    construction = analysis_json.get("construction", {})
    design_details = analysis_json.get("design_details", {})
    visual = analysis_json.get("visual_impression", {})
    body = analysis_json.get("body_compatibility", {})
    commercial = analysis_json.get("commercial", {})
    ecommerce = analysis_json.get("ecommerce", {})
    meta = analysis_json.get("_meta", {})

    # 构建 HTML
    html = f'''
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; max-width: 100%; margin: 0 auto; padding: 24px; background-color: #FFFFFF; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">

        <!-- 头部区域 -->
        <div style="margin-bottom: 24px;">
            <h1 style="font-size: 26px; font-weight: 700; color: #111827; margin: 0 0 16px 0; line-height: 1.3;">
                {ecommerce.get("title", "商品详情")}
            </h1>
            <div style="display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 12px;">
                {render_pill(basic_info.get("category", ""), "#DBEAFE", "#1E40AF")}
                {render_pill(basic_info.get("gender", ""), "#FCE7F3", "#9F1239")}
                {render_pill(style.get("primary_style", ""), "#FEF3C7", "#92400E")}
                {''.join([render_pill(s, "#E0E7FF", "#4338CA") for s in style.get("secondary_styles", [])])}
            </div>
            <div>
                {render_pill(commercial.get("price_tier", ""), "#D1FAE5", "#065F46")}
            </div>
        </div>
    '''

    # 核心属性网格
    html += render_section_title("核心属性", "📋")
    html += '''
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-bottom: 16px;">
        <div style="padding: 16px; background-color: #F9FAFB; border-radius: 8px; border: 1px solid #E5E7EB;">
    '''

    # 左列
    primary_color = colors.get("primary_color", "")
    if primary_color:
        html += '<div style="margin-bottom: 16px;"><span style="color: #6B7280; font-size: 13px; font-weight: 500;">主色调：</span><div style="margin-top: 6px;">'
        html += render_color_block(primary_color)
        html += '</div></div>'

    html += render_info_item("色彩方案", colors.get("color_scheme", ""))

    # 面料信息
    fabric_info = material.get("primary_fabric", "")
    if material.get("fabric_blend"):
        fabric_info += f" ({material.get('fabric_blend')})"
    if fabric_info:
        html += render_info_item("面料", fabric_info)
    html += render_info_item("克重", material.get("fabric_weight", ""))
    html += render_info_item("质感", material.get("texture", ""))

    # 版型信息
    fit_info = ""
    if construction.get("silhouette"):
        fit_info += construction.get("silhouette")
    if construction.get("fit"):
        fit_info += " / " + construction.get("fit") if fit_info else construction.get("fit")
    if construction.get("length"):
        fit_info += " / " + construction.get("length") if fit_info else construction.get("length")
    html += render_info_item("版型", fit_info)

    html += '</div>'

    # 右列
    html += '<div style="padding: 16px; background-color: #F9FAFB; border-radius: 8px; border: 1px solid #E5E7EB;">'

    html += render_info_item("领型", construction.get("neckline", ""))
    html += render_info_item("袖型", construction.get("sleeve_type", ""))
    html += render_info_item("腰线", construction.get("waistline", ""))
    html += render_info_item("图案", design_details.get("pattern_type", ""))

    decorations = design_details.get("decorations", [])
    if decorations:
        html += render_info_item("装饰", "、".join(decorations))

    craft = design_details.get("craft_techniques", [])
    if craft:
        html += render_info_item("工艺", "、".join(craft))

    html += '</div></div>'

    # 设计亮点
    if visual.get("overall_feel") or visual.get("design_highlight"):
        html += render_section_title("设计亮点", "✨")

        if visual.get("overall_feel"):
            html += render_quote_card(visual.get("overall_feel"))

        if visual.get("design_highlight"):
            html += render_highlight_card(visual.get("design_highlight"))

    # 体型适配
    if body.get("suitable_body_types") or body.get("flattering_features"):
        html += render_section_title("体型适配", "👥")

        if body.get("suitable_body_types"):
            html += '<div style="margin-bottom: 12px;"><span style="color: #6B7280; font-size: 13px; font-weight: 500;">适合体型：</span></div>'
            html += render_body_type_icons(body.get("suitable_body_types"))

        if body.get("flattering_features"):
            html += '<div style="margin-top: 16px; padding: 12px; background-color: #FFF7ED; border-radius: 8px; border: 1px solid #FDBA74;">'
            html += f'<div style="color: #9A3412; font-size: 14px; line-height: 1.6;"><strong>修饰效果：</strong>{body.get("flattering_features")}</div>'
            html += '</div>'

    # 搭配建议
    coordination = commercial.get("coordination_suggestions", [])
    if coordination:
        html += render_section_title("搭配建议", "👗")
        html += render_numbered_list(coordination)

    # 电商信息
    html += render_section_title("电商信息", "🛍️")

    # 搜索关键词
    keywords = ecommerce.get("search_keywords", [])
    if keywords:
        html += '<div style="margin-bottom: 16px;"><span style="color: #6B7280; font-size: 13px; font-weight: 500; display: block; margin-bottom: 8px;">搜索关键词：</span>'
        html += render_tag_cloud(keywords)
        html += '</div>'

    # Hashtags
    hashtags = ecommerce.get("hashtags", [])
    if hashtags:
        html += '<div style="margin-bottom: 16px;"><span style="color: #6B7280; font-size: 13px; font-weight: 500; display: block; margin-bottom: 8px;">话题标签：</span>'
        html += '<div style="display: flex; flex-wrap: wrap; gap: 8px;">'
        for tag in hashtags:
            html += f'<span style="color: #6366F1; font-size: 13px; font-weight: 500;">{tag}</span>'
        html += '</div></div>'

    # 商品描述
    description = ecommerce.get("description", "")
    if description:
        html += '<div style="margin-bottom: 16px;"><span style="color: #6B7280; font-size: 13px; font-weight: 500; display: block; margin-bottom: 8px;">商品描述：</span>'
        html += f'<div style="padding: 12px; background-color: #F9FAFB; border-radius: 8px; border: 1px solid #E5E7EB; color: #374151; font-size: 14px; line-height: 1.6;">{description}</div>'
        html += '</div>'

    # 卖点
    selling_points = commercial.get("selling_points", [])
    if selling_points:
        html += '<div style="margin-bottom: 16px;"><span style="color: #6B7280; font-size: 13px; font-weight: 500; display: block; margin-bottom: 8px;">核心卖点：</span>'
        html += '<ul style="margin: 0; padding-left: 20px; color: #374151; font-size: 14px; line-height: 1.8;">'
        for point in selling_points:
            html += f'<li>{point}</li>'
        html += '</ul></div>'

    # 分数展示（如果有）
    if meta:
        scores = []
        if "reranker_score" in meta:
            scores.append(("Reranker 分数", meta["reranker_score"], "#6366F1"))
        if "vector_similarity" in meta:
            scores.append(("向量相似度", meta["vector_similarity"], "#10B981"))
        if "bm25_score" in meta:
            scores.append(("BM25 分数", meta["bm25_score"], "#F59E0B"))

        if scores:
            html += render_section_title("相关性评分", "📊")
            html += '<div style="padding: 16px; background-color: #F9FAFB; border-radius: 8px; border: 1px solid #E5E7EB;">'

            # 找出最大值用于归一化
            max_score = max(score[1] for score in scores if score[1] is not None)
            if max_score == 0:
                max_score = 1.0

            for label, value, color in scores:
                if value is not None:
                    html += render_bar_chart(label, value, max_score, color)

            html += '</div>'

    # 技术信息
    if meta.get("model") or meta.get("image"):
        html += render_section_title("技术信息", "⚙️")
        html += '<div style="padding: 12px; background-color: #F9FAFB; border-radius: 8px; border: 1px solid #E5E7EB; font-size: 12px; color: #6B7280;">'

        if meta.get("model"):
            html += f'<div style="margin-bottom: 6px;"><strong>分析模型：</strong>{meta.get("model")}</div>'
        if meta.get("image"):
            html += f'<div style="margin-bottom: 6px;"><strong>图片路径：</strong>{meta.get("image")}</div>'
        if meta.get("prompt_tokens"):
            html += f'<div style="margin-bottom: 6px;"><strong>Prompt Tokens：</strong>{meta.get("prompt_tokens"):,}</div>'
        if meta.get("completion_tokens"):
            html += f'<div><strong>Completion Tokens：</strong>{meta.get("completion_tokens"):,}</div>'

        html += '</div>'

    html += '</div>'

    return html
