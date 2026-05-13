import { NextRequest, NextResponse } from "next/server";
import { revokeCurrentSession } from "@/lib/server/auth";
import { createLogoutUrl } from "@/lib/server/oidc";

async function logout(request: NextRequest) {
  const idToken = await revokeCurrentSession();
  const keycloakLogoutUrl = await createLogoutUrl(idToken);
  return NextResponse.redirect(keycloakLogoutUrl ?? new URL("/", request.url));
}

export async function GET(request: NextRequest) {
  return logout(request);
}

export async function POST(request: NextRequest) {
  return logout(request);
}
