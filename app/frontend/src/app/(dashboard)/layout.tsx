import { DashboardLayout } from "@/components/dashboard-layout";
import { getCurrentSession, isTelecomOfficeUser } from "@/lib/server/auth";
import { getOrganizationName } from "@/lib/server/user-organizations";

export const dynamic = "force-dynamic";

// Each page still checks the session and role itself and redirects when needed;
// this layout only reads the session to fill in the shared header and nav bar.
export default async function SignedInLayout({ children }: { children: React.ReactNode }) {
  const session = await getCurrentSession();
  if (!session) {
    return children;
  }

  const displayName = session.name ?? session.username ?? session.email ?? "an authorized user";
  const orgName = await getOrganizationName(session.subject);
  const homeHref = isTelecomOfficeUser(session.roles) ? "/dashboard" : "/bge-dashboard";

  return (
    <DashboardLayout
      displayName={displayName}
      orgName={orgName ?? undefined}
      homeHref={homeHref}
      showAdmin={session.roles.includes("to_admin")}
    >
      {children}
    </DashboardLayout>
  );
}
