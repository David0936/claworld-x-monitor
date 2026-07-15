import { NextRequest, NextResponse } from "next/server";
import { CHANNELS, getNews } from "@/lib/news";

export async function GET(request: NextRequest) {
  const channel = request.nextUrl.searchParams.get("channel");
  const market = request.nextUrl.searchParams.get("market");
  const limit = Math.min(100, Math.max(1, Number(request.nextUrl.searchParams.get("limit") || 30)));
  const validChannel = CHANNELS.some((item) => item.key === channel) ? channel : null;
  const items = (await getNews())
    .filter((item) => (!validChannel || item.channel === validChannel) && (!market || item.market === market))
    .slice(0, limit);
  return NextResponse.json({ updatedAt: new Date().toISOString(), count: items.length, items }, { headers: { "Access-Control-Allow-Origin": "*", "Cache-Control": "public, s-maxage=900, stale-while-revalidate=3600" } });
}
