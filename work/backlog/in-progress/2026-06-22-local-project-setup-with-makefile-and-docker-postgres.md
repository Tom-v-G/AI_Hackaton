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
