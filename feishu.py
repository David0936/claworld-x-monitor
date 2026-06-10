"""飞书自定义机器人推送（interactive 卡片）。股票命中时红色置顶。"""
import base64
import hashlib
import hmac
import time

import requests


def _sign(timestamp, secret):
    s = f"{timestamp}\n{secret}"
    h = hmac.new(s.encode("utf-8"), b"", hashlib.sha256).digest()
    return base64.b64encode(h).decode("utf-8")


def push_card(webhook, secret, title, lark_md, hit=False, site_url="", button_text="查看后台", template=None):
    """发一张飞书卡片。template 指定头色（如 'purple'）；否则 hit→红、普通→蓝。返回 (ok, info)。"""
    if not webhook:
        return False, "未配置 FEISHU_WEBHOOK"
    elements = [{"tag": "div", "text": {"tag": "lark_md", "content": lark_md}}]
    if site_url:
        elements.append({"tag": "hr"})
        elements.append({
            "tag": "action",
            "actions": [{
                "tag": "button",
                "text": {"tag": "plain_text", "content": button_text},
                "type": "primary",
                "url": site_url,
            }],
        })
    card = {
        "msg_type": "interactive",
        "card": {
            "config": {"wide_screen_mode": True},
            "header": {
                "template": template or ("red" if hit else "blue"),
                "title": {"tag": "plain_text", "content": title},
            },
            "elements": elements,
        },
    }
    if secret:
        ts = str(int(time.time()))
        card = {"timestamp": ts, "sign": _sign(ts, secret), **card}
    try:
        r = requests.post(webhook, json=card, timeout=15)
        return r.ok, f"HTTP {r.status_code} {r.text[:120]}"
    except Exception as e:
        return False, str(e)


def bots_from_config(cfg):
    """取飞书机器人列表 [{note,webhook,secret}]；兼容旧的单个 FEISHU_WEBHOOK。"""
    bots = cfg.get("FEISHU_BOTS")
    if isinstance(bots, list) and bots:
        return bots
    if cfg.get("FEISHU_WEBHOOK"):
        return [{"note": "默认", "webhook": cfg["FEISHU_WEBHOOK"], "secret": cfg.get("FEISHU_SECRET", "")}]
    return []


def push_all(bots, title, content, hit=False, site_url="", template=None, author=None):
    """推送到飞书群。bot 的 accounts 限定它只发哪些博主（空=全部）；author 为本条作者。
    返回 [(note, ok, info), ...]。"""
    results = []
    for b in bots or []:
        wh = (b.get("webhook") or "").strip()
        if not wh:
            continue
        accts = b.get("accounts") or []
        if author and accts and author not in accts:
            continue  # 该机器人只发指定博主，本条作者不在其中 → 跳过
        ok, info = push_card(wh, (b.get("secret") or "").strip(), title, content,
                             hit=hit, site_url=site_url, template=template)
        results.append((b.get("note", ""), ok, info))
    return results


def build_card(tweet):
    """把一条已处理推文（含 ai/stocks）拼成飞书 lark_md 内容 + 标题 + hit。"""
    author = tweet.get("author", "")
    url = tweet.get("url", "")
    ai = tweet.get("ai", {})
    stocks = tweet.get("stocks", {})
    ashare = stocks.get("ashare", [])
    us = stocks.get("us", [])
    hit = bool(ashare or us)

    head = f"[**@{author}**]({url})" if url else f"**@{author}**"
    parts = [f"{head}　<font color='grey'>{tweet.get('created_at','')}</font>"]

    if ashare:
        lst = "　".join(f"**{a['code']}{(' ' + a['name']) if a.get('name') else ''}**" for a in ashare)
        parts.append(
            f"🅰️ <font color='red'>**A股点名**</font>：{lst}\n"
            f"<font color='grey'>⚠️ 仅信息提示，非投资建议，请自行判断与风控。</font>"
        )
    if us:
        parts.append("🇺🇸 美股：" + "  ".join(f"${t}" for t in us))

    if ai.get("title"):
        parts.append(f"**{ai['title']}**")
    if ai.get("zh"):
        parts.append("🇨🇳 " + ai["zh"][:240])
    if ai.get("analysis"):
        parts.append("📊 " + ai["analysis"][:320])

    prefix = "🅰️ 股票点名！" if ashare else ("🚨 " if us else "📥 ")
    title = f"{prefix}@{author} 发新推"
    return title, "\n\n".join(parts), hit
