# Local Project Setup with Makefile and Docker Postgres

## Type

feature

## Context

`de_lekbak` is a standalone app with an independently owned backend and frontend. Team members may work primarily on one side of the stack, so local project setup should not require every developer to know all backend, frontend, database, and migration commands by heart.

After a fresh pull from `main`, developers should be able to run one Makefile command that prepares the local development environment, starts the local Postgres database, creates the expected development database when needed, installs/synchronizes dependencies, and applies Alembic migrations.

The backend already owns Postgres-only configuration and Alembic migration wiring under `de_lekbak/backend`. The missing piece is local orchestration for Dockerized Postgres plus a team-friendly setup command.

## Functional Requirements

- Provide a single local setup command for developers after a fresh pull from `main`.
- Start a local Postgres database for `de_lekbak` as part of setup.
- Ensure the default local database, user, and password expected by the backend are created for first-time local setup.
- Apply Alembic migrations to the local database as part of setup.
- Keep backend and frontend setup available as separate Makefile targets so developers can work within their stack boundaries.
- Preserve `de_lekbak` as a standalone app with no runtime dependency on `cve-intelligence`.

## Technical Requirements

- Add `de_lekbak`-owned Docker Compose configuration for local Postgres.
- Configure local Postgres defaults to match existing backend settings:
  - database: `de_lekbak`
  - user: `de_lekbak`
  - password: `de_lekbak`
  - host port: `5432`
- Add a Makefile owned by `de_lekbak`; recommended location is `de_lekbak/Makefile` so the workflow remains scoped to the standalone app.
- Add a top-level setup target, recommended name `setup`, that composes the local setup flow.
- Add separate Makefile targets for at least:
  - starting Postgres with Docker Compose
  - waiting until Postgres is ready before migrations run
  - applying Alembic migrations from `de_lekbak/backend`
  - backend dependency setup from `de_lekbak/backend`
  - frontend dependency setup from `de_lekbak/frontend`
- Use existing backend tooling from `de_lekbak/backend`, including `uv` and `uv run alembic upgrade head`.
- Use existing frontend tooling from `de_lekbak/frontend`, preferably `npm ci` when `package-lock.json` is present and appropriate for reproducible installs.
- Document the new setup workflow in `de_lekbak/README.md` or a nearby app-owned developer doc.
- Do not add destructive database reset behavior to the default setup path.
- If a destructive reset target is added, it must be explicitly named and must not run as part of `setup`.

Technical decisions:

- Decision: use Docker Compose as the default local Postgres route for now.
- Rationale: it gives frontend-leaning and backend-leaning developers a shared, repeatable local database without requiring manual Postgres installation or administration.
- Decision: `make setup` should start/create the local database and run Alembic upgrades.
- Rationale: the user wants a single post-pull command that initializes the project enough to continue development.
- Decision: keep backend, frontend, database, and migration setup as separate Makefile targets under the composed setup target.
- Rationale: this preserves team ownership boundaries and makes partial setup/debugging possible.
- Decision: avoid a default destructive reset.
- Rationale: reset behavior can destroy local developer data and should be an explicit separate choice if introduced.

Rejected alternatives:

- Rejected: require developers to run Postgres manually outside the project setup flow.
- Reason: this does not meet the requirement that setup starts and creates the local database.
- Rejected: use the existing `cve-intelligence` Docker Compose setup.
- Reason: `de_lekbak` must remain standalone and must not require `cve-intelligence` at runtime.
- Rejected: make Alembic upgrades a backend-only manual step.
- Reason: applying migrations is part of the desired single-command setup after pulling from `main`.

## Acceptance Criteria

- A developer can run one Makefile command after a fresh pull from `main` to set up the local `de_lekbak` environment.
- The setup command starts a Dockerized Postgres instance for `de_lekbak`.
- On first startup, Dockerized Postgres creates the default `de_lekbak` database and `de_lekbak` user expected by backend settings.
- The setup command waits until Postgres is ready before running Alembic migrations.
- The setup command runs Alembic upgrade to `head` from `de_lekbak/backend` successfully against the Dockerized database.
- Backend setup and frontend setup are available as separate Makefile targets.
- Database startup and migration upgrade are available as separate Makefile targets.
- The documented setup command and targets are discoverable from `de_lekbak` project documentation.
- Existing backend validation commands still work from `de_lekbak/backend`: `uv run pytest` and `uv run ruff check .`.
- Existing frontend validation commands still work from `de_lekbak/frontend`: `npm run build` and `npm run lint`.
- The implementation does not introduce runtime imports from or runtime requirements on `cve-intelligence`.

## Analysis

### Likely Impact

