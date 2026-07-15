import { list, put } from "@vercel/blob";
import preview from "@/data/preview-daily.json";
import type { DailyBriefing } from "@/lib/types";

const PREFIX = "daily/";

export async function getDaily(date?: string): Promise<DailyBriefing> {
  if (!process.env.BLOB_READ_WRITE_TOKEN) return preview as DailyBriefing;

  try {
    const target = date ? `${PREFIX}${date}.json` : undefined;
    const { blobs } = await list({ prefix: target || PREFIX, limit: 100 });
    const blob = target
      ? blobs.find((item) => item.pathname === target)
      : blobs.sort((a, b) => b.pathname.localeCompare(a.pathname))[0];
    if (!blob) return preview as DailyBriefing;
    const response = await fetch(blob.url, { cache: "no-store" });
    if (!response.ok) throw new Error("日报读取失败");
    return (await response.json()) as DailyBriefing;
  } catch {
    return preview as DailyBriefing;
  }
}

export async function getArchive(): Promise<Array<{ date: string; url: string }>> {
  if (!process.env.BLOB_READ_WRITE_TOKEN) return [{ date: preview.date, url: `/daily/${preview.date}` }];
  try {
    const { blobs } = await list({ prefix: PREFIX, limit: 100 });
    return blobs
      .map((blob) => blob.pathname.match(/^daily\/(\d{4}-\d{2}-\d{2})\.json$/)?.[1])
      .filter((date): date is string => Boolean(date))
      .sort((a, b) => b.localeCompare(a))
      .map((date) => ({ date, url: `/daily/${date}` }));
  } catch {
    return [];
  }
}

export async function saveDaily(daily: DailyBriefing) {
  return put(`${PREFIX}${daily.date}.json`, JSON.stringify(daily), {
    access: "public",
    addRandomSuffix: false,
    contentType: "application/json",
  });
}
