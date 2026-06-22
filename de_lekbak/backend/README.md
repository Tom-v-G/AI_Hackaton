# De Lekbak Backend

Standalone FastAPI backend for viral CVE rankings. It reimplements the API shape needed by the viral dashboard and does not import from `cve-intelligence`.

## Commands

```bash
uv run uvicorn de_lekbak_backend.main:app --reload
uv run pytest
uv run ruff check .
```

## Preview Bluesky data without storing it

Fetch public Bluesky search results and print matching posts without writing to PostgreSQL:

```bash
uv run python -m de_lekbak_backend.scripts.preview_bluesky --limit 20
```

The script uses Bluesky's unauthenticated public appview endpoint at `https://api.bsky.app`. The `public.api.bsky.app` host currently returns `403` for `app.bsky.feed.searchPosts`.

Optional examples:

```bash
uv run python -m de_lekbak_backend.scripts.preview_bluesky --terms "CVE,RCE,exploit" --limit 10
uv run python -m de_lekbak_backend.scripts.preview_bluesky --include-no-cve --limit 10
```
