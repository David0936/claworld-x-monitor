# 📈 Claworld Monitor — X(Twitter) 财经监控 + 股票秒筛

自部署的 X(Twitter) 财经博主监控系统：**多账号实时监控 → AI 翻译 / 中文标题 / 财经解读 → 推文秒筛股票（A股 + 美股）→ 飞书推送 + Web 后台**。

为「盯财经博主、第一时间抓到股票线索」而做：博主一发推，几十秒内飞书弹卡片，点名的 A股 / 美股自动红色置顶。

---

## ⚠️ 免责声明（务必先读）

- 本软件**仅对公开社交媒体内容做信息聚合、翻译与提醒，不构成任何投资建议**，**不对任何股票 / 基金 / 加密货币做推荐或背书**。
- 推文中识别出的股票代码 / 名称，**只是对被监控公开账号言论的客观标注**，不代表作者或本软件的观点或操作建议。
- 是否买卖、何时买卖，**风险自负，请独立判断**。财经信息可能延迟、遗漏或出错，作者不对任何损失负责。
- 使用者须遵守所在地法律法规及各数据源 / 服务商的条款，**严格合规合法**，不得抓取或二次分发受版权 / 付费墙保护的内容。

## 📜 使用许可

**个人免费自用，禁止任何形式的商业使用**（出售、付费服务 / 订阅、转卖等）。详见 [LICENSE](LICENSE)。

---

## ✨ 功能

- 🔍 **多账号实时监控**：twitterapi.io 用户时间线接口，按间隔轮询，含**回复**抓取
- 🤖 **AI 处理**：中文翻译 + 一句中文标题 + 120–160 字财经解读；**Claude 与通义千问 / OpenAI 兼容接口设置里一键切换**
- 🅰️ **A股秒筛**：内置 ~5200 只沪深 A 股名录，识别推文里的**六位代码或公司名**（含 AI 把英文名映射回中文名，如 LeaderDrive → 绿的谐波/688017），命中即红色置顶
- 🇺🇸 **美股秒筛**：识别 `$TICKER`
- 📱 **飞书推送（多群）**：每个群可填备注、可**按博主路由**（这个机器人只推哪些博主）；命中股票红色卡片
- 🌐 **Web 后台**：信息流（公开免登录）、按博主频道标签 / 仅看命中股票、推文详情、北京时间、推文 / 回复标注、设置页、登录鉴权、一键启停、手动补推
- ⚠️ 股票提示均标注「仅信息提示，非投资建议」

---

## 🚀 使用方式

### 方式一：Mac 桌面版（推荐，双击即用，免命令行）
1. 到 **Releases** 下载 `Claworld Monitor.app`（或自行构建，见下）；
2. 双击打开 —— 首次若提示「身份不明开发者」：**右键 App → 打开 → 再点"打开"**（只需一次）；
3. 弹出窗口后到**设置**页填好 API（见下「API 配置指南」），回首页点**开始监控**。

> 桌面版本机单用户、**免登录**；数据存于 `~/Library/Application Support/Claworld Monitor/`。

### 方式二：一键脚本（Mac / Windows，免敲命令）
下载本项目后，在文件管理器里**双击**：
- **Mac**：`run.command`
- **Windows**：`run.bat`

