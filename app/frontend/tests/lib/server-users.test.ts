import { beforeEach, describe, expect, it, vi } from "vitest";

const { query } = vi.hoisted(() => ({ query: vi.fn() }));

vi.mock("@/lib/server/db", () => ({ query }));
vi.mock("next/headers", () => ({ cookies: vi.fn() }));
vi.mock("next/navigation", () => ({ redirect: vi.fn() }));
vi.mock("@/lib/server/env", () => ({ authEnv: vi.fn(), sessionCookieName: vi.fn() }));

import { isTelecomOfficeUser } from "@/lib/server/auth";
import { getOrganizationName } from "@/lib/server/user-organizations";

describe("isTelecomOfficeUser", () => {
  it("is true for the Telecom Office roles", () => {
    expect(isTelecomOfficeUser(["to_admin"])).toBe(true);
    expect(isTelecomOfficeUser(["org_user", "to_viewer"])).toBe(true);
  });

  it("is false for org roles only", () => {
    expect(isTelecomOfficeUser(["org_admin", "org_user"])).toBe(false);
    expect(isTelecomOfficeUser([])).toBe(false);
  });
});

describe("getOrganizationName", () => {
  beforeEach(() => {
    query.mockReset();
  });

  it("returns the user's organization name, looked up by Entra object ID", async () => {
    query.mockResolvedValue({ rows: [{ name: "Ministry of Health" }] });

    await expect(getOrganizationName("oid-1")).resolves.toBe("Ministry of Health");
    expect(query).toHaveBeenCalledWith(expect.stringContaining("user_organizations"), ["oid-1"]);
  });

  it("returns null when the user has no organization", async () => {
    query.mockResolvedValue({ rows: [] });

    await expect(getOrganizationName("oid-1")).resolves.toBeNull();
  });
});
