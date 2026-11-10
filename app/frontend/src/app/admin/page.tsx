import { redirect } from "next/navigation";
import { requireAuthorizedSession } from "@/lib/server/auth";
import { listAppAssignments } from "@/lib/server/graph";
import { listOrganizationOptions, listTapUsers } from "@/lib/server/user-organizations";
import { AdminClient, type AdminUserRow } from "./admin-client";

export const dynamic = "force-dynamic";

export default async function AdminPage() {
  const session = await requireAuthorizedSession("/admin");
  // Only TO admins manage users and their organizations.
  if (!session.roles.includes("to_admin")) {
    redirect("/unauthorized");
  }
  const displayName = session.name ?? session.username ?? session.email ?? "an authorized user";

  let users: AdminUserRow[] = [];
  let loadError = false;
  try {
    const assignments = await listAppAssignments();
    const tapUsers = await listTapUsers(assignments.map((a) => a.principalId));
    users = assignments.map((a) => ({
      ...a,
      lastLoginAt: tapUsers.get(a.principalId)?.lastLoginAt ?? null,
      organization: tapUsers.get(a.principalId)?.organization ?? null,
    }));
  } catch (error) {
    console.error("Failed to list TAP users", error);
    loadError = true;
  }
  const organizationOptions = await listOrganizationOptions();

  return (
    <AdminClient
      displayName={displayName}
      users={users}
      organizationOptions={organizationOptions}
      loadError={loadError}
    />
  );
}
