import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { HomeClient } from "@/app/home-client";

vi.mock("next/image", () => ({
  default: ({ alt }: { alt: string }) => <img alt={alt} />,
}));
vi.mock("@/components/footer", () => ({ AppFooter: () => null }));

describe("HomeClient", () => {
  it("renders the welcome heading", () => {
    render(<HomeClient />);

    expect(
      screen.getByRole("heading", { level: 1, name: /telecom access point/i }),
    ).toBeInTheDocument();
  });

  it("renders the login and contact links", () => {
    render(<HomeClient />);

    expect(screen.getByRole("link", { name: "Log in with IDIR" })).toHaveAttribute(
      "href",
      "/auth/login?returnTo=/dashboard",
    );
    expect(screen.getByRole("link", { name: "Telecom Office" })).toHaveAttribute(
      "href",
      "mailto:LCTZ.CIOAdminReports@gov.bc.ca",
    );
  });

  it("links to the CHEFS test form in a new tab when configured", () => {
    const formUrl = "https://submit.digital.gov.bc.ca/app/form/submit?f=abc";
    render(<HomeClient chefsFormUrl={formUrl} />);

    const link = screen.getByRole("link", { name: /CHEFS test form/i });
    expect(link).toHaveAttribute("href", formUrl);
    expect(link).toHaveAttribute("target", "_blank");
    expect(link).toHaveAttribute("rel", "noopener noreferrer");
  });

  it("hides the CHEFS test form link when not configured", () => {
    render(<HomeClient />);

    expect(screen.queryByRole("link", { name: /CHEFS test form/i })).not.toBeInTheDocument();
  });

  it("renders the feature cards", () => {
    render(<HomeClient />);

    expect(screen.getByText("Dashboards")).toBeInTheDocument();
    expect(screen.getByText("Reports")).toBeInTheDocument();
    expect(screen.getByText("Spend Insights")).toBeInTheDocument();
  });
});
