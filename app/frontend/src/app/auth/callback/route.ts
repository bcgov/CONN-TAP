import { NextRequest, NextResponse } from "next/server";
import { appUrl, publicRequestUrl } from "@/lib/server/app-url";
import { consumeOauthState, createSessionFromTokens, setSessionCookie } from "@/lib/server/auth";
import { exchangeAuthorizationCode } from "@/lib/server/oidc";

export async function GET(request: NextRequest) {
  const state = request.nextUrl.searchParams.get("state");
  if (!state) {
    return NextResponse.redirect(appUrl("/?authError=missing_state"));
  }

  const transaction = await consumeOauthState(state);
  if (!transaction) {
    return NextResponse.redirect(appUrl("/?authError=invalid_state"));
  }

  try {
    const tokens = await exchangeAuthorizationCode(
      publicRequestUrl(request),
      state,
      transaction.pkceVerifier,
      transaction.nonce
    );
    const sessionToken = await createSessionFromTokens(tokens);
    await setSessionCookie(sessionToken);

    return NextResponse.redirect(appUrl(transaction.returnTo));
  } catch (error) {
    console.error("Keycloak callback failed:", error);
    return NextResponse.redirect(appUrl("/?authError=callback_failed"));
  }
}
