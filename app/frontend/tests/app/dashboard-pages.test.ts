import { beforeEach, describe, expect, it, vi } from "vitest";

// redirect() stops the page in Next.js; throwing does the same here.
const { redirect, session } = vi.hoisted(() => ({
  redirect: vi.fn((path: string) => {
    throw new Error(`redirect:${path}`);
  }),
  session: { roles: [] as string[], subject: "oid-1", name: "Alice", username: null, email: null },
}));

vi.mock("next/navigation", () => ({ redirect }));
vi.mock("@/lib/server/auth", () => ({
  requireAuthorizedSession: vi.fn(async () => session),
  isTelecomOfficeUser: (roles: string[]) =>
    roles.includes("to_admin") || roles.includes("to_viewer"),
}));
vi.mock("@/lib/server/user-organizations", () => ({
  getOrganizationName: vi.fn(async () => "Ministry of Health"),
}));
vi.mock("@/lib/server/datasets", () => ({
  getVisibleDatasetIds: vi.fn(async () => new Set(["isp-spend-indicators"])),
}));
vi.mock("@/app/bge-dashboard/bge-dashboard-client", () => ({ BgeDashboardClient: () => null }));
vi.mock("@/app/dashboard/dashboard-client", () => ({ DashboardClient: () => null }));

import BgeDashboardPage from "@/app/bge-dashboard/page";
import DashboardPage from "@/app/dashboard/page";

beforeEach(() => {
  redirect.mockClear();
});

describe("BGE dashboard page", () => {
  it("renders for org users with their organization", async () => {
    session.roles = ["org_user"];

    const page = await BgeDashboardPage();

    expect(redirect).not.toHaveBeenCalled();
    expect(page.props).toEqual({ displayName: "Alice", orgName: "Ministry of Health" });
  });

  it("sends Telecom Office users to the main dashboard", async () => {
    session.roles = ["to_viewer"];

    await expect(BgeDashboardPage()).rejects.toThrow("redirect:/dashboard");
  });
});

describe("Main dashboard page", () => {
  it("renders for Telecom Office users", async () => {
    session.roles = ["to_admin"];

    const page = await DashboardPage();

    expect(redirect).not.toHaveBeenCalled();
    expect(page.props).toMatchObject({
      displayName: "Alice",
      orgName: "Ministry of Health",
      visibleDatasetIds: ["isp-spend-indicators"],
      isAdmin: true,
    });
  });

  it("sends org users to the BGE dashboard", async () => {
    session.roles = ["org_admin"];

    await expect(DashboardPage()).rejects.toThrow("redirect:/bge-dashboard");
  });
});
