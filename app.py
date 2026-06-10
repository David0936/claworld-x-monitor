"""
Claworld Monitor —— X(Twitter) 财经监控 + 股票秒筛（Flask 后台）。

多账号实时监控 → AI 翻译/中文标题/财经解读 → A股/美股秒筛 → 飞书推送 → Web 后台。
AI 支持 Claude 与通义千问（OpenAI 兼容）设置里一键切换。
"""
import functools
import json
import os
import secrets
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from flask import (Flask, flash, jsonify, redirect, render_template, request,
                   session, url_for)

import feishu
import llm
import stock_screen
from monitor import Monitor
from store import TweetStore

ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "config.json"
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

DEFAULTS = {
    "TWITTER_API_KEY": "",
    "AI_ENABLED": True,
    "AI_PROVIDER": "claude",            # claude | openai
    "CLAUDE_API_KEY": "",
    "CLAUDE_MODEL": "claude-opus-4-8",
    "LLM_URL": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "LLM_API_KEY": "",
    "LLM_MODEL": "qwen-plus",
    "TARGET_ACCOUNTS": ["aleabitoreddit"],
    "CHECK_INTERVAL": 60,
    "INITIAL_HOURS": 24,
    "FEISHU_WEBHOOK": "",
    "FEISHU_SECRET": "",
    "FEISHU_BOTS": [],          # [{note, webhook, secret, accounts}] 多飞书群，可按博主路由
    "SITE_URL": "",
    "STOCK_SCREEN": True,
}

# ---- 全局状态 ----
store = TweetStore(str(DATA_DIR))
screener = stock_screen.load_screener()
monitoring_status = {
    "running": False,
    "current_status": "未启动",
    "current_account": "",
    "processed_tweets": 0,
    "last_update": None,
    "next_check_time": None,
}
monitor_instance = None
monitor_thread = None
_lock = threading.Lock()


def load_config():
    cfg = dict(DEFAULTS)
    if CONFIG_PATH.exists():
        try:
            cfg.update(json.loads(CONFIG_PATH.read_text(encoding="utf-8")))
        except Exception:
            pass
    return cfg


def save_config(cfg):
    CONFIG_PATH.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")


def fetch_profiles(cfg):
    """拉取监控账号的头像/昵称/粉丝数，缓存到 config['PROFILES']（{user:{avatar,name,followers}}）。"""
    key = (cfg.get("TWITTER_API_KEY") or "").strip()
    profiles = dict(cfg.get("PROFILES") or {})
    if not key:
        return profiles
    for acct in cfg.get("TARGET_ACCOUNTS", []):
        try:
            r = requests.get("https://api.twitterapi.io/twitter/user/info",
                             headers={"X-API-Key": key}, params={"userName": acct}, timeout=15)
            data = (r.json() or {}).get("data") or {}
            if data.get("userName"):
                profiles[acct] = {
                    "avatar": (data.get("profilePicture") or "").replace("_normal.", "_400x400."),
                    "name": data.get("name", ""),
                    "followers": data.get("followers", 0),
                }
        except Exception:
            pass
    cfg["PROFILES"] = profiles
    save_config(cfg)
    return profiles


def ensure_secrets(cfg):
    """首启生成 SECRET_KEY 与默认密码。"""
    changed = False
    if not cfg.get("SECRET_KEY"):
        cfg["SECRET_KEY"] = secrets.token_hex(16)
        changed = True
    if not cfg.get("ADMIN_PASSWORD"):
        pw = secrets.token_urlsafe(9)
        cfg["ADMIN_PASSWORD"] = pw
        (DATA_DIR / "default_password.txt").write_text(pw, encoding="utf-8")
        print(f"==== 默认登录密码：{pw} （也已写入 data/default_password.txt）====")
        changed = True
    if changed:
        save_config(cfg)
    return cfg


config = ensure_secrets(load_config())

app = Flask(__name__)
app.secret_key = config["SECRET_KEY"]


def login_required(f):
    @functools.wraps(f)
    def wrap(*a, **k):
        if not session.get("auth"):
            return redirect(url_for("login"))
        return f(*a, **k)
    return wrap


def to_beijing(s):
    """把推特格式（Tue Jun 09 05:42:08 +0000 2026）或 ISO 时间转成北京时间字符串。"""
    if not s:
        return ""
    dt = None
    try:
        dt = datetime.strptime(s, "%a %b %d %H:%M:%S %z %Y")
    except Exception:
        try:
            dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        except Exception:
            return s
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S")


app.jinja_env.filters["beijing"] = to_beijing


# ---- 监控启停 ----
def start_monitoring():
    global monitor_instance, monitor_thread
    with _lock:
        if monitoring_status["running"]:
            return False, "已在运行"
        cfg = load_config()
        if not cfg.get("TWITTER_API_KEY"):
            return False, "未配置 TWITTER_API_KEY"
        try:
            fetch_profiles(cfg)   # 刷新监控账号头像/昵称缓存
        except Exception:
            pass
        monitor_instance = Monitor(cfg, store, screener, monitoring_status)
        monitor_thread = threading.Thread(target=monitor_instance.run, daemon=True)
        monitor_thread.start()
        return True, "已启动"


def stop_monitoring():
    global monitor_instance
    with _lock:
        if monitor_instance:
            monitor_instance.stop()
        monitoring_status["running"] = False
        monitoring_status["current_status"] = "已停止"
        return True, "已停止"


