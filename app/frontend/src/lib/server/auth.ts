import "server-only";

import { randomUUID } from "crypto";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { authEnv, sessionCookieName } from "./env";
import { createOpaqueToken, decryptToken, encryptToken, hashAccessToken, hashSessionToken } from "./crypto";
import { ensureAuthSchema, query } from "./db";
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
  await ensureAuthSchema();
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
  await ensureAuthSchema();
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

  await ensureAuthSchema();
  await query(
    `INSERT INTO auth_sessions (
       id,
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
     VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb, $8, $9, $10, $11, $12, $13)`,
    [
      randomUUID(),
      sessionHash,
      subject,
      claimString(claims, "preferred_username") ?? claimString(claims, "username"),
      claimString(claims, "email"),
      claimString(claims, "name"),
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

async function invalidateSession(sessionHash: string): Promise<void> {
  await query("UPDATE auth_sessions SET revoked_at = now(), updated_at = now() WHERE session_hash = $1", [
    sessionHash,
  ]);
  await clearSessionCookie();
}

export async function getCurrentSession(options: { refresh?: boolean } = {}): Promise<ServerSession | null> {
  const cookieStore = await cookies();
  const sessionToken = cookieStore.get(sessionCookieName())?.value;
  if (!sessionToken) return null;

  const { refreshWindowSeconds } = authEnv();

  await ensureAuthSchema();
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
    const refreshed = await refreshAccessToken(refreshToken);
    if (!refreshed?.access_token) {
      await invalidateSession(sessionHash);
      return null;
    }

    accessToken = refreshed.access_token;
    refreshToken = refreshed.refresh_token ?? refreshToken;
    const expiresIn = refreshed.expiresIn() ?? 300;
    row.access_token_expires_at = new Date(Date.now() + expiresIn * 1000);
    row.access_token_hash = hashAccessToken(accessToken);

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
        row.access_token_hash,
        row.access_token_expires_at,
      ]
    );
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
