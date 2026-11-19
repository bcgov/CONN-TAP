import { NextRequest, NextResponse } from "next/server";
import { revokeCurrentSession } from "@/lib/server/auth";
import { createLogoutUrl } from "@/lib/server/oidc";

async function logout(_request: NextRequest) {
  // End the TAP session, then sign the user out of Entra too. Otherwise the
  // next "Log in" would sign them straight back in without asking.
  await revokeCurrentSession();
  return NextResponse.redirect(await createLogoutUrl());
}

export async function GET(request: NextRequest) {
  return logout(request);
}

export async function POST(request: NextRequest) {
  return logout(request);
}
