import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

vi.mock("next/navigation", () => ({ usePathname: () => "/admin" }));
vi.mock("@/app/(dashboard)/admin/actions", () => ({ setOrganizationAction: vi.fn() }));
// The users table has its own tests; here it only needs to show it was given rows.
vi.mock("@/components/chart-data-table", () => ({
  ChartDataTable: ({ data }: { data: unknown[] }) => <p>{data.length} users</p>,
}));

import { AdminClient } from "@/app/(dashboard)/admin/admin-client";

describe("AdminClient", () => {
  it("shows the users table", () => {
    render(<AdminClient users={[]} organizationOptions={[]} loadError={false} />);

    expect(screen.getByText("Manage users")).toBeInTheDocument();
    expect(screen.getByText("0 users")).toBeInTheDocument();
  });

  it("shows a message when the users couldn't be loaded", () => {
    render(<AdminClient users={[]} organizationOptions={[]} loadError />);

    expect(screen.getByText(/Couldn.t load users from Entra/)).toBeInTheDocument();
  });
});
