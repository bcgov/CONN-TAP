import type { ReactElement } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

// redirect() stops the page in Next.js; throwing does the same here.
const { redirect, session, currentSession } = vi.hoisted(() => {
  const session = { roles: [] as string[], subject: "oid-1", name: "Alice", username: null, email: null };
  return {
    redirect: vi.fn((path: string) => {
      throw new Error(`redirect:${path}`);
    }),
    session,
    currentSession: { value: session as typeof session | null },
  };
});

vi.mock("next/navigation", () => ({ redirect }));
vi.mock("@/lib/server/auth", () => ({
  getCurrentSession: vi.fn(async () => currentSession.value),
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
vi.mock("@/app/(dashboard)/bge-dashboard/bge-dashboard-client", () => ({ BgeDashboardClient: () => null }));
vi.mock("@/app/(dashboard)/dashboard/dashboard-client", () => ({ DashboardClient: () => null }));

import BgeDashboardPage from "@/app/(dashboard)/bge-dashboard/page";
import DashboardPage from "@/app/(dashboard)/dashboard/page";
import SignedInLayout from "@/app/(dashboard)/layout";

beforeEach(() => {
  redirect.mockClear();
  currentSession.value = session;
});

describe("Signed-in layout", () => {
  it("gives the header and nav bar the user's name, organization and links", async () => {
    session.roles = ["to_admin"];

    const layout = (await SignedInLayout({ children: "page" })) as ReactElement;

    expect(layout.props).toMatchObject({
      displayName: "Alice",
      orgName: "Ministry of Health",
      homeHref: "/dashboard",
      showAdmin: true,
      children: "page",
    });
  });

  it("links org users home to the BGE dashboard, without Admin", async () => {
    session.roles = ["org_user"];

    const layout = (await SignedInLayout({ children: "page" })) as ReactElement;

    expect(layout.props).toMatchObject({ homeHref: "/bge-dashboard", showAdmin: false });
  });

  it("shows just the page when nobody is signed in", async () => {
    currentSession.value = null;

    expect(await SignedInLayout({ children: "page" })).toBe("page");
  });
});

describe("BGE dashboard page", () => {
  it("renders for org users", async () => {
    session.roles = ["org_user"];

    await BgeDashboardPage();

    expect(redirect).not.toHaveBeenCalled();
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
    expect(page.props).toEqual({ visibleDatasetIds: ["isp-spend-indicators"] });
  });

  it("sends org users to the BGE dashboard", async () => {
    session.roles = ["org_admin"];

    await expect(DashboardPage()).rejects.toThrow("redirect:/bge-dashboard");
  });
});
