import Link from "next/link";
import { Activity, Github, Newspaper, Radar } from "lucide-react";

export function Header() {
  return (
    <header className="siteHeader">
      <div className="headerInner">
        <Link href="/daily" className="brand" aria-label="Claworld 投资雷达首页">
          <span className="brandMark"><Radar size={19} strokeWidth={2.2} /></span>
          <span><b>CLAWORLD</b><small>INVESTMENT RADAR</small></span>
        </Link>
        <nav className="mainNav" aria-label="主导航">
          <Link href="/news" className="active"><Newspaper size={15} /> 新闻雷达</Link>
          <Link href="/daily"><Activity size={15} /> 每日简报</Link>
          <Link href="/archive">归档</Link>
          <a href="https://github.com/David0936/claworld-x-monitor" target="_blank" rel="noreferrer" aria-label="GitHub"><Github size={17} /></a>
        </nav>
      </div>
    </header>
  );
}
