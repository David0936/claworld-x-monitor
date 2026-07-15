import { getNews } from "@/lib/news";

const site = process.env.NEXT_PUBLIC_SITE_URL || "https://claworld-invest-radar.vercel.app";
const escape = (value: string) => value.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

export async function GET() {
  const items = (await getNews()).slice(0, 50).map((item) => `<item><title>${escape(item.title)}</title><link>${escape(item.url)}</link><guid isPermaLink="false">${escape(item.id)}</guid><pubDate>${new Date(item.publishedAt).toUTCString()}</pubDate><description>${escape(item.summary)}</description><category>${escape(item.channel)}</category></item>`).join("");
  const xml = `<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>Claworld AI 投资新闻雷达</title><link>${site}/news</link><description>AI 产业、美股韩股、美国政策与全球供应链动态</description><language>zh-CN</language><lastBuildDate>${new Date().toUTCString()}</lastBuildDate>${items}</channel></rss>`;
  return new Response(xml, { headers: { "Content-Type": "application/rss+xml; charset=utf-8", "Cache-Control": "public, s-maxage=900, stale-while-revalidate=3600", "Access-Control-Allow-Origin": "*" } });
}
