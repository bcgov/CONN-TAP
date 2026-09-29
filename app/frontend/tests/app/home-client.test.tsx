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

  it("renders the feature cards", () => {
    render(<HomeClient />);

    expect(screen.getByText("Dashboards")).toBeInTheDocument();
    expect(screen.getByText("Reports")).toBeInTheDocument();
    expect(screen.getByText("Spend Insights")).toBeInTheDocument();
  });
});
