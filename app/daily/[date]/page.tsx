import { DailyView } from "@/components/daily-view";
import { AppShell } from "@/components/app-shell";
import { getDaily } from "@/lib/data";

export const dynamic = "force-dynamic";

export default async function DatedDailyPage({ params }: { params: Promise<{ date: string }> }) {
  const { date } = await params;
  const daily = await getDaily(date);
  return <AppShell><div className="pageWidth"><DailyView daily={daily} /></div></AppShell>;
}
