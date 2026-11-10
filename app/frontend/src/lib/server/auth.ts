import "server-only";

import { randomUUID } from "crypto";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { authEnv, sessionCookieName } from "./env";
import { createOpaqueToken, hashSessionToken } from "./crypto";
import { query } from "./db";

export const ALLOWED_ROLES = ["to_admin", "to_viewer", "org_admin", "org_user"] as const;
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
}

interface SessionRow {
  session_hash: string;
  subject: string;
  username: string | null;
  email: string | null;
  name: string | null;
  claims: Record<string, unknown> | null;
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

function claimString(claims: Record<string, unknown>, name: string): string | null {
  const value = claims[name];
  return typeof value === "string" && value.length > 0 ? value : null;
}

// Entra app roles assigned to the user arrive in the `roles` claim.
export function extractRoles(claims: Record<string, unknown> | null): string[] {
  if (!claims) return [];
  const roles = claims["roles"];
  if (!Array.isArray(roles)) return [];
  return roles.filter((r): r is string => typeof r === "string");
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
  claims(): Record<string, unknown> | undefined;
}): Promise<string> {
  const now = new Date();
  const { sessionTtlSeconds } = authEnv();
  const sessionExpiresAt = new Date(now.getTime() + sessionTtlSeconds * 1000);
  // User details and roles come from the ID token, which openid-client has
  // already validated (signature, issuer, audience, nonce, expiry).
  const claims = tokens.claims() ?? {};
  // `oid` is the user's Entra object ID: the same for this user across apps
  // in the tenant, unlike `sub`.
  const subject = claimString(claims, "oid");

  if (!subject) {
    throw new Error("Entra ID token is missing the oid claim");
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
    `INSERT INTO users (entra_object_id, username, given_name, family_name, email, display_name, last_login_at, updated_at)
     VALUES ($1, $2, $3, $4, $5, $6, now(), now())
     ON CONFLICT (entra_object_id) DO UPDATE
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
       session_expires_at
     )
     VALUES ($1, $2, $3, $4, $5, $6, $7, $8::jsonb, $9)`,
    [
      randomUUID(),
      userId,
      sessionHash,
      subject,
      username,
      email,
      sessionName,
      JSON.stringify(claims),
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

export async function getCurrentSession(): Promise<ServerSession | null> {
  const cookieStore = await cookies();
  const sessionToken = cookieStore.get(sessionCookieName())?.value;
  if (!sessionToken) return null;

  const sessionHash = hashSessionToken(sessionToken);
  const result = await query<SessionRow>(
    `SELECT session_hash,
            subject,
            username,
            email,
            name,
            claims,
            session_expires_at
       FROM auth_sessions
      WHERE session_hash = $1
        AND revoked_at IS NULL
        AND session_expires_at > now()`,
    [sessionHash]
  );

  const row = result.rows[0];
  if (!row) return null;

  await query("UPDATE auth_sessions SET last_seen_at = now() WHERE session_hash = $1", [sessionHash]);

  return {
    authenticated: true,
    sessionHash,
    subject: row.subject,
    username: row.username,
    email: row.email,
    name: row.name,
    roles: extractRoles(row.claims),
    expiresAt: row.session_expires_at.toISOString(),
  };
}

export async function requireSession(returnTo: string): Promise<ServerSession> {
  const session = await getCurrentSession();
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

export async function revokeCurrentSession(): Promise<void> {
  const session = await getCurrentSession();
  if (session) {
    await invalidateSession(session.sessionHash);
  } else {
    await clearSessionCookie();
  }
}
