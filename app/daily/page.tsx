import { DailyView } from "@/components/daily-view";
import { Header } from "@/components/header";
import { getDaily } from "@/lib/data";

export const dynamic = "force-dynamic";

export default async function DailyPage() {
  const daily = await getDaily();
  return <><Header /><div className="shell"><DailyView daily={daily} /></div></>;
}
