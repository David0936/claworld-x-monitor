import { Bot, Braces, Check, ExternalLink, Rss } from "lucide-react";
import { AppShell } from "@/components/app-shell";

const site = process.env.NEXT_PUBLIC_SITE_URL || "https://claworld-invest-radar.vercel.app";

export default function AgentPage() {
  const prompt = `请接入 Claworld AI 投资新闻雷达：${site}/agent-skill/SKILL.md\n先阅读 Skill，再用公开只读 API 回答“过去 24 小时 AI 产业链最重要的 5 条新闻是什么？”。`;
  return <AppShell><main className="standardPage pageWidth agentPage"><header className="pageTitle"><span>AGENT · 开发者接入</span><h1>让 Agent 直接使用 <em>CLAWORLD</em></h1><p>Skill 负责理解问题；RSS 与 REST API 负责稳定传递时间线、分类与日报。公开只读，无需登录。</p></header><div className="agentModes"><a href="#skill"><Bot /><b>Agent Skill</b><span>让 Agent 自动理解问题</span></a><a href={`${site}/feed.xml`} target="_blank"><Rss /><b>RSS</b><span>订阅最新公开动态</span></a><a href={`${site}/api/news`} target="_blank"><Braces /><b>REST API</b><span>给程序与工作流使用</span></a></div><section className="agentPanel" id="skill"><span>推荐路径 · AGENT-FIRST</span><h2>把这一段发给你的 Agent</h2><pre>{prompt}</pre><div className="endpointRow"><a href="/agent-skill/SKILL.md" target="_blank">查看 SKILL.md <ExternalLink size={14} /></a><a href="/api/news" target="_blank">测试 News API <ExternalLink size={14} /></a><a href="/api/daily" target="_blank">测试 Daily API <ExternalLink size={14} /></a></div></section><section className="topicSection"><div className="sectionLabel"><h2>安装、验证、再开始使用</h2></div><div className="stepsGrid">{["审阅 SKILL.md，确认仅访问公开只读接口", "按 Agent 平台要求安装到用户级 Skills 目录", "发送验证问题，检查答案包含时间窗与原文链接"].map((step, index) => <div key={step}><i>{index + 1}</i><Check size={16} /><p>{step}</p></div>)}</div></section></main></AppShell>;
}
