import { DailyView } from "@/components/daily-view";
import { AppShell } from "@/components/app-shell";
import { getDaily } from "@/lib/data";

export const dynamic = "force-dynamic";

export default async function DailyPage() {
  const daily = await getDaily();
  return <AppShell><div className="pageWidth"><DailyView daily={daily} /></div></AppShell>;
}
