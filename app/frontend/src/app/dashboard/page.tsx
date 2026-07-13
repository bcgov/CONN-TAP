import { requireAuthorizedSession } from "@/lib/server/auth";
import { getVisibleDatasetIds } from "@/lib/server/datasets";
import { DashboardClient } from "./dashboard-client";

export const dynamic = "force-dynamic";

export default async function DashboardPage() {
  const session = await requireAuthorizedSession("/dashboard");
  const displayName = session.name ?? session.username ?? session.email ?? "an authorized user";
  const visibleDatasetIds = [...(await getVisibleDatasetIds(session))];

  return <DashboardClient displayName={displayName} visibleDatasetIds={visibleDatasetIds} />;
}
