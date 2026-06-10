---
name: claworld-monitor
description: 帮用户安装、配置并运行 Claworld Monitor —— X(Twitter) 财经博主监控 + 股票秒筛 + 飞书推送。当用户说"部署/安装/跑起来 Claworld、财经监控、盯盘/盯推机器人、监控某财经博主"时使用。跨平台（Mac/Windows/Linux）。
---

# 安装并运行 Claworld Monitor

你要帮用户把 **Claworld Monitor** 跑起来：一个 Python/Flask 应用，监控 X 财经博主 → AI 翻译/解读 → A股·美股秒筛 → 飞书推送 + Web 后台。跨平台。**一步步带用户做，每步确认结果再下一步。**

## 0. 判断环境
- 先确认操作系统（Mac / Windows / Linux），下面命令按系统选用。
- 检查 Python：`python3 --version`（Windows 多为 `python --version`），需 ≥ 3.9。
  - 没装：引导去 https://www.python.org/downloads/ 安装；**Windows 安装时务必勾选 "Add Python to PATH"**。

## 1. 获取代码
- 用户没有代码 → `git clone <项目仓库地址>`，然后 `cd` 进项目目录。
- 已有 → `cd` 到该目录。

## 2. 装依赖并启动
- **Mac / Linux**：
  ```bash
  python3 -m venv .venv
  .venv/bin/pip install -r requirements.txt
  .venv/bin/python start.py
  ```
- **Windows**：
  ```bat
  python -m venv .venv
  .venv\Scripts\python -m pip install -r requirements.txt
  .venv\Scripts\python start.py
  ```
- 也可直接双击仓库里的 `run.command`(Mac) / `run.bat`(Windows) 一键完成。
- 首次启动**控制台会打印默认登录密码**（也写入 `data/default_password.txt`）。记下它。
- 打开 **http://localhost:5001** 登录。

## 3. 引导配置 API（用户最容易卡在这）
登录后到**设置**页填（无需改 JSON）。三类，帮用户逐个搞定，告诉他去哪注册/充值：
- **twitterapi.io（必填，X 数据源）**：https://twitterapi.io 注册 → 按量充值（约 $0.001/次）→ 复制 API Key → 填「twitterapi.io API Key」。
- **AI（必填其一）**：
  - Claude：https://console.anthropic.com 拿 key，选「Claude」；
  - 或 OpenAI 兼容/通义千问：通义千问 https://dashscope.console.aliyun.com ，URL `https://dashscope.aliyuncs.com/compatible-mode/v1`，模型 `qwen-plus`；选「通义千问/OpenAI兼容」。
- **飞书（可选）**：飞书群 → 群机器人 → 自定义机器人 → 复制 Webhook → 设置页「+ 添加飞书群」粘上。
- 填**监控账号**（X 用户名，逗号分隔，不带 @）。
- 保存 → 回首页点**开始监控**。首轮回填历史只入库不推送，之后新推才推。

## 4. 常见问题
- 点「开始监控」报「未配置 TWITTER_API_KEY」→ 去设置页填 key。
- AI 显示「处理失败 / 401 invalid」→ key 填错或账户无余额，核对/充值。
- 端口 5001 被占用 → 用 `PORT=5002 ...` 环境变量换端口。
- 飞书没收到 → 检查 Webhook 是否填对；若飞书机器人开了「签名校验」，要把密钥也填上。

## ⚠️ 务必提醒用户
- 本工具**仅做公开信息聚合与提醒，不构成投资建议，不推荐任何股票**；是否买卖风险自负。
- 数据源、AI 都需用户**自己的付费 key**；请遵守各平台条款，合规使用。
