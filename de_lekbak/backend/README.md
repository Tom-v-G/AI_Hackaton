# De Lekbak Backend

Standalone FastAPI backend for viral CVE rankings. It reimplements the API shape needed by the viral dashboard and does not import from `cve-intelligence`.

## Commands

```bash
uv run uvicorn de_lekbak_backend.main:app --reload
uv run pytest
uv run ruff check .
```
