import { XMLParser } from "fast-xml-parser";
import type { NewsChannelKey, NewsItem, NewsMarket } from "@/lib/types";

type Source = { name: string; url: string; channel: NewsChannelKey; market: NewsMarket; type: "官网" | "监管" };

export const CHANNELS: Array<{ key: NewsChannelKey; name: string; short: string }> = [
  { key: "ai", name: "AI 产业新闻", short: "模型、产品、算力需求" },
  { key: "government", name: "美国政府新闻", short: "政策、监管、订单与限制" },
  { key: "wallstreet", name: "华尔街机构新闻", short: "投行、资管与机构观点" },
  { key: "supply-chain", name: "全球 AI 产业链", short: "美股、韩股与关键供应商" },
  { key: "microcap", name: "微盘股动态", short: "公告、停牌与异常催化" },
];

const SOURCES: Source[] = [
  { name: "Google AI", url: "https://blog.google/technology/ai/rss/", channel: "ai", market: "美股", type: "官网" },
  { name: "NVIDIA Newsroom", url: "https://nvidianews.nvidia.com/releases.xml", channel: "ai", market: "美股", type: "官网" },
  { name: "White House", url: "https://www.whitehouse.gov/news/feed/", channel: "government", market: "美股", type: "监管" },
  { name: "SEC", url: "https://www.sec.gov/news/pressreleases.rss", channel: "government", market: "美股", type: "监管" },
  { name: "FTC", url: "https://www.ftc.gov/feeds/press-release.xml", channel: "government", market: "美股", type: "监管" },
  { name: "AMD", url: "https://ir.amd.com/rss/news-releases.xml", channel: "supply-chain", market: "美股", type: "官网" },
  { name: "Samsung Newsroom", url: "https://news.samsung.com/global/feed", channel: "supply-chain", market: "韩股", type: "官网" },
  { name: "SK hynix Newsroom", url: "https://news.skhynix.com/feed/", channel: "supply-chain", market: "韩股", type: "官网" },
];

const COMPANIES: Array<[RegExp, string]> = [
  [/\bnvidia\b/i, "NVDA"], [/\bamd\b|advanced micro devices/i, "AMD"], [/\bgoogle\b|alphabet/i, "GOOGL"],
  [/\bmicrosoft\b/i, "MSFT"], [/\bmeta\b/i, "META"], [/\bamazon\b|\baws\b/i, "AMZN"],
  [/\bbroadcom\b/i, "AVGO"], [/\bmicron\b/i, "MU"], [/\bcoreweave\b/i, "CRWV"],
  [/\bpalantir\b/i, "PLTR"], [/\btsmc\b|taiwan semiconductor/i, "TSM"],
  [/\bsamsung\b/i, "005930.KS"], [/sk hynix/i, "000660.KS"], [/hanmi semiconductor/i, "042700.KS"],
];

const POSITIVE = /launch|record|growth|expand|partnership|award|contract|approve|investment|breakthrough|surge|beat|upgrade/i;
const NEGATIVE = /ban|restrict|investigation|lawsuit|decline|delay|cut|warning|suspend|fraud|risk|recall|probe|downgrade/i;
const AI_RELEVANT = /artificial intelligence|\bai\b|chip|semiconductor|data cent(?:er|re)|cloud|gpu|hbm|memory|foundry|export control|tariff|technology|robot|power|energy|nuclear|china|korea|taiwan|antitrust|cyber|defense/i;

