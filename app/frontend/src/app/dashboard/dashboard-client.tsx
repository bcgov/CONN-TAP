"use client";

import { Header, Heading } from "@bcgov/design-system-react-components";
import Link from "next/link";
import { UserCircle2 } from "lucide-react";
import { DashboardSidebar } from "@/components/dashboard-sidebar";
import { MinimalFooter } from "@/components/minimal-footer";

export function DashboardClient({ displayName }: { displayName: string }) {
  return (
    <div className="dashboard-shell">
      <DashboardSidebar />

      <div className="dashboard-right">
        <Header
          title="Telecom Access Point"
          skipLinks={[
            <a key="main" href="#main-content">
              Skip to main content
            </a>,
          ]}
          logoLinkElement={<Link href="/" title="Government of British Columbia" prefetch={false} />}
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
          <main id="main-content" className="dashboard-main">
            <Heading level={1}>Welcome to the Telecom Access Point</Heading>
            <p style={{ color: "#313131", marginBottom: "2rem" }}>
              You are signed in as {displayName}.
            </p>
          </main>
          <MinimalFooter />
        </div>
      </div>
    </div>
  );
}
