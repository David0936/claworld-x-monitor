import Link from "next/link";
import { Activity, ArrowUpRight, Building2, Cpu, Landmark, RadioTower, ScanSearch, Sparkles, Zap } from "lucide-react";
import { CHANNELS } from "@/lib/news";
import type { NewsChannelKey, NewsItem, NewsMarket } from "@/lib/types";

const ICONS = { ai: Sparkles, government: Landmark, wallstreet: Building2, "supply-chain": Cpu, microcap: Zap };

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
  const counts = Object.fromEntries(CHANNELS.map((channel) => [channel.key, items.filter((item) => item.channel === channel.key).length]));
  const filtered = items.filter((item) => (active === "all" || item.channel === active) && (market === "全部" || item.market === market));
  const us = sentimentStats(items, "美股");
  const kr = sentimentStats(items, "韩股");

  return (
    <div className="radarLayout">
      <aside className="radarSidebar">
        <div className="radarIdentity"><span><ScanSearch size={18} /></span><div><b>新闻雷达</b><small>AI INVESTMENT SIGNALS</small></div></div>
        <nav className="channelNav" aria-label="新闻频道">
          <Link href="/news" className={active === "all" ? "selected" : ""}><RadioTower size={17} /><span>全部动态<small>跨频道时间流</small></span><i>{items.length}</i></Link>
          {CHANNELS.map((channel) => {
            const Icon = ICONS[channel.key];
            return <Link href={`/news?channel=${channel.key}`} className={active === channel.key ? "selected" : ""} key={channel.key}><Icon size={17} /><span>{channel.name}<small>{channel.short}</small></span><i>{counts[channel.key]}</i></Link>;
          })}
        </nav>
        <div className="sourceNote"><b>当前信源</b><p>官网 / 美国监管 / X</p><span>付费新闻 API 暂未接入</span></div>
      </aside>

      <main className="newsMain">
        <section className="newsTopline">
          <div><span className="liveDot" /> LIVE INTELLIGENCE</div>
          <p>从情绪和催化出发，追踪美股、韩股 AI 新闻票</p>
        </section>
        <section className="moodRow">
          <div className="moodCard"><span>US · 美股 AI</span><b>{us.label}</b><div><i style={{ width: `${us.score}%` }} /></div><small>新闻情绪 {us.score}/100</small></div>
          <div className="moodCard"><span>KR · 韩股 AI</span><b>{kr.label}</b><div><i style={{ width: `${kr.score}%` }} /></div><small>新闻情绪 {kr.score}/100</small></div>
          <div className="pulseCard"><Activity size={18} /><span>最新抓取</span><b>{items.length}</b><small>条有效动态</small></div>
        </section>

        <section className="feedHead">
          <div><h1>{active === "all" ? "全部动态" : CHANNELS.find((channel) => channel.key === active)?.name}</h1><p>按发布时间排序 · 点击回到原始信源</p></div>
          <div className="marketFilters">
            {(["全部", "美股", "韩股", "全球"] as const).map((item) => <Link className={market === item ? "active" : ""} href={`/news?${active === "all" ? "" : `channel=${active}&`}market=${encodeURIComponent(item)}`} key={item}>{item}</Link>)}
          </div>
        </section>

        <div className="newsFeed">
          {filtered.map((item) => (
            <article className="newsCard" key={item.id}>
              <div className="newsMeta"><span className={`sentiment ${item.sentiment}`}>{item.sentiment}</span><span>{item.market}</span><span>{item.sourceType}</span><time>{relativeTime(item.publishedAt)}</time></div>
              <h2><a href={item.url} target="_blank" rel="noreferrer">{item.title}</a></h2>
              {item.summary && item.summary !== item.title && <p>{item.summary}</p>}
              {!!item.symbols.length && <div className="newsSymbols">{item.symbols.map((symbol) => <span key={symbol}>${symbol}</span>)}</div>}
              <a className="newsSource" href={item.url} target="_blank" rel="noreferrer"><span>{item.source}</span><ArrowUpRight size={14} /></a>
            </article>
          ))}
          {!filtered.length && <div className="newsEmpty"><RadioTower size={24} /><b>这个频道还没有抓到动态</b><p>官网源会自动恢复；华尔街与微盘股频道可在 Vercel 配置对应 X 账号后启用。</p></div>}
        </div>
      </main>
    </div>
  );
}
