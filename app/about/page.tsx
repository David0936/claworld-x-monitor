import { ExternalLink, Github, Youtube } from "lucide-react";
import { AppShell } from "@/components/app-shell";

export default function AboutPage() {
  return <AppShell><main className="standardPage pageWidth"><header className="pageTitle"><span>ABOUT · 关于我</span><h1>David 小鱼 · Claworld</h1><p>持续追踪 AI 产业、公开市场与自建工具。这个站点把分散在官网、监管机构和 X 的新闻，整理成投资者可以快速核验的时间线。</p></header><section className="aboutHero"><div><h2>为什么做这个</h2><p>美股和韩股的 AI 标的经常由新闻、政策、供应链与市场情绪共同驱动。Claworld 不替你下结论，只负责更快发现线索、保留原始来源，并把风险放在同一屏里。</p></div><span className="aboutClaw"><img src="/brand/logo-light.png" alt="Claworld 红色蟹钳标识" /></span></section><div className="aboutLinks"><a href="https://github.com/David0936" target="_blank"><Github /> GitHub <ExternalLink size={14} /></a><a href="https://x.com/shark1996_" target="_blank">X · @Shark1996_ <ExternalLink size={14} /></a><a href="https://www.youtube.com/@Singularity2026" target="_blank"><Youtube /> YouTube <ExternalLink size={14} /></a></div><p className="legalNote">本站仅聚合公开信息并提供研究辅助，不构成投资建议。新闻与 AI 摘要可能延迟、遗漏或出错，请回到原始来源独立判断。</p></main></AppShell>;
}
