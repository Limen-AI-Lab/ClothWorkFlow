"""语义文本生成 + jieba 中文分词"""

import re

# ============ jieba 分词（服装领域） ============

_JIEBA_INITIALIZED = False

_CUSTOM_WORDS = [
    "连衣裙", "半裙", "A字裙", "百褶裙", "鱼尾裙", "直筒裤", "阔腿裤", "工装裤",
    "卫衣", "T恤", "polo衫", "针织衫", "马甲", "风衣", "羽绒服", "牛仔裤",
    "oversized", "修身", "宽松", "高腰", "低腰", "中腰", "落肩",
    "V领", "圆领", "翻领", "立领", "一字肩", "吊带", "挂脖", "抹胸",
    "显瘦", "显高", "遮肉", "收腰", "拉长", "修饰",
    "街头", "韩系", "欧美", "复古", "甜美", "暗黑", "波西米亚", "极简",
    "Y2K", "多巴胺", "美拉德", "老钱风", "静奢", "辣妹风", "新中式",
    "纯棉", "涤纶", "雪纺", "蕾丝", "丝绒", "亚麻", "真丝", "牛仔",
    "水洗做旧", "磨毛", "印花", "刺绣", "扎染", "提花",
    "梨形", "苹果形", "沙漏形", "倒三角",
    "日常通勤", "休闲逛街", "海滩度假", "正式商务",
]

_STOP_WORDS = {
    "的", "了", "是", "在", "和", "有", "与", "等", "为", "一", "不",
    "也", "就", "都", "而", "及", "这", "那", "你", "我", "他", "她",
    "它", "们", "着", "把", "被", "到", "从", "让", "给", "上", "下",
    "中", "很", "会", "能", "要", "可以", "可", "比较", "非常", "适合",
    "什么", "怎么", "哪", "想", "想要", "需要", "找", "一件", "一条", "一个",
}


def tokenize_chinese(text: str) -> list[str]:
    """jieba 分词，带服装领域自定义词典 + 停用词过滤"""
    import jieba

    global _JIEBA_INITIALIZED
    if not _JIEBA_INITIALIZED:
        for w in _CUSTOM_WORDS:
            jieba.add_word(w)
        _JIEBA_INITIALIZED = True

    words = jieba.lcut(text)
    return [w.strip() for w in words if w.strip() and len(w.strip()) > 1 and w.strip() not in _STOP_WORDS]


# ============ 语义文本生成 ============

def _safe(d: dict, key: str) -> str | None:
    """安全取值，null 字符串视为 None"""
    v = d.get(key)
    if v is None or v == "null":
        return None
    return str(v)


