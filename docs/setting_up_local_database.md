# Setting up a local PostgreSQL database and raw ingestion

This guide walks through running PostgreSQL locally, creating the **`raw_data`** schema and tables defined under `local_dev/raw_ingestion/`, then loading Excel source files using the ingestion scripts.

The examples use database name **`app`**, user **`postgres`**, and password **`mysecretpassword`** (change these if you prefer; keep the password out of git and shell history where possible).

---

## Step 1: Install PostgreSQL

Pick **one** of the following approaches.

### Option A: Container (Rancher Desktop or Podman Desktop)

You can run PostgreSQL in a container without a full Postgres install on the host. Rancher Desktop and Podman Desktop are desktop apps that bundle a container engine and tooling for macOS, Windows, and Linux.

This project recommends **[Rancher Desktop](https://rancherdesktop.io/)**—it integrates well across platforms and exposes a **`docker`**-compatible CLI in typical setups once the application is installed and running. **[Podman Desktop](https://podman-desktop.io/)** is another solid option if you prefer a rootless-focused stack; substitute **`podman`** for **`docker`** in every command below (`podman run`, `podman stop`, and so on—the flags are the same).

After your chosen desktop is installed, start it and wait until the engine is healthy, then continue.

**macOS / Linux — copy-paste:**

```bash
docker run --name app-local-postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=mysecretpassword \
  -e POSTGRES_DB=app \
  -p 5432:5432 \
  -d postgres:16
```

**Windows (PowerShell) — copy-paste:**

```powershell
docker run --name app-local-postgres `
  -e POSTGRES_USER=postgres `
  -e POSTGRES_PASSWORD=mysecretpassword `
  -e POSTGRES_DB=app `
  -p 5432:5432 `
  -d postgres:16
```

- **Stopping:** `docker stop app-local-postgres` (Podman users: `podman stop app-local-postgres`)
- **Starting again:** `docker start app-local-postgres` (Podman: `podman start app-local-postgres`)
- **Port conflict:** If something else uses `5432`, map a different host port, for example `-p 5433:5432`, and use `localhost:5433` in `DATABASE_URL` below.

---

### Option B: Install PostgreSQL from the PostgreSQL website

1. Download an installer or package for your operating system from the official PostgreSQL downloads page: [https://www.postgresql.org/download/](https://www.postgresql.org/download/)
2. Run the installer and complete the setup wizard. Choose (or remember) the superuser password you set during installation—you will use that instead of `mysecretpassword` in `DATABASE_URL` unless you align them manually.
3. Ensure the **`psql`** client is on your `PATH`, or invoke it via the full path the installer documents (often under “Application Stack Builder” / “SQL Shell” on Windows, or Terminal on macOS after Homebrew/apt install flows).
4. Create a database for this project if the installer did not create one named `app`:

   ```bash
   createdb -U postgres app
   ```

   (On Windows you can run equivalent commands from PowerShell once `createdb` is on PATH, or use pgAdmin below to create a database named `app`.)

---

## Step 2: Apply schemas and run the ingestion scripts

All commands below assume your **current working directory is the repository root** (the folder that contains `local_dev/`).

### Put source Excel files outside this repository

Do not commit spreadsheets into the repo. Use a folder **outside** the clone for your workbook trees so paths stay portable and confidential data stays out of version control.

**Examples:**

| Platform | Example folder |
|----------|----------------|
| macOS | `~/Documents/ngta-local-excels` |
| macOS | `~/Data/ngta-ingest-source` |
| Windows | `C:\Users\<YourUsername>\Documents\ngta-local-excels` |
| Windows | `D:\local-data\ngta-ingest-source` |

Create subfolders according to each script’s layout (summarized below). Replace the paths in the sample commands with your actual folders.

---

### Prerequisites: Python packages and connection string

Set a Postgres connection URI. Adjust host, port, user, password, and database name to match Docker or your local install:

```bash
export DATABASE_URL=postgresql://postgres:mysecretpassword@localhost:5432/app
```

**Windows PowerShell:**

```powershell
$env:DATABASE_URL = "postgresql://postgres:mysecretpassword@localhost:5432/app"
```

Install Python dependencies once per ingestion area (each has its own `requirements.txt`; installing all three is fine):

```bash
pip install -r local_dev/raw_ingestion/ngta_postgres_ingest/requirements.txt
pip install -r local_dev/raw_ingestion/tsma_postgres_ingest/requirements.txt
pip install -r local_dev/raw_ingestion/tsma_other_postgres_ingest/requirements.txt
```

---

### Deploy database objects (`raw_data` schema)

Run each `schema.sql` against the target database (`DATABASE_URL`). They are idempotent for `CREATE SCHEMA IF NOT EXISTS` and table/index creation.

```bash
psql "$DATABASE_URL" -f local_dev/raw_ingestion/ngta_postgres_ingest/schema.sql
psql "$DATABASE_URL" -f local_dev/raw_ingestion/tsma_postgres_ingest/schema.sql
psql "$DATABASE_URL" -f local_dev/raw_ingestion/tsma_other_postgres_ingest/schema.sql
```

**Windows PowerShell** (quoted variable):

```powershell
psql $env:DATABASE_URL -f local_dev/raw_ingestion/ngta_postgres_ingest/schema.sql
psql $env:DATABASE_URL -f local_dev/raw_ingestion/tsma_postgres_ingest/schema.sql
psql $env:DATABASE_URL -f local_dev/raw_ingestion/tsma_other_postgres_ingest/schema.sql
```

Order does not matter for a fresh database; rerun safely when scripts add new definitions.

---

### Sample ingestion commands

Replace the italicized paths with your **outside-repo** folders.

#### 1) NGTA Telus / Rogers (`ngta_postgres_ingest`)

Expects workbooks under a root like:

- `telus/` (any depth) for Telus files
- `rogers/cellular/`, `rogers/voice/`, and/or `rogers/data/` for Rogers

```bash
python local_dev/raw_ingestion/ngta_postgres_ingest/ingest_raw_excel_folder.py ~/Documents/ngta-local-excels/ngta_spend_root
python local_dev/raw_ingestion/ngta_postgres_ingest/ingest_raw_excel_folder.py "C:/Users/YourUsername/Documents/ngta-local-excels/ngta_spend_root"
```

Optional: `--source-period 2025-06-01`, `--dry-run` (no database writes).

#### 2) TSMA core / lite (`tsma_postgres_ingest`)

Expects paths such as `<root>/tsma/wireless/`, `<root>/tsma/wireline/`, `<root>/tsma/master/`, `tsma_lite/wireless/`, `tsma_lite/wireline/`.

```bash
python local_dev/raw_ingestion/tsma_postgres_ingest/ingest_tsma_excel_folder.py ~/Documents/ngta-local-excels/tsma_root
python local_dev/raw_ingestion/tsma_postgres_ingest/ingest_tsma_excel_folder.py "C:/Users/YourUsername/Documents/ngta-local-excels/tsma_root"
```

#### 3) TSMA Other (`tsma_other_postgres_ingest`)

Expects a `tsma_other` root with workbooks directly in:

- `managed_security/`
- `managed_router/`

```bash
python local_dev/raw_ingestion/tsma_other_postgres_ingest/ingest_tsma_other_excel_folder.py ~/Documents/ngta-local-excels/tsma_other
python local_dev/raw_ingestion/tsma_other_postgres_ingest/ingest_tsma_other_excel_folder.py "C:/Users/YourUsername/Documents/ngta-local-excels/tsma_other"
```

Each script accepts `--dsn` to override `DATABASE_URL` for a single run if needed.

---

## Connecting to your database

There is more than one way to inspect or query PostgreSQL locally.

### pgAdmin

[pgAdmin](https://www.pgadmin.org/) is a graphical administration and SQL client aimed at Postgres. Install it from the pgAdmin downloads page link above, register a server with host **localhost**, port **5432** (or the port you mapped), user **postgres**, and your chosen password. You can browse the **`raw_data`** schema and tables after the schemas have been applied.

### `psql`

`psql` is the official command-line client (bundled with most PostgreSQL installations and easy to invoke from a container shell, for example `docker exec -it app-local-postgres psql -U postgres -d app`, or `podman exec …` if you use Podman). It is lightweight and fits automation and copying SQL from documentation.

Either tool connects to **the same** database referenced by **`DATABASE_URL`**; the ingestion scripts themselves use that URI via `psycopg`.

---

## Quick reference

| Item | Default in this doc |
|------|---------------------|
| Database | `app` |
| User | `postgres` |
| Password (Docker example) | `mysecretpassword` |
| JDBC/URI pattern | `postgresql://postgres:mysecretpassword@localhost:5432/app` |
| Schema created by ingestion SQL | `raw_data` |
