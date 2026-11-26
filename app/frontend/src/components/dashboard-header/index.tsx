"use client";

import { Button, Header } from "@bcgov/design-system-react-components";
import Link from "next/link";
import styles from "./dashboard-header.module.css";

type DashboardHeaderProps = {
  displayName: string;
  orgName?: string;
  title?: string;
  signOutHref?: string;
};

export function DashboardHeader({
  displayName,
  orgName = "Telecom Office",
  title = "Telecom Access Point",
  signOutHref = "/auth/logout",
}: DashboardHeaderProps) {
  const initial = displayName.trim().charAt(0).toUpperCase();

  return (
    <div className={styles.header}>
      <Header
        title={title}
        skipLinks={[
          <a key="main" href="#main-content">
            Skip to main content
          </a>,
        ]}
        logoLinkElement={
          <Link href="/" title="Government of British Columbia" prefetch={false} />
        }
      >
        <div className={styles.user}>
          <div className={styles.identity}>
            <span className={styles.avatar} aria-hidden="true">
              {initial}
            </span>
            <div className={styles.names}>
              <span className={styles.displayName}>{displayName}</span>
              <span className={styles.orgName}>{orgName}</span>
            </div>
          </div>
          <span className={styles.divider} aria-hidden="true" />
          <Button
            variant="secondary"
            onPress={() => {
              window.location.href = signOutHref;
            }}
          >
            Sign out
          </Button>
        </div>
      </Header>
    </div>
  );
}
