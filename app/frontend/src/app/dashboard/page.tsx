import { requireSession } from "@/lib/server/auth";
import { DashboardClient } from "./dashboard-client";

export default async function DashboardPage() {
  const session = await requireSession("/dashboard");
  const displayName = session.name ?? session.username ?? session.email ?? "an authorized user";

  return <DashboardClient displayName={displayName} />;
}
