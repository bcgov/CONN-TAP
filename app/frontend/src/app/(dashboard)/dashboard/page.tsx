import { redirect } from "next/navigation";
import { isTelecomOfficeUser, requireAuthorizedSession } from "@/lib/server/auth";
import { getVisibleDatasetIds } from "@/lib/server/datasets";
import { DashboardClient } from "./dashboard-client";

export const dynamic = "force-dynamic";

export default async function DashboardPage() {
  const session = await requireAuthorizedSession("/dashboard");
  if (!isTelecomOfficeUser(session.roles)) {
    redirect("/bge-dashboard");
  }

  const visibleDatasetIds = [...(await getVisibleDatasetIds())];

  return <DashboardClient visibleDatasetIds={visibleDatasetIds} />;
}
