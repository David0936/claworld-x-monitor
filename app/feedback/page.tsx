import { ExternalLink, Github, MessageCircle } from "lucide-react";
import { AppShell } from "@/components/app-shell";

export default function FeedbackPage() {
  const issue = "https://github.com/David0936/claworld-x-monitor/issues/new?title=%5B%E5%8F%8D%E9%A6%88%5D%20&body=%E9%A1%B5%E9%9D%A2%2F%E5%8A%9F%E8%83%BD%EF%BC%9A%0A%0A%E9%97%AE%E9%A2%98%E6%88%96%E5%BB%BA%E8%AE%AE%EF%BC%9A%0A%0A%E6%88%AA%E5%9B%BE%2F%E9%93%BE%E6%8E%A5%EF%BC%9A";
  return <AppShell><main className="standardPage pageWidth feedbackPage"><header className="pageTitle"><span>FEEDBACK · 反馈</span><h1>告诉我哪里还不够好</h1><p>错漏新闻、分类不准、信源建议或功能需求，都欢迎直接提交。</p></header><div className="feedbackOptions"><a href={issue} target="_blank"><Github /><div><b>提交 GitHub Issue</b><p>适合 Bug、功能需求和可公开讨论的建议。</p></div><ExternalLink size={16} /></a><a href="https://x.com/shark1996_" target="_blank"><MessageCircle /><div><b>在 X 联系我</b><p>适合快速交流信源与市场线索。</p></div><ExternalLink size={16} /></a></div></main></AppShell>;
}
