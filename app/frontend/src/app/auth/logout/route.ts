import { NextRequest, NextResponse } from "next/server";
import { revokeCurrentSession } from "@/lib/server/auth";

async function logout(request: NextRequest) {
  // We don't use the keycloak logout endpoint as that will sign out the user from the IDP
  // In the future when more than one IDP is available we will have to revisit this and implement a more robust solution for handling logout across multiple IDPs
  // as some will need to use the keycloak logout endpoint and some won't
  // const keycloakLogoutUrl = await createLogoutUrl(idToken);
  // return NextResponse.redirect(keycloakLogoutUrl ?? new URL("/", request.url));
  await revokeCurrentSession();
  return NextResponse.redirect(new URL("/", request.url));
}

export async function GET(request: NextRequest) {
  return logout(request);
}

export async function POST(request: NextRequest) {
  return logout(request);
}
