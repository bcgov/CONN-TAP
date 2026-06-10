import "server-only";

import { randomUUID } from "crypto";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { authEnv, sessionCookieName } from "./env";
import { createOpaqueToken, decryptToken, encryptToken, hashAccessToken, hashSessionToken } from "./crypto";
import { query } from "./db";
import { refreshAccessToken } from "./oidc";

export const ALLOWED_ROLES = ["global_admin", "global_analyst"] as const;
export type AllowedRole = (typeof ALLOWED_ROLES)[number];

export interface PublicSession {
  authenticated: true;
  subject: string;
  username: string | null;
  email: string | null;
  name: string | null;
  expiresAt: string;
  roles: string[];
}

export interface ServerSession extends PublicSession {
  sessionHash: string;
  accessToken: string;
  refreshToken: string | null;
  idToken: string | null;
  accessTokenExpiresAt: Date;
}

interface SessionRow {
  session_hash: string;
  subject: string;
  username: string | null;
  email: string | null;
  name: string | null;
  claims: Record<string, unknown> | null;
  encrypted_access_token: string;
  encrypted_refresh_token: string | null;
  encrypted_id_token: string | null;
  access_token_hash: string;
  access_token_expires_at: Date;
  session_expires_at: Date;
}

export function sanitizeReturnTo(value: string | null): string {
  if (!value || !value.startsWith("/") || value.startsWith("//")) {
    return "/dashboard";
  }
  if (value.startsWith("/auth/") || value === "/unauthorized") {
    return "/dashboard";
  }
  return value;
}

function decodeJwtPayload(token: string | undefined): Record<string, unknown> {
  if (!token) return {};
  const [, payload] = token.split(".");
  if (!payload) return {};
  try {
    return JSON.parse(Buffer.from(payload, "base64url").toString("utf8")) as Record<string, unknown>;
  } catch {
    return {};
  }
}

function claimString(claims: Record<string, unknown>, name: string): string | null {
  const value = claims[name];
  return typeof value === "string" && value.length > 0 ? value : null;
}

function extractClientRoles(claims: Record<string, unknown> | null): string[] {
  if (!claims) return [];
  const clientRoles = claims["client_roles"];
  if (!Array.isArray(clientRoles)) return [];
  return clientRoles.filter((r): r is string => typeof r === "string");
}

export function hasAuthorizedRole(roles: string[]): boolean {
  return roles.some((r) => (ALLOWED_ROLES as readonly string[]).includes(r));
}

export function publicSession(session: ServerSession): PublicSession {
  return {
    authenticated: true,
    subject: session.subject,
    username: session.username,
    email: session.email,
    name: session.name,
    expiresAt: session.expiresAt,
    roles: session.roles,
  };
}

export async function saveOauthState(
  state: string,
  pkceVerifier: string,
  nonce: string,
  returnTo: string
): Promise<void> {
  await query("DELETE FROM auth_oauth_states WHERE expires_at < now()");
  await query(
    `INSERT INTO auth_oauth_states (state_hash, pkce_verifier, nonce, return_to, expires_at)
     VALUES ($1, $2, $3, $4, now() + interval '10 minutes')`,
    [hashSessionToken(state), pkceVerifier, nonce, sanitizeReturnTo(returnTo)]
  );
}

export async function consumeOauthState(state: string): Promise<{
  pkceVerifier: string;
  nonce: string;
  returnTo: string;
} | null> {
  const stateHash = hashSessionToken(state);
  const result = await query<{
    pkce_verifier: string;
    nonce: string;
    return_to: string;
  }>(
    `DELETE FROM auth_oauth_states
      WHERE state_hash = $1 AND expires_at > now()
      RETURNING pkce_verifier, nonce, return_to`,
    [stateHash]
  );

  const row = result.rows[0];
  if (!row) return null;
  return {
    pkceVerifier: row.pkce_verifier,
    nonce: row.nonce,
    returnTo: sanitizeReturnTo(row.return_to),
  };
}

