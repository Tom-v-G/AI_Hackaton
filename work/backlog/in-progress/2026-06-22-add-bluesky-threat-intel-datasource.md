# Add Bluesky Threat Intel Datasource

## Type

feature

## Context

De Lekbak tracks viral CVEs from public discussion sources. The current `de_lekbak` backend is a standalone FastAPI app with router, service, repository, schema, settings, database, Alembic, and test layers under `de_lekbak/backend/`.

The older `cve-intelligence/` app is present as prior art only. It provides reference patterns for async SQLAlchemy, PostgreSQL, Alembic migrations, HTTP clients, structured logging, repositories, ingestion services, and NVD data processing. `de_lekbak` must not import from or require `cve-intelligence` at runtime.

Add Bluesky/ATProto as a new social threat-intelligence datasource while preserving existing De Lekbak behavior and keeping NVD enrichment optional. A De Lekbak database baseline now exists and should be reused rather than recreated.

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
- Reuse the existing De Lekbak database infrastructure under `de_lekbak/backend/de_lekbak_backend/db/`.
- Reuse the existing Alembic infrastructure under `de_lekbak/backend/alembic/`.
- Add only a new Alembic revision for `bluesky_mentions`; do not recreate or replace the existing baseline revision.
- Use the PostgreSQL database already configured for De Lekbak through `DE_LEKBAK_DATABASE_URL` and the existing settings in `de_lekbak_backend.core.config.Settings`.
- Do not add a second database or new Docker database service.
- Add a new table `bluesky_mentions` in the existing PostgreSQL database.
- Use the local `de_lekbak` backend as the implementation owner; do not import from `cve-intelligence`, `cve_intelligence`, or `app`.
- Follow the already-present De Lekbak database patterns, which were derived from the `cve-intelligence` prior art:
  - repository receives an `AsyncSession`
  - existing async SQLAlchemy session factory
  - existing Alembic async migration pattern
  - Pydantic settings via `pydantic-settings`
  - `httpx.AsyncClient` for external API calls
  - service-layer business logic with thin controllers
  - structured logging pattern if logging is added
- Do not add database dependencies or DB settings unless an implementation-specific gap remains; SQLAlchemy, asyncpg, Alembic, database URL, and pool settings already exist.
- Support Bluesky configuration via environment variables in the existing De Lekbak settings style using the `DE_LEKBAK_` prefix:
  - `DE_LEKBAK_BLUESKY_ENABLED=true`
  - `DE_LEKBAK_BLUESKY_POLL_INTERVAL_SECONDS=300`
  - `DE_LEKBAK_BLUESKY_SEARCH_TERMS=CVE,CVE-,vulnerability,exploit,0day,RCE,PoC,critical vulnerability`
  - configurable engagement weights for likes, replies, reposts, and quotes
- Use prefixed De Lekbak settings for Bluesky; do not introduce unprefixed `BLUESKY_*` environment variables unless explicitly required later.
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
- Reject adding a new database: requirement is to reuse the existing De Lekbak PostgreSQL configuration.
- Reject recreating DB infrastructure: De Lekbak already has `db/base.py`, `db/session.py`, `alembic.ini`, `alembic/env.py`, dependencies, and a baseline migration.
- Reject automatic background polling for this story: manual refresh, CLI, or service-call ingestion is sufficient and reduces lifecycle/scheduler complexity.
- Reject analytics API endpoints for this story: repository functions are enough for future endpoints and keep the scope focused.

## Acceptance Criteria

- New backend runtime code is located only under `de_lekbak/backend/de_lekbak_backend/`.
- A new Alembic revision for De Lekbak is located under `de_lekbak/backend/alembic/versions/` and depends on the existing baseline revision.
- The new migration creates `bluesky_mentions` in the configured De Lekbak PostgreSQL database with all required columns and indexes.
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

## Analysis

### Likely Impact

- Primary implementation lane: `Settings` config -> Bluesky provider/service -> SQLAlchemy model/repository -> De Lekbak Alembic revision -> backend tests.
- `de_lekbak/backend/de_lekbak_backend/core/config.py` - add `DE_LEKBAK_`-prefixed Bluesky enable/search/interval/engagement-weight settings; existing `Settings` already uses `env_prefix="DE_LEKBAK_"`.
- `de_lekbak/backend/de_lekbak_backend/services/` - add `BlueskyThreatIntelService` plus a provider abstraction and Bluesky polling provider; current service layer is thin and owns business behavior in `viral_cve_service.py`.
- `de_lekbak/backend/de_lekbak_backend/repositories/` - add an async-session-backed Bluesky repository for UPSERT and analytics queries; existing DB session infrastructure provides `AsyncSession` via `db/session.py`.
- `de_lekbak/backend/de_lekbak_backend/db/` or a new local `models/` package - add/import the `bluesky_mentions` ORM model so `Base.metadata` is migration-aware; current `Base` is empty and Alembic uses `Base.metadata` in `alembic/env.py`.
- `de_lekbak/backend/alembic/versions/` - add one revision depending on `20260622_0001`; the existing baseline revision is intentionally empty and should not be replaced.

