# Entra ID Authentication Setup

This app signs users in with the BC Gov Entra ID tenant using a server-side OpenID Connect authorization-code flow (with PKCE) and a confidential client. IDIR users, guests from other organizations (who sign in with their own organization's account) and email one-time-code guests all sign in the same way.

The browser only stores an opaque `HttpOnly` session cookie. No tokens are kept: the ID token's claims (user details and roles) are saved on the session row at sign-in.

## Environment Variables

Frontend/Next.js:

```bash
APP_BASE_URL=http://localhost:3001
BACKEND_INTERNAL_URL=http://localhost:8000

ENTRA_TENANT_ID=replace-with-bc-gov-tenant-id
ENTRA_CLIENT_ID=replace-with-application-client-id
ENTRA_CLIENT_SECRET=replace-with-client-secret

SESSION_COOKIE_NAME=telecom_session
SESSION_SECRET=replace-with-at-least-32-bytes-or-base64-secret
# Optional, default 8 hours
SESSION_TTL_SECONDS=28800

POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=app
POSTGRES_PASSWORD=app
POSTGRES_DB=app
# Omit or true on RDS/EKS (default). Set false for local docker-compose Postgres.
POSTGRES_SSL=false
```

FastAPI needs only `SESSION_COOKIE_NAME` and `SESSION_SECRET` (same values as Next.js). It does not talk to Entra.
For local `docker compose`, those values are loaded from `frontend/.env.local.example` and, when present, `frontend/.env.local` — no separate backend env file is required.

Generate a local session secret with:

```bash
openssl rand -base64 32
```

## Database (schema `app`)

Session and user data are stored in Postgres schema **`app`** (database `app`). Tables are created by Alembic, not at request time.

Before first login locally, run migrations from [`app/README.md`](../README.md#database-migrations-alembic) (`alembic upgrade head` in `app/backend`).

Tables:

- `app.users` — one row per person, keyed by Entra object ID (`entra_object_id`, the `oid` claim); upserted on login
- `app.auth_sessions` — opaque session (hashed) plus the ID token claims
- `app.auth_oauth_states` — short-lived PKCE/state for `/auth/login`

## Entra App Registration

One app registration per environment (dev, test, prod), managed with the BC Gov Entra team:

- Platform: **Web**, redirect URIs `https://<host>/auth/callback` and `https://<host>/` (dev also `http://localhost:3001/auth/callback` and `http://localhost:3001/`). The site root is where Entra sends the user after logout.
- A client secret (note its expiry and renew it before then)
- App roles whose **Value** matches the role names used by the app: `global_admin`, `global_analyst`, `org_admin`, `org_analyst`
- Optional claims on the ID token: `email`, `given_name`, `family_name`
- Enterprise application: **Assignment required = Yes**, so only users given a role (directly or through an access package) can sign in

## Roles

Roles come from the ID token's `roles` claim (Entra app roles assigned to the user). They are read at sign-in, so a role change takes effect the next time the user signs in.

- `ALLOWED_ROLES` in `src/lib/server/auth.ts` lists the roles that may open the dashboard; anyone else is sent to `/unauthorized`. `org_admin` and `org_analyst` are left out until organization-level data access is built.
- Each dataset's `required_roles` (backend `service.py`) decides which datasets a role can see.
- Each role also has its own Postgres role, and the backend runs every request's queries as it. See [Database users and roles](../README.md#database-users-and-roles).

## Flow

1. `/auth/login` creates a short-lived server-side state/PKCE transaction and redirects to Entra.
2. Entra signs the user in: IDIR, the guest's own organization, or an email one-time code.
3. `/auth/callback` exchanges the code using the client secret, validates the ID token, upserts `app.users`, creates an `app.auth_sessions` row with the ID token claims, and sets `telecom_session`.
4. `/dashboard` is gated server-side and redirects unauthenticated users to `/auth/login` and users without an allowed role to `/unauthorized`.
5. Browser API calls go to same-origin `/api/...`; Next validates the session and forwards the request with the session cookie to FastAPI.
6. FastAPI looks up the session cookie in `app.auth_sessions` on each `/api/v1/*` request and reads the user's roles from the stored claims.
7. `/auth/logout` revokes the session row, clears the cookie and sends the user to Entra's sign-out page, which returns them to the TAP home page.

A session lasts `SESSION_TTL_SECONDS`. After that the user is sent back to Entra, which signs them in again without a prompt if their Entra session is still active.

## Frontend Usage

Use a normal link for login:

```tsx
<a href="/auth/login?returnTo=/dashboard">Log in</a>
```

Use `/auth/session` for display-only user info in client components.
