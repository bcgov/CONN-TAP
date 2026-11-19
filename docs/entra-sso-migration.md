# Keycloak → Entra ID sign-in migration

Tracks the move from BC Gov Common Hosted SSO (Keycloak, client `conn-hub-6434`) to
signing in directly with the BC Gov Entra ID tenant, so that IDIR users, guests from
other organizations (e.g. PHSA) and email one-time-code users can all sign in.

Branch: `feat/entra-sso`

## How sign-in works after the move

```
user → TAP /auth/login → BC Gov Entra → (IDIR, the guest's own org, or email code)
     ← Entra ID token (with app roles) → TAP /auth/callback → TAP session cookie
```

- Next.js runs the OIDC authorization code flow, validates the ID token and creates a
  session row in `app.auth_sessions`.
- FastAPI trusts the session cookie (looked up in `app.auth_sessions`). It does not
  validate tokens itself.
- Roles come from the ID token's `roles` claim (Entra app roles). They are read at
  sign-in, so a role change takes effect at the next sign-in.

## Steps

| # | Step | Status |
|---|------|--------|
| 1 | Backend trusts the session cookie only; Next.js stops sending the bearer token | Done |
| 2a | Next.js reads `ENTRA_TENANT_ID` / `ENTRA_CLIENT_ID` / `ENTRA_CLIENT_SECRET` | Done |
| 2b | Deploy config (Helm values, deploy workflows) uses the `ENTRA_*` variables | Done |
| 2c | Roles read from the `roles` claim (frontend and backend) | Done |
| 2d | User info from the ID token; users keyed on Entra `oid` (migration) | Done |
| 3a | Remove token refresh | Done |
| 3b | Stop storing tokens; drop the unused token columns | Done |
| 3c | Remove token encryption, `TOKEN_ENCRYPTION_KEY`, and the unused Keycloak logout code | Done |
| 4a | Replace `KEYCLOAK.md` with `ENTRA.md`; README authentication section | Done |
| 4b | Deploy docs and remaining Keycloak wording (docker-compose comment, UI text) | Done |
| 5 | Settings outside the repo (Entra, GitHub vars/secrets), testing, retire Keycloak | To do |

### Step 1 – Backend trusts the session cookie

Changes:

- `app/backend/app/core/auth.py`: removed bearer-token / JWKS validation. The user and
  roles are read from the session row (`auth_sessions.claims`).
- `app/frontend/src/app/api/[...path]/route.ts`, `app/frontend/src/lib/server/datasets.ts`:
  no longer send `Authorization: Bearer`.
- Removed `KEYCLOAK_ISSUER_URL` / `KEYCLOAK_CLIENT_ID` from the backend (config, `.env.example`,
  Helm values, deploy workflows) and `PyJWT` from `requirements.txt`.
- Test stubs for `jwt` / `fastapi.security` removed from `tests/app/conftest.py`.

- `app/frontend/tests/lib/datasets.test.ts`: updated for the removed bearer header.

Still works with Keycloak: roles are read from `client_roles` until step 2c.

### Step 2a – Next.js reads the Entra settings

- `app/frontend/src/lib/server/env.ts`: the issuer is built from `ENTRA_TENANT_ID`
  (`https://login.microsoftonline.com/<tenant-id>/v2.0`); client ID and secret come from
  `ENTRA_CLIENT_ID` / `ENTRA_CLIENT_SECRET`.
- `.env.example`, `.env.local.example`, `playwright.config.ts`: renamed to the `ENTRA_*` variables.

From here on, local sign-in needs the Entra values in `frontend/.env.local`.

### Step 2b – Deploy config uses the Entra settings

- `.github/workflows/app-deploy-{dev,test,prod}.yml`: read `ENTRA_TENANT_ID` and
  `ENTRA_CLIENT_ID` (GitHub environment variables) and `ENTRA_CLIENT_SECRET` (GitHub
  environment secret). The deploy stops with a clear message if any is missing; there are
  no defaults, because each environment has its own app registration.
- The client secret goes into the frontend Kubernetes secret as `ENTRA_CLIENT_SECRET`.
- `helm/conn-tap/values.yaml`: frontend env now lists `ENTRA_TENANT_ID` / `ENTRA_CLIENT_ID`
  (empty; set by the workflows).

### Step 2c – Roles from the `roles` claim

- `app/frontend/src/lib/server/auth.ts` (`extractRoles`) and `app/backend/app/core/auth.py`
  read the user's roles from the `roles` claim (Entra app roles) instead of Keycloak's
  `client_roles`. Both read the claims saved on the session row at sign-in.
- The app role **Value** in Entra must match the names in `ALLOWED_ROLES`
  (`global_admin`, `global_analyst`) and the datasets' `required_roles`.

### Step 2d – User details from the ID token, users keyed on `oid`

- `app/frontend/src/lib/server/auth.ts` (`createSessionFromTokens`): user details and roles
  come only from the validated ID token. The access token is no longer decoded (Entra
  issues it for Microsoft Graph, not for TAP).
