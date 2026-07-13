import { beforeEach, describe, expect, it, vi } from "vitest";

import type { ServerSession } from "@/lib/server/auth";

const mockCookieGet = vi.fn();
vi.mock("next/headers", () => ({
  cookies: vi.fn(async () => ({ get: mockCookieGet })),
}));

vi.mock("@/lib/server/env", () => ({
  authEnv: vi.fn(() => ({ backendInternalUrl: "http://backend:8000" })),
  sessionCookieName: vi.fn(() => "telecom_session"),
}));

import { getVisibleDatasetIds } from "@/lib/server/datasets";

const session = { accessToken: "access-token-123" } as ServerSession;

function jsonResponse(status: number, body: unknown) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  } as Response;
}

describe("getVisibleDatasetIds", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockCookieGet.mockReturnValue({ value: "cookie-value" });
    vi.stubGlobal("fetch", vi.fn());
  });

  it("returns the dataset ids from a successful response", async () => {
    vi.mocked(fetch).mockResolvedValue(jsonResponse(200, [{ id: "ds-1" }, { id: "ds-2" }]));

    const result = await getVisibleDatasetIds(session);

    expect(result).toEqual(new Set(["ds-1", "ds-2"]));
  });

  it("requests the backend datasets endpoint with auth and session cookie headers", async () => {
    vi.mocked(fetch).mockResolvedValue(jsonResponse(200, []));

    await getVisibleDatasetIds(session);

    expect(fetch).toHaveBeenCalledWith("http://backend:8000/api/v1/datasets", {
      headers: {
        authorization: "Bearer access-token-123",
        cookie: "telecom_session=cookie-value",
      },
      cache: "no-store",
    });
  });

  it("returns an empty set when the response is not ok", async () => {
    vi.mocked(fetch).mockResolvedValue(jsonResponse(500, { error: "boom" }));

    const result = await getVisibleDatasetIds(session);

    expect(result).toEqual(new Set());
  });

  it("returns an empty set when no datasets are returned", async () => {
    vi.mocked(fetch).mockResolvedValue(jsonResponse(200, []));

    const result = await getVisibleDatasetIds(session);

    expect(result).toEqual(new Set());
  });
});
