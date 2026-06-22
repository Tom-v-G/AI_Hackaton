# De Lekbak Viral CVE Dashboard

Standalone hackathon app for tracking CVEs that are currently gaining attention across public discussion sources.

## Structure

- `backend/` - independent FastAPI API for viral CVE rankings.
- `frontend/` - independent Vite/React dashboard shell.

The app is intentionally owned by `de_lekbak` and does not import from or require the existing `cve-intelligence` project at runtime.

## Quick start

From the `de_lekbak/` directory, run the full local setup after a fresh pull:

```bash
make setup
```

This synchronizes backend and frontend dependencies, starts the app-owned Dockerized Postgres database, waits until it is ready, and applies Alembic migrations.

Local Postgres defaults match the backend settings:

- database: `de_lekbak`
- user: `de_lekbak`
- password: `de_lekbak`
- host port: `5432`

Useful setup targets:

```bash
make backend-setup  # uv sync --all-extras --dev in backend/
make frontend-setup # npm ci in frontend/
make db-up          # docker compose up -d postgres
make db-wait        # wait for Postgres readiness
make migrate        # uv run alembic upgrade head in backend/
```

The default setup path is non-destructive; it does not drop or reset the local database volume.

Backend:

```bash
cd backend
uv run uvicorn de_lekbak_backend.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```
