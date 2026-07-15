import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Claworld 新闻雷达｜AI 产业美股韩股情绪与催化",
  description: "聚合 AI 产业、美国政府、华尔街机构、全球供应链与微盘股动态，追踪美股韩股新闻情绪。",
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || "https://claworld-x-monitor.vercel.app"),
  openGraph: {
    title: "Claworld 投资雷达",
    description: "AI 产业美股韩股情绪、新闻与催化雷达",
    type: "website",
    locale: "zh_CN",
    images: [{ url: "/brand/logo-light.png", width: 1200, height: 169, alt: "Claworld" }],
  },
  icons: { icon: "/brand/logo-light.png" },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
