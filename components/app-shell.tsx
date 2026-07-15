"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Bot, CalendarDays, Clock3, FileClock, FolderKanban, Github, Heart, MessageCircle, Rss, Send, UserRound } from "lucide-react";

const groups = [
  { label: "内容", items: [
    { href: "/news", label: "时间线", icon: Clock3 },
    { href: "/daily", label: "AI 日报", icon: CalendarDays },
    { href: "/topics", label: "分类主题", icon: FolderKanban },
  ] },
  { label: "接入", items: [
    { href: "/agent", label: "Agent 接入", icon: Bot },
    { href: "/feed.xml", label: "RSS 订阅", icon: Rss, external: true },
  ] },
  { label: "更多", items: [
    { href: "/about", label: "关于我", icon: UserRound },
    { href: "/changelog", label: "更新日志", icon: FileClock },
    { href: "/feedback", label: "反馈", icon: MessageCircle },
  ] },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  return (
    <div className="appFrame">
      <aside className="appSidebar">
        <Link href="/news" className="sideBrand">
          <span className="clawCrop"><Image src="/brand/logo-light.png" alt="Claworld" width={3925} height={554} priority /></span>
          <span><b>CLAWORLD</b><small>AI INVESTMENT INTELLIGENCE</small></span>
        </Link>
        <div className="sideRule" />
        {groups.map((group) => <nav className="sideGroup" key={group.label} aria-label={group.label}>
          <span className="sideGroupLabel">{group.label}</span>
          {group.items.map((item) => {
            const Icon = item.icon;
            const active = pathname === item.href || (item.href !== "/news" && pathname.startsWith(`${item.href}/`));
            return <Link href={item.href} className={active ? "active" : ""} key={item.href} target={item.external ? "_blank" : undefined}><Icon size={17} /><span>{item.label}</span></Link>;
          })}
        </nav>)}
        <div className="sideFoot">
          <a href="https://github.com/David0936/claworld-x-monitor" target="_blank" rel="noreferrer"><Github size={15} /> Open Source</a>
          <span><Heart size={13} /> David 小鱼</span>
        </div>
      </aside>
      <header className="mobileHeader">
        <Link href="/news"><span className="clawCrop"><Image src="/brand/logo-light.png" alt="Claworld" width={3925} height={554} /></span><b>CLAWORLD</b></Link>
        <Link href="/feedback" aria-label="反馈"><Send size={17} /></Link>
      </header>
      <div className="appContent">{children}</div>
      <nav className="mobileNav" aria-label="移动端导航">
        {groups[0].items.concat(groups[1].items[0], groups[2].items[0]).map((item) => { const Icon = item.icon; return <Link href={item.href} className={pathname.startsWith(item.href) ? "active" : ""} key={item.href}><Icon size={18} /><span>{item.label.replace("AI ", "")}</span></Link>; })}
      </nav>
    </div>
  );
}
