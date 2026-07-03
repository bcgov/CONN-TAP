import "server-only";

import { cookies } from "next/headers";
import { authEnv, sessionCookieName } from "./env";
import type { ServerSession } from "./auth";

/**
 * Dataset ids the given session is authorized to see. The backend filters
 * this against each dataset's `required_roles` (set on its `service.py`), so
 * any page can call this instead of duplicating a role/dataset map here.
 */
export async function getVisibleDatasetIds(session: ServerSession): Promise<Set<string>> {
  const cookieStore = await cookies();
  const sessionCookie = cookieStore.get(sessionCookieName())?.value;

  const response = await fetch(`${authEnv().backendInternalUrl}/api/v1/datasets`, {
    headers: {
      authorization: `Bearer ${session.accessToken}`,
      cookie: `${sessionCookieName()}=${sessionCookie}`,
    },
    cache: "no-store",
  });
  if (!response.ok) return new Set();
  const datasets = (await response.json()) as { id: string }[];
  return new Set(datasets.map((d) => d.id));
}
