import { NextRequest, NextResponse } from "next/server";
import { authEnv } from "@/lib/server/env";

const TOKEN_HEADER = "x-chefs-token";

// Public entry point for CHEFS event-subscription callbacks. It sits outside
// /api because that proxy requires a user session; the backend checks the
// shared token, so this only forwards the body and token header.
export async function POST(request: NextRequest) {
  const upstream = await fetch(`${authEnv().backendInternalUrl}/hooks/chefs`, {
    method: "POST",
    headers: {
      "content-type": "application/json",
      [TOKEN_HEADER]: request.headers.get(TOKEN_HEADER) ?? "",
    },
    body: await request.arrayBuffer(),
    cache: "no-store",
  });

  return NextResponse.json(await upstream.json().catch(() => null), { status: upstream.status });
}
