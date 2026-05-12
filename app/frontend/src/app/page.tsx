"use client";

import Link from "next/link";
import {
  Footer,
  FooterLinks,
  Header,
  Heading,
  Link as BcLink,
  SvgBcLogo,
} from "@bcgov/design-system-react-components";

const ACKNOWLEDGEMENT = (
  <p>
    The B.C. Public Service acknowledges the territories of First Nations around B.C. and is
    grateful to carry out our work on these lands. We acknowledge the rights, interests,
    priorities, and concerns of all Indigenous Peoples - First Nations, Métis, and Inuit -
    respecting and acknowledging their distinct cultures, histories, rights, laws, and governments.
  </p>
);

const FOOTER_LINKS = (
  <FooterLinks
    title="More info"
    links={[
      <a key="home" href="https://www2.gov.bc.ca/gov/content/home">
        Home
      </a>,
      <a key="copyright" href="https://www2.gov.bc.ca/gov/content?id=1AAACC9C65754E4D89A118B875E0FBDA">
        Copyright
      </a>,
      <a key="accessibility" href="https://www2.gov.bc.ca/gov/content?id=E08E79740F9C41B9B0C484685CC5E412">
        Accessibility
      </a>,
      <a key="disclaimer" href="https://www2.gov.bc.ca/gov/content?id=79F93E018712422FBC8E674A67A70535">
        Disclaimer
      </a>,
      <a key="privacy" href="https://www2.gov.bc.ca/gov/content?id=9E890E16955E4FF4BF3B0E07B4722932">
        Privacy
      </a>,
      <a key="contact" href="https://www2.gov.bc.ca/gov/content?id=6A77C17D0CCB48F897F8598CCC019111">
        Contact Us
      </a>,
    ]}
  />
);

export default function HomePage() {
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
          <BcLink href="#" isButton buttonVariant="primary" size="large">
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

      <Footer acknowledgement={ACKNOWLEDGEMENT}>
        <>
          <div className="bcds-footer--logo">
            <SvgBcLogo id="bcgov-logo-footer" />
          </div>
          {FOOTER_LINKS}
        </>
      </Footer>
    </div>
  );
}
