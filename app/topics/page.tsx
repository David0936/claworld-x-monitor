import Link from "next/link";
import { ArrowRight, Building2, Cpu, Landmark, Sparkles, Zap } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { CHANNELS, getNews } from "@/lib/news";

const icons = { ai: Sparkles, government: Landmark, wallstreet: Building2, "supply-chain": Cpu, microcap: Zap };
const companyGroups = [
  { title: "AI 芯片与算力", symbols: "NVDA · AMD · AVGO · TSM · MU" },
  { title: "韩国半导体", symbols: "Samsung · SK hynix · Hanmi" },
  { title: "云与模型平台", symbols: "MSFT · GOOGL · AMZN · META" },
  { title: "AI 应用与数据", symbols: "PLTR · CRWV · 软件应用" },
];

export const dynamic = "force-dynamic";

export default async function TopicsPage() {
  const news = await getNews();
  return <AppShell><main className="standardPage pageWidth"><header className="pageTitle"><span>TOPICS · 分类地图</span><h1>按主题看 AI 投资新闻</h1><p>把政策、机构观点、产业链和微盘股催化拆开，减少信息流里的噪音。</p></header><section className="topicSection"><div className="sectionLabel"><h2>新闻频道</h2><p>按信息来源与市场角色分类</p></div><div className="topicGrid">{CHANNELS.map((channel) => { const Icon = icons[channel.key]; const count = news.filter((item) => item.channel === channel.key).length; return <Link href={`/news?channel=${channel.key}`} className="topicCard" key={channel.key}><Icon size={22} /><h3>{channel.name}</h3><p>{channel.short}</p><span>查看 {count} 条动态 <ArrowRight size={14} /></span></Link>; })}</div></section><section className="topicSection"><div className="sectionLabel"><h2>产业链主题</h2><p>美股与韩股的关键公司组</p></div><div className="topicGrid companyGrid">{companyGroups.map((group) => <div className="topicCard" key={group.title}><h3>{group.title}</h3><p>{group.symbols}</p><span>持续追踪</span></div>)}</div></section></main></AppShell>;
}
