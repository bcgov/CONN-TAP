import { defineConfig, devices } from "@playwright/test";

const e2eEnv = {
  APP_BASE_URL: "http://localhost:3001",
  BACKEND_INTERNAL_URL: "http://localhost:8000",
  KEYCLOAK_ISSUER_URL: "https://example.com/auth/realms/test",
  KEYCLOAK_CLIENT_ID: "test-client",
  KEYCLOAK_CLIENT_SECRET: "test-client-secret",
  SESSION_SECRET: "test-session-secret-32-characters-min",
  TOKEN_ENCRYPTION_KEY: "test-token-encryption-key-32-chars",
  POSTGRES_HOST: "localhost",
  POSTGRES_PORT: "5432",
  POSTGRES_USER: "app",
  POSTGRES_PASSWORD: "app",
  POSTGRES_DB: "app",
  POSTGRES_SSL: "false",
};

export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: process.env.CI ? "github" : "list",
  use: {
    baseURL: e2eEnv.APP_BASE_URL,
    trace: "on-first-retry",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: {
    // Dev server exercises App Router + async server components without standalone start quirks.
    command: "pnpm dev",
    url: e2eEnv.APP_BASE_URL,
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
    env: e2eEnv,
  },
});
