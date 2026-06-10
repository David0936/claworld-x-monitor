"""
AI 层：翻译 + 中文摘要标题 + 财经解读。支持两种供应商，设置里可切换：
  - claude  : Anthropic Messages API（质量高，财经分析向）
  - openai  : OpenAI 兼容接口（默认通义千问 qwen-plus，便宜、国内直连）

对外只暴露 process_tweet(config, text) -> {title, zh, en, analysis}。
"""
import json
import re
import time

import requests

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"


def _claude(config, prompt, system, max_tokens):
    key = (config.get("CLAUDE_API_KEY") or "").strip()
    model = config.get("CLAUDE_MODEL") or "claude-opus-4-8"
    if not key:
        raise RuntimeError("缺少 CLAUDE_API_KEY")
    r = requests.post(
        ANTHROPIC_URL,
        headers={
            "x-api-key": key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": model,
            "max_tokens": max_tokens,
            "thinking": {"type": "disabled"},
            "system": system,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=40,
    )
    r.raise_for_status()
    data = r.json()
    for b in data.get("content", []):
        if b.get("type") == "text":
            return b["text"]
    return ""


def _openai(config, prompt, system, max_tokens):
    from openai import OpenAI  # 延迟导入，未装也不影响 claude 路径

    key = (config.get("LLM_API_KEY") or "").strip()
    url = config.get("LLM_URL") or "https://dashscope.aliyuncs.com/compatible-mode/v1"
    model = config.get("LLM_MODEL") or "qwen-plus"
    if not key:
        raise RuntimeError("缺少 LLM_API_KEY")
    client = OpenAI(api_key=key, base_url=url)
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        max_tokens=max_tokens,
        timeout=40,
    )
    return completion.choices[0].message.content or ""


def ai_complete(config, prompt, system="You are a helpful assistant.", max_tokens=1200, retries=3):
    provider = (config.get("AI_PROVIDER") or "openai").lower()
    fn = _claude if provider == "claude" else _openai
    last = ""
    for attempt in range(retries):
        try:
            out = fn(config, prompt, system, max_tokens)
            if out and out.strip():
                return out.strip()
        except Exception as e:
            last = str(e)
            msg = last.lower()
            if "429" in msg or "rate" in msg:
                time.sleep(8)
            elif "timeout" in msg or "timed out" in msg:
                time.sleep(4)
            elif "401" in msg or "invalid api key" in msg or "403" in msg:
                break  # 鉴权错误不重试
            else:
                time.sleep(2)
    return f"[AI 处理失败] {last}"


SYSTEM = (
    "你是财经投研助手。面向中文用户处理推文：中文翻译/清理、一句中文标题、约120-160字财经解读。"
    "保留 $股票代码、六位A股代码、数字、@账号、链接原样。"
    "若提到 A 股上市公司——包括以英文名/别名提及的（例如 LeaderDrive 即“绿的谐波”、代码 688017）——"
    "译文与标题请用其规范中文简称，不要音译生造，并在代码段给出其 6 位 A 股代码；"
    "拿不准的宁可留空，绝不编造代码。客观、不喊单、不做投资建议。"
)

# 用分隔符格式而非 JSON：译文里常含引号/换行，会撑破 JSON 字符串导致截断；分隔符对此免疫。
PROMPT_TMPL = """处理下面这条推文。严格按以下格式输出，每个 ### 标记独占一行，标记之间填对应内容：
###标题###
（中文一句标题）
###代码###
（涉及的 A 股 6 位代码，多个用逗号分隔；没有就留空）
###中文###
（完整中文翻译，保持原意，勿省略）
###解读###
（120-160字财经解读：背景、可能影响、需验证点）

推文：
{text}"""


def _parse_sections(s):
    """解析 ###标题###/###代码###/###中文###/###解读### 分隔格式，内容可含任意引号换行。"""
    keymap = {"标题": "title", "代码": "codes", "中文": "zh", "解读": "analysis"}
    out = {}
    parts = re.split(r"#{2,4}\s*(标题|代码|中文|解读)\s*#{2,4}", s)
    for i in range(1, len(parts) - 1, 2):
        k = keymap.get(parts[i].strip())
        if k:
            out[k] = parts[i + 1].strip()
    return out


def process_tweet(config, text):
    """返回 {title, zh, en, analysis}；失败时降级为原文。"""
    if not text or not text.strip():
        return {"title": "(空推文)", "zh": "", "analysis": "", "ashares": []}
    raw = ai_complete(config, PROMPT_TMPL.format(text=text[:5000]), system=SYSTEM, max_tokens=4000)
    sec = _parse_sections(raw)
    if sec.get("zh") or sec.get("title") or sec.get("analysis"):
        codes = [c for c in re.split(r"[,，\s]+", sec.get("codes", "")) if c.isdigit() and len(c) == 6]
        return {
            "title": (sec.get("title") or text[:40])[:120],
            "zh": sec.get("zh") or "",
            "analysis": sec.get("analysis") or "",
            "ashares": [{"code": c} for c in codes],
        }
    # 实在解析不出：降级为原文，至少不丢信息
    return {"title": text[:40], "zh": text, "analysis": "" if raw.startswith("[AI") else raw, "ashares": []}
