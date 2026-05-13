"use client";

import {
  Footer,
  FooterLinks,
  SvgBcLogo,
} from "@bcgov/design-system-react-components";
import { useAuth } from "@/lib/auth-context";

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

export function AppFooter() {
  const { isAuthenticated, username } = useAuth();

  return (
    <Footer acknowledgement={ACKNOWLEDGEMENT}>
      <>
        <div className="bcds-footer--logo">
          <SvgBcLogo id="bcgov-logo-footer" />
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", width: "100%" }}>
          <div>{FOOTER_LINKS}</div>
          {isAuthenticated && username && (
            <div style={{ display: "flex", alignItems: "center", gap: "1rem", paddingRight: "2rem" }}>
              <span style={{ fontSize: "0.875rem", color: "#474543" }}>
                Signed in as: <strong>{username}</strong>
              </span>
              <button
                onClick={() => {
                  window.location.href = "/auth/logout";
                }}
                style={{
                  padding: "0.5rem 1rem",
                  backgroundColor: "#003366",
                  color: "white",
                  border: "none",
                  borderRadius: "0.25rem",
                  cursor: "pointer",
                  fontSize: "0.875rem",
                  fontFamily: "BC Sans, system-ui, -apple-system, sans-serif",
                }}
              >
                Logout
              </button>
            </div>
          )}
        </div>
      </>
    </Footer>
  );
}
