"use client";

import Link from "next/link";
import {
  Header,
  Heading,
  Link as BcLink,
} from "@bcgov/design-system-react-components";
import { AppFooter } from "@/components/footer";

export function HomeClient() {
  return (
    <div className="telecom-landing__shell">
      <Header
        title="Telecom Hub"
        skipLinks={[
          <a key="main" href="#main-content">
            Skip to main content
          </a>,
        ]}
        logoLinkElement={
          <Link href="/" title="Government of British Columbia" prefetch={false} />
        }
      />

      <main id="main-content" className="telecom-main">
        <Heading level={1}>Welcome to the Telecom Hub</Heading>

        <p className="telecom-main__intro">
          Explore dashboards, reports, contract information, spend and savings analytics, and key
          performance metrics for telecom services.
        </p>

        <div className="telecom-main__login-block">
          <BcLink
            href="/auth/login?returnTo=/dashboard"
            isButton
            buttonVariant="primary"
            size="large"
          >
            Login with IDIR
          </BcLink>
          <p className="telecom-main__login-hint">
            Use your IDIR credentials to securely access the system.
          </p>
        </div>

        <div className="telecom-main__access">
          <strong>Need access?</strong>
          <br />
          Contact your Telecom Office administrator or{" "}
          <BcLink href="mailto:example@gov.bc.ca">email us</BcLink> to request access.
        </div>

        <Heading className="telecom-main__features-title" level={2}>
          What you can do in Telecom Hub
        </Heading>

        <ul className="telecom-main__list">
          <li>
            <strong>View Reports</strong>
            <br />
            Access ready-made reports that summarize key telecom data, trends, and performance
            insights.
          </li>
          <li>
            <strong>Analyze Data</strong>
            <br />
            Explore interactive dashboards to filter, compare, and understand telecom metrics
            across services and organizations.
          </li>
          <li>
            <strong>Customize dashboards</strong>
            <br />
            Customize dashboards to visualize the data that matters most to your team.
          </li>
        </ul>
      </main>

      <AppFooter />
    </div>
  );
}
