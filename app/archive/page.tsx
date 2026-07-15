import Link from "next/link";
import { CalendarDays, ChevronRight } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { getArchive } from "@/lib/data";

export const dynamic = "force-dynamic";

export default async function ArchivePage() {
  const archive = await getArchive();
  const groups = archive.reduce<Record<string, typeof archive>>((acc, item) => {
    const month = item.date.slice(0, 7);
    (acc[month] ||= []).push(item);
    return acc;
  }, {});
  return <AppShell><main className="archive pageWidth"><div className="archiveIntro"><span>ARCHIVE</span><h1>历史日报</h1><p>按日期回看 AI 产业叙事、资金关注点和风险信号如何变化。</p></div>{Object.entries(groups).map(([month, items]) => <section key={month}><h2>{month.replace("-", " 年 ")} 月</h2>{items.map((item) => <Link href={item.url} key={item.date}><CalendarDays size={17} /><span>{item.date}</span><ChevronRight size={16} /></Link>)}</section>)}</main></AppShell>;
}
