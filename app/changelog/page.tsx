import { AppShell } from "@/components/app-shell";

const entries = [
  { version: "2.2.0", date: "2026-07-15", title: "Claworld 红色品牌版", items: ["使用官方 Logo 与红色视觉系统", "新增时间线与分类主题", "开放 RSS、REST API 与 Agent Skill", "新增关于、反馈和更新日志页面"] },
  { version: "2.1.0", date: "2026-07-15", title: "多频道新闻雷达", items: ["新增 AI 产业、美国政府、华尔街、全球产业链与微盘股频道", "接入免费官网与监管 RSS", "新增美股、韩股新闻情绪"] },
  { version: "2.0.0", date: "2026-07-15", title: "AI 投资日报上线", items: ["部署 Vercel 日报网站", "新增 Blob 历史归档", "每天北京时间 08:00 自动生成"] },
];

export default function ChangelogPage() {
  return <AppShell><main className="standardPage pageWidth"><header className="pageTitle"><span>CHANGELOG · 产品记录</span><h1>更新日志</h1><p>每次上线了什么、为什么改，都留在这里。</p></header><div className="changeList">{entries.map((entry) => <article key={entry.version}><div className="changeMeta"><b>v{entry.version}</b><time>{entry.date}</time></div><div><h2>{entry.title}</h2><ul>{entry.items.map((item) => <li key={item}>{item}</li>)}</ul></div></article>)}</div></main></AppShell>;
}
