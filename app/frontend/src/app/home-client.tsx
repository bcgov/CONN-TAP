"use client";

import Image from "next/image";
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
        title="Telecom Access Point"
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
        <section className="dashboard-card telecom-main__card">
          <Heading level={1}>
            Welcome to the
            <br />
            Telecom Access Point
          </Heading>
          <hr className="telecom-main__rule" />

          <p>Access telecom information for your organization.</p>
          <p>
            The Telecom Access Point (TAP) provides access to telecom dashboards, reports, and
            spend insights.
          </p>

          <div>
            <p className="telecom-main__login-label">Sign in to get started</p>
            <BcLink
              href="/auth/login?returnTo=/dashboard"
              isButton
              buttonVariant="primary"
              size="large"
            >
              Log in with IDIR
            </BcLink>
          </div>

          <div className="telecom-main__access">
            <strong>Need access?</strong>
            <p>
              Contact the{" "}
              <BcLink href="mailto:LCTZ.CIOAdminReports@gov.bc.ca">Telecom Office</BcLink> to
              request access and provide feedback.
            </p>
          </div>
        </section>

        <Heading className="telecom-main__features-title" level={2}>
          What you can do in the Telecom Access Point
        </Heading>
        <p>
          View reports and analyze telecom data to better understand telecom spending within your
          organization.
        </p>

        <ul className="telecom-main__features">
          <li className="dashboard-card telecom-feature">
            <Image src="/assets/dashboards.svg" alt="" width={334} height={186} />
            <strong>Dashboards</strong>
          </li>
          <li className="dashboard-card telecom-feature">
            <Image src="/assets/reports.svg" alt="" width={334} height={186} />
            <strong>Reports</strong>
          </li>
          <li className="dashboard-card telecom-feature">
            <Image src="/assets/spend-insights.svg" alt="" width={334} height={186} />
            <strong>Spend Insights</strong>
          </li>
        </ul>
      </main>

      <AppFooter showAcknowledgement />
    </div>
  );
}
