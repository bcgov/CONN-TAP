import { redirect } from "next/navigation";
import { isTelecomOfficeUser, requireAuthorizedSession } from "@/lib/server/auth";
import { getOrganizationName } from "@/lib/server/user-organizations";
import { BgeDashboardClient } from "./bge-dashboard-client";

export const dynamic = "force-dynamic";

export default async function BgeDashboardPage() {
  const session = await requireAuthorizedSession("/bge-dashboard");
  if (isTelecomOfficeUser(session.roles)) {
    redirect("/dashboard");
  }

  const displayName = session.name ?? session.username ?? session.email ?? "an authorized user";
  const orgName = await getOrganizationName(session.subject);

  return <BgeDashboardClient displayName={displayName} orgName={orgName ?? undefined} />;
}
