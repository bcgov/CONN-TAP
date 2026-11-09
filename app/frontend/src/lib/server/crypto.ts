import "server-only";

import { createHmac, randomBytes } from "crypto";
import { authEnv } from "./env";

function decodeBase64Secret(name: string, value: string, minBytes: number): Buffer {
  if (/^[A-Za-z0-9+/]+={0,2}$/.test(value) && value.length % 4 === 0) {
    const decoded = Buffer.from(value, "base64");
    if (decoded.length >= minBytes) return decoded;
  }

  const raw = Buffer.from(value);
  if (raw.length >= minBytes) return raw;

  throw new Error(`${name} must be base64 encoded or raw text with at least ${minBytes} bytes`);
}

export function createOpaqueToken(): string {
  return randomBytes(32).toString("base64url");
}

export function hashSessionToken(token: string): string {
  const { sessionSecret } = authEnv();
  const key = decodeBase64Secret("SESSION_SECRET", sessionSecret, 32);
  return createHmac("sha256", key).update(token).digest("base64url");
}

