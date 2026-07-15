import Link from "next/link";
import { ArrowUpRight, CalendarDays, ChevronRight, Clock3, Radio, ShieldAlert, Sparkles } from "lucide-react";
import type { DailyBriefing, Opportunity } from "@/lib/types";

function formatDate(date: string) {
  return new Intl.DateTimeFormat("zh-CN", { timeZone: "Asia/Shanghai", year: "numeric", month: "long", day: "numeric", weekday: "long" }).format(new Date(`${date}T12:00:00+08:00`));
}

function OpportunityCard({ item, index }: { item: Opportunity; index: number }) {
  const tone = item.impact === "利好" ? "positive" : item.impact === "利空" ? "negative" : "neutral";
  return (
    <article className="opportunity" id={item.id}>
      <div className="opportunityRail"><span>{String(index + 1).padStart(2, "0")}</span></div>
      <div className="opportunityBody">
        <div className="itemMeta">
          <span className={`signal ${tone}`}>{item.impact}</span>
          <span>{item.horizon}</span>
          <span>置信度 {item.confidence}</span>
        </div>
        <h3>{item.title}</h3>
        <p className="itemSummary">{item.summary}</p>
        <div className="thesis"><Sparkles size={16} /><div><b>投资逻辑</b><p>{item.thesis}</p></div></div>
        {!!item.tickers?.length && (
          <div className="tickers">
            {item.tickers.map((ticker) => <span key={`${ticker.market}-${ticker.symbol}`}><i>{ticker.market}</i>{ticker.symbol}{ticker.name ? ` · ${ticker.name}` : ""}</span>)}
          </div>
        )}
        <div className="risk"><ShieldAlert size={15} /><span><b>风险：</b>{item.risk}</span></div>
        <a className="source" href={item.sourceUrl} target="_blank" rel="noreferrer">
          <span>{item.source || `X · @${item.author}`}</span><ArrowUpRight size={15} />
        </a>
      </div>
    </article>
  );
}

export function DailyView({ daily }: { daily: DailyBriefing }) {
  const allItems = daily.categories.flatMap((category) => category.items);
  let runningIndex = 0;
  return (
    <>
      <section className="editionBar">
        <div><Radio size={14} /><span>每日 08:00 更新</span></div>
        <Link href="/archive">查看全部日报 <ChevronRight size={14} /></Link>
      </section>

      <section className="hero">
        <div className="eyebrow">CLAWORLD INTELLIGENCE · {daily.status === "preview" ? "PREVIEW" : "DAILY"}</div>
        <div className="dateLine"><CalendarDays size={16} /> {formatDate(daily.date)}</div>
        <h1>{daily.title}</h1>
        <p>{daily.summary}</p>
        {daily.status === "preview" && <div className="previewNotice">当前为无密钥预览。接入环境变量后，首份真实日报将在下一次定时任务运行时替换此页。</div>}
        <div className="stats">
          <div><strong>{daily.stats.posts}</strong><span>监测帖子</span></div>
          <div><strong>{daily.stats.sources}</strong><span>信息源</span></div>
          <div><strong>{daily.stats.opportunities}</strong><span>投资线索</span></div>
          <div><strong>{daily.stats.tickers}</strong><span>关联标的</span></div>
        </div>
      </section>

      <div className="pageGrid">
        <aside className="contents">
          <span className="asideLabel">今日目录</span>
          {daily.categories.map((category, i) => (
            <a href={`#${category.key}`} key={category.key}><b>{String(i + 1).padStart(2, "0")}</b><span>{category.name}<small>{category.items.length} 条线索</small></span></a>
          ))}
          <div className="asideDisclaimer">信息聚合与研究辅助<br />不构成任何投资建议</div>
        </aside>

        <main className="report">
          <section className="pulse">
            <span>MARKET PULSE</span>
            <p>{daily.marketPulse}</p>
          </section>
          {daily.categories.map((category, categoryIndex) => {
            const start = runningIndex;
            runningIndex += category.items.length;
            return (
              <section className="category" id={category.key} key={category.key}>
                <div className="categoryHeader">
                  <span>{String(categoryIndex + 1).padStart(2, "0")}</span>
                  <div><h2>{category.name}</h2><p>{category.description}</p></div>
                </div>
                {category.items.map((item, itemIndex) => <OpportunityCard item={item} index={start + itemIndex} key={item.id} />)}
              </section>
            );
          })}
          {!allItems.length && <div className="empty">今天没有达到收录门槛的投资线索。</div>}
          <footer className="reportFooter">
            <Clock3 size={15} /> 生成于 {new Date(daily.generatedAt).toLocaleString("zh-CN", { timeZone: "Asia/Shanghai" })} · AI 摘要可能出错，请核验原文
          </footer>
        </main>
      </div>
    </>
  );
}