function stripHtml(value: unknown) {
  return String(value || "")
    .replace(/<[^>]*>/g, " ")
    .replace(/&nbsp;|&#160;/g, " ")
    .replace(/&amp;/g, "&")
    .replace(/&quot;|&#34;/g, '"')
    .replace(/\s+/g, " ")
    .trim();
}

function asArray<T>(value: T | T[] | undefined): T[] {
  return value == null ? [] : Array.isArray(value) ? value : [value];
}

function pickLink(item: Record<string, unknown>) {
  const link = item.link;
  if (typeof link === "string") return link;
  if (link && typeof link === "object") return String((link as Record<string, unknown>)["@_href"] || "");
  return String(item.guid || item.id || "");
}

function symbolsFor(text: string) {
  return COMPANIES.filter(([pattern]) => pattern.test(text)).map(([, symbol]) => symbol);
}

function sentimentFor(text: string): NewsItem["sentiment"] {
  const positive = (text.match(new RegExp(POSITIVE.source, "gi")) || []).length;
  const negative = (text.match(new RegExp(NEGATIVE.source, "gi")) || []).length;
  return positive > negative ? "偏多" : negative > positive ? "偏空" : "中性";
}

async function fetchSource(source: Source): Promise<NewsItem[]> {
  try {
    const response = await fetch(source.url, {
      headers: { "User-Agent": process.env.NEWS_USER_AGENT || "Claworld Investment Radar contact@claworld.ai" },
      next: { revalidate: 1800 },
      signal: AbortSignal.timeout(9000),
    });
    if (!response.ok) return [];
    const xml = await response.text();
    const parsed = new XMLParser({ ignoreAttributes: false, processEntities: false }).parse(xml);
    const rawItems = asArray<Record<string, unknown>>(parsed?.rss?.channel?.item || parsed?.feed?.entry);
    return rawItems.slice(0, 12).map((item, index) => {
      const title = stripHtml(item.title);
      const summary = stripHtml(item.description || item.summary || item.content).slice(0, 360);
      const publishedAt = String(item.pubDate || item.published || item.updated || new Date().toISOString());
      const url = pickLink(item);
      const text = `${title} ${summary}`;
      return {
        id: `${source.name}-${url || index}`,
        channel: source.channel,
        title,
        summary,
        url,
        source: source.name,
        publishedAt: Number.isNaN(new Date(publishedAt).getTime()) ? new Date().toISOString() : new Date(publishedAt).toISOString(),
        market: source.market,
        sentiment: sentimentFor(text),
        symbols: symbolsFor(text),
        sourceType: source.type,
      };
    }).filter((item) => item.title && item.url && (source.channel === "ai" || AI_RELEVANT.test(`${item.title} ${item.summary}`)));
  } catch {
    return [];
  }
}

const X_GROUPS: Partial<Record<NewsChannelKey, string>> = {
  ai: "AI_X_ACCOUNTS",
  government: "US_GOV_X_ACCOUNTS",
  wallstreet: "WALL_STREET_X_ACCOUNTS",
  "supply-chain": "SUPPLY_CHAIN_X_ACCOUNTS",
  microcap: "MICROCAP_X_ACCOUNTS",
};

async function fetchXAccount(account: string, channel: NewsChannelKey): Promise<NewsItem[]> {
  if (!process.env.TWITTER_API_KEY) return [];
  try {
    const response = await fetch(`https://api.twitterapi.io/twitter/user/last_tweets?userName=${encodeURIComponent(account)}&includeReplies=false`, {
      headers: { "X-API-Key": process.env.TWITTER_API_KEY },
      next: { revalidate: 3600 },
      signal: AbortSignal.timeout(9000),
    });
    if (!response.ok) return [];
    const payload = await response.json();
    const tweets = payload?.data?.tweets || payload?.tweets || [];
    return tweets.slice(0, 5).map((tweet: Record<string, unknown>) => {
      const text = stripHtml(tweet.text || tweet.full_text);
      const id = String(tweet.id || tweet.id_str || "");
      const symbols = symbolsFor(text);
      const market: NewsMarket = symbols.some((symbol) => symbol.endsWith(".KS")) ? "韩股" : "美股";
      return {
        id: `x-${id}`,
        channel,
        title: text.length > 95 ? `${text.slice(0, 95)}…` : text,
        summary: text,
        url: String(tweet.url || `https://x.com/${account}/status/${id}`),
        source: `X · @${account}`,
        publishedAt: new Date(String(tweet.createdAt || tweet.created_at || Date.now())).toISOString(),
        market,
        sentiment: sentimentFor(text),
        symbols,
        sourceType: "X" as const,
      };
    }).filter((item: NewsItem) => item.title && item.url && (channel === "microcap" || AI_RELEVANT.test(`${item.title} ${item.summary}`)));
  } catch {
    return [];
  }
}

export async function getNews() {
  const official = await Promise.all(SOURCES.map(fetchSource));
  const xTasks = Object.entries(X_GROUPS).flatMap(([channel, envName]) =>
    (process.env[envName!] || "").split(",").map((value) => value.trim().replace(/^@/, "")).filter(Boolean)
      .map((account) => fetchXAccount(account, channel as NewsChannelKey))
  );
  const xItems = await Promise.all(xTasks);
  return [...official.flat(), ...xItems.flat()]
    .filter((item, index, all) => all.findIndex((other) => other.url === item.url) === index)
    .sort((a, b) => b.publishedAt.localeCompare(a.publishedAt));
}
