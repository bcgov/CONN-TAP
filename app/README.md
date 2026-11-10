# App

End-to-end application skeleton:

- **`backend/`** — FastAPI + SQLAlchemy 2 + pandas + dbt (dbt-core / dbt-postgres).
- **`frontend/`** — Next.js 16 + React 19 + React Query (`@tanstack/react-query`) + `react-plotly.js` + `@bcgov/design-system-react-components` + server-side Entra ID authentication.
- **`db/`** — Postgres 16 image with `pg_partman` for partitioning plus `pg_trgm` / `btree_gin` / `btree_gist` for advanced indexing.
- **`docker-compose.yml`** — Local development stack for Postgres and the FastAPI backend. The Next.js frontend is intended to run locally by default.

## Local development

```bash
cd app
docker compose up --build
```

### Database migrations (Alembic)

Postgres database `app` DDL is managed by **Alembic** in `backend/`:

| Schema | Contents |
|--------|----------|
| `app` | Auth and user tables |
| `raw_data` | NGTA / TSMA raw landing tables (SQL under `alembic/raw_data/`) |

After Postgres is up:

```bash
cd app/backend
# match POSTGRES_* to docker-compose (host localhost, user app, password app, POSTGRES_SSL=false)
POSTGRES_HOST=localhost POSTGRES_PORT=5432 POSTGRES_USER=app POSTGRES_PASSWORD=app POSTGRES_DB=app POSTGRES_SSL=false \
  alembic upgrade head
```

Or via the backend container:

```bash
cd app
docker compose run --rm backend alembic upgrade head
```

Then load spreadsheets with the scripts in [`docs/setting_up_local_database.md`](../docs/setting_up_local_database.md) (optional for local dev) and run **dbt** (see [Running dbt](#running-dbt)).

Run the frontend locally in a separate terminal:

```bash
cd app/frontend
pnpm install
pnpm dev
```

If you want the frontend in Docker again, enable the optional profile:

```bash
cd app
docker compose --profile frontend up --build
```

Services:

| Service  | URL                          |
| -------- | ---------------------------- |
| Frontend | http://localhost:3001        |
| Backend  | http://localhost:8000        |
| API docs | http://localhost:8000/docs   |
| Postgres | postgres://app:app@localhost:5432/app |

Local file changes auto-reload:

- Backend: `uvicorn --reload` watches `./backend/app`.
- Frontend: run `pnpm dev` locally for reliable Fast Refresh on macOS.

To verify backend auto-reload from Docker Compose:

1. Start the stack with `docker compose up --build` from `app/`.
2. Open `http://localhost:8000/docs`.
3. Edit a file under `backend/app/`, for example change a response string in an API route.
4. Watch the backend container logs for a reload message from Uvicorn.
5. Refresh `/docs` or call the changed endpoint again to confirm the new code is live.

The backend container bind-mounts `./backend` into `/app` and starts `uvicorn app.main:app --reload --reload-dir /app/app`, so Python code changes under `backend/app/` should reload automatically.

## Authentication

This application signs users in with the **BC Gov Entra ID** tenant (IDIR users, guests from other organizations, and email one-time-code guests).

For Entra setup, environment variables, roles and the authentication flow, see [ENTRA.md](./frontend/ENTRA.md).

### Quick Start - Authentication

1. Copy `frontend/.env.local.example` to `frontend/.env.local` and set `ENTRA_TENANT_ID`, `ENTRA_CLIENT_ID` and `ENTRA_CLIENT_SECRET` from the dev app registration (and any other overrides).
   `pnpm dev` and Docker Compose both use the same auth-related variables from these files.

2. `docker compose` loads `frontend/.env.local.example`, then merges `frontend/.env.local` when it exists.
   Compose overrides host-only values inside the stack (`POSTGRES_HOST=postgres`, `BACKEND_INTERNAL_URL=http://backend:8000`).
   You do not need a separate backend `.env` for local session secrets as long as `.env.local` matches what Next.js uses.

3. Users log in via the landing page and are redirected to a secure dashboard after authentication. The browser receives only an opaque `HttpOnly` session cookie.

## Database users and roles

Each part of the app connects to Postgres as its own user, with only the access it needs. Created by Alembic migration `013_database_roles`.

| User | Used by | Access |
|------|---------|--------|
| `dbadmin` (RDS) / `app` (local) | Migrate job: Alembic and dbt | Owner of everything |
| `tap_web` | Frontend | Only `app.users`, `app.auth_sessions`, `app.auth_oauth_states` |
| `tap_api` | Backend | Reads `app.auth_sessions`, then switches to the user's role (below). No data access on its own. |

For every API request the backend switches to the Postgres role that matches the user's Entra app role (`app/core/roles.py`, highest role wins). The switch lasts for that transaction only, so the connection goes back to `tap_api` afterwards.

| Entra app role | Postgres role | Data |
|----------------|---------------|------|
| `to_admin` | `tap_to_admin` | All of `analytics` and `reference_data` |
| `to_viewer` | `tap_to_viewer` | All of `analytics` and `reference_data` |
| `org_admin` | `tap_org_admin` | None yet (organization-level access to come) |
| `org_user` | `tap_org_user` | None yet (organization-level access to come) |

New tables in `analytics` and `reference_data` are readable by the global roles automatically, as long as dbt and Alembic run as the same user that ran migration 013.

Passwords on RDS: Terraform (`infra/modules/postgres_rds`) creates them in Secrets Manager as `<license>-<env>/rds-tap-api` and `<license>-<env>/rds-tap-web`. The deploy's migrate job sets them in Postgres (`app/db/set_login_passwords.py`). Locally, the backend and frontend still connect as `app`.

## Running dbt

From inside the backend container (or any environment with dbt installed):

```bash
cd app/backend/dbt
DBT_PROFILES_DIR=. dbt run
DBT_PROFILES_DIR=. dbt test
```

### Tests

Tests live in `seeds/_seeds.yml` (alias-to-reference-data relationships) and `models/intermediate/_intermediate.yml` (not_null/unique checks on the unioned spend model). `dbt test` also runs in the Helm `db-migrate` job on every deploy.

## Building production images for EKS

Each component has its own Dockerfile and is independently buildable / pushable:

```bash
# Backend
docker build -t <registry>/app-backend:<tag> ./app/backend

# Frontend (multi-stage, standalone Next.js output)
docker build -t <registry>/app-frontend:<tag> ./app/frontend

# Postgres (only if self-hosting; prefer RDS/Aurora in production)
docker build -t <registry>/app-postgres:<tag> ./app/db
```

Push to ECR and reference the images from your EKS Deployments / Helm charts.
The frontend image uses Next.js [`output: "standalone"`](https://nextjs.org/docs/app/api-reference/next-config-js/output) for minimal runtime footprint.

## Project layout

```
app/
├── backend/
│   ├── alembic/             # migrations: schemas `app`, `raw_data`
│   │   └── raw_data/        # raw landing DDL (NGTA / TSMA)
│   ├── alembic.ini
│   ├── app/                 # FastAPI source
│   │   ├── api/endpoints/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   └── schemas/
│   ├── dbt/                 # dbt project (profile reads env vars)
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/app/             # Next.js App Router
│   ├── Dockerfile           # production (standalone)
│   ├── Dockerfile.dev       # local dev with hot reload
│   └── package.json
├── db/
│   ├── Dockerfile           # Postgres + pg_partman
│   └── init/                # bootstrap SQL (extensions, partitioned tables)
└── docker-compose.yml
```
