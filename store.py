"""推文存储：JSON 文件，按 id 去重，最多保留 N 条。线程安全（粗粒度锁）。"""
import json
import threading
from datetime import datetime, timezone
from pathlib import Path


def _created_key(tweet):
    """把 created_at 解析为可比较的时间，用于按真实时间排序。
    created_at 形如 'Tue Jun 09 01:58:57 +0000 2026'，直接按字符串排序会因
    星期前缀（Mon/Tue…）而错乱，故在此解析成带时区的 datetime。"""
    s = tweet.get("created_at", "") or ""
    for fmt in ("%a %b %d %H:%M:%S %z %Y", "%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            dt = datetime.strptime(s, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except Exception:
            continue
    return datetime.min.replace(tzinfo=timezone.utc)


class TweetStore:
    def __init__(self, data_dir="data", max_keep=2000):
        self.path = Path(data_dir) / "tweets.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.max_keep = max_keep
        self._lock = threading.Lock()
        self._tweets = self._load()
        self._tweets.sort(key=_created_key, reverse=True)
        self._ids = {t.get("id") for t in self._tweets}

    def _load(self):
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return []

    def _save(self):
        tmp = self.path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(self._tweets, ensure_ascii=False, indent=1), encoding="utf-8")
        tmp.replace(self.path)

    def has(self, tweet_id):
        return tweet_id in self._ids

    def add(self, tweet):
        """新增一条（已去重则返回 False）。"""
        tid = tweet.get("id")
        with self._lock:
            if not tid or tid in self._ids:
                return False
            self._ids.add(tid)
            self._tweets.append(tweet)
            self._tweets.sort(key=_created_key, reverse=True)
            if len(self._tweets) > self.max_keep:
                for t in self._tweets[self.max_keep:]:
                    self._ids.discard(t.get("id"))
                self._tweets = self._tweets[: self.max_keep]
            self._save()
            return True

    def all(self):
        with self._lock:
            return list(self._tweets)

    def get(self, tweet_id):
        return next((t for t in self._tweets if t.get("id") == tweet_id), None)

    def authors(self):
        return sorted({t.get("author", "") for t in self._tweets if t.get("author")})
