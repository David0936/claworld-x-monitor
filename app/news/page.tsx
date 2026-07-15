import { Header } from "@/components/header";
import { NewsRadar } from "@/components/news-radar";
import { CHANNELS, getNews } from "@/lib/news";
import type { NewsChannelKey, NewsMarket } from "@/lib/types";

export const dynamic = "force-dynamic";

export default async function NewsPage({ searchParams }: { searchParams: Promise<{ channel?: string; market?: string }> }) {
  const params = await searchParams;
  const active: NewsChannelKey | "all" = CHANNELS.some((channel) => channel.key === params.channel) ? params.channel as NewsChannelKey : "all";
  const market: NewsMarket | "全部" = ["美股", "韩股", "全球"].includes(params.market || "") ? params.market as NewsMarket : "全部";
  const items = await getNews();
  return <><Header /><NewsRadar items={items} active={active} market={market} /></>;
}
