import { NextRequest, NextResponse } from "next/server";
import { appUrl } from "@/lib/server/app-url";
import { revokeCurrentSession } from "@/lib/server/auth";

async function logout(_request: NextRequest) {
  // Ends only the TAP session. The user stays signed in to Entra (and to their
  // own organization), so other apps they use are not signed out.
  await revokeCurrentSession();
  return NextResponse.redirect(appUrl("/"));
}

export async function GET(request: NextRequest) {
  return logout(request);
}

export async function POST(request: NextRequest) {
  return logout(request);
}
