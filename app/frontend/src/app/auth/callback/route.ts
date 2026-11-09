import { NextRequest, NextResponse } from "next/server";
import { appUrl, publicRequestUrl } from "@/lib/server/app-url";
import {
  consumeOauthState,
  createSessionFromTokens,
  extractRoles,
  hasAuthorizedRole,
  setSessionCookie,
} from "@/lib/server/auth";
import { exchangeAuthorizationCode } from "@/lib/server/oidc";

export async function GET(request: NextRequest) {
  // Entra sends `error` instead of a code when sign-in did not finish,
  // e.g. `access_denied` when the user cancels or is not allowed in.
  const entraError = request.nextUrl.searchParams.get("error");
  if (entraError) {
    console.error(
      "Entra sign-in error:",
      entraError,
      request.nextUrl.searchParams.get("error_description")
    );
    const authError = entraError === "access_denied" ? "access_denied" : "signin_failed";
    return NextResponse.redirect(appUrl(`/?authError=${authError}`));
  }

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
    // No TAP role, no session: users must be given a role before they can sign in.
    if (!hasAuthorizedRole(extractRoles(tokens.claims() ?? null))) {
      return NextResponse.redirect(appUrl("/unauthorized"));
    }
    const sessionToken = await createSessionFromTokens(tokens);
    await setSessionCookie(sessionToken);

    return NextResponse.redirect(appUrl(transaction.returnTo));
  } catch (error) {
    console.error("Entra callback failed:", error);
    return NextResponse.redirect(appUrl("/?authError=callback_failed"));
  }
}