- Users are identified by `oid` (Entra object ID), stored in the session's `subject` and
  in `app.users.entra_object_id`.
- Migration `011_users_entra_object_id` renames `app.users.keycloak_subject` to
  `entra_object_id`. Existing Keycloak rows stay; those people get a new row on their
  first Entra sign-in.
- Error messages now say Entra instead of Keycloak.

### Step 3a – Remove token refresh

Sign-in asks only for `openid profile email`, so Entra returns no refresh token and the
refresh code never ran. A TAP session now simply lasts `SESSION_TTL_SECONDS` (default 8
hours); after that the user is sent back to Entra, which signs them in again without a
prompt if their Entra session is still active.

- `app/frontend/src/lib/server/auth.ts`: `getCurrentSession()` no longer takes a `refresh`
  option or refreshes tokens.
- `app/frontend/src/lib/server/oidc.ts`: removed `refreshAccessToken`.
- `app/frontend/src/lib/server/env.ts`: removed `TOKEN_REFRESH_WINDOW_SECONDS`.
- `app/frontend/src/app/api/[...path]/route.ts`: calls `getCurrentSession()`.

### Step 3b – Stop storing tokens

TAP only needs the ID token's claims (user details, roles), which are saved on the
session row as `claims`. The tokens themselves are no longer kept. The ID token is not
kept either: signing the user out of Entra on logout, if wanted later, works without it.

- `app/frontend/src/lib/server/auth.ts`: `createSessionFromTokens` saves only the claims;
  `getCurrentSession` no longer reads or decrypts tokens; `ServerSession` lost
  `accessToken`, `refreshToken`, `idToken`, `accessTokenExpiresAt`.
