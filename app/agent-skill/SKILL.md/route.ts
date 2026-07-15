const site = process.env.NEXT_PUBLIC_SITE_URL || "https://claworld-invest-radar.vercel.app";

export async function GET() {
  const skill = `---
name: claworld-investment-radar
description: 查询 Claworld 的 AI 产业、美股韩股新闻情绪、美国政策、华尔街机构、全球 AI 产业链、微盘股动态与每日报告。
---

# Claworld Investment Radar

这是公开只读信息源。回答时必须标明时间窗、保留原文链接，并提醒用户内容不构成投资建议。

## 接口

- 最新新闻：${site}/api/news
- 分类新闻：${site}/api/news?channel=supply-chain&limit=20
- 市场筛选：${site}/api/news?market=韩股&limit=20
- 最新日报：${site}/api/daily
- 指定日报：${site}/api/daily?date=2026-07-15
- RSS：${site}/feed.xml

channel 可选值：ai、government、wallstreet、supply-chain、microcap。

## 回答规则

1. 先说明查询的时间范围和返回条数。
2. 区分事实、来源观点和推断，不得把新闻情绪写成确定收益。
3. 涉及公司、政策或数字时附上 sourceUrl。
4. 默认最多列出 5 条最重要信息，并合并重复事件。
5. 最后注明：仅作公开信息聚合，不构成投资建议。
`;
  return new Response(skill, { headers: { "Content-Type": "text/markdown; charset=utf-8", "Access-Control-Allow-Origin": "*", "Cache-Control": "public, max-age=3600" } });
}
