import "server-only";

import { Pool, type QueryResult, type QueryResultRow } from "pg";
import { postgresEnv, postgresSslEnabled } from "./env";

declare global {
  // eslint-disable-next-line no-var
  var telecomPgPool: Pool | undefined;
}

const pool =
  globalThis.telecomPgPool ??
  new Pool({
    connectionString: postgresEnv().connectionString,
    ssl: postgresSslEnabled() ? { rejectUnauthorized: false } : false,
  });

if (process.env.NODE_ENV !== "production") {
  globalThis.telecomPgPool = pool;
}

let schemaReady: Promise<void> | null = null;

export async function ensureAuthSchema(): Promise<void> {
  if (schemaReady) return schemaReady;

  schemaReady = query(`
    CREATE TABLE IF NOT EXISTS auth_sessions (
      id UUID PRIMARY KEY,
      session_hash TEXT NOT NULL UNIQUE,
      subject TEXT NOT NULL,
      username TEXT,
      email TEXT,
      name TEXT,
      claims JSONB NOT NULL DEFAULT '{}'::jsonb,
      encrypted_access_token TEXT NOT NULL,
      encrypted_refresh_token TEXT,
      encrypted_id_token TEXT,
      access_token_hash TEXT NOT NULL,
      access_token_expires_at TIMESTAMPTZ NOT NULL,
      session_expires_at TIMESTAMPTZ NOT NULL,
      revoked_at TIMESTAMPTZ,
      last_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
      created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );

    CREATE INDEX IF NOT EXISTS auth_sessions_session_hash_idx ON auth_sessions (session_hash);
    CREATE INDEX IF NOT EXISTS auth_sessions_subject_idx ON auth_sessions (subject);
    CREATE INDEX IF NOT EXISTS auth_sessions_expires_idx ON auth_sessions (session_expires_at);

    CREATE TABLE IF NOT EXISTS auth_oauth_states (
      state_hash TEXT PRIMARY KEY,
      pkce_verifier TEXT NOT NULL,
      nonce TEXT NOT NULL,
      return_to TEXT NOT NULL,
      expires_at TIMESTAMPTZ NOT NULL,
      created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );

    CREATE INDEX IF NOT EXISTS auth_oauth_states_expires_idx ON auth_oauth_states (expires_at);
  `).then(() => undefined);

  return schemaReady;
}

export async function query<T extends QueryResultRow = QueryResultRow>(
  text: string,
  params?: unknown[]
): Promise<QueryResult<T>> {
  return pool.query<T>(text, params);
}
