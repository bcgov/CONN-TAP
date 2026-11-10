"use client";

import { Header, Heading } from "@bcgov/design-system-react-components";
import Link from "next/link";
import { useState, useTransition } from "react";
import { UserCircle2 } from "lucide-react";
import type { MRT_ColumnDef } from "material-react-table";
import { ConfidentialityBanner } from "@/components/confidentiality-banner";
import { DashboardSidebar } from "@/components/dashboard-sidebar";
import { MinimalFooter } from "@/components/minimal-footer";
import { ChartDataTable } from "@/components/chart-data-table";
import type { AppAssignment } from "@/lib/server/graph";
import type { OrganizationOption } from "@/lib/server/user-organizations";
import { setOrganizationAction } from "./actions";
import styles from "./admin.module.css";

export type AdminUserRow = AppAssignment & {
  lastLoginAt: string | null;
  /** Current organization as a drop-down value, or null. */
  organization: string | null;
};

const TO_ROLES = ["to_admin", "to_viewer"];

function formatDate(value: string | null): string {
  return value ? new Date(value).toLocaleDateString("en-CA") : "";
}

function OrganizationSelect({
  user,
  options,
}: {
  user: AdminUserRow;
  options: OrganizationOption[];
}) {
  // Starts on the user's current organization; Save replaces it.
  const [organization, setOrganization] = useState(user.organization ?? "");
  const [error, setError] = useState(false);
  const [isPending, startTransition] = useTransition();

  function save() {
    setError(false);
    startTransition(async () => {
      try {
        await setOrganizationAction(user.principalId, user.displayName, organization);
      } catch {
        setError(true);
      }
    });
  }

  return (
    <div className={styles.assign}>
      <select
        aria-label={`Organization for ${user.displayName}`}
        value={organization}
        onChange={(e) => setOrganization(e.target.value)}
      >
        <option value="">Choose an organization…</option>
        {options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
      <button
        type="button"
        onClick={save}
        disabled={!organization || organization === (user.organization ?? "") || isPending}
      >
        {isPending ? "Saving…" : "Save"}
      </button>
      {error && <span className={styles.error}>Couldn&apos;t save.</span>}
    </div>
  );
}

export function AdminClient({
  displayName,
  users,
  organizationOptions,
  loadError,
}: {
  displayName: string;
  users: AdminUserRow[];
  organizationOptions: OrganizationOption[];
  loadError: boolean;
}) {
  const columns: MRT_ColumnDef<AdminUserRow>[] = [
    { accessorKey: "displayName", header: "Name" },
    { accessorKey: "role", header: "Role" },
    {
      accessorKey: "lastLoginAt",
      header: "Last sign-in",
      Cell: ({ row }) => formatDate(row.original.lastLoginAt) || "Not yet",
    },
    {
      id: "organization",
      header: "Organization",
      // Organizations are assigned to people, not to Entra groups. TO roles
      // see every organization, so they don't get one.
      Cell: ({ row }) => {
        if (row.original.principalType !== "User") return "Group";
        if (TO_ROLES.includes(row.original.role)) return "All organizations";
        return <OrganizationSelect user={row.original} options={organizationOptions} />;
      },
    },
  ];

  return (
    <div className="dashboard-page">
      <ConfidentialityBanner />
      <div className="dashboard-shell">
        <DashboardSidebar showAdmin />

        <div className="dashboard-right">
          <Header
            title="Telecom Access Point"
            skipLinks={[
              <a key="main" href="#main-content">
                Skip to main content
              </a>,
            ]}
            logoLinkElement={
              <Link
                href="/"
                title="Government of British Columbia"
                prefetch={false}
              />
            }
          >
            <div className="dashboard-header__user">
              <UserCircle2 size={20} aria-hidden="true" />
              <span>{displayName}</span>
              <button
                onClick={() => {
                  window.location.href = "/auth/logout";
                }}
                className="dashboard-header__logout"
              >
                Logout
              </button>
            </div>
          </Header>

          <div className="dashboard-content">
            <main id="main-content" className={`dashboard-main ${styles.page}`}>
              <Heading level={2}>Manage users</Heading>
              {loadError ? (
                <p>Couldn&apos;t load users from Entra. Check the server logs.</p>
              ) : (
                <ChartDataTable
                  columns={columns}
                  data={users}
                  emptyLabel="No users are assigned to TAP in Entra."
                />
              )}
            </main>
            <MinimalFooter />
          </div>
        </div>
      </div>
    </div>
  );
}
