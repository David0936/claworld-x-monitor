# 📈 Claworld Monitor — X (Twitter) Finance Monitor + Stock Screener

[![Release](https://img.shields.io/github/v/release/David0936/Serenity-X-Monitor?label=version&color=brightgreen)](https://github.com/David0936/Serenity-X-Monitor/releases/latest)
[![Changelog](https://img.shields.io/badge/changelog-log-blue)](CHANGELOG.md)
[![License](https://img.shields.io/badge/license-personal%20non--commercial-orange)](LICENSE)
[![Stars](https://img.shields.io/github/stars/David0936/Serenity-X-Monitor?style=social)](https://github.com/David0936/Serenity-X-Monitor)

[简体中文](README.md) | **English**

A self-hosted monitor for finance accounts on X (Twitter): **multi-account real-time monitoring → AI translation / Chinese headline / market read → instant stock screening (A-shares + US) → Feishu / Telegram push + web dashboard**.

Built for "watching finance posters and catching stock signals first": the moment a poster tweets, within seconds a card lands in Feishu/Telegram, and any A-share / US ticker mentioned is auto-pinned in red.

![Claworld Monitor](tutorial/render/01-cover.png)

---

## ⚠️ Disclaimer (read first)

- This software **only aggregates, translates, and notifies on PUBLIC social-media content; it is NOT investment advice** and **does not recommend or endorse any stock, fund, or crypto asset**.
- Stock codes / names detected in tweets are **an objective annotation of the monitored public account's words**, not the author's view or any trade suggestion.
- Whether and when to trade is **at your own risk and judgment**. Financial info may be delayed, incomplete, or wrong; the author is not liable for any loss.
- You must comply with local laws and the terms of each data / AI / third-party provider. Do not scrape or redistribute copyrighted or paywalled content.

## 📜 License

**Free for personal, non-commercial use; any commercial use is prohibited** (selling, paid services / subscriptions, resale, etc.). See [LICENSE](LICENSE).

---

## ✨ Features

- 🔍 **Multi-account real-time monitoring**: twitterapi.io user-timeline API, polled on an interval, **including replies**
- 🤖 **AI processing**: Chinese translation + a one-line Chinese headline + a 120–160 char market read; **switch between Claude and Qwen / any OpenAI-compatible endpoint in settings**
- 🅰️ **Instant A-share screening**: built-in directory of ~5,200 Shanghai/Shenzhen A-shares, detecting **6-digit codes or company names** in tweets (incl. AI mapping English names back to Chinese, e.g. LeaderDrive → 绿的谐波/688017); hits are pinned in red
- 🇺🇸 **US screening**: detects `$TICKER`
- 📱 **Push (multi-channel)**: **Feishu** groups and **Telegram** bots — each can carry a note and be **routed per-poster** (which posters this bot/group receives); stock hits are red cards
- 🌐 **Web dashboard**: public feed, per-poster channel tags, Beijing time, tweet/reply labels, settings page, one-click start/stop, manual re-push
- ⬇️ **In-app one-click update**: when a new GitHub release exists, the settings page shows an update button — pulls the latest code and restarts; your config and stored tweets are preserved
- 🖥 **Mac desktop app** (double-click, single-user, no login)
- ⚠️ "Information only, not investment advice" labeled throughout

---

## 🚀 How to run

### Option 1 — Mac desktop app (recommended, double-click, no CLI)
1. Download `Claworld Monitor.app` from **Releases** (or build it yourself, below);
2. Double-click — if macOS warns about an "unidentified developer": **right-click the app → Open → Open** (once);
3. In the window, fill in your API keys on the **Settings** page (see "API setup" below), then go back and click **Start**.

> The desktop app is single-user and **login-free**; data lives in `~/Library/Application Support/Claworld Monitor/`.

### Option 2 — One-click script (Mac / Windows, no commands)
After downloading the project, **double-click** in your file manager:
- **Mac**: `run.command`
- **Windows**: `run.bat`

It creates a virtualenv, installs deps, starts the server and opens your browser. (Requires [Python 3](https://www.python.org/downloads/); on Windows check "Add to PATH" during install.)

### Option 3 — From source (developers / server deploy)
```bash
pip3 install -r requirements.txt
python3 start.py            # http://localhost:5001
```
**Login-free by default, ready out of the box** — open it and fill in the **Settings** page. If you need login protection (public/commercial deploy), enable it and set a password under "Settings → Login Protection".

### Option 4 — Let an AI agent install it (Skill)
Copy the `skill/claworld-monitor` folder into `~/.claude/skills/`, then tell Claude Code "help me deploy Claworld finance monitor" — the agent will clone, install deps, configure APIs, and run it (Mac/Win/Linux).

### 🔨 Build the Mac .app yourself
```bash
bash build-mac.sh           # output: dist/Claworld Monitor.app
```

> On the first run, historical tweets within the "look-back hours" are **stored but not pushed** (to avoid flooding); only new tweets after that are pushed.

### 🔄 Updating
- **Source version**: when a new release exists, the Settings page shows a "⬇️ One-click update" button — it pulls the latest code and restarts; your config (API keys / posters / push channels) and stored tweets are **preserved**. You can also `git pull && restart` manually.
- **Desktop .app**: download the new build from [Releases](https://github.com/David0936/Serenity-X-Monitor/releases/latest) and replace it.
- See changes in [CHANGELOG.md](CHANGELOG.md).

---

## 🔑 API setup (where to register / top up)

Three kinds of keys, configure as needed. **All entered on the Settings page.**

### 1) X data source — twitterapi.io (required)
- Register: **https://twitterapi.io** (a third-party X data service, not official X)
- Pay-as-you-go (~$0.001 per call, no monthly fee); top up under "Top up credits"
- Get the `API Key` → paste into "twitterapi.io API Key" in Settings
- ⚠️ Don't confuse it with similarly named services (e.g. twtapi.io); keys are not interchangeable

### 2) AI model (one required; AI can be turned off to use screening only)
Pick one in Settings:
- **Claude (official)**: get a key at **https://console.anthropic.com** → choose the "Claude" radio, fill `Claude API Key`
- **Qwen / OpenAI-compatible endpoint**: any OpenAI-compatible API → choose "Qwen / OpenAI-compatible", fill `URL / Key / Model`
  - Qwen: register at **https://dashscope.console.aliyun.com**, URL `https://dashscope.aliyuncs.com/compatible-mode/v1`, model e.g. `qwen-plus`
  - Or any OpenAI-compatible relay (its base_url + key + a supported model name)

> Tip: when using a "relay", even if it proxies a Claude model, pick the **OpenAI-compatible** option (the Claude radio goes to Anthropic's official endpoint).

### 3) Feishu / Telegram push (optional, free)
**Feishu**: group settings → **Bots** → add a **Custom Bot** → copy the **Webhook URL** → on the Settings page click "+ Add Feishu group", fill a note + webhook (add the signing secret if you enabled signature verification).

**Telegram**: message `@BotFather`, send `/newbot`, get a **Bot Token** → add the bot to a group or send it a message first → open `https://api.telegram.org/bot<token>/getUpdates` to find the **chat_id** → on the Settings page fill token + chat_id under "Telegram push".

Both support multiple channels and **per-poster routing** (uncheck = all); stock hits are auto-pinned in red.

---

## 🅰️ A-share directory

- `data/ashares.json` (code → Chinese short name, ~5,200 names).
- Rebuild / refresh: `python3 scripts/build-ashares.py`.
- Detection logic in `stock_screen.py`: codes first (directory arbitration + amount/date de-noising), names second (longest match + common-word de-noising + short names need context); AI-detected English names are merged after directory arbitration.

---

## 📂 Structure

| File | Role |
|---|---|
| `app.py` | Flask backend: routes, auth, settings, start/stop, manual push |
| `monitor.py` | Monitor loop (accounts → AI → stocks → push → store) |
| `llm.py` | AI layer: Claude / OpenAI-compatible (Qwen) switchable |
| `stock_screen.py` | Stock screening (A-share code/name + US `$ticker`) |
| `feishu.py` | Feishu card push (multi-group + per-poster routing) |
| `telegram.py` | Telegram bot push (multi-bot + per-poster routing) |
| `store.py` | Tweet storage + dedup |
| `data/ashares.json` | A-share directory |
| `scripts/build-ashares.py` | Rebuild the directory |

---

## 👤 Author

Built by **David小鱼 (Claworld)**.

- 📰 WeChat: **自家的鱼鱼 / Claworld**
- 🐦 X: [@Shark1996_](https://x.com/shark1996_)
- ▶️ YouTube: [@Singularity2026](https://www.youtube.com/@Singularity2026)
- 📕 Xiaohongshu: [David小鱼](https://xhslink.com/m/6WBQosGc8F6)

---

## 📝 Changelog

Every change is logged in [CHANGELOG.md](CHANGELOG.md) (also visible on the in-app "About" page).

---

## License

**MIT License** — see [LICENSE](LICENSE). **Use, modify, redistribute and sell freely; commercial use needs no permission.** X and AI APIs are paid services with setup overhead, so you're welcome to self-host and open it up to others or charge them to join.

🌐 Part of the **Claworld** ecosystem — more projects at <https://github.com/David0936>.

> ⚠️ Information aggregation only, **not financial advice**, use at your own risk (see the financial disclaimer in LICENSE). © 2026 David小鱼 / Claworld
