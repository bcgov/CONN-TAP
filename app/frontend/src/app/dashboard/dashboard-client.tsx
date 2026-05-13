"use client";

import { Header, Heading } from "@bcgov/design-system-react-components";
import Link from "next/link";
import { UserCircle2 } from "lucide-react";
import { DashboardSidebar } from "@/components/dashboard-sidebar";

export function DashboardClient({ displayName }: { displayName: string }) {
  return (
    <div className="dashboard-shell">
      <Header
        title="Telecom Hub"
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

      <div className="dashboard-body">
        <DashboardSidebar />
        <main id="main-content" className="dashboard-main">
          <Heading level={1}>Welcome to the Telecom Dashboard</Heading>
          <p style={{ color: "#313131", marginBottom: "2rem" }}>
            You are signed in as {displayName}.
          </p>
        </main>
      </div>
    </div>
  );
}
