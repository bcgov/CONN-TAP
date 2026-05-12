# App

End-to-end application skeleton:

- **`backend/`** — FastAPI + SQLAlchemy 2 + pandas + dbt (dbt-core / dbt-postgres).
- **`frontend/`** — Next.js 15 + React 19 + React Query (`@tanstack/react-query`) + `react-plotly.js` + `@bcgov/design-system-react-components`.
- **`db/`** — Postgres 16 image with `pg_partman` for partitioning plus `pg_trgm` / `btree_gin` / `btree_gist` for advanced indexing.
- **`docker-compose.yml`** — Local development stack for Postgres and the FastAPI backend. The Next.js frontend is intended to run locally by default.

## Local development

```bash
cd app
docker compose up --build
```

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

## Running dbt

From inside the backend container (or any environment with dbt installed):

```bash
cd app/backend/dbt
DBT_PROFILES_DIR=. dbt run
DBT_PROFILES_DIR=. dbt test
```

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
