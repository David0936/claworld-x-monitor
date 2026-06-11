"""Telegram Bot 推送（sendMessage，HTML 解析）。股票命中时标题加红色警示 emoji。

配置：cfg["TELEGRAM_BOTS"] = [{note, token, chat_id, accounts}]
- token：找 @BotFather 创建 bot 拿到的 token（形如 123456:ABC-DEF...）
- chat_id：目标会话 id。私聊给自己=你的用户 id；群=负数 id；频道=@频道用户名。
  拿 id 最简单：把 bot 拉进群/给 bot 发条消息，访问
  https://api.telegram.org/bot<token>/getUpdates 看 chat.id。
- accounts：该 bot 只推哪些博主（空=全部），用于分流。
"""
import html as _html

import requests

API = "https://api.telegram.org/bot{token}/sendMessage"


def bots_from_config(cfg):
    """取 Telegram 机器人列表 [{note, token, chat_id, accounts}]。"""
    bots = cfg.get("TELEGRAM_BOTS")
    return bots if isinstance(bots, list) and bots else []


def send(token, chat_id, text, site_url="", button_text="查看后台"):
    """发一条 Telegram 消息（HTML）。返回 (ok, info)。"""
    if not (token and chat_id):
        return False, "未配置 token / chat_id"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    if site_url:
        payload["reply_markup"] = {
            "inline_keyboard": [[{"text": button_text, "url": site_url}]]
        }
    try:
        r = requests.post(API.format(token=token), json=payload, timeout=15)
        ok = r.ok and (r.json() or {}).get("ok", False)
        return ok, f"HTTP {r.status_code} {r.text[:120]}"
    except Exception as e:
        return False, str(e)


def push_all(bots, text, hit=False, site_url="", author=None):
    """推送到所有 Telegram bot。bot.accounts 限定它只发哪些博主（空=全部）。
    返回 [(note, ok, info), ...]。"""
    results = []
    for b in bots or []:
        token = (b.get("token") or "").strip()
        chat_id = str(b.get("chat_id") or "").strip()
        if not (token and chat_id):
            continue
        accts = b.get("accounts") or []
        if author and accts and author not in accts:
            continue
        ok, info = send(token, chat_id, text, site_url=site_url)
        results.append((b.get("note", ""), ok, info))
    return results


def build_message(tweet):
    """把一条已处理推文拼成 Telegram HTML 文本，返回 (text, hit)。"""
    def esc(s):
        return _html.escape(str(s or ""))

    author = tweet.get("author", "")
    url = tweet.get("url", "")
    ai = tweet.get("ai", {})
    stocks = tweet.get("stocks", {})
    ashare = stocks.get("ashare", [])
    us = stocks.get("us", [])
    hit = bool(ashare or us)

    head = f'<a href="{esc(url)}"><b>@{esc(author)}</b></a>' if url else f"<b>@{esc(author)}</b>"
    parts = [f"{head}  <i>{esc(tweet.get('created_at',''))}</i>"]

    if ashare:
        lst = "  ".join(
            f"<b>{esc(a['code'])}{(' ' + esc(a['name'])) if a.get('name') else ''}</b>"
            for a in ashare
        )
        parts.append(f"🅰️ <b>A股点名</b>：{lst}\n<i>⚠️ 仅信息提示，非投资建议，请自行判断与风控。</i>")
    if us:
        parts.append("🇺🇸 美股：" + "  ".join(f"${esc(t)}" for t in us))

    if ai.get("title"):
        parts.append(f"<b>{esc(ai['title'])}</b>")
    if ai.get("zh"):
        parts.append("🇨🇳 " + esc(ai["zh"][:240]))
    if ai.get("analysis"):
        parts.append("📊 " + esc(ai["analysis"][:320]))

    prefix = "🅰️ 股票点名！" if ashare else ("🚨 " if us else "📥 ")
    title = f"{prefix}@{esc(author)} 发新推"
    return f"<b>{title}</b>\n\n" + "\n\n".join(parts), hit
