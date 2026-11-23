import { requireAuthorizedSession } from "@/lib/server/auth";
import { getOrganizationName } from "@/lib/server/user-organizations";
import { BgeDashboardClient } from "./bge-dashboard-client";

export const dynamic = "force-dynamic";

export default async function BgeDashboardPage() {
  const session = await requireAuthorizedSession("/bge-dashboard");
  const displayName = session.name ?? session.username ?? session.email ?? "an authorized user";
  const orgName = await getOrganizationName(session.subject);
  const isAdmin = session.roles.includes("to_admin");

  return (
    <BgeDashboardClient
      displayName={displayName}
      orgName={orgName ?? undefined}
      isAdmin={isAdmin}
    />
  );
}
