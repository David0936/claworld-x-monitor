"""
Claworld Monitor —— X(Twitter) 财经监控 + 股票秒筛（Flask 后台）。

多账号实时监控 → AI 翻译/中文标题/财经解读 → A股/美股秒筛 → 飞书推送 → Web 后台。
AI 支持 Claude 与通义千问（OpenAI 兼容）设置里一键切换。
"""
import functools
import json
import os
import secrets
import sys
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from flask import (Flask, flash, jsonify, redirect, render_template, request,
                   session, url_for)

import feishu
import telegram
import llm
import stock_screen
from monitor import Monitor
from store import TweetStore

# 路径：打包成 Mac .app 后，资源(模板/静态/A股名录种子)从 bundle 读，
# 可写数据(配置/推文)落到用户目录；源码运行时两者都是项目目录（行为不变）。
if getattr(sys, "frozen", False):
    RESOURCE = Path(sys._MEIPASS)
    APP_DIR = Path.home() / "Library" / "Application Support" / "Claworld Monitor"
else:
    RESOURCE = Path(__file__).resolve().parent
    APP_DIR = RESOURCE
APP_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_PATH = APP_DIR / "config.json"
DATA_DIR = APP_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
ASHARES_PATH = RESOURCE / "data" / "ashares.json"

# 桌面模式（打包成 .app，或本地以 CLAWORLD_DESKTOP=1 运行）：本机单用户，免登录、自动管理员。
DESKTOP = getattr(sys, "frozen", False) or os.environ.get("CLAWORLD_DESKTOP") == "1"

VERSION = "1.2.0"
GITHUB_REPO = "David0936/Serenity-X-Monitor"    # 发布后填 "GitHub用户名/仓库名"，即启用更新检查（留空则不检查）
_ver_cache = {"latest": "", "ts": 0.0}


