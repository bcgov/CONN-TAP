import { getCurrentSession } from "@/lib/server/auth";
import { UnauthorizedClient } from "./unauthorized-client";

export default async function UnauthorizedPage() {
  const session = await getCurrentSession();
  const displayName = session?.name ?? session?.username ?? null;

  return <UnauthorizedClient displayName={displayName} />;
}
