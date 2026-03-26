"""Gemini 多模态服装图片分析"""

import base64
import json
import mimetypes
from pathlib import Path

import httpx

from .config import OPENROUTER_API_URL, DEFAULT_ANALYSIS_MODEL, ANALYZE_MAX_TOKENS, ANALYZE_TEMPERATURE

# 50+ 维度分析 Prompt
CLOTHING_ANALYSIS_PROMPT = """你是一位拥有20年经验的资深服装行业分析师，精通面料工艺、版型设计、时尚趋势和电商运营。
请对这张服装商品图片进行全方位深度分析。

请严格按照以下 JSON 格式输出，不要输出任何其他内容：

{
  "basic_info": {
    "category": "服装大类（连衣裙/T恤/衬衫/卫衣/夹克/西装/大衣/风衣/羽绒服/毛衣/针织衫/polo衫/背心/裤子/半裙/套装/连体裤等）",
    "subcategory": "细分品类（如：A字连衣裙、机车夹克、阔腿裤、百褶裙、工装裤等）",
    "gender": "目标性别（男装/女装/中性）",
    "age_range": "适合年龄段（如：18-25/25-35/35-45/全年龄）",
    "season": ["适合季节列表，如：春、夏"],
    "occasion": ["适用场合列表（日常通勤/休闲逛街/约会/派对/运动/海滩度假/正式商务/居家/校园/户外等）"]
  },

  "style": {
    "primary_style": "主要风格（街头/休闲/商务/复古/韩系/欧美/甜美/暗黑/工装/学院/极简/运动/波西米亚/朋克/哥特/新中式等）",
    "secondary_styles": ["次要风格标签列表"],
    "aesthetic": "美学调性（如：Y2K、老钱风、静奢、多巴胺、美拉德、新中式、辣妹风等当下流行美学，无明显则填 null）",
    "trend_relevance": "潮流相关度描述（如：2024秋冬流行的美拉德色系、经典百搭款不受潮流影响等）"
  },

  "colors": {
    "primary_color": "主色（具体色名：黑色/白色/米白/奶白/藏青/深灰/炭灰/酒红/砖红/玫红/粉色/裸粉/雾蓝/天蓝/墨绿/卡其/焦糖/驼色等）",
    "secondary_colors": ["辅色列表，无则空列表"],
    "color_scheme": "配色方案（纯色/撞色/渐变/拼色/同色系深浅等）",
    "color_temperature": "色温（暖色调/冷色调/中性色调）",
    "color_saturation": "饱和度（高饱和鲜艳/中等/低饱和莫兰迪/无彩色）",
    "color_season": "适合的个人色彩季型（春暖/夏冷/秋暖/冬冷/百搭）"
  },

  "material": {
    "primary_fabric": "主要面料（纯棉/精梳棉/有机棉/涤纶/锦纶/氨纶/真丝/醋酸/天丝/莫代尔/亚麻/羊毛/羊绒/牛仔/灯芯绒/丝绒/雪纺/欧根纱/蕾丝/皮革/PU皮/尼龙/摇粒绒等）",
    "fabric_blend": "面料混纺推测（如：棉95%+氨纶5%、涤纶混纺等，不确定填 null）",
    "fabric_weight": "面料克重/厚度（轻薄<150g/中等150-250g/中厚250-350g/厚实>350g）",
    "texture": "质感描述（光滑/磨毛/水洗做旧/肌理感/绒面/哑光/亮面/透明/半透明等）",
    "drape": "垂坠感（硬挺/适中/柔软垂坠/飘逸）",
    "elasticity": "弹性（无弹/微弹/中弹/高弹）",
    "transparency": "透明度（不透/微透/半透/透明）",
    "hand_feel_guess": "触感推测（柔软亲肤/顺滑冰凉/粗犷硬朗/蓬松保暖等）"
  },

  "construction": {
    "silhouette": "廓形（A型/H型/X型/O型/茧型/修身直筒/伞形/斗篷型等）",
    "fit": "版型（紧身/修身/合身/常规/宽松/oversized/落肩等）",
    "length": "衣长（超短/短款/常规/中长/长款/超长及踝）",
    "neckline": "领型（圆领/V领/U领/方领/翻领/立领/高领/堆堆领/吊带/挂脖/一字肩/抹胸/西装领/连帽/polo领等，不适用填 null）",
    "sleeve_type": "袖型（无袖/飞袖/泡泡袖/灯笼袖/喇叭袖/插肩袖/蝙蝠袖/公主袖/荷叶袖/短袖/五分袖/七分袖/长袖等，不适用填 null）",
    "waistline": "腰线（高腰/中腰/低腰/无腰线/松紧腰/系带收腰等，不适用填 null）",
    "hem": "下摆设计（平摆/弧形摆/荷叶边/开叉/不规则/收口/毛边等）",
    "back_design": "背部设计（常规/露背/镂空/蝴蝶结系带/拉链等，无特殊填 null）",
    "closure": "开合方式（套头/前拉链/侧拉链/前纽扣/暗扣/系带/粘扣/无等）"
  },

  "design_details": {
    "pattern_type": "图案类型（纯色/格纹/条纹/波点/碎花/印花/扎染/迷彩/豹纹/字母logo/卡通/抽象/几何/民族风等）",
    "pattern_description": "图案具体描述（如：胸前大幅蝴蝶图案印花、细条纹、小碎花等，纯色填 null）",
    "decorations": ["装饰元素列表（蝴蝶结/蕾丝花边/铆钉/亮片/珠饰/流苏/羽毛/链条/金属扣/刺绣/贴布/织带/毛球等，无则空列表）"],
    "pockets": "口袋（无口袋/贴袋/插袋/暗袋/工装口袋/胸袋等）",
    "stitching": "缝线工艺（常规/明线装饰/双针缝/包缝/锁边等，无明显特征填 null）",
    "craft_techniques": ["工艺技法列表（水洗/做旧/扎染/褶皱/烫金/植绒/数码印花/丝网印/热转印/提花/编织/镂空/烧花/压褶等，无则空列表）"],
    "functional_features": ["功能性设计列表（防晒/速干/吸湿排汗/防风/保暖/可拆卸/两穿/反光条等，无则空列表）"]
  },

  "visual_impression": {
    "overall_feel": "整体视觉感受（一句话，如：干净利落的都市通勤感、张扬个性的街头暗黑风等）",
    "design_highlight": "最大设计亮点（如：胸前立体花朵装饰、独特的不对称剪裁等）",
    "visual_weight": "视觉重量感（轻盈/适中/厚重/量感强）"
  },

  "body_compatibility": {
    "suitable_body_types": ["适合体型列表（梨形/苹果形/沙漏形/直筒型/倒三角等）"],
    "flattering_features": "修饰优点（如：高腰线拉长腿部比例、A字裙遮胯显瘦等）",
    "size_range_guess": "尺码范围推测（S-XL/均码/大码友好等）"
  },

  "commercial": {
    "price_tier": "价格定位（白菜价<50/平价50-150/中端150-500/中高端500-1500/高端>1500，单位人民币）",
    "target_audience": "核心目标客群（如：20-30岁追求个性的都市青年男性）",
    "selling_points": ["3-5个核心卖点列表（如：280g重磅纯棉、水洗做旧工艺、宽松不挑身材等）"],
    "similar_brands_style": "相似品牌风格参考（如：类似Zara基础款风格、偏向Supreme街头风等）",
    "coordination_suggestions": ["3条搭配建议（如：搭配高腰阔腿裤+帆布鞋打造休闲look）"]
  },

  "ecommerce": {
    "title": "电商标题（25-40字，包含核心属性关键词，如：2024秋季新款水洗做旧蝴蝶印花重磅纯棉圆领长袖卫衣男）",
    "search_keywords": ["8-12个电商搜索关键词"],
    "hashtags": ["5-8个社交媒体标签（如：#街头风、#oversize、#水洗做旧等）"],
    "description": "商品详情描述（80-120字，突出面料、工艺、设计亮点和穿着场景）"
  },

  "image_info": {
    "image_type": "图片类型（模特上身图/平铺图/挂拍图/多角度展示/细节图/多色展示等）",
    "available_colors_shown": ["图片中展示的可选颜色列表，只有一个颜色则只填一个"],
    "has_size_info": "图片中是否包含尺码信息（true/false）",
    "has_fabric_info": "图片中是否包含面料信息文字（true/false）",
    "brand_visible": "可见的品牌名称（无则填 null）"
  }
}

分析要求：
- 只分析图片中的服装本身，忽略模特的容貌和体型特征
- 充分利用图片中可见的文字信息（如克重、面料标注等）
- 如果图片中展示了多个颜色的同款，在 available_colors_shown 中全部列出
- 如果图片中有多件服装（如套装），分析整套；如果是不相关的多件，分析最突出的那件
- 如果某个字段确实无法从图片判断，填 null
- 必须输出合法 JSON，不要添加 markdown 代码块标记"""


