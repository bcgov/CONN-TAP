import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

vi.mock("next/navigation", () => ({ usePathname: () => "/dashboard" }));

import { DashboardLayout } from "@/components/dashboard-layout";

describe("DashboardLayout", () => {
  it("wraps the page in the banner, nav bar, header and footer", () => {
    render(
      <DashboardLayout displayName="Alice" orgName="Ministry of Health" showAdmin>
        <main>Page content</main>
      </DashboardLayout>,
    );

    expect(screen.getByText("Confidentiality Alert")).toBeInTheDocument();
    expect(screen.getByRole("navigation", { name: "Main navigation" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Admin" })).toBeInTheDocument();
    expect(screen.getByText("Ministry of Health")).toBeInTheDocument();
    expect(screen.getByText("Page content")).toBeInTheDocument();
    expect(screen.getByRole("navigation", { name: "Footer links" })).toBeInTheDocument();
  });
});
