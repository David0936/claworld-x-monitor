import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Claworld 投资雷达｜AI 产业投资机会日报",
  description: "聚合财经博主公开观点，提炼 AI 产业链投资线索、影响标的与反向风险。",
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || "https://claworld-x-monitor.vercel.app"),
  openGraph: {
    title: "Claworld 投资雷达",
    description: "每天 08:00 更新的 AI 产业投资机会日报",
    type: "website",
    locale: "zh_CN",
  },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