export async function createSessionFromTokens(tokens: {
  access_token?: string;
  refresh_token?: string;
  id_token?: string;
  expiresIn(): number | undefined;
  claims(): Record<string, unknown> | undefined;
}): Promise<string> {
  if (!tokens.access_token) {
    throw new Error("Keycloak did not return an access token");
  }

  const now = new Date();
  const { sessionTtlSeconds } = authEnv();
  const expiresIn = tokens.expiresIn() ?? 300;
  const accessTokenExpiresAt = new Date(now.getTime() + expiresIn * 1000);
  const sessionExpiresAt = new Date(now.getTime() + sessionTtlSeconds * 1000);
  const idClaims = tokens.claims() ?? {};
  const accessClaims = decodeJwtPayload(tokens.access_token);
  const claims = { ...accessClaims, ...idClaims };
  const subject = claimString(claims, "sub");

  if (!subject) {
    throw new Error("Keycloak token is missing a subject claim");
  }

  const sessionToken = createOpaqueToken();
  const sessionHash = hashSessionToken(sessionToken);
  const username = claimString(claims, "preferred_username") ?? claimString(claims, "username");
  const givenName = claimString(claims, "given_name");
  const familyName = claimString(claims, "family_name");
  const email = claimString(claims, "email");
  const displayName = claimString(claims, "name");
  const sessionName =
    displayName ?? ([givenName, familyName].filter(Boolean).join(" ") || null);

  const userResult = await query<{ id: string }>(
    `INSERT INTO users (keycloak_subject, username, given_name, family_name, email, display_name, last_login_at, updated_at)
     VALUES ($1, $2, $3, $4, $5, $6, now(), now())
     ON CONFLICT (keycloak_subject) DO UPDATE
       SET username = COALESCE(EXCLUDED.username, users.username),
           given_name = COALESCE(EXCLUDED.given_name, users.given_name),
           family_name = COALESCE(EXCLUDED.family_name, users.family_name),
           email = COALESCE(EXCLUDED.email, users.email),
           display_name = COALESCE(EXCLUDED.display_name, users.display_name),
           last_login_at = now(),
           updated_at = now()
     RETURNING id`,
    [subject, username, givenName, familyName, email, displayName]
  );

  const userId = userResult.rows[0]?.id;
  if (!userId) {
    throw new Error("Failed to upsert application user");
  }

  await query(
    `INSERT INTO auth_sessions (
       id,
       user_id,
       session_hash,
       subject,
       username,
       email,
       name,
       claims,
       encrypted_access_token,
       encrypted_refresh_token,
       encrypted_id_token,
       access_token_hash,
       access_token_expires_at,
       session_expires_at
     )
     VALUES ($1, $2, $3, $4, $5, $6, $7, $8::jsonb, $9, $10, $11, $12, $13, $14)`,
    [
      randomUUID(),
      userId,
      sessionHash,
      subject,
      username,
      email,
      sessionName,
      JSON.stringify(claims),
      encryptToken(tokens.access_token),
      encryptToken(tokens.refresh_token),
      encryptToken(tokens.id_token),
      hashAccessToken(tokens.access_token),
      accessTokenExpiresAt,
      sessionExpiresAt,
    ]
  );

  return sessionToken;
}

export async function setSessionCookie(sessionToken: string): Promise<void> {
  const { cookieName, sessionTtlSeconds, secureCookies } = authEnv();
  const cookieStore = await cookies();
  cookieStore.set(cookieName, sessionToken, {
    httpOnly: true,
    secure: secureCookies,
    sameSite: "lax",
    path: "/",
    maxAge: sessionTtlSeconds,
  });
}

export async function clearSessionCookie(): Promise<void> {
  const { cookieName, secureCookies } = authEnv();
  const cookieStore = await cookies();
  cookieStore.set(cookieName, "", {
    httpOnly: true,
    secure: secureCookies,
    sameSite: "lax",
    path: "/",
    maxAge: 0,
  });
}

