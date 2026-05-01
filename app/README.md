# DMP Application

End-to-end application skeleton:

- **`backend/`** — FastAPI + SQLAlchemy 2 + pandas + dbt (dbt-core / dbt-postgres).
- **`frontend/`** — Next.js 15 + React 19 + React Query (`@tanstack/react-query`) + `react-plotly.js` + `@bcgov/design-system-react-components`.
- **`db/`** — Postgres 16 image with `pg_partman` for partitioning plus `pg_trgm` / `btree_gin` / `btree_gist` for advanced indexing.
- **`docker-compose.yml`** — Local development stack (live reload for both backend and frontend, volume-mounted source).

## Local development

```bash
cd app
docker compose up --build
```

Services:

| Service  | URL                          |
| -------- | ---------------------------- |
| Frontend | http://localhost:3000        |
| Backend  | http://localhost:8000        |
| API docs | http://localhost:8000/docs   |
| Postgres | postgres://dmp:dmp@localhost:5432/dmp |

Local file changes auto-reload:

- Backend: `uvicorn --reload` watches `./backend/app`.
- Frontend: Next.js dev server with filesystem polling enabled for Docker.

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
docker build -t <registry>/dmp-backend:<tag> ./app/backend

# Frontend (multi-stage, standalone Next.js output)
docker build -t <registry>/dmp-frontend:<tag> ./app/frontend

# Postgres (only if self-hosting; prefer RDS/Aurora in production)
docker build -t <registry>/dmp-postgres:<tag> ./app/db
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
