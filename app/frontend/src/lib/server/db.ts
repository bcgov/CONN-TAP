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
    options: "-c search_path=app,public",
  });

if (process.env.NODE_ENV !== "production") {
  globalThis.telecomPgPool = pool;
}

export async function query<T extends QueryResultRow = QueryResultRow>(
  text: string,
  params?: unknown[]
): Promise<QueryResult<T>> {
  return pool.query<T>(text, params);
}
