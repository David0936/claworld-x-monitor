import { NextRequest, NextResponse } from "next/server";
import { getDaily } from "@/lib/data";

export async function GET(request: NextRequest) {
  const date = request.nextUrl.searchParams.get("date") || undefined;
  return NextResponse.json(await getDaily(date), { headers: { "Access-Control-Allow-Origin": "*", "Cache-Control": "public, s-maxage=900, stale-while-revalidate=3600" } });
}
