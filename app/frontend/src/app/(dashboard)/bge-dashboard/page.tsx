import { redirect } from "next/navigation";
import { isTelecomOfficeUser, requireAuthorizedSession } from "@/lib/server/auth";
import { BgeDashboardClient } from "./bge-dashboard-client";

export const dynamic = "force-dynamic";

export default async function BgeDashboardPage() {
  const session = await requireAuthorizedSession("/bge-dashboard");
  if (isTelecomOfficeUser(session.roles)) {
    redirect("/dashboard");
  }

  return <BgeDashboardClient />;
}
