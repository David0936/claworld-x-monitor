import Link from "next/link";
import { Activity, ArrowUpRight, RadioTower } from "lucide-react";
import { CHANNELS } from "@/lib/news";
import type { NewsChannelKey, NewsItem, NewsMarket } from "@/lib/types";

function relativeTime(iso: string) {
  const hours = Math.max(0, Math.round((Date.now() - new Date(iso).getTime()) / 3600000));
  if (hours < 1) return "刚刚";
  if (hours < 24) return `${hours} 小时前`;
  return `${Math.floor(hours / 24)} 天前`;
}

function sentimentStats(items: NewsItem[], market: NewsMarket) {
  const selected = items.filter((item) => item.market === market);
  const score = selected.reduce((sum, item) => sum + (item.sentiment === "偏多" ? 1 : item.sentiment === "偏空" ? -1 : 0), 0);
  const label = score > 2 ? "情绪偏多" : score < -2 ? "情绪偏空" : "情绪中性";
  return { label, score: selected.length ? Math.round(50 + (score / selected.length) * 30) : 50 };
}

export function NewsRadar({ items, active, market }: { items: NewsItem[]; active: NewsChannelKey | "all"; market: NewsMarket | "全部" }) {
  const filtered = items.filter((item) => (active === "all" || item.channel === active) && (market === "全部" || item.market === market));
  const us = sentimentStats(items, "美股");
  const kr = sentimentStats(items, "韩股");
  const grouped = filtered.reduce<Record<string, NewsItem[]>>((acc, item) => {
    const key = new Intl.DateTimeFormat("zh-CN", { timeZone: "Asia/Shanghai", month: "long", day: "numeric" }).format(new Date(item.publishedAt));
    (acc[key] ||= []).push(item);
    return acc;
  }, {});

  return (
    <main className="newsMain pageWidth">
        <section className="newsTopline">
          <div><span className="liveDot" /> LIVE INTELLIGENCE</div>
          <p>官网 · 美国监管 · X · 每 30 分钟刷新</p>
        </section>
        <header className="pageTitle">
          <span>CLAWORLD SIGNAL STREAM</span>
          <h1>{active === "all" ? "AI 产业时间线" : CHANNELS.find((channel) => channel.key === active)?.name}</h1>
          <p>从情绪和催化出发，追踪美股、韩股 AI 产业链新闻票。</p>
        </header>
        <section className="moodRow">
          <div className="moodCard"><span>US · 美股 AI</span><b>{us.label}</b><div><i style={{ width: `${us.score}%` }} /></div><small>新闻情绪 {us.score}/100</small></div>
          <div className="moodCard"><span>KR · 韩股 AI</span><b>{kr.label}</b><div><i style={{ width: `${kr.score}%` }} /></div><small>新闻情绪 {kr.score}/100</small></div>
          <div className="pulseCard"><Activity size={18} /><span>最新抓取</span><b>{items.length}</b><small>条有效动态</small></div>
        </section>

        <section className="feedHead">
          <div className="channelTabs"><Link href="/news" className={active === "all" ? "active" : ""}>全部</Link>{CHANNELS.map((channel) => <Link href={`/news?channel=${channel.key}`} className={active === channel.key ? "active" : ""} key={channel.key}>{channel.name.replace("新闻", "")}</Link>)}</div>
          <div className="marketFilters">
            {(["全部", "美股", "韩股", "全球"] as const).map((item) => <Link className={market === item ? "active" : ""} href={`/news?${active === "all" ? "" : `channel=${active}&`}market=${encodeURIComponent(item)}`} key={item}>{item}</Link>)}
          </div>
        </section>

        <div className="newsFeed timelineFeed">
          {Object.entries(grouped).map(([date, dateItems]) => <section className="timelineDay" key={date}>
            <div className="timelineDate"><b>{date}</b><span>{dateItems.length} 条动态</span></div>
            {dateItems.map((item) => (
              <article className="newsCard timelineCard" key={item.id}>
                <div className="timeRail"><time>{new Date(item.publishedAt).toLocaleTimeString("zh-CN", { timeZone: "Asia/Shanghai", hour: "2-digit", minute: "2-digit", hour12: false })}</time><i /></div>
                <div className="timelineBody">
                  <div className="newsMeta"><span className={`sentiment ${item.sentiment}`}>{item.sentiment}</span><span>{item.market}</span><span>{item.sourceType}</span><time>{relativeTime(item.publishedAt)}</time></div>
                  <h2><a href={item.url} target="_blank" rel="noreferrer">{item.title}</a></h2>
                  {item.summary && item.summary !== item.title && <p>{item.summary}</p>}
                  {!!item.symbols.length && <div className="newsSymbols">{item.symbols.map((symbol) => <span key={symbol}>${symbol}</span>)}</div>}
                  <a className="newsSource" href={item.url} target="_blank" rel="noreferrer"><span>{item.source}</span><ArrowUpRight size={14} /></a>
                </div>
              </article>
            ))}
          </section>)}
          {!filtered.length && <div className="newsEmpty"><RadioTower size={24} /><b>这个频道还没有抓到动态</b><p>官网源会自动恢复；华尔街与微盘股频道可在 Vercel 配置对应 X 账号后启用。</p></div>}
        </div>
      </main>
  );
}