async function revokeSessionInDatabase(sessionHash: string): Promise<void> {
  await query("UPDATE auth_sessions SET revoked_at = now(), updated_at = now() WHERE session_hash = $1", [
    sessionHash,
  ]);
}

/** Revoke DB session and clear cookie. Call only from Route Handlers or Server Actions. */
async function invalidateSession(sessionHash: string): Promise<void> {
  await revokeSessionInDatabase(sessionHash);
  await clearSessionCookie();
}

const ACTIVE_SESSION_SQL = `SELECT session_hash,
            subject,
            username,
            email,
            name,
            claims,
            encrypted_access_token,
            encrypted_refresh_token,
            encrypted_id_token,
            access_token_hash,
            access_token_expires_at,
            session_expires_at
       FROM auth_sessions
      WHERE session_hash = $1
        AND revoked_at IS NULL
        AND session_expires_at > now()`;

declare global {
  // eslint-disable-next-line no-var
  var telecomRefreshFlights: Map<string, Promise<ServerSession | null>> | undefined;
}

const refreshFlights = globalThis.telecomRefreshFlights ?? new Map<string, Promise<ServerSession | null>>();

if (process.env.NODE_ENV !== "production") {
  globalThis.telecomRefreshFlights = refreshFlights;
}

function accessTokenNeedsRefresh(accessTokenExpiresAt: Date, refreshWindowSeconds: number): boolean {
  const refreshAt = accessTokenExpiresAt.getTime() - refreshWindowSeconds * 1000;
  return Date.now() >= refreshAt;
}

async function loadActiveSessionRow(sessionHash: string): Promise<SessionRow | null> {
  const result = await query<SessionRow>(ACTIVE_SESSION_SQL, [sessionHash]);
  return result.rows[0] ?? null;
}

function decryptSessionTokens(row: SessionRow): {
  accessToken: string;
  refreshToken: string | null;
  idToken: string | null;
} | null {
  try {
    const accessToken = decryptToken(row.encrypted_access_token);
    const refreshToken = decryptToken(row.encrypted_refresh_token);
    const idToken = decryptToken(row.encrypted_id_token);
    if (!accessToken) return null;
    return { accessToken, refreshToken, idToken };
  } catch {
    return null;
  }
}

function buildServerSession(
  row: SessionRow,
  tokens: { accessToken: string; refreshToken: string | null; idToken: string | null },
): ServerSession {
  return {
    authenticated: true,
    sessionHash: row.session_hash,
    subject: row.subject,
    username: row.username,
    email: row.email,
    name: row.name,
    roles: extractClientRoles(row.claims),
    accessToken: tokens.accessToken,
    refreshToken: tokens.refreshToken,
    idToken: tokens.idToken,
    accessTokenExpiresAt: row.access_token_expires_at,
    expiresAt: row.session_expires_at.toISOString(),
  };
}

async function touchLastSeen(sessionHash: string): Promise<void> {
  await query("UPDATE auth_sessions SET last_seen_at = now() WHERE session_hash = $1", [sessionHash]);
}

async function persistRefreshedTokens(
  sessionHash: string,
  accessToken: string,
  refreshToken: string | null,
  idToken: string | null,
  refreshedIdToken: string | undefined,
  accessTokenExpiresAt: Date,
): Promise<void> {
  await query(
    `UPDATE auth_sessions
        SET encrypted_access_token = $2,
            encrypted_refresh_token = $3,
            encrypted_id_token = COALESCE($4, encrypted_id_token),
            access_token_hash = $5,
            access_token_expires_at = $6,
            last_seen_at = now(),
            updated_at = now()
      WHERE session_hash = $1`,
    [
      sessionHash,
      encryptToken(accessToken),
      encryptToken(refreshToken ?? undefined),
      encryptToken(refreshedIdToken),
      hashAccessToken(accessToken),
      accessTokenExpiresAt,
    ],
  );
}