def analysis_to_semantic_text(item: dict) -> str:
    """将结构化分析 JSON 转为语义丰富的自然语言段落"""
    parts = []

    basic = item.get("basic_info", {})
    if _safe(basic, "category"):
        parts.append(f"这是一件{basic.get('gender', '')}{basic['category']}，细分品类{basic.get('subcategory', '')}。")
    if _safe(basic, "age_range"):
        parts.append(f"适合{basic['age_range']}岁。")
    seasons = basic.get("season", [])
    if seasons:
        parts.append(f"适合{'、'.join(seasons)}季。")
    occasions = basic.get("occasion", [])
    if occasions:
        parts.append(f"场合：{'、'.join(occasions)}。")

    style = item.get("style", {})
    ps = _safe(style, "primary_style")
    if ps:
        s = f"风格{ps}"
        ss = style.get("secondary_styles", [])
        if ss:
            s += f"，兼具{'、'.join(ss)}"
        parts.append(s + "。")
    if _safe(style, "aesthetic"):
        parts.append(f"美学：{style['aesthetic']}。")
    if _safe(style, "trend_relevance"):
        parts.append(f"潮流：{style['trend_relevance']}。")

    colors = item.get("colors", {})
    if _safe(colors, "primary_color"):
        c = f"颜色{colors['primary_color']}"
        sc = colors.get("secondary_colors", [])
        if sc:
            c += f"搭配{'、'.join(sc)}"
        if _safe(colors, "color_scheme"):
            c += f"，{colors['color_scheme']}"
        parts.append(c + "。")
    ct = _safe(colors, "color_temperature")
    cs = _safe(colors, "color_saturation")
    if ct:
        parts.append(f"{ct}，{cs or ''}。")

    material = item.get("material", {})
    if _safe(material, "primary_fabric"):
        m = f"面料{material['primary_fabric']}"
        if _safe(material, "fabric_weight"):
            m += f"，{material['fabric_weight']}"
        parts.append(m + "。")
    mat_d = []
    for label, key in [("质感", "texture"), ("垂坠", "drape"), ("弹性", "elasticity"), ("触感", "hand_feel_guess")]:
        if _safe(material, key):
            mat_d.append(f"{label}{material[key]}")
    if mat_d:
        parts.append("、".join(mat_d) + "。")

    construction = item.get("construction", {})
    con = []
    for key, label in [("silhouette", "廓形"), ("fit", "版型"), ("length", "衣长")]:
        if _safe(construction, key):
            con.append(f"{label}{construction[key]}")
    if con:
        parts.append("、".join(con) + "。")
    det = []
    for key, label in [("neckline", "领型"), ("sleeve_type", "袖型"), ("waistline", "腰线"),
                       ("hem", "下摆"), ("back_design", "背部"), ("closure", "开合")]:
        if _safe(construction, key):
            det.append(f"{label}{construction[key]}")
    if det:
        parts.append("、".join(det) + "。")

    details = item.get("design_details", {})
    pt = _safe(details, "pattern_type")
    if pt and pt != "纯色":
        d = f"图案{pt}"
        if _safe(details, "pattern_description"):
            d += f"（{details['pattern_description']}）"
        parts.append(d + "。")
    for key, label in [("decorations", "装饰"), ("craft_techniques", "工艺"), ("functional_features", "功能")]:
        vals = details.get(key, [])
        if vals:
            parts.append(f"{label}：{'、'.join(vals)}。")

    visual = item.get("visual_impression", {})
    for key in ("overall_feel", "design_highlight"):
        v = _safe(visual, key)
        if v:
            parts.append(v + ("。" if not v.endswith("。") else ""))

    body = item.get("body_compatibility", {})
    bt = body.get("suitable_body_types", [])
    if bt:
        parts.append(f"适合{'、'.join(bt)}体型。")
    if _safe(body, "flattering_features"):
        parts.append(f"修饰效果：{body['flattering_features']}。")

    commercial = item.get("commercial", {})
    if _safe(commercial, "price_tier"):
        parts.append(f"价格{commercial['price_tier']}。")
    sp = commercial.get("selling_points", [])
    if sp:
        parts.append(f"卖点：{'；'.join(sp)}。")
    coord = commercial.get("coordination_suggestions", [])
    if coord:
        parts.append(f"搭配：{'；'.join(coord)}。")

    ecom = item.get("ecommerce", {})
    if _safe(ecom, "title"):
        parts.append(f"标题：{ecom['title']}。")
    if _safe(ecom, "description"):
        parts.append(ecom["description"])
    kw = ecom.get("search_keywords", [])
    if kw:
        parts.append(f"关键词：{'、'.join(kw)}。")

    return "\n".join(parts)


def analysis_to_bm25_tokens(item: dict) -> list[str]:
    """将分析结果转为 jieba 分词后的 token 列表，供 BM25 使用"""
    text_parts = []

    for section_key, fields in [
        ("basic_info", ["category", "subcategory", "gender"]),
        ("style", ["primary_style", "aesthetic"]),
        ("colors", ["primary_color", "color_scheme", "color_temperature", "color_saturation"]),
        ("material", ["primary_fabric", "fabric_weight", "texture", "drape", "elasticity", "hand_feel_guess"]),
        ("construction", ["silhouette", "fit", "length", "neckline", "sleeve_type", "waistline", "hem", "closure"]),
        ("visual_impression", ["overall_feel", "design_highlight"]),
        ("commercial", ["price_tier"]),
    ]:
        section = item.get(section_key, {})
        for f in fields:
            v = _safe(section, f)
            if v:
                text_parts.append(v)

    # 列表字段
    for section_key, list_fields in [
        ("basic_info", ["season", "occasion"]),
        ("style", ["secondary_styles"]),
        ("colors", ["secondary_colors"]),
        ("design_details", ["decorations", "craft_techniques", "functional_features"]),
        ("body_compatibility", ["suitable_body_types"]),
        ("commercial", ["selling_points"]),
        ("ecommerce", ["search_keywords"]),
    ]:
        section = item.get(section_key, {})
        for f in list_fields:
            text_parts.extend(section.get(f, []))

    # 单独处理
    v = _safe(item.get("body_compatibility", {}), "flattering_features")
    if v:
        text_parts.append(v)
    v = _safe(item.get("ecommerce", {}), "title")
    if v:
        text_parts.append(v)
    v = _safe(item.get("design_details", {}), "pattern_description")
    if v:
        text_parts.append(v)

    return tokenize_chinese(" ".join(text_parts))