会自动建虚拟环境、装依赖、起服务并打开浏览器。（前提：已装 [Python 3](https://www.python.org/downloads/)；Win 安装时勾选 "Add to PATH"。）

### 方式三：源码运行（开发者 / 部署到服务器）
```bash
pip3 install -r requirements.txt
python3 start.py            # http://localhost:5001
```
首次启动控制台会打印**默认登录密码**（也写入 `data/default_password.txt`）；登录后到**设置**页填写各项。

### 方式四：让 AI Agent 帮你装（Skill）
把 `skill/claworld-monitor` 文件夹拷到 `~/.claude/skills/`，然后对 Claude Code 说「帮我部署 Claworld 财经监控」，Agent 会带你 clone、装依赖、配 API、跑起来（Mac/Win/Linux 通用）。

### 🔨 自行构建 Mac .app
```bash
bash build-mac.sh           # 产物：dist/Claworld Monitor.app
```

> 首轮会按「回溯小时数」把历史推**只入库不推送**，避免刷屏；之后的新推才推送。

---

## 🔑 API 配置指南（去哪注册 / 充值）

三类 key，按需配置。**全部在【设置】页面填写**。

### 1) X 数据源 — twitterapi.io（必填）
- 注册：**https://twitterapi.io** （第三方 X 数据服务，非 X 官方）
- 充值：**按量预付费**（约 $0.001/次调用，无需月费），后台「Top up credits」充值
- 拿到 `API Key` → 填设置页「twitterapi.io API Key」
- ⚠️ 注意别和名字相近的服务（如 twtapi.io）搞混，key 不通用

### 2) AI 模型（必填其一，可关闭 AI 仅用秒筛）
设置页二选一：
- **Claude（官方）**：注册 **https://console.anthropic.com** 拿 key（美元计费）→ 选「Claude」单选钮、填 `Claude API Key`
- **通义千问 / OpenAI 兼容接口**：任何 OpenAI 兼容的接口都行 → 选「通义千问 / OpenAI兼容」、填 `URL / Key / Model`
  - 通义千问：注册 **https://dashscope.console.aliyun.com** ，URL 用 `https://dashscope.aliyuncs.com/compatible-mode/v1`，Model 如 `qwen-plus`
  - 也可用任意 OpenAI 兼容中转站（填它的 base_url + key + 支持的模型名）

> 提示：若用「中转站」即使它代理的是 Claude 模型，也要选 **openai/兼容** 这条（Claude 单选钮走的是 Anthropic 官方地址）。

### 3) 飞书推送（可选，免费）
- 飞书群 → 群设置 → **群机器人** → 添加机器人 → **自定义机器人** → 复制 **Webhook 地址**
- 设置页「飞书推送」点「+ 添加飞书群」→ 填备注 + 粘 Webhook（安全设置选「签名校验」的话把密钥也填上）
- 可加多个群；每个群能**勾选只推哪些博主**（不勾=全部）

---

## 🅰️ A股名录

- `data/ashares.json`（代码 → 中文简称，~5200 只）。
- 重建 / 刷新：`python3 scripts/build-ashares.py`。
- 检测逻辑见 `stock_screen.py`：代码优先（名录裁决 + 金额 / 日期去噪），公司名其次（最长匹配 + 常用词去噪 + 短名需上下文）；AI 识别的英文名经名录裁决后并入。

---

## 📂 结构

| 文件 | 作用 |
|---|---|
| `app.py` | Flask 后台：路由、鉴权、设置、启停、手动推送 |
| `monitor.py` | 监控主循环（多账号 → AI → 股票 → 飞书 → 存储） |
| `llm.py` | AI 层：Claude / OpenAI 兼容(通义千问) 可切换 |
| `stock_screen.py` | 股票秒筛（A股代码/名称 + 美股 $ticker） |
| `feishu.py` | 飞书卡片推送（多群 + 按博主路由） |
| `store.py` | 推文存储 + 去重 |
| `data/ashares.json` | A股名录 |
| `scripts/build-ashares.py` | 重建名录 |

---

## 👤 作者 / 关注我

由 **David小鱼 (Claworld)** 开发。欢迎关注，交流财经科技 & 自建工具：

- 📰 微信公众号：**自家的鱼鱼 / Claworld**
- 🐦 X：[@Shark1996_](https://x.com/shark1996_)
- ▶️ YouTube：[@Singularity2026](https://www.youtube.com/@Singularity2026)
- 📕 小红书：[David小鱼](https://xhslink.com/m/6WBQosGc8F6)

---

## License

个人非商业使用许可（禁止商用）— 见 [LICENSE](LICENSE)。© 2026 David小鱼 / Claworld