async function refreshSessionAccessToken(
  sessionHash: string,
  refreshWindowSeconds: number,
): Promise<ServerSession | null> {
  const row = await loadActiveSessionRow(sessionHash);
  if (!row) return null;

  const tokens = decryptSessionTokens(row);
  if (!tokens) return null;

  if (!tokens.refreshToken || !accessTokenNeedsRefresh(row.access_token_expires_at, refreshWindowSeconds)) {
    await touchLastSeen(sessionHash);
    return buildServerSession(row, tokens);
  }

  const refreshed = await refreshAccessToken(tokens.refreshToken);
  if (refreshed?.access_token) {
    const accessToken = refreshed.access_token;
    const refreshToken = refreshed.refresh_token ?? tokens.refreshToken;
    const idToken = refreshed.id_token ?? tokens.idToken;
    const accessTokenExpiresAt = new Date(Date.now() + (refreshed.expiresIn() ?? 300) * 1000);

    await persistRefreshedTokens(
      sessionHash,
      accessToken,
      refreshToken,
      idToken,
      refreshed.id_token,
      accessTokenExpiresAt,
    );

    return buildServerSession(
      { ...row, access_token_expires_at: accessTokenExpiresAt },
      { accessToken, refreshToken, idToken },
    );
  }

  // Refresh failed (for example invalid_grant when the refresh token was already used).
  // Re-read the row in case another concurrent request refreshed successfully.
  const reread = await loadActiveSessionRow(sessionHash);
  if (!reread) return null;

  const retokens = decryptSessionTokens(reread);
  if (!retokens) return null;

  if (!accessTokenNeedsRefresh(reread.access_token_expires_at, refreshWindowSeconds)) {
    await touchLastSeen(sessionHash);
    return buildServerSession(reread, retokens);
  }

  return null;
}

async function singleFlightRefresh(
  sessionHash: string,
  refreshWindowSeconds: number,
): Promise<ServerSession | null> {
  const inFlight = refreshFlights.get(sessionHash);
  if (inFlight) return inFlight;

  const flight = refreshSessionAccessToken(sessionHash, refreshWindowSeconds).finally(() => {
    refreshFlights.delete(sessionHash);
  });
  refreshFlights.set(sessionHash, flight);
  return flight;
}

export async function getCurrentSession(options: { refresh?: boolean } = {}): Promise<ServerSession | null> {
  const cookieStore = await cookies();
  const sessionToken = cookieStore.get(sessionCookieName())?.value;
  if (!sessionToken) return null;

  const { refreshWindowSeconds } = authEnv();
  const sessionHash = hashSessionToken(sessionToken);
  const row = await loadActiveSessionRow(sessionHash);
  if (!row) return null;

  const tokens = decryptSessionTokens(row);
  if (!tokens) return null;

  if (
    options.refresh &&
    tokens.refreshToken &&
    accessTokenNeedsRefresh(row.access_token_expires_at, refreshWindowSeconds)
  ) {
    return singleFlightRefresh(sessionHash, refreshWindowSeconds);
  }

  await touchLastSeen(sessionHash);
  return buildServerSession(row, tokens);
}

export async function requireSession(returnTo: string): Promise<ServerSession> {
  const session = await getCurrentSession({ refresh: true });
  if (!session) {
    redirect(`/auth/login?returnTo=${encodeURIComponent(returnTo)}`);
  }
  return session;
}

export async function requireAuthorizedSession(returnTo: string): Promise<ServerSession> {
  const session = await requireSession(returnTo);
  if (!hasAuthorizedRole(session.roles)) {
    redirect("/unauthorized");
  }
  return session;
}

export async function revokeCurrentSession(): Promise<string | null> {
  const session = await getCurrentSession();
  if (session) {
    await invalidateSession(session.sessionHash);
  } else {
    await clearSessionCookie();
  }
  return session?.idToken ?? null;
}
