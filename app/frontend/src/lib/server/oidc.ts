import "server-only";

import {
  ClientSecretBasic,
  authorizationCodeGrant,
  buildAuthorizationUrl,
  buildEndSessionUrl,
  calculatePKCECodeChallenge,
  discovery,
  randomNonce,
  randomPKCECodeVerifier,
  randomState,
  refreshTokenGrant,
  type Configuration,
} from "openid-client";
import { authEnv } from "./env";

let oidcConfig: Promise<Configuration> | null = null;

export function redirectUri(): string {
  return `${authEnv().appBaseUrl}/auth/callback`;
}

export function getOidcConfig(): Promise<Configuration> {
  if (oidcConfig) return oidcConfig;

  const { issuerUrl, clientId, clientSecret } = authEnv();
  oidcConfig = discovery(
    new URL(issuerUrl),
    clientId,
    { client_secret: clientSecret },
    ClientSecretBasic(clientSecret)
  );

  return oidcConfig;
}

export async function createAuthorizationRequest(returnTo: string) {
  const config = await getOidcConfig();
  const state = randomState();
  const nonce = randomNonce();
  const pkceVerifier = randomPKCECodeVerifier();
  const pkceChallenge = await calculatePKCECodeChallenge(pkceVerifier);

  const url = buildAuthorizationUrl(config, {
    redirect_uri: redirectUri(),
    scope: "openid profile email",
    state,
    nonce,
    code_challenge: pkceChallenge,
    code_challenge_method: "S256",
  });

  return { url, state, nonce, pkceVerifier, returnTo };
}

export async function exchangeAuthorizationCode(
  currentUrl: URL,
  expectedState: string,
  pkceVerifier: string,
  expectedNonce: string
) {
  const config = await getOidcConfig();
  return authorizationCodeGrant(config, currentUrl, {
    expectedState,
    pkceCodeVerifier: pkceVerifier,
    expectedNonce,
  });
}

export async function refreshAccessToken(refreshToken: string) {
  try {
    const config = await getOidcConfig();
    return await refreshTokenGrant(config, refreshToken);
  } catch (error) {
    console.warn("Access token refresh failed:", error);
    return null;
  }
}

export async function createLogoutUrl(idToken: string | null): Promise<URL | null> {
  if (!idToken) return null;

  const config = await getOidcConfig();
  return buildEndSessionUrl(config, {
    id_token_hint: idToken,
    post_logout_redirect_uri: `${authEnv().appBaseUrl}/`,
  });
}
