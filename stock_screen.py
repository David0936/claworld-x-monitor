"""
推文秒筛股票：从一条推文里识别提到的沪深 A 股（代码/公司名）和美股 $Ticker。

A 股（精度优先，依据研究结论）：
  - 代码：六位代码候选 → 必须命中白名单 codeMap（白名单是权威，自动排除指数 000300、
    基金 510300、浏览量等噪声）→ 再排除被 ￥/$ 或 元/万/亿/%/年/月/日 包裹的金额/日期。
  - 公司名：只匹配白名单里的真实简称；最长匹配优先 + 区间去重防止包含式重复；
    <4 字短名需附近有股票线索词或代码同现；deny-list 常用词只允许靠代码命中。
美股：$TICKER 正则（1-6 个大写字母）。

白名单 data/ashares.json 由 scripts/build-ashares.py 生成；线上还会从东方财富刷新。
"""
import json
import re
from pathlib import Path

DATA = Path(__file__).resolve().parent / "data" / "ashares.json"

# 六位 A 股代码候选（白名单做最终裁决）
CODE_RE = re.compile(r"(?<!\d)(?:60[0135]|68[89]|00[0-3]|30[01])\d{3}(?!\d)")
US_RE = re.compile(r"\$([A-Z]{1,6})\b")
STOCK_CUE = re.compile(r"股|涨|跌|买|卖|建仓|减仓|持仓|主力|游资|涨停|跌停|标的|代码|龙头|板块|A股|加仓|抄底|拉升")

DENY = {
    "中国", "东方", "长城", "光明", "三一", "华夏", "海尔", "美的", "格力", "茅台",
    "万科", "比亚", "三花", "光大", "中信", "招商", "平安", "建设", "工商", "海康",
    "长虹", "苏宁", "同花", "金龙", "国电", "大众", "上海", "深圳", "北京", "海南",
    "西藏", "新华", "时代", "未来", "永辉", "顺丰", "京东", "中航", "南方", "东风",
    "广发", "兴业", "二三四五", "三六零", "完美", "幸福", "胜利", "英雄", "巨人", "天地",
}


class StockScreener:
    def __init__(self, stocks: dict):
        self.code_map = dict(stocks or {})
        self.name_to_code = {}
        names = []
        for code, name in self.code_map.items():
            if not name or len(name) < 2 or name in DENY:
                continue
            if name not in self.name_to_code:
                self.name_to_code[name] = code
                names.append(name)
        names.sort(key=len, reverse=True)  # 最长匹配优先
        self.names = names

    @property
    def size(self):
        return len(self.code_map)

    def detect_ashares(self, text: str):
        if not text or not self.code_map:
            return []
        found = {}
        # PASS 1 代码
        for m in CODE_RE.finditer(text):
            code = m.group(0)
            if code not in self.code_map:
                continue
            before = text[m.start() - 1] if m.start() > 0 else ""
            after = text[m.end(): m.end() + 8]
            if before in "￥$":
                continue
            if re.match(r"^\s*(万|亿|%|％|年|月|日|号)", after):
                continue
            if after.startswith("元"):
                continue
            found[code] = {"code": code, "name": self.code_map.get(code, ""), "via": "code"}
        # PASS 2 公司名（最长优先 + 区间去重防包含式重复）
        spans = []  # 已认领的 [start,end)

        def overlaps(a, b):
            return any(not (b <= s or a >= e) for s, e in spans)

        for name in self.names:
            start = 0
            while True:
                idx = text.find(name, start)
                if idx == -1:
                    break
                end = idx + len(name)
                start = end
                if overlaps(idx, end):
                    continue
                code = self.name_to_code[name]
                if len(name) < 4 and code not in found and not self._near_cue(text, idx, len(name)):
                    continue
                if code not in found:
                    found[code] = {"code": code, "name": name, "via": "name"}
                spans.append((idx, end))
        return list(found.values())[:5]

    @staticmethod
    def _near_cue(text, idx, span):
        s = max(0, idx - 8)
        e = min(len(text), idx + span + 8)
        return bool(STOCK_CUE.search(text[s:e]))

    def detect_us(self, text: str):
        if not text:
            return []
        return sorted(set(US_RE.findall(text)))

    def screen(self, text: str):
        """返回 {'ashare': [...], 'us': [...], 'hit': bool}"""
        ashare = self.detect_ashares(text)
        us = self.detect_us(text)
        return {"ashare": ashare, "us": us, "hit": bool(ashare or us)}

    def merge_text(self, stocks: dict, text: str):
        """对额外文本（通常是 AI 译文/标题）再秒筛一次并并入已有结果。
        作用：英文名经 AI 翻成规范中文名后（如 LeaderDrive→绿的谐波），
        能被名录按中文名命中，不依赖模型是否填了结构化字段。"""
        if not isinstance(stocks, dict) or not text:
            return stocks
        extra = self.screen(text)
        seen = {a.get("code") for a in stocks.setdefault("ashare", [])}
        for a in extra["ashare"]:
            # 译文偏保守：只采纳代码命中 或 ≥4字中文名命中；短名（如“机器人”）在啰嗦译文里易误报，不采纳
            if a.get("via") == "name" and len(a.get("name", "")) < 4:
                continue
            if a["code"] not in seen:
                stocks["ashare"].append(a)
                seen.add(a["code"])
        us = stocks.setdefault("us", [])
        for u in extra["us"]:
            if u not in us:
                us.append(u)
        stocks["us"] = sorted(set(us))
        stocks["hit"] = bool(stocks["ashare"] or stocks["us"])
        return stocks

    def apply_ai_ashares(self, stocks: dict, ai_items):
        """把 AI 识别出的 A 股（含英文名→代码的映射）并入结果。

        只采纳**白名单（code_map）里真实存在**的 6 位代码，防止 AI 编造；
        名称一律以白名单为准（self.code_map[code]）。就地更新 stocks 并刷新 hit。
        """
        if not isinstance(stocks, dict):
            return stocks
        ashare = stocks.setdefault("ashare", [])
        existing = {a.get("code") for a in ashare}
        for item in ai_items or []:
            code = item.get("code") if isinstance(item, dict) else item
            code = str(code or "").strip()
            if code in self.code_map and code not in existing:
                ashare.append({"code": code, "name": self.code_map[code], "via": "ai"})
                existing.add(code)
        stocks["hit"] = bool(ashare or stocks.get("us"))
        return stocks


def load_screener(path: Path = DATA) -> StockScreener:
    try:
        j = json.loads(Path(path).read_text(encoding="utf-8"))
        return StockScreener(j.get("stocks", {}))
    except Exception:
        return StockScreener({})


if __name__ == "__main__":
    s = load_screener()
    print("白名单:", s.size)
    tests = [
        ("代码命中", "今天关注 600519，逻辑很强"),
        ("代码+线索", "贵州茅台600519要建仓"),
        ("美股", "看好 $NVDA 和 $TSM 的算力链"),
        ("金额误报应空", "成交额 600519 万元"),
        ("3字名+线索", "比亚迪要涨停了"),
        ("长名", "东方财富数据不错"),
    ]
    for label, t in tests:
        print(f"  {label}: {t} → {s.screen(t)}")