### Possible Adjacent Touchpoints

- `de_lekbak/backend/tests/test_app.py` - existing assertions cover settings prefix, async session behavior, empty metadata, refresh behavior, and no `cve_intelligence`/`app` imports; the metadata assertion will need to reflect the new local model table.
- `de_lekbak/backend/de_lekbak_backend/api/v1/viral_cves.py` - avoid changing unless choosing the existing refresh path as the manual trigger; a direct service-call or local CLI-style entrypoint is enough for this story.
- `de_lekbak/backend/pyproject.toml` - only touch if an executable/CLI entrypoint is chosen and existing dependencies are insufficient; story says DB/http dependencies should already exist.

### Existing Patterns / Prior Art

- `de_lekbak/backend/de_lekbak_backend/db/session.py` - local pattern for async engine/session factory and commit/rollback dependency.
- `de_lekbak/backend/alembic/env.py` and `de_lekbak/backend/alembic/versions/20260622_0001_initial_database_baseline.py` - local migration wiring and baseline revision to extend.
- `cve-intelligence/app/repositories/base.py` - prior-art shape for repositories receiving `AsyncSession`; copy/reimplement locally only.
- `cve-intelligence/app/models/cve.py` and `cve-intelligence/alembic/versions/001_initial_schema.py` - prior-art examples for PostgreSQL `ARRAY`, indexes, UUID primary keys, and Alembic table/index definitions.
- `cve-intelligence/app/services/ingestion/nvd_ingestion.py` and `cve-intelligence/app/clients/http.py` - prior-art for service-owned ingestion flow and `httpx.AsyncClient` lifecycle; do not import these modules.

### Layer Boundaries

- Touch first: De Lekbak backend settings, local provider/service/repository/model, Alembic revision, and focused backend tests.
- Avoid unless evidence emerges: frontend dashboard, analytics API endpoints, background scheduler/lifespan polling, Docker/database services, NVD enrichment model, and any runtime imports from `cve-intelligence`, `cve_intelligence`, or `app`.
- Inference: keep the existing viral CVE refresh endpoint behavior stable; Bluesky ingestion can remain a separately callable backend service path unless implementers deliberately wire it as the story's manual trigger.

### Verification Plan

**Unit Tests**:

- CVE regex extraction, including multiple CVEs per post and posts with no CVE.
- Engagement scoring with default and overridden weights.
- Bluesky provider parsing for `app.bsky.feed.searchPosts` responses and `sort=latest` request parameters.
- Repository UPSERT statement behavior for duplicate `post_uri`, changed text, count updates, `indexed_at`, and extracted CVE arrays.
- Repository analytics query construction/results where practical.

**Integration Tests**:

- If DB-backed tests are available, apply the new migration and verify insert/update plus GIN/index-compatible array storage for `bluesky_mentions`.

**E2E / Manual Validation**:

- Manually trigger Bluesky ingestion via the chosen service-call/CLI/refresh path with a mocked or controlled provider and confirm existing health and viral CVE endpoints still behave as before.

**Additional Checks (as applicable)**:

- Confirm no new database service/settings or runtime imports from `cve-intelligence`, `cve_intelligence`, or `app` were introduced.

## Validation update (2026-06-22 13:45)

* Validation passed with no regressions found.
* Gate result: PASS.
* Baseline checks passed or had no unrelated failures observed: `uv run pytest` and `uv run ruff check .` passed from `de_lekbak/backend/`.
* Touched-scope coverage: no material regression; focused tests cover settings, provider parsing, extraction, scoring, ingestion filtering, UPSERT statement construction, analytics query construction, metadata registration, health, refresh, and dependency-boundary behavior.
* Security review: completed; reviewed external public API fetching, config/env handling, database UPSERT/query construction, and dependency-boundary changes with no story-blocking issue found.
* Retained exploratory artifacts: none; no browser/UI validation required for this backend-only story.
* Validated checklist items: Bluesky provider uses public searchPosts endpoint with `sort=latest`; default and prefixed configurable search/settings exist; CVE regex extraction stores arrays through service/repository input; engagement weights are configurable and match default formula; duplicate `post_uri` uses PostgreSQL UPSERT updating counts, score, indexed timestamp, CVEs, and changed text; repository analytics functions exist for trending CVEs, top engagement, unique post counts per CVE, and active authors; new model/migration create `bluesky_mentions` with required columns and indexes; migration depends on existing baseline; runtime code is under `de_lekbak_backend`; no new database service or second database was found; no forbidden `cve-intelligence`, `cve_intelligence`, or `app` runtime imports were found; existing health and viral CVE refresh behavior remains covered.
* Providers covered: Bluesky public API provider with mocked `httpx.AsyncClient`; no additional provider variants required.