- Primary implementation lane: `de_lekbak/Makefile` -> `de_lekbak/docker-compose.yml` -> `de_lekbak/backend` Alembic/uv commands -> `de_lekbak/frontend` npm install command -> `de_lekbak/README.md` documentation.
- `de_lekbak/Makefile` - likely new orchestration entry point; no app-owned Makefile currently exists, and the story asks for composed `setup` plus separate backend/frontend/db/migration targets.
- `de_lekbak/docker-compose.yml` - likely new app-owned local Postgres config; current lookup found no `de_lekbak` compose file, while backend defaults already expect `de_lekbak:de_lekbak@localhost:5432/de_lekbak` in `de_lekbak/backend/de_lekbak_backend/core/config.py`.
- `de_lekbak/backend/alembic/env.py` - existing migration execution path already reads `get_settings().database_url`, so the Makefile should run migrations from `de_lekbak/backend` rather than changing Alembic wiring.
- `de_lekbak/README.md` - current quick start documents separate manual backend/frontend startup only; it needs the new `make setup` workflow and target discovery.

### Possible Adjacent Touchpoints

- `de_lekbak/backend/README.md` - may need a small pointer if backend-specific setup docs mention database or Alembic commands.
- `de_lekbak/frontend/package-lock.json` - already present, so the frontend setup target should prefer `npm ci`; package files should not need dependency changes.
- `.gitignore` or compose volume naming - only if implementation creates local env/cache artifacts outside Docker-managed named volumes.

### Existing Patterns / Prior Art

- `cve-intelligence/docker/docker-compose.yml` - closest Docker Compose prior art: Postgres 16 Alpine, explicit `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, port `5432:5432`, named volume, and `pg_isready` healthcheck. Reuse the shape, but keep the new file owned under `de_lekbak/` and change names/credentials to `de_lekbak`.
- `de_lekbak/backend/de_lekbak_backend/core/config.py` - source of truth for local database defaults and `DE_LEKBAK_` env prefix.
- `de_lekbak/backend/pyproject.toml` and `de_lekbak/frontend/package.json` - source of truth for existing backend/frontend tooling; setup should call `uv` and npm scripts without introducing alternate package managers.

### Layer Boundaries

- Touch first: app-owned developer tooling/docs (`de_lekbak/Makefile`, `de_lekbak/docker-compose.yml`, `de_lekbak/README.md`) and only command-level integration with existing backend/frontend tooling.
- Avoid unless evidence emerges: backend API/service/repository/schema code, Alembic migration contents, frontend React/API/hook/component code, and any runtime dependency on `cve-intelligence/`.

### Verification Plan

**Integration Tests**:

- Validate `make setup` from `de_lekbak/` starts Postgres, waits for readiness, installs/synchronizes backend and frontend dependencies, and runs `uv run alembic upgrade head` successfully against the Dockerized database.
- Validate individual Makefile targets work independently for database startup, readiness wait, migrations, backend setup, and frontend setup.

**E2E / Manual Validation**:

- From a clean local state without an existing app database volume, confirm Dockerized Postgres creates database/user/password `de_lekbak` and exposes port `5432`.
- Confirm setup is non-destructive by default and does not reset or drop an existing local database.

**Additional Checks (as applicable)**:

- Confirm the implementation remains scoped to `de_lekbak/` and does not require running or importing from `cve-intelligence/`.

## Implementation handoff (2026-06-22 14:18)

- Added `de_lekbak/docker-compose.yml` with app-owned Postgres 16 configuration using database/user/password `de_lekbak` and host port `5432`.
- Added `de_lekbak/Makefile` with `setup`, `backend-setup`, `frontend-setup`, `db-up`, `db-wait`, and `migrate` targets.
- Documented the setup workflow and non-destructive default behavior in `de_lekbak/README.md`.
- Validation passed: `docker compose config`, `make -n setup`, `make backend-setup`, `uv run ruff check .`, `uv run pytest`, `npm run build`, `npm run lint`, `make setup` from `de_lekbak/`, and `git diff --check`.
- Note: `npm ci` reported existing package audit findings during `make setup` (5 vulnerabilities: 2 low, 2 moderate, 1 high); build and lint still passed.

## Validation update (2026-06-22 14:20)

* Validation passed with no regressions found.
* Gate result: PASS.
* Baseline checks passed or had no unrelated failures observed.
* Touched-scope coverage: no material regression; no coverage command is configured for this tooling/docs-only setup change.
* Security review: completed; local-only default Postgres credentials are documented and scoped to Docker Compose, no destructive default database reset target was introduced, and no runtime import from `cve-intelligence` was found in `de_lekbak` Python code.
* Retained exploratory artifacts: none.
* Validated checklist items: single `make setup` command, Dockerized Postgres startup, default database/user/password, readiness wait before migrations, Alembic upgrade from backend, separate backend/frontend/db/migration targets, README discoverability, backend pytest/ruff, frontend build/lint, non-destructive setup path, and standalone `de_lekbak` boundary.
* Providers covered: local Docker Compose Postgres for `de_lekbak`.
