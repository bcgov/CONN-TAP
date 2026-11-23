"use client";

import { Header } from "@bcgov/design-system-react-components";
import Link from "next/link";

export function DashboardHeader({
  displayName,
  orgName = "Telecom Office",
}: {
  displayName: string;
  orgName?: string;
}) {
  const initial = displayName.trim().charAt(0).toUpperCase();

  return (
    <Header
      title="Telecom Access Point"
      skipLinks={[
        <a key="main" href="#main-content">
          Skip to main content
        </a>,
      ]}
      logoLinkElement={
        <Link href="/" title="Government of British Columbia" prefetch={false} />
      }
    >
      <div className="dashboard-header__user">
        <div className="dashboard-header__identity">
          <span className="dashboard-header__avatar" aria-hidden="true">
            {initial}
          </span>
          <div className="dashboard-header__name">
            <span className="dashboard-header__display-name">{displayName}</span>
            <span className="dashboard-header__org">{orgName}</span>
          </div>
        </div>
        <span className="dashboard-header__divider" aria-hidden="true" />
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
  );
}
