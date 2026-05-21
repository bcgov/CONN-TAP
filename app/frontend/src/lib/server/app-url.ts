import "server-only";

import type { NextRequest } from "next/server";
import { authEnv } from "./env";

/** Browser-facing origin from APP_BASE_URL (not the in-cluster Host on request.url). */
export function publicAppOrigin(): string {
  return authEnv().appBaseUrl;
}

/** Rebuild the current request URL using APP_BASE_URL for OIDC callbacks and redirects. */
export function publicRequestUrl(request: NextRequest): URL {
  const pathAndQuery = `${request.nextUrl.pathname}${request.nextUrl.search}`;
  return new URL(pathAndQuery, publicAppOrigin());
}

/** Absolute URL for a path on the public app (e.g. /dashboard). */
export function appUrl(path: string): URL {
  return new URL(path, publicAppOrigin());
}
