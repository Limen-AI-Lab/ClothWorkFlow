"""用 Gemini 解析搜索意图：单品 vs 搭配，搭配时拆成多条检索 query。"""

import json
import os
import re
import time
from typing import Any

import httpx

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"

DEFAULT_INTENT_MODEL = os.getenv("GEMINI_SEARCH_INTENT_MODEL", "gemini-3-flash-preview")

SYSTEM_INSTRUCTION = """你是服装电商检索助手。根据用户中文需求判断检索模式，只输出一个 JSON 对象（不要 markdown 围栏）。

规则：
1. mode 为 "single"：用户只要一件单品、明确某一类衣服、或明显针对单品。
2. mode 为 "outfit"：用户要搭配、整套、场景穿搭、怎么配、穿什么好看等多件组合。
3. single：必须填 single_query，一条精炼中文检索句，保留风格/颜色/场景/性别等。
4. outfit：必须填 slots 数组。通常含上装+下装两条；若用户明确连衣裙/套装一件式，可只含 role 为 dress 的一条。
5. 每个 slot：role 只能是 top、bottom、dress；query 为该件的检索短句，继承用户的风格/颜色/场合。
6. reason：一句简短中文说明判断依据。

JSON 字段：mode, reason, single_query（single 时）, slots（outfit 时，每项含 role, query）。

示例：
{"mode":"single","reason":"只要上衣","single_query":"男款藏青色商务休闲长袖衬衫"}
{"mode":"outfit","reason":"整套通勤","slots":[{"role":"top","query":"女 米色宽松针织开衫 通勤"},{"role":"bottom","query":"女 深蓝直筒牛仔长裤"}]}
"""


def category_bucket(category: str) -> str:
    c = (category or "").strip()
    if not c:
        return "top"
    if "连衣裙" in c:
        return "dress"
    if "套装" in c:
        return "dress"
    if "裤" in c:
        return "bottom"
    if "裙" in c:
        return "bottom"
    return "top"


def build_bucket_index(meta_list: list[dict]) -> dict[str, frozenset[int]]:
    buckets: dict[str, set[int]] = {"top": set(), "bottom": set(), "dress": set()}
    for i, m in enumerate(meta_list):
        b = category_bucket(m.get("category", ""))
        buckets[b].add(i)
    return {k: frozenset(v) for k, v in buckets.items()}


def _strip_code_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```\s*$", "", text)
    return text.strip()


def _parse_model_json(text: str) -> dict[str, Any]:
    return json.loads(_strip_code_fence(text))


def _extract_text(data: dict[str, Any]) -> str:
    cands = data.get("candidates") or []
    if not cands:
        raise ValueError("Gemini 无候选回复")
    parts = (cands[0].get("content") or {}).get("parts") or []
    if not parts or "text" not in parts[0]:
        raise ValueError("Gemini 回复缺少文本")
    return parts[0]["text"]


def gemini_classify_search_intent(
    user_query: str,
    api_key: str,
    *,
    model: str | None = None,
    timeout_s: float = 45.0,
) -> tuple[dict[str, Any], int]:
    """
    调用 Gemini，返回 (解析后的意图 dict, 耗时毫秒)。
    意图 dict 经规范化，含 mode、reason、single_query 或 slots。
    """
    model = model or DEFAULT_INTENT_MODEL
    url = f"{GEMINI_API_BASE}/models/{model}:generateContent"
    t0 = time.time()
    with httpx.Client(timeout=timeout_s) as client:
        r = client.post(
            url,
            params={"key": api_key},
            json={
                "systemInstruction": {"parts": [{"text": SYSTEM_INSTRUCTION}]},
                "contents": [
                    {
                        "role": "user",
                        "parts": [{"text": f"用户需求：\n{user_query.strip()}"}],
                    }
                ],
                "generationConfig": {
                    "temperature": 0.2,
                    "responseMimeType": "application/json",
                },
            },
        )
        r.raise_for_status()
        raw = r.json()
    gemini_ms = int(round((time.time() - t0) * 1000))

    text = _extract_text(raw)
    plan = _parse_model_json(text)
    return normalize_intent_plan(plan, user_query.strip()), gemini_ms


def normalize_intent_plan(plan: dict[str, Any], fallback_query: str) -> dict[str, Any]:
    mode = plan.get("mode")
    if mode not in ("single", "outfit"):
        mode = "single"
    reason = plan.get("reason")
    if not isinstance(reason, str):
        reason = ""

    if mode == "single":
        sq = plan.get("single_query")
        if not isinstance(sq, str) or not sq.strip():
            sq = fallback_query
        return {"mode": "single", "reason": reason, "single_query": sq.strip(), "slots": []}

    slots_raw = plan.get("slots")
    slots: list[dict[str, str]] = []
    if isinstance(slots_raw, list):
        for item in slots_raw:
            if not isinstance(item, dict):
                continue
            role = item.get("role")
            q = item.get("query")
            if role not in ("top", "bottom", "dress"):
                continue
            if not isinstance(q, str) or not q.strip():
                continue
            slots.append({"role": role, "query": q.strip()})

    if not slots:
        return {
            "mode": "single",
            "reason": reason or "搭配解析为空，按单品检索",
            "single_query": fallback_query,
            "slots": [],
        }

    return {"mode": "outfit", "reason": reason, "single_query": "", "slots": slots}


ROLE_TO_BUCKET = {"top": "top", "bottom": "bottom", "dress": "dress"}

SLOT_LABEL_ZH = {"top": "上装", "bottom": "下装", "dress": "连衣裙/套装"}
