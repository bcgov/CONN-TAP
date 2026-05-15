"use client";

import Link from "next/link";
import {
  Header,
  Heading,
  Link as BcLink,
} from "@bcgov/design-system-react-components";
import { ShieldX } from "lucide-react";
import { AppFooter } from "@/components/footer";

export function UnauthorizedClient({
  displayName,
}: {
  displayName: string | null;
}) {
  return (
    <div className="telecom-landing__shell">
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
      />

      <main id="main-content" className="telecom-main">
        <div className="unauthorized-icon">
          <ShieldX size={48} aria-hidden="true" />
        </div>

        <Heading level={1}>Access Denied</Heading>

        <p className="telecom-main__intro">
          {displayName ? (
            <>
              Sorry <strong>{displayName}</strong>, you do not have the required
              role to access this application.
            </>
          ) : (
            <>
              Sorry, you do not have the required role to access this
              application.
            </>
          )}
        </p>

        <p>
          Please contact your Telecom Office administrator or{" "}
          <BcLink href="mailto:example@gov.bc.ca">email us</BcLink> to request
          access.
        </p>

        <div className="unauthorized-actions">
          <BcLink href="/auth/logout" isButton buttonVariant="primary">
            Sign out
          </BcLink>
          <BcLink href="/" isButton buttonVariant="secondary">
            Back to home
          </BcLink>
        </div>
      </main>

      <AppFooter showAcknowledgement />
    </div>
  );
}
