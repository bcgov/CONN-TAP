import { redirect } from "next/navigation";
import { isTelecomOfficeUser, requireAuthorizedSession } from "@/lib/server/auth";
import { getVisibleDatasetIds } from "@/lib/server/datasets";
import { getOrganizationName } from "@/lib/server/user-organizations";
import { DashboardClient } from "./dashboard-client";

export const dynamic = "force-dynamic";

export default async function DashboardPage() {
  const session = await requireAuthorizedSession("/dashboard");
  if (!isTelecomOfficeUser(session.roles)) {
    redirect("/bge-dashboard");
  }

  const displayName = session.name ?? session.username ?? session.email ?? "an authorized user";
  const visibleDatasetIds = [...(await getVisibleDatasetIds())];

  const orgName = await getOrganizationName(session.subject);
  const isAdmin = session.roles.includes("to_admin");

  return (
    <DashboardClient
      displayName={displayName}
      orgName={orgName ?? undefined}
      visibleDatasetIds={visibleDatasetIds}
      isAdmin={isAdmin}
    />
  );
}
