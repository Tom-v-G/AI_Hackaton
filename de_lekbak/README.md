# De Lekbak Viral CVE Dashboard

Standalone hackathon app for tracking CVEs that are currently gaining attention across public discussion sources.

## Structure

- `backend/` - independent FastAPI API for viral CVE rankings.
- `frontend/` - independent Vite/React dashboard shell.

The app is intentionally owned by `de_lekbak` and does not import from or require the existing `cve-intelligence` project at runtime.

## Quick start

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
