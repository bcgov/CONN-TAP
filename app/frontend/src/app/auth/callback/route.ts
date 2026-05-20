import { NextRequest, NextResponse } from "next/server";
import { consumeOauthState, createSessionFromTokens, setSessionCookie } from "@/lib/server/auth";
import { exchangeAuthorizationCode } from "@/lib/server/oidc";

export async function GET(request: NextRequest) {
  const state = request.nextUrl.searchParams.get("state");
  if (!state) {
    return NextResponse.redirect(new URL("/?authError=missing_state", request.url));
  }

  const transaction = await consumeOauthState(state);
  if (!transaction) {
    return NextResponse.redirect(new URL("/?authError=invalid_state", request.url));
  }

  try {
    const tokens = await exchangeAuthorizationCode(
      new URL(request.url),
      state,
      transaction.pkceVerifier,
      transaction.nonce
    );
    const sessionToken = await createSessionFromTokens(tokens);
    await setSessionCookie(sessionToken);

    return NextResponse.redirect(new URL(transaction.returnTo, request.url));
  } catch (error) {
    console.error("Keycloak callback failed:", error);
    return NextResponse.redirect(new URL("/?authError=callback_failed", request.url));
  }
}