- `app/backend/app/models/auth.py`: token columns removed from `AuthSession`.
- Migration `012_drop_session_tokens` drops `encrypted_access_token`,
  `encrypted_refresh_token`, `encrypted_id_token`, `access_token_hash`,
  `access_token_expires_at` from `app.auth_sessions`, and **deletes all existing
  sessions** (Keycloak sessions can't be used with Entra). Everyone signs in again.

### Step 3c – Remove token encryption and old logout code

- `app/frontend/src/lib/server/crypto.ts`: removed `encryptToken`, `decryptToken`,
  `hashAccessToken`. Only the session-cookie helpers remain.
- `TOKEN_ENCRYPTION_KEY` removed from `env.ts`, `.env.example`, `.env.local.example`,
  `playwright.config.ts` and the three deploy workflows.
- `app/frontend/src/lib/server/oidc.ts`: removed the unused `createLogoutUrl`.
- `app/frontend/src/app/auth/logout/route.ts`: replaced the commented-out Keycloak logout
  with a short note. Logout ends only the TAP session; the user stays signed in to Entra.

### Step 4a – Entra setup doc

- `app/frontend/KEYCLOAK.md` replaced by `app/frontend/ENTRA.md`: env vars, tables,
  app registration settings, roles, sign-in flow.
- `app/README.md`: authentication section and stack summary point to Entra and `ENTRA.md`.

### Step 4b – Remaining wording

- `app/frontend/src/app/home-client.tsx`: login button says "Log in" instead of
  "Log in with IDIR" (external users don't have IDIR). Unit and e2e tests updated.
- `docs/app-deploy-dev.md`: dev secrets/variables list the `ENTRA_*` values.
- `app/docker-compose.yml`: header comment no longer mentions Keycloak.

No Keycloak references remain outside the migration history.

## GitHub settings to create (per environment: dev, test, prod)

Settings → Environments → `<env>`:

| Kind | Name | Value |
|------|------|-------|
| Variable | `ENTRA_TENANT_ID` | BC Gov tenant ID |
| Variable | `ENTRA_CLIENT_ID` | Application (client) ID of that environment's app registration |
| Secret | `ENTRA_CLIENT_SECRET` | Client secret value of that app registration |

After Entra is live everywhere, delete `KEYCLOAK_ISSUER_URL`, `KEYCLOAK_CLIENT_ID`,
`KEYCLOAK_CLIENT_SECRET` and `TOKEN_ENCRYPTION_KEY`.

## Entra-side checklist (per environment)

| Item | DEV | TEST | PROD |
|------|-----|------|------|
| App registration | Done | Done | |
| Web redirect URI `https://<host>/auth/callback` | Done | Done | |
| ID tokens enabled | Done | Done | |
| Client secret (note expiry) | | | |
| App roles `global_admin`, `global_analyst` (Value must match exactly) | | | |
| Optional claims `email`, `given_name`, `family_name` on ID token | | | |
| `http://localhost:3001/auth/callback` (dev only) | | n/a | n/a |
| Homepage URL `https://<host>/dashboard` | | | |
| Assignment required = Yes | Done | | |
| Access packages / user assignment | | | |

Values needed per environment: tenant ID, client (application) ID, client secret. They
are kept in the GitHub environment settings and local `.env.local` only, never in the repo.

## Improvements

### Block sign-in for users without a TAP role (done)

Today two things stop people who were not added by an admin:

1. Entra: **Assignment required = Yes** on the Enterprise app. Anyone not assigned
   (including IDIR users) is refused by Entra (AADSTS50105) and never reaches TAP.
2. TAP: the dashboard only opens for `ALLOWED_ROLES` (`global_admin`, `global_analyst`);
   others are sent to `/unauthorized`.

Gap: the role check guards the dashboard page, not sign-in. If a user were ever signed
in without a role (e.g. Assignment required switched to No in one environment), a
session would still be created, and that session can call the API directly for the
datasets with no `required_roles`: `total_spend_over_time`, `spend_by_sector`,
`isp_spending`, `isp_spend_indicators`, `service_category_spend_plotly`.

Fix: in `app/frontend/src/app/auth/callback/route.ts`, do not create a session when the
user has no allowed role (`hasAuthorizedRole`); redirect to `/unauthorized` instead.
Then no session exists without a role, whatever the Entra settings.

### Log out of Entra too, not only TAP (done in code; redirect URI in step 2 still to register)

Microsoft's OIDC guide (https://learn.microsoft.com/en-us/entra/identity-platform/v2-protocols-oidc,
"Send a sign-out request") says sign-out must do **both**: clear the app's session **and**
redirect the user to Entra's logout endpoint. If either is skipped, "the user may remain
authenticated and not be prompted to sign-in the next time they use your app".

Today `/auth/logout` only clears the TAP session. Clicking **Log in** again signs the user
straight back in without asking, because their Entra session is still active. On a shared
computer the next person would get in as the previous user.

Fix:

1. In `app/frontend/src/app/auth/logout/route.ts`, after `revokeCurrentSession()`, redirect
   to Entra's `end_session_endpoint` (from the discovery document) with
   `post_logout_redirect_uri=https://<host>/`. No stored ID token is needed; Entra may
   show an account picker.
2. Register `https://<host>/` (and `http://localhost:3001/` for dev) as a Web redirect URI
   on each app registration, next to `/auth/callback`. Entra only redirects to registered URIs.

Trade-off: this also signs the user out of Microsoft in that browser, so other Microsoft
sites (Outlook on the web, Teams web, etc.) will ask them to sign in again.

### Single sign-out (optional; only if required)

With front-channel logout, signing out of another app in the tenant also signs the user
out of TAP. Needs:

1. A **Front-channel logout URL** on the app registration (Authentication → Settings),
   e.g. `https://<host>/auth/frontchannel-logout`.
2. A route at that URL that ends the user's TAP session and returns `200`.

Not needed unless someone asks for it.

### Clearer sign-in error messages (done)

When Entra sends an error back to `/auth/callback` (e.g. `access_denied` when the user
cancels or refuses consent), TAP shows the generic `/?authError=callback_failed`. Reading
Entra's `error` parameter and showing a plain message ("Sign-in was cancelled", "You don't
have access to TAP – contact the Telecom Office") would help users and support.

### Turn off the implicit "ID tokens" setting (tidy-up)

The Entra team ticked **ID tokens (used for implicit and hybrid flows)** on the app
registration, following the guide's example, which uses `response_type=id_token`. TAP uses
the authorization code flow with PKCE (`response_type=code`): Entra returns a short-lived
code and TAP's server exchanges it, using the client secret, for the ID token, so no token
passes through the browser. The checkbox is not needed. After testing, ask the Entra team
to untick it in each environment, so a flow TAP doesn't use is closed.

## Before go-live checklist

- [x] Decide on / implement **Block sign-in for users without a TAP role** (see Improvements)
- [x] Decide on / implement **Log out of Entra too, not only TAP** (see Improvements)
- [ ] Site root `https://<host>/` registered as a redirect URI in every environment (needed for logout)
- [ ] Enterprise app **Assignment required = Yes** in every environment
- [ ] App roles created with Values `global_admin`, `global_analyst`
- [ ] `openid` added to API permissions and admin consent granted
- [ ] Redirect URI is `https://<host>/auth/callback` (not the site root) in every environment
- [ ] GitHub variables/secret `ENTRA_TENANT_ID`, `ENTRA_CLIENT_ID`, `ENTRA_CLIENT_SECRET` set per environment
- [ ] Client secret expiry date recorded
- [ ] Tested on dev: IDIR user, guest from another org, email-code user, user with no role
- [ ] Users told they must sign in again (migration 012 clears sessions)
- [ ] After prod is live: remove `KEYCLOAK_*` / `TOKEN_ENCRYPTION_KEY` settings, retire CSS client `conn-hub-6434`

## Open questions

- Is a PHSA "admin" an admin of all of TAP, or only of PHSA's users/data? Decides the
  app roles.
- Will we manage users through an access package, or get rights to invite guests and
  assign roles directly?
