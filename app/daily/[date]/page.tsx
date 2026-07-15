import { DailyView } from "@/components/daily-view";
import { Header } from "@/components/header";
import { getDaily } from "@/lib/data";

export const dynamic = "force-dynamic";

export default async function DatedDailyPage({ params }: { params: Promise<{ date: string }> }) {
  const { date } = await params;
  const daily = await getDaily(date);
  return <><Header /><div className="shell"><DailyView daily={daily} /></div></>;
}