# ---- 路由 ----
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("password") == load_config().get("ADMIN_PASSWORD"):
            session["auth"] = True
            return redirect(url_for("index"))
        flash("密码错误")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
def index():
    # 信息流公开，访客免登录即可查看
    tweets = store.all()
    author = request.args.get("author", "").strip()
    only_stock = request.args.get("stock") == "1"
    if author:
        tweets = [t for t in tweets if t.get("author", "").lower() == author.lower()]
    if only_stock:
        tweets = [t for t in tweets if t.get("stocks", {}).get("hit")]
    return render_template(
        "index.html",
        tweets=tweets,
        authors=store.authors(),
        author=author,
        only_stock=only_stock,
        status=monitoring_status,
        screener_size=screener.size,
        is_admin=bool(session.get("auth")),
        profiles=load_config().get("PROFILES", {}),
    )


@app.route("/tweet/<tweet_id>")
def tweet_detail(tweet_id):
    t = store.get(tweet_id)
    if not t:
        flash("推文不存在")
        return redirect(url_for("index"))
    return render_template("tweet_detail.html", tweet=t, status=monitoring_status,
                           is_admin=bool(session.get("auth")))


@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    cfg = load_config()
    if request.method == "POST":
        f = request.form
        cfg["TWITTER_API_KEY"] = f.get("TWITTER_API_KEY", "").strip()
        cfg["AI_ENABLED"] = f.get("AI_ENABLED") == "on"
        cfg["AI_PROVIDER"] = f.get("AI_PROVIDER", "claude")
        cfg["CLAUDE_API_KEY"] = f.get("CLAUDE_API_KEY", "").strip()
        cfg["CLAUDE_MODEL"] = f.get("CLAUDE_MODEL", "claude-opus-4-8").strip()
        cfg["LLM_URL"] = f.get("LLM_URL", "").strip()
        cfg["LLM_API_KEY"] = f.get("LLM_API_KEY", "").strip()
        cfg["LLM_MODEL"] = f.get("LLM_MODEL", "qwen-plus").strip()
        cfg["TARGET_ACCOUNTS"] = [a.strip().lstrip("@") for a in f.get("TARGET_ACCOUNTS", "").replace("，", ",").split(",") if a.strip()]
        cfg["CHECK_INTERVAL"] = max(15, int(f.get("CHECK_INTERVAL", 60) or 60))
        cfg["INITIAL_HOURS"] = int(f.get("INITIAL_HOURS", 24) or 24)
        notes = f.getlist("bot_note")
        webhooks = f.getlist("bot_webhook")
        secs = f.getlist("bot_secret")
        accts = f.getlist("bot_accounts")
        bots = []
        for i, wh in enumerate(webhooks):
            wh = wh.strip()
            if wh:
                acc_raw = (accts[i] if i < len(accts) else "").replace("，", ",")
                bots.append({
                    "note": (notes[i].strip() if i < len(notes) else ""),
                    "webhook": wh,
                    "secret": (secs[i].strip() if i < len(secs) else ""),
                    "accounts": [a.strip().lstrip("@") for a in acc_raw.split(",") if a.strip()],
                })
        cfg["FEISHU_BOTS"] = bots
        cfg["FEISHU_WEBHOOK"] = ""   # 已迁移到多群 FEISHU_BOTS
        cfg["FEISHU_SECRET"] = ""
        cfg["SITE_URL"] = f.get("SITE_URL", "").strip()
        if f.get("NEW_PASSWORD", "").strip():
            cfg["ADMIN_PASSWORD"] = f.get("NEW_PASSWORD").strip()
        save_config(cfg)
        flash("已保存。重启监控后生效。")
        return redirect(url_for("settings"))
    return render_template("settings.html", cfg=cfg, status=monitoring_status, screener_size=screener.size)


@app.route("/api/push/<tweet_id>", methods=["POST"])
@login_required
def api_push(tweet_id):
    """管理员手动把某条推文补推到飞书。"""
    cfg = load_config()
    t = store.get(tweet_id)
    if not t:
        return jsonify(ok=False, msg="推文不存在"), 404
    title, content, hit = feishu.build_card(t)
    bots = feishu.bots_from_config(cfg)
    if not bots:
        return jsonify(ok=False, msg="未配置飞书群")
    results = feishu.push_all(bots, title, content, hit=hit, site_url=cfg.get("SITE_URL", ""))
    okn = sum(1 for _, ok, _ in results if ok)
    return jsonify(ok=okn > 0, msg=f"已推送到 {okn}/{len(results)} 个群")


@app.route("/api/start", methods=["POST"])
@login_required
def api_start():
    ok, msg = start_monitoring()
    return jsonify(ok=ok, msg=msg)


@app.route("/api/stop", methods=["POST"])
@login_required
def api_stop():
    ok, msg = stop_monitoring()
    return jsonify(ok=ok, msg=msg)


@app.route("/api/status")
@login_required
def api_status():
    s = dict(monitoring_status)
    s["beijing_last_update"] = to_beijing(s.get("last_update"))
    s["count"] = len(store.all())
    return jsonify(s)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    print(f"启动 Web 后台 http://0.0.0.0:{port}  （A股白名单 {screener.size} 只）")
    app.run(host="0.0.0.0", port=port, debug=False)
