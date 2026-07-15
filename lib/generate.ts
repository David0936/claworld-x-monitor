import type { DailyBriefing } from "@/lib/types";

type RawPost = {
  id: string;
  author: string;
  text: string;
  url: string;
  createdAt: string;
};

const X_API = "https://api.twitterapi.io/twitter/user/last_tweets";

function beijingDate() {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Shanghai",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(new Date());
}

async function fetchAccount(account: string, since: number): Promise<RawPost[]> {
  const response = await fetch(`${X_API}?userName=${encodeURIComponent(account)}&includeReplies=true`, {
    headers: { "X-API-Key": process.env.TWITTER_API_KEY || "" },
    cache: "no-store",
  });
  if (!response.ok) throw new Error(`@${account} 抓取失败 (${response.status})`);
  const payload = await response.json();
  const tweets = payload?.data?.tweets || payload?.tweets || [];
  return tweets
    .map((tweet: Record<string, unknown>) => ({
      id: String(tweet.id || tweet.id_str || ""),
      author: account,
      text: String(tweet.text || tweet.full_text || ""),
      url: String(tweet.url || `https://x.com/${account}/status/${tweet.id || tweet.id_str}`),
      createdAt: String(tweet.createdAt || tweet.created_at || ""),
    }))
    .filter((tweet: RawPost) => tweet.id && tweet.text && new Date(tweet.createdAt).getTime() >= since);
}

function extractJson(text: string) {
  const fenced = text.match(/```(?:json)?\s*([\s\S]*?)```/i)?.[1];
  const candidate = fenced || text.slice(text.indexOf("{"), text.lastIndexOf("}") + 1);
  return JSON.parse(candidate);
}

async function analyze(posts: RawPost[]): Promise<DailyBriefing> {
  const baseUrl = (process.env.LLM_BASE_URL || "https://api.openai.com/v1").replace(/\/$/, "");
  const model = process.env.LLM_MODEL || "gpt-4.1-mini";
  const compact = posts.slice(0, 80).map((post) => ({ ...post, text: post.text.slice(0, 1200) }));
  const prompt = `你是严谨的 AI 产业投资研究编辑。根据下列财经博主公开帖子，生成当天中文投资线索日报。

规则：
1. 只保留与 AI 产业投资相关且有信息增量的内容；合并重复观点。
2. 区分事实、博主判断和你的推断；不得编造代码、数字或来源。
3. 关注算力/基础设施、应用/商业化、资本/公司、政策/地缘、风险/反向信号。
4. 每条必须给出投资逻辑、风险、影响方向、置信度、周期和原帖链接。不是投资建议。
5. 输出纯 JSON，不要 markdown。结构严格为：
{"title":"总标题","summary":"120字总述","marketPulse":"80字市场脉搏","categories":[{"key":"compute","name":"分类名","description":"分类说明","items":[{"id":"原帖id或组合id","title":"标题","summary":"事实摘要","thesis":"为什么值得投资者关注","impact":"利好|利空|中性|待验证","confidence":"高|中|低","horizon":"短期|中期|长期","tickers":[{"symbol":"代码或产业链名称","name":"公司名可空","market":"A股|港股|美股|加密|产业链"}],"risk":"反证或主要风险","source":"X · @账号","sourceUrl":"原帖URL","author":"账号","publishedAt":"原帖时间"}]}]}

原始帖子：${JSON.stringify(compact)}`;

  const response = await fetch(`${baseUrl}/chat/completions`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${process.env.LLM_API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model,
      temperature: 0.2,
      response_format: { type: "json_object" },
      messages: [
        { role: "system", content: "你只输出合法 JSON，忠于来源，不提供个性化投资建议。" },
        { role: "user", content: prompt },
      ],
    }),
  });
  if (!response.ok) throw new Error(`AI 分析失败 (${response.status}): ${(await response.text()).slice(0, 300)}`);
  const payload = await response.json();
  const result = extractJson(payload?.choices?.[0]?.message?.content || "");
  const categories = Array.isArray(result.categories) ? result.categories.filter((c: { items?: unknown[] }) => c.items?.length) : [];
  const opportunities = categories.reduce((sum: number, c: { items: unknown[] }) => sum + c.items.length, 0);
  const tickers = new Set(categories.flatMap((c: { items: Array<{ tickers?: Array<{ symbol: string }> }> }) => c.items.flatMap((i) => (i.tickers || []).map((t) => t.symbol))));
  return {
    date: beijingDate(),
    generatedAt: new Date().toISOString(),
    status: "live",
    title: result.title || "AI 产业投资机会日报",
    summary: result.summary || "",
    marketPulse: result.marketPulse || "",
    stats: {
      sources: new Set(posts.map((post) => post.author)).size,
      posts: posts.length,
      opportunities,
      tickers: tickers.size,
    },
    categories,
  };
}

export async function generateDaily() {
  if (!process.env.TWITTER_API_KEY) throw new Error("缺少 TWITTER_API_KEY");
  if (!process.env.LLM_API_KEY) throw new Error("缺少 LLM_API_KEY");
  const accounts = (process.env.TARGET_ACCOUNTS || "aleabitoreddit")
    .split(",")
    .map((item) => item.trim().replace(/^@/, ""))
    .filter(Boolean);
  const since = Date.now() - 28 * 60 * 60 * 1000;
  const results = await Promise.allSettled(accounts.map((account) => fetchAccount(account, since)));
  const posts = results.flatMap((result) => (result.status === "fulfilled" ? result.value : []));
  const unique = [...new Map(posts.map((post) => [post.id, post])).values()];
  if (!unique.length) throw new Error("过去 28 小时没有抓取到可分析的帖子");
  return analyze(unique);
}
