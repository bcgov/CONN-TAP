"use client";

import { Header, Heading } from "@bcgov/design-system-react-components";
import Link from "next/link";
import { AppFooter } from "@/components/footer";

export function DashboardClient({ displayName }: { displayName: string }) {
  return (
    <div className="telecom-landing__shell">
      <Header
        title="Telecom Hub"
        skipLinks={[
          <a key="main" href="#main-content">
            Skip to main content
          </a>,
        ]}
        logoLinkElement={<Link href="/" title="Government of British Columbia" prefetch={false} />}
      />

      <main id="main-content" className="telecom-main">
        <Heading level={1}>Welcome to the Telecom Dashboard</Heading>
        <p style={{ color: "#313131", marginBottom: "2rem" }}>
          You are signed in as {displayName}.
        </p>
      </main>

      <AppFooter />
    </div>
  );
}
