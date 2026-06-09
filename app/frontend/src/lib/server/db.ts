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

export type QueryFn = <T extends QueryResultRow = QueryResultRow>(
  text: string,
  params?: unknown[],
) => Promise<QueryResult<T>>;

export async function query<T extends QueryResultRow = QueryResultRow>(
  text: string,
  params?: unknown[],
): Promise<QueryResult<T>> {
  return pool.query<T>(text, params);
}

export async function withTransaction<T>(fn: (txQuery: QueryFn) => Promise<T>): Promise<T> {
  const client = await pool.connect();
  const txQuery: QueryFn = (text, params) => client.query(text, params);
  try {
    await client.query("BEGIN");
    const result = await fn(txQuery);
    await client.query("COMMIT");
    return result;
  } catch (e) {
    await client.query("ROLLBACK");
    throw e;
  } finally {
    client.release();
  }
}
