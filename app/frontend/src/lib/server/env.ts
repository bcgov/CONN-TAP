import "server-only";

const DEFAULT_COOKIE_NAME = "telecom_session";
const DEFAULT_SESSION_TTL_SECONDS = 8 * 60 * 60;
const DEFAULT_REFRESH_WINDOW_SECONDS = 60;

export function sessionCookieName(): string {
  return process.env.SESSION_COOKIE_NAME ?? DEFAULT_COOKIE_NAME;
}

function required(name: string): string {
  const value = process.env[name];
  if (!value) {
    throw new Error(`Missing required environment variable: ${name}`);
  }
  return value;
}

function optionalInt(name: string, fallback: number): number {
  const value = process.env[name];
  if (!value) return fallback;
  const parsed = Number.parseInt(value, 10);
  if (!Number.isFinite(parsed) || parsed <= 0) {
    throw new Error(`Environment variable ${name} must be a positive integer`);
  }
  return parsed;
}

export interface AuthEnv {
  appBaseUrl: string;
  backendInternalUrl: string;
  issuerUrl: string;
  clientId: string;
  clientSecret: string;
  cookieName: string;
  sessionSecret: string;
  tokenEncryptionKey: string;
  sessionTtlSeconds: number;
  refreshWindowSeconds: number;
  secureCookies: boolean;
}

let cachedAuthEnv: AuthEnv | null = null;

function loadAuthEnv(): AuthEnv {
  const appBaseUrl = required("APP_BASE_URL").replace(/\/$/, "");
  const issuerUrl = required("KEYCLOAK_ISSUER_URL").replace(/\/$/, "");

  return {
    appBaseUrl,
    backendInternalUrl: (process.env.BACKEND_INTERNAL_URL ?? "http://backend:8000").replace(/\/$/, ""),
    issuerUrl,
    clientId: required("KEYCLOAK_CLIENT_ID"),
    clientSecret: required("KEYCLOAK_CLIENT_SECRET"),
    cookieName: sessionCookieName(),
    sessionSecret: required("SESSION_SECRET"),
    tokenEncryptionKey: required("TOKEN_ENCRYPTION_KEY"),
    sessionTtlSeconds: optionalInt("SESSION_TTL_SECONDS", DEFAULT_SESSION_TTL_SECONDS),
    refreshWindowSeconds: optionalInt("TOKEN_REFRESH_WINDOW_SECONDS", DEFAULT_REFRESH_WINDOW_SECONDS),
    secureCookies: appBaseUrl.startsWith("https://"),
  };
}

export function authEnv(): AuthEnv {
  cachedAuthEnv ??= loadAuthEnv();
  return cachedAuthEnv;
}

const POSTGRES_SSL_DISABLE_VALUES = new Set(["false", "0", "off", "no", "disable", "disabled"]);

/** RDS and other managed Postgres require TLS; local docker-compose Postgres does not. */
export function postgresSslEnabled(): boolean {
  const raw = process.env.POSTGRES_SSL?.trim().toLowerCase();
  if (!raw) return true;
  return !POSTGRES_SSL_DISABLE_VALUES.has(raw);
}

export function postgresEnv() {
  if (process.env.DATABASE_URL) {
    return { connectionString: process.env.DATABASE_URL };
  }

  const host = process.env.POSTGRES_HOST ?? "localhost";
  const port = process.env.POSTGRES_PORT ?? "5432";
  const user = process.env.POSTGRES_USER ?? "app";
  const password = process.env.POSTGRES_PASSWORD ?? "app";
  const database = process.env.POSTGRES_DB ?? "app";

  return {
    connectionString: `postgresql://${encodeURIComponent(user)}:${encodeURIComponent(
      password
    )}@${host}:${port}/${database}`,
  };
}
