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

interface RefreshedTokens {
  accessToken: string;
  refreshToken: string | null;
  idToken: string | null;
  accessTokenExpiresAt: Date;
}

/**
 * De-duplicates concurrent refreshes for the same session. A single dashboard
 * load fires many parallel API calls; without this, each one would submit the
 * same refresh token to Keycloak simultaneously. Keycloak rotates refresh
 * tokens, so only the first submission succeeds and the rest fail with
 * `invalid_grant` ("Token is not active"), tearing down the session.
 */
const inflightRefreshes = new Map<string, Promise<RefreshedTokens | null>>();

function decryptRowTokens(
  row: Pick<SessionRow, "encrypted_access_token" | "encrypted_refresh_token" | "encrypted_id_token">
): { accessToken: string | null; refreshToken: string | null; idToken: string | null } | null {
  try {
    return {
      accessToken: decryptToken(row.encrypted_access_token),
      refreshToken: decryptToken(row.encrypted_refresh_token),
      idToken: decryptToken(row.encrypted_id_token),
    };
  } catch {
    return null;
  }
}

async function readActiveSessionRow(sessionHash: string): Promise<SessionRow | null> {
  const result = await query<SessionRow>(
    `SELECT session_hash,
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
        AND session_expires_at > now()`,
    [sessionHash]
  );
  return result.rows[0] ?? null;
}

async function performRefresh(
  sessionHash: string,
  staleRefreshToken: string,
  refreshWindowSeconds: number
): Promise<RefreshedTokens | null> {
  // Re-read the latest row: another worker (or an earlier request in this same
  // burst) may have already rotated the token while we waited for our turn.
  const latest = await readActiveSessionRow(sessionHash);
  if (!latest) return null;

  const decrypted = decryptRowTokens(latest);
  if (!decrypted?.accessToken) return null;

  const stillNeedsRefresh =
    Date.now() >= latest.access_token_expires_at.getTime() - refreshWindowSeconds * 1000;
  if (!stillNeedsRefresh && decrypted.refreshToken) {
    // Someone else already refreshed; reuse their fresh tokens, no Keycloak call.
    return {
      accessToken: decrypted.accessToken,
      refreshToken: decrypted.refreshToken,
      idToken: decrypted.idToken,
      accessTokenExpiresAt: latest.access_token_expires_at,
    };
  }

  const currentRefreshToken = decrypted.refreshToken ?? staleRefreshToken;
  const refreshed = await refreshAccessToken(currentRefreshToken);
  if (!refreshed?.access_token) {
    // The refresh failed. Re-read the latest row, because a concurrent worker
    // (another instance, or an earlier request in this burst) may have rotated
    // the token. We use the freshest copy for both recovery checks below.
    const recovered = await readActiveSessionRow(sessionHash);
    const recoveredTokens = recovered ? decryptRowTokens(recovered) : null;

    if (recovered && recoveredTokens?.accessToken) {
      // Case 1: someone else rotated successfully (refresh token changed) -> use it.
      if (
        recoveredTokens.refreshToken &&
        recoveredTokens.refreshToken !== currentRefreshToken
      ) {
        return {
          accessToken: recoveredTokens.accessToken,
          refreshToken: recoveredTokens.refreshToken,
          idToken: recoveredTokens.idToken,
          accessTokenExpiresAt: recovered.access_token_expires_at,
        };
      }

      // Case 2: nobody rotated, but we refresh early (refreshWindowSeconds before
      // expiry), so the current access token is very likely still valid. Keep
      // serving it instead of destroying the session over a transient/raced
      // refresh failure; a later request will retry the refresh.
      if (recovered.access_token_expires_at.getTime() > Date.now()) {
        return {
          accessToken: recoveredTokens.accessToken,
          refreshToken: recoveredTokens.refreshToken ?? currentRefreshToken,
          idToken: recoveredTokens.idToken,
          accessTokenExpiresAt: recovered.access_token_expires_at,
        };
      }
    }

    // The access token is actually expired and refresh failed: session is dead.
    await revokeSessionInDatabase(sessionHash);
    return null;
  }

  const accessToken = refreshed.access_token;
  const refreshToken = refreshed.refresh_token ?? currentRefreshToken;
  const idToken = refreshed.id_token ?? decrypted.idToken;
  const expiresIn = refreshed.expiresIn() ?? 300;
  const accessTokenExpiresAt = new Date(Date.now() + expiresIn * 1000);

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
      encryptToken(refreshToken),
      encryptToken(refreshed.id_token),
      hashAccessToken(accessToken),
      accessTokenExpiresAt,
    ]
  );

  return { accessToken, refreshToken, idToken, accessTokenExpiresAt };
}

function refreshSessionTokens(
  sessionHash: string,
  staleRefreshToken: string,
  refreshWindowSeconds: number
): Promise<RefreshedTokens | null> {
  const existing = inflightRefreshes.get(sessionHash);
  if (existing) return existing;

  const task = performRefresh(sessionHash, staleRefreshToken, refreshWindowSeconds).finally(() => {
    inflightRefreshes.delete(sessionHash);
  });
  inflightRefreshes.set(sessionHash, task);
  return task;
}

export async function getCurrentSession(options: { refresh?: boolean } = {}): Promise<ServerSession | null> {
  const cookieStore = await cookies();
  const sessionToken = cookieStore.get(sessionCookieName())?.value;
  if (!sessionToken) return null;

  const { refreshWindowSeconds } = authEnv();

  const sessionHash = hashSessionToken(sessionToken);
  const result = await query<SessionRow>(
    `SELECT session_hash,
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
        AND session_expires_at > now()`,
    [sessionHash]
  );

  const row = result.rows[0];
  if (!row) return null;

  let accessToken: string | null;
  let refreshToken: string | null;
  let idToken: string | null;
  try {
    accessToken = decryptToken(row.encrypted_access_token);
    refreshToken = decryptToken(row.encrypted_refresh_token);
    idToken = decryptToken(row.encrypted_id_token);
  } catch {
    return null;
  }

  if (!accessToken) return null;

  const refreshAt = row.access_token_expires_at.getTime() - refreshWindowSeconds * 1000;
  if (options.refresh && refreshToken && Date.now() >= refreshAt) {
    const refreshed = await refreshSessionTokens(sessionHash, refreshToken, refreshWindowSeconds);
    if (!refreshed) {
      // Refresh genuinely failed (token revoked at the IdP); session is dead.
      return null;
    }

    accessToken = refreshed.accessToken;
    refreshToken = refreshed.refreshToken;
    idToken = refreshed.idToken;
    row.access_token_expires_at = refreshed.accessTokenExpiresAt;
  } else {
    await query("UPDATE auth_sessions SET last_seen_at = now() WHERE session_hash = $1", [sessionHash]);
  }

  return {
    authenticated: true,
    sessionHash,
    subject: row.subject,
    username: row.username,
    email: row.email,
    name: row.name,
    roles: extractClientRoles(row.claims),
    accessToken,
    refreshToken,
    idToken,
    accessTokenExpiresAt: row.access_token_expires_at,
    expiresAt: row.session_expires_at.toISOString(),
  };
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
