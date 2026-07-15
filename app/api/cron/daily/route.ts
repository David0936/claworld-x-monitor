import { NextRequest, NextResponse } from "next/server";
import { saveDaily } from "@/lib/data";
import { generateDaily } from "@/lib/generate";

export const maxDuration = 300;

export async function GET(request: NextRequest) {
  const secret = process.env.CRON_SECRET;
  if (!secret || request.headers.get("authorization") !== `Bearer ${secret}`) {
    return NextResponse.json({ ok: false, error: "Unauthorized" }, { status: 401 });
  }
  try {
    const daily = await generateDaily();
    const blob = await saveDaily(daily);
    return NextResponse.json({ ok: true, date: daily.date, opportunities: daily.stats.opportunities, url: blob.url });
  } catch (error) {
    return NextResponse.json({ ok: false, error: error instanceof Error ? error.message : "生成失败" }, { status: 500 });
  }
}
