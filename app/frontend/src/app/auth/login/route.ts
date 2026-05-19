import { NextRequest, NextResponse } from "next/server";
import { createAuthorizationRequest } from "@/lib/server/oidc";
import { sanitizeReturnTo, saveOauthState } from "@/lib/server/auth";

export async function GET(request: NextRequest) {
  const returnTo = sanitizeReturnTo(request.nextUrl.searchParams.get("returnTo"));
  const authRequest = await createAuthorizationRequest(returnTo);

  await saveOauthState(
    authRequest.state,
    authRequest.pkceVerifier,
    authRequest.nonce,
    authRequest.returnTo
  );

  return NextResponse.redirect(authRequest.url);
}
