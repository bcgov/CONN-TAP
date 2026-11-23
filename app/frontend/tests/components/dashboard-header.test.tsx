import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

vi.mock("next/navigation", () => ({ usePathname: () => "/bge-dashboard" }));

import { DashboardHeader } from "@/components/dashboard-header";
import { DashboardSidebar } from "@/components/dashboard-sidebar";

describe("DashboardHeader", () => {
  it("shows the user's initial, name and organization", () => {
    render(<DashboardHeader displayName="alice" orgName="Ministry of Health" />);

    expect(screen.getByText("A")).toBeInTheDocument();
    expect(screen.getByText("alice")).toBeInTheDocument();
    expect(screen.getByText("Ministry of Health")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Sign out" })).toBeInTheDocument();
  });

  it("shows Telecom Office when there is no organization", () => {
    render(<DashboardHeader displayName="Alice" />);

    expect(screen.getByText("Telecom Office")).toBeInTheDocument();
  });
});

describe("DashboardSidebar", () => {
  it("links Home to the given dashboard and marks it as the current page", () => {
    render(<DashboardSidebar homeHref="/bge-dashboard" />);

    const home = screen.getByRole("link", { name: "Home" });
    expect(home).toHaveAttribute("href", "/bge-dashboard");
    expect(home).toHaveAttribute("aria-current", "page");
    expect(screen.queryByRole("link", { name: "Admin" })).not.toBeInTheDocument();
  });

  it("links Home to the main dashboard by default and can show Admin", () => {
    render(<DashboardSidebar showAdmin />);

    const home = screen.getByRole("link", { name: "Home" });
    expect(home).toHaveAttribute("href", "/dashboard");
    expect(home).not.toHaveAttribute("aria-current");
    expect(screen.getByRole("link", { name: "Admin" })).toHaveAttribute("href", "/admin");
  });
});
