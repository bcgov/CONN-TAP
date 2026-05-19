import "server-only";

import { createCipheriv, createDecipheriv, createHash, createHmac, randomBytes } from "crypto";
import { authEnv } from "./env";

const ENCRYPTION_VERSION = "v1";

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

export function hashAccessToken(token: string): string {
  return createHash("sha256").update(token).digest("base64url");
}

export function encryptToken(token: string | undefined): string | null {
  if (!token) return null;

  const { tokenEncryptionKey } = authEnv();
  const key = decodeBase64Secret("TOKEN_ENCRYPTION_KEY", tokenEncryptionKey, 32).subarray(0, 32);
  const iv = randomBytes(12);
  const cipher = createCipheriv("aes-256-gcm", key, iv);
  const ciphertext = Buffer.concat([cipher.update(token, "utf8"), cipher.final()]);
  const tag = cipher.getAuthTag();

  return [
    ENCRYPTION_VERSION,
    iv.toString("base64url"),
    tag.toString("base64url"),
    ciphertext.toString("base64url"),
  ].join(".");
}

export function decryptToken(value: string | null): string | null {
  if (!value) return null;

  const [version, iv, tag, ciphertext] = value.split(".");
  if (version !== ENCRYPTION_VERSION || !iv || !tag || !ciphertext) {
    throw new Error("Unsupported encrypted token format");
  }

  const { tokenEncryptionKey } = authEnv();
  const key = decodeBase64Secret("TOKEN_ENCRYPTION_KEY", tokenEncryptionKey, 32).subarray(0, 32);
  const decipher = createDecipheriv("aes-256-gcm", key, Buffer.from(iv, "base64url"));
  decipher.setAuthTag(Buffer.from(tag, "base64url"));

  return Buffer.concat([
    decipher.update(Buffer.from(ciphertext, "base64url")),
    decipher.final(),
  ]).toString("utf8");
}
