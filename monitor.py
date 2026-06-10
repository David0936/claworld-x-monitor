"""
Claworld Monitor · 监控核心。

按时间窗口轮询 twitterapi.io（多账号），对每条新推 → AI 处理（翻译/标题/解读）
+ 股票秒筛 + 飞书推送 + 存储。跑在后台线程里，通过 status 字典向 Web 后台汇报。
首轮回溯（INITIAL_HOURS）只入库不推送，避免历史推文刷屏；之后的新推才推飞书。
"""
import threading
import time
from datetime import datetime, timedelta

import requests

import feishu
import llm

LAST_TWEETS_URL = "https://api.twitterapi.io/twitter/user/last_tweets"


def _parse_created(s):
    if not s:
        return None
    for fmt in ("%a %b %d %H:%M:%S %z %Y", "%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            return datetime.strptime(s, fmt).replace(tzinfo=None) - timedelta(0)
        except Exception:
            continue
    return None


class Monitor:
    def __init__(self, config, store, screener, status):
        self.config = config
        self.store = store
        self.screener = screener
        self.status = status
        self._stop = threading.Event()
        self._primed = False

    def stop(self):
        self._stop.set()

    # ---- twitterapi.io ----
    def _search(self, account, since_dt):
        """拉取该账号的最近推文（用户时间线，实时），只返回比 since_dt 更新的。

        改用 user/last_tweets 而非 advanced_search：推特"搜索索引"对最近几小时的
        推文有滞后，时间线接口才实时。按游标向后翻页，翻到早于 since_dt 即停。
        """
        api_key = (self.config.get("TWITTER_API_KEY") or "").strip()
        headers = {"X-API-Key": api_key}
        out, cursor, guard = [], None, 0
        while guard < 10:
            guard += 1
            params = {"userName": account, "includeReplies": "true"}
            if cursor:
                params["cursor"] = cursor
            try:
                r = requests.get(LAST_TWEETS_URL, headers=headers, params=params, timeout=30)
            except Exception as e:
                self.status["current_status"] = f"抓取出错：{e}"
                break
            if r.status_code != 200:
                self.status["current_status"] = f"twitterapi.io HTTP {r.status_code}"
                break
            data = r.json()
            block = data.get("data")
            tweets = block.get("tweets", []) if isinstance(block, dict) else (data.get("tweets") or [])
            if not tweets:
                break
            reached_old = False
            for t in tweets:
                t["author"] = account
                ct = _parse_created(t.get("createdAt"))
                if since_dt and ct and ct <= since_dt:
                    reached_old = True
                    continue
                out.append(t)
            if reached_old:
                break
            if data.get("has_next_page") and data.get("next_cursor"):
                cursor = data["next_cursor"]
                continue
            break
        return out

    # ---- 单条处理 ----
    def _process(self, raw, push):
        tid = str(raw.get("id") or raw.get("id_str") or "")
        text = raw.get("text") or raw.get("full_text") or ""
        author = raw.get("author", "")
        if not tid or self.store.has(tid):
            return
        url = raw.get("url") or f"https://x.com/{author}/status/{tid}"
        stocks = self.screener.screen(text)

        ai = {}
        if self.config.get("AI_ENABLED", True):
            try:
                ai = llm.process_tweet(self.config, text)
            except Exception as e:
                ai = {"title": text[:40], "zh": text, "en": "", "analysis": f"[AI失败] {e}"}

        # AI 识别出的 A 股（含英文名/别名映射）→ 白名单裁决后并入命中
        if ai.get("ashares"):
            self.screener.apply_ai_ashares(stocks, ai.get("ashares"))
        # 译文/标题里被规范成中文名的公司（如 LeaderDrive→绿的谐波）补筛一遍
        if ai.get("zh") or ai.get("title"):
            self.screener.merge_text(stocks, (ai.get("zh") or "") + " " + (ai.get("title") or ""))

        tweet = {
            "id": tid,
            "author": author,
            "created_at": raw.get("createdAt") or raw.get("created_at") or "",
            "text": text,
            "url": url,
            "stocks": stocks,
            "ai": ai,
            "is_reply": bool(raw.get("isReply")),
            "fetched_at": datetime.utcnow().isoformat(),
        }
        self.store.add(tweet)
        self.status["processed_tweets"] = self.status.get("processed_tweets", 0) + 1

        if push:
            title, content, hit = feishu.build_card(tweet)
            bots = feishu.bots_from_config(self.config)
            # 命中推文/新推加强标注，方便在群里一眼识别
            results = feishu.push_all(bots, "🆕 最新推文 · " + title,
                                      "🆕 **最新推文**\n\n" + content,
                                      hit=hit, site_url=self.config.get("SITE_URL", ""),
                                      author=author)
            print(f"  飞书{'(命中股票)' if hit else ''}推送 {len(results)} 群：{[(n, ok) for n, ok, _ in results]}")

    # ---- 主循环 ----
    def run(self):
        interval = max(15, int(self.config.get("CHECK_INTERVAL", 60)))
        hours = int(self.config.get("INITIAL_HOURS", 24))
        last_checked = datetime.utcnow() - timedelta(hours=hours)
        accounts = [a.strip() for a in self.config.get("TARGET_ACCOUNTS", []) if a.strip()]
        self.status.update(running=True, processed_tweets=0, current_status="正在初始化…")
        print(f"开始监控 {accounts}，间隔 {interval}s，回溯 {hours}h")

        while not self._stop.is_set():
            until = datetime.utcnow()
            for acct in accounts:
                if self._stop.is_set():
                    break
                self.status["current_account"] = acct
                self.status["current_status"] = f"检查 @{acct}…"
                raws = self._search(acct, last_checked)
                now_ = datetime.utcnow()
                # 最旧→最新处理；首轮回填不推，但30分钟内的新推即便首轮也推，
                # 避免重启时把刚发的推/回复当历史吞掉（不推送）
                for raw in sorted(raws, key=lambda t: _parse_created(t.get("createdAt")) or datetime.min):
                    ct = _parse_created(raw.get("createdAt"))
                    recent = ct is not None and (now_ - ct) <= timedelta(minutes=30)
                    self._process(raw, push=(self._primed or recent))
            self._primed = True
            last_checked = until
            self.status["last_update"] = datetime.utcnow().isoformat()
            self.status["next_check_time"] = (until + timedelta(seconds=interval)).isoformat()
            self.status["current_status"] = "待命中…"
            # 可中断的睡眠
            self._stop.wait(interval)

        self.status.update(running=False, current_status="已停止", current_account="")
        print("监控已停止。")
