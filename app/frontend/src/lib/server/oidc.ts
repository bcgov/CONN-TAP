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

// Entra's sign-out page. After signing the user out it sends them back to the
// TAP home page, which must be registered as a redirect URI on the app.
export async function createLogoutUrl(): Promise<URL> {
  const config = await getOidcConfig();
  return buildEndSessionUrl(config, {
    post_logout_redirect_uri: `${authEnv().appBaseUrl}/`,
  });
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
