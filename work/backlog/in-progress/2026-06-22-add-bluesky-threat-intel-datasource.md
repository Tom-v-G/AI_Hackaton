# Add Bluesky Threat Intel Datasource

## Type

feature

## Context

De Lekbak tracks viral CVEs from public discussion sources. The current `de_lekbak` backend is a standalone FastAPI app with router, service, repository, schema, settings, and test layers under `de_lekbak/backend/de_lekbak_backend/`.

The older `cve-intelligence/` app is present as prior art only. It provides reference patterns for async SQLAlchemy, PostgreSQL, Alembic migrations, HTTP clients, structured logging, repositories, ingestion services, and NVD data processing. `de_lekbak` must not import from or require `cve-intelligence` at runtime.

Add Bluesky/ATProto as a new social threat-intelligence datasource while preserving existing De Lekbak behavior and keeping NVD enrichment optional.

## Functional Requirements

- Add a separate Bluesky threat-intelligence ingestion capability for public Bluesky posts.
- Use the public Bluesky API endpoint `https://public.api.bsky.app/xrpc/app.bsky.feed.searchPosts`.
- Search with `sort=latest`.
- Support these search terms by default: `CVE`, `CVE-`, `vulnerability`, `exploit`, `0day`, `RCE`, `PoC`, `critical vulnerability`.
- Extract CVE IDs from post text with regex `CVE-\d{4}-\d+`.
- Store all CVE IDs found in a post as an array.
- Calculate engagement score as `like_count + (reply_count * 1.5) + (repost_count * 2) + (quote_count * 2)`.
- Make engagement weights configurable.
- Deduplicate posts by `post_uri`.
- On duplicate posts, update counts, engagement score, and `indexed_at`.
- On duplicate posts, update text only when the incoming text differs.
- Provide repository-level analytics functions for future API endpoints:
  - trending CVEs from the last 24 hours
  - top posts by engagement score
  - unique post count per CVE
  - most active authors
- Manual refresh, CLI, or direct service-call ingestion is sufficient for this story; no automatic background polling is required.

## Technical Requirements

- Place all new backend runtime code under `de_lekbak/backend/de_lekbak_backend/`.
- Add new Alembic migration infrastructure under `de_lekbak/backend/alembic/`.
- Use the same PostgreSQL database as the existing Docker environment from `cve-intelligence/docker/docker-compose.yml`.
- Do not add a second database.
- Add a new table `bluesky_mentions` in the existing PostgreSQL database.
- Use the local `de_lekbak` backend as the implementation owner; do not import from `cve-intelligence`, `cve_intelligence`, or `app`.
- Reimplement useful prior-art patterns from `cve-intelligence` where appropriate:
  - async SQLAlchemy session factory pattern
  - repository receives an `AsyncSession`
  - Alembic async migration pattern
  - Pydantic settings via `pydantic-settings`
  - `httpx.AsyncClient` for external API calls
  - service-layer business logic with thin controllers
  - structured logging pattern if logging is added
- Add local database dependencies to `de_lekbak/backend/pyproject.toml`, expected to include SQLAlchemy, asyncpg, and Alembic.
- Add local DB configuration to `de_lekbak_backend.core.config.Settings`, including database URL and pool options, using the existing settings style.
- Support Bluesky configuration via environment variables in the existing De Lekbak settings style:
  - `BLUESKY_ENABLED=true`
  - `BLUESKY_POLL_INTERVAL_SECONDS=300`
  - `BLUESKY_SEARCH_TERMS=CVE,CVE-,vulnerability,exploit,0day,RCE,PoC,critical vulnerability`
  - configurable engagement weights for likes, replies, reposts, and quotes
- Decide whether Bluesky env vars are unprefixed or adapted to the current `DE_LEKBAK_` settings prefix before implementation; document the final choice in code/tests.
- Model `bluesky_mentions` with these fields:
  - `id` UUID primary key
  - `post_uri` unique
  - `cid`
  - `author_did`
  - `author_handle`
  - `display_name`
  - `created_at`
  - `indexed_at`
  - `text`
  - `like_count`
  - `reply_count`
  - `repost_count`
  - `quote_count`
  - `engagement_score`
  - `extracted_cves` as `text[]`
  - `inserted_at`
- Add indexes:
  - `created_at`
  - `author_handle`
  - `extracted_cves` using GIN
  - `engagement_score DESC`
- Implement UPSERT semantics using `post_uri` as the unique conflict target.
- Keep business logic in `BlueskyThreatIntelService`:
  - fetch posts
  - extract CVEs
  - calculate engagement score
  - persist results
  - process duplicates
- Add a provider abstraction such as `ThreatIntelProvider.fetch_posts()` so later sources can be added without major changes.
- Implement Bluesky as one provider implementation, designed so future Jetstream or Firehose implementations can replace the polling provider.
- Keep analytics as repository functions only; do not add API endpoints for analytics in this story.
- Preserve existing endpoints and tests for health and viral CVE refresh behavior.
- Add unit tests for CVE extraction, engagement scoring, provider parsing, service behavior, and repository query/upsert construction where practical.
- Add integration tests only if the local De Lekbak test infrastructure supports database-backed tests without making the suite brittle.
- Validate with `uv run pytest` and `uv run ruff check .` from `de_lekbak/backend/`.

Rejected alternatives and rationale:

- Reject importing from `cve-intelligence`: project rules require `de_lekbak` to remain standalone and existing tests enforce this boundary.
- Reject adding a new database: requirement is to reuse the existing Docker PostgreSQL database.
- Reject automatic background polling for this story: manual refresh, CLI, or service-call ingestion is sufficient and reduces lifecycle/scheduler complexity.
- Reject analytics API endpoints for this story: repository functions are enough for future endpoints and keep the scope focused.

## Acceptance Criteria

- New backend runtime code is located only under `de_lekbak/backend/de_lekbak_backend/`.
- Alembic migration files for De Lekbak are located under `de_lekbak/backend/alembic/`.
- The migration creates `bluesky_mentions` in the existing PostgreSQL database with all required columns and indexes.
- No new database service or second database is introduced.
- `de_lekbak` does not import from `cve-intelligence`, `cve_intelligence`, or `app`.
- Bluesky search uses the public `app.bsky.feed.searchPosts` endpoint with `sort=latest`.
- Default search terms include all required terms, including `critical vulnerability`.
- Posts with one or more CVE IDs are persisted with `extracted_cves` populated as an array.
- Engagement score uses configurable weights and matches the required default formula.
- Re-ingesting an existing `post_uri` performs an UPSERT and updates counts, engagement score, indexed timestamp, and changed text.
- Repository functions exist for trending CVEs in the last 24 hours, top posts by engagement, unique posts per CVE, and most active authors.
- Bluesky ingestion can be triggered manually through a service call, CLI, or refresh path without requiring automatic background polling.
- Existing De Lekbak health and viral CVE behavior remains non-breaking.
- Tests cover extraction, scoring, deduplication/upsert behavior, and analytics query behavior where practical.
- Backend validation passes with the relevant test and lint commands.
