# Keycloak Authentication Setup

This app uses a server-side OpenID Connect authorization-code flow with a confidential Keycloak client. The browser only stores an opaque `HttpOnly` session cookie; Keycloak tokens are encrypted in Postgres and used server-side.

## Environment Variables

Frontend/Next.js:

```bash
APP_BASE_URL=http://localhost:3001
BACKEND_INTERNAL_URL=http://localhost:8000

KEYCLOAK_ISSUER_URL=https://dev.loginproxy.gov.bc.ca/auth/realms/standard
KEYCLOAK_CLIENT_ID=conn-hub-6434
KEYCLOAK_CLIENT_SECRET=replace-with-confidential-client-secret

SESSION_COOKIE_NAME=telecom_session
SESSION_SECRET=replace-with-at-least-32-bytes-or-base64-secret
TOKEN_ENCRYPTION_KEY=replace-with-at-least-32-bytes-or-base64-key

POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=app
POSTGRES_PASSWORD=app
POSTGRES_DB=app
# Omit or true on RDS/EKS (default). Set false for local docker-compose Postgres.
POSTGRES_SSL=false
```

FastAPI needs the same session settings:

```bash
KEYCLOAK_ISSUER_URL=https://dev.loginproxy.gov.bc.ca/auth/realms/standard
KEYCLOAK_CLIENT_ID=conn-hub-6434
SESSION_COOKIE_NAME=telecom_session
SESSION_SECRET=replace-with-the-same-secret-used-by-next
```

Generate local secrets with:

```bash
openssl rand -base64 32
```

## Database (schema `app`)

Session and user data are stored in Postgres schema **`app`** (database `app`). Tables are created by Alembic, not at request time.

Before first login locally, run migrations from [`app/README.md`](../README.md#database-migrations-app-schema) (`alembic upgrade head` in `app/backend`).

Tables:

- `app.users` — stable identity keyed by Keycloak `sub` (upserted on login)
- `app.auth_sessions` — opaque session + encrypted tokens
- `app.auth_oauth_states` — short-lived PKCE/state for `/auth/login`

## Keycloak Client

Configure the Keycloak client as confidential:

- Client authentication: on
- Standard flow: on
- Valid redirect URI: `http://localhost:3001/auth/callback`
- Valid post-logout redirect URI: `http://localhost:3001/`
- Web origins: `http://localhost:3001`

Use the matching environment URL for test/prod, for example `https://test.loginproxy.gov.bc.ca/auth/realms/standard` or `https://loginproxy.gov.bc.ca/auth/realms/standard`.

## Flow

1. `/auth/login` creates a short-lived server-side state/PKCE transaction and redirects to Keycloak.
2. `/auth/callback` exchanges the code using the confidential client secret, upserts `app.users`, creates an `app.auth_sessions` row, and sets `telecom_session`.
3. `/dashboard` is gated server-side and redirects unauthenticated users to `/auth/login`.
4. Browser API calls go to same-origin `/api/...`; Next validates the session, refreshes tokens when needed, and forwards to FastAPI.
5. FastAPI validates the session cookie, bearer token signature, issuer/audience, subject match, and token hash on each `/api/v1/*` request.
6. `/auth/logout` revokes the session row, clears the cookie, and redirects through Keycloak logout when an ID token is available.

## Frontend Usage

Use a normal link for login:

```tsx
<a href="/auth/login?returnTo=/dashboard">Login with IDIR</a>
```

Use `/auth/session` for display-only user info in client components. Tokens are intentionally unavailable to browser JavaScript.