def encode_image_base64(image_path: Path) -> tuple[str, str]:
    mime_type = mimetypes.guess_type(str(image_path))[0] or "image/jpeg"
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    return b64, mime_type


def analyze_single_image(
    image_path: Path,
    api_key: str,
    model: str = DEFAULT_ANALYSIS_MODEL,
    timeout: int = 120,
) -> dict:
    """调用 OpenRouter Gemini 分析单张服装图片，返回结构化 JSON"""
    b64, mime_type = encode_image_base64(image_path)

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": CLOTHING_ANALYSIS_PROMPT},
                    {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{b64}"}},
                ],
            }
        ],
        "max_tokens": ANALYZE_MAX_TOKENS,
        "temperature": ANALYZE_TEMPERATURE,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    with httpx.Client(timeout=timeout) as client:
        resp = client.post(OPENROUTER_API_URL, headers=headers, json=payload)
        resp.raise_for_status()

    data = resp.json()
    if "error" in data:
        raise RuntimeError(f"API 错误: {data['error']}")

    content = data["choices"][0]["message"]["content"].strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[1] if "\n" in content else content[3:]
    if content.endswith("```"):
        content = content[:-3]
    content = content.strip()

    try:
        result = json.loads(content)
    except json.JSONDecodeError:
        result = {"raw_response": content, "_parse_error": True}

    usage = data.get("usage", {})
    result["_meta"] = {
        "image": str(image_path),
        "model": model,
        "prompt_tokens": usage.get("prompt_tokens"),
        "completion_tokens": usage.get("completion_tokens"),
    }
    return result


def collect_images(path: Path, recursive: bool = False) -> list[Path]:
    """收集目录下的图片文件"""
    extensions = {".jpg", ".jpeg", ".png", ".webp"}
    if path.is_file():
        return [path] if path.suffix.lower() in extensions else []
    pattern = "**/*" if recursive else "*"
    return [f for f in sorted(path.glob(pattern)) if f.is_file() and f.suffix.lower() in extensions]