def latest_version():
    """查 GitHub 最新 release tag（每小时缓存一次）；未配置 GITHUB_REPO 则返回空。"""
    import time as _t
    if not GITHUB_REPO:
        return ""
    # 命中缓存（成功或失败都缓存 1 小时，避免每次打开设置页都阻塞重试）
    if _t.time() - _ver_cache["ts"] < 3600:
        return _ver_cache["latest"]
    try:
        r = requests.get(f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest", timeout=3)
        _ver_cache["latest"] = ((r.json() or {}).get("tag_name") or "").lstrip("v")
    except Exception:
        pass
    _ver_cache["ts"] = _t.time()   # 失败也记时间戳，1 小时内不再重试
    return _ver_cache["latest"]

DEFAULTS = {
    "TWITTER_API_KEY": "",
    "AI_ENABLED": True,
    "AI_PROVIDER": "claude",            # claude | openai
    "CLAUDE_API_KEY": "",
    "CLAUDE_MODEL": "claude-opus-4-8",
    "LLM_URL": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "LLM_API_KEY": "",
    "LLM_MODEL": "qwen-plus",
    "AUTH_ENABLED": False,             # 是否启用登录密码保护（商用部署可开）
    "ADMIN_PASSWORD": "",              # 启用后的登录密码，由使用者自行设置
    "TARGET_ACCOUNTS": ["aleabitoreddit"],
    "CHECK_INTERVAL": 60,
    "INITIAL_HOURS": 24,
    "FEISHU_WEBHOOK": "",
    "FEISHU_SECRET": "",
    "FEISHU_BOTS": [],          # [{note, webhook, secret, accounts}] 多飞书群，可按博主路由
    "TELEGRAM_BOTS": [],        # [{note, token, chat_id, accounts}] 多 Telegram bot，可按博主路由
    "SITE_URL": "",
    "STOCK_SCREEN": True,
}

# ---- 全局状态 ----
store = TweetStore(str(DATA_DIR))
screener = stock_screen.load_screener(ASHARES_PATH)
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
    targets = cfg.get("TARGET_ACCOUNTS", [])
    profiles = {u: p for u, p in (cfg.get("PROFILES") or {}).items() if u in targets}
    if not key:
        cfg["PROFILES"] = profiles
        save_config(cfg)
        return profiles
    for acct in targets:
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
    if changed:
        save_config(cfg)
    return cfg


config = ensure_secrets(load_config())

app = Flask(__name__,
            template_folder=str(RESOURCE / "templates"),
            static_folder=str(RESOURCE / "static"))
app.secret_key = config["SECRET_KEY"]


def auth_on():
    """是否开启了登录密码保护（且已设密码才真正生效，避免锁死）。"""
    cfg = load_config()
    return bool(cfg.get("AUTH_ENABLED") and cfg.get("ADMIN_PASSWORD"))


@app.context_processor
def _inject_globals():
    return {"auth_enabled": auth_on()}


@app.before_request
def _auto_auth():
    # 未开启登录保护时：直接开放管理权限，免登录即用
    if not auth_on() and not session.get("auth"):
        session["auth"] = True


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
    if not auth_on():            # 未开启密码保护，直接进信息流
        return redirect(url_for("index"))
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
        # Telegram 机器人（多个，可按博主分流）
        tg_notes = f.getlist("tg_note")
        tg_tokens = f.getlist("tg_token")
        tg_chats = f.getlist("tg_chat")
        tg_accts = f.getlist("tg_accounts")
        tg_bots = []
        for i, tok in enumerate(tg_tokens):
            tok = tok.strip()
            chat = (tg_chats[i].strip() if i < len(tg_chats) else "")
            if tok and chat:
                acc_raw = (tg_accts[i] if i < len(tg_accts) else "").replace("，", ",")
                tg_bots.append({
                    "note": (tg_notes[i].strip() if i < len(tg_notes) else ""),
                    "token": tok,
                    "chat_id": chat,
                    "accounts": [a.strip().lstrip("@") for a in acc_raw.split(",") if a.strip()],
                })
        cfg["TELEGRAM_BOTS"] = tg_bots
        cfg["SITE_URL"] = f.get("SITE_URL", "").strip()
        # 登录保护：开关 + 自设密码（留空则沿用旧密码）
        new_pw = f.get("ADMIN_PASSWORD", "").strip()
        if new_pw:
            cfg["ADMIN_PASSWORD"] = new_pw
        want_auth = f.get("AUTH_ENABLED") == "on"
        if want_auth and not cfg.get("ADMIN_PASSWORD"):
            want_auth = False
            flash("请先设置一个登录密码，登录保护暂未开启。")
        cfg["AUTH_ENABLED"] = want_auth
        save_config(cfg)
        flash("已保存。重启监控后生效。")
        return redirect(url_for("settings"))
    latest = latest_version()
    return render_template("settings.html", cfg=cfg, status=monitoring_status,
                           screener_size=screener.size, version=VERSION,
                           latest=latest, update_available=bool(latest and latest != VERSION),
                           github_repo=GITHUB_REPO)


@app.route("/api/push/<tweet_id>", methods=["POST"])
@login_required
def api_push(tweet_id):
    """管理员手动把某条推文补推到飞书。"""
    cfg = load_config()
    t = store.get(tweet_id)
    if not t:
        return jsonify(ok=False, msg="推文不存在"), 404
    fs_bots = feishu.bots_from_config(cfg)
    tg_bots = telegram.bots_from_config(cfg)
    if not fs_bots and not tg_bots:
        return jsonify(ok=False, msg="未配置飞书群或 Telegram bot")
    title, content, hit = feishu.build_card(t)
    results = feishu.push_all(fs_bots, title, content, hit=hit, site_url=cfg.get("SITE_URL", ""))
    tg_text, _ = telegram.build_message(t)
    results += telegram.push_all(tg_bots, tg_text, hit=hit, site_url=cfg.get("SITE_URL", ""))
    okn = sum(1 for _, ok, _ in results if ok)
    return jsonify(ok=okn > 0, msg=f"已推送到 {okn}/{len(results)} 个渠道")


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


def _git(*args, timeout=90):
    import subprocess
    return subprocess.run(["git", *args], cwd=str(RESOURCE),
                          capture_output=True, text=True, timeout=timeout)


@app.route("/api/update", methods=["POST"])
@login_required
def api_update():
    """一键同步 GitHub 最新版：拉代码 → 重启。config.json/data 已 gitignore，设置不受影响。"""
    if getattr(sys, "frozen", False):
        return jsonify(ok=False, msg="打包版(.app)请到 GitHub Releases 下载新版替换；源码版才支持一键更新。")
    if not (RESOURCE / ".git").exists():
        return jsonify(ok=False, msg="当前不是 git 安装目录，无法自动更新。请用 git clone 的版本，或手动下载替换。")
    try:
        if _git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip() in ("", "HEAD"):
            return jsonify(ok=False, msg="当前处于游离 HEAD，请先切回分支。")
        _git("fetch", "origin", "--tags", "--force")
        # 优先切到最新 release tag（vX 或 X），否则跟随远端默认分支
        latest = latest_version()
        target = ""
        for cand in ([f"v{latest}", latest] if latest else []):
            if _git("rev-parse", "--verify", "--quiet", cand).returncode == 0:
                target = cand
                break
        if not target:
            branch = _git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip() or "main"
            target = f"origin/{branch}"
        r = _git("reset", "--hard", target)
        if r.returncode != 0:
            return jsonify(ok=False, msg="更新失败：" + (r.stderr or r.stdout)[-300:])
        head = _git("log", "-1", "--pretty=%h %s").stdout.strip()
    except Exception as e:
        return jsonify(ok=False, msg=f"更新出错：{e}")

    # 延迟 1 秒重启自身以加载新代码（先把响应返回给前端）
    def _restart():
        import time
        time.sleep(1.0)
        os.execv(sys.executable, [sys.executable, *sys.argv])
    threading.Thread(target=_restart, daemon=True).start()
    _ver_cache["ts"] = 0.0   # 清版本缓存，重启后立即反映新版本
    return jsonify(ok=True, msg=f"已同步到 {target}（{head}）· 正在重启，约 3 秒后请刷新页面。")


@app.route("/api/restart", methods=["POST"])
@login_required
def api_restart():
    """一键重启监控：停止 → 重新载入配置启动（改完设置即用）。"""
    stop_monitoring()
    ok, msg = start_monitoring()
    return jsonify(ok=ok, msg=("已重启 · " + msg) if ok else msg)


@app.route("/tutorial")
def tutorial():
    """使用教程：X API / 博主 / 飞书 / AI 配置怎么填。"""
    return render_template("tutorial.html", status=monitoring_status)


# ---- 关于 / 更新日志 ----
AUTHOR_LINKS = [
    {"label": "微信公众号", "name": "自家的鱼鱼 / Claworld", "url": ""},
    {"label": "X (Twitter)", "name": "@Shark1996_", "url": "https://x.com/shark1996_"},
    {"label": "YouTube", "name": "@Singularity2026", "url": "https://www.youtube.com/@Singularity2026"},
    {"label": "小红书", "name": "David小鱼", "url": "https://xhslink.com/m/6WBQosGc8F6"},
]


def _render_changelog():
    """读 CHANGELOG.md 做轻量 markdown 渲染（##/###/- /文本）。"""
    import html as _h
    try:
        lines = (RESOURCE / "CHANGELOG.md").read_text(encoding="utf-8").splitlines()
    except Exception:
        return "<p class='muted'>暂无更新日志。</p>"
    out, in_ul = [], False
    for ln in lines:
        s = ln.rstrip()
        if s.startswith("### "):
            if in_ul: out.append("</ul>"); in_ul = False
            out.append(f"<h6 class='mt-3 fw-bold'>{_h.escape(s[4:])}</h6>")
        elif s.startswith("## "):
            if in_ul: out.append("</ul>"); in_ul = False
            out.append(f"<div class='cl-ver'>{_h.escape(s[3:])}</div>")
        elif s.startswith("# ") or s.startswith("<!--") or s.startswith("本项目版本"):
            continue
        elif s.startswith("- "):
            if not in_ul: out.append("<ul class='mb-2'>"); in_ul = True
            out.append(f"<li>{_h.escape(s[2:]).replace('**','')}</li>")
        elif s.strip() == "":
            if in_ul: out.append("</ul>"); in_ul = False
        else:
            if in_ul: out.append("</ul>"); in_ul = False
            out.append(f"<p class='muted mb-1'>{_h.escape(s)}</p>")
    if in_ul: out.append("</ul>")
    return "\n".join(out)


@app.route("/about")
def about():
    latest = latest_version()
    return render_template("about.html", status=monitoring_status, version=VERSION,
                           changelog=_render_changelog(), links=AUTHOR_LINKS,
                           latest=latest, update_available=bool(latest and latest != VERSION),
                           github_repo=GITHUB_REPO)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    print(f"启动 Web 后台 http://0.0.0.0:{port}  （A股白名单 {screener.size} 只）")
    app.run(host="0.0.0.0", port=port, debug=False)
