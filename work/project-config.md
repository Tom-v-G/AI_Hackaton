# Project Config

This file is the canonical, human-readable source of truth for repo structure, guideline loading, review triggers, and repo-level command rules.

If another repo document conflicts with this file, follow this file.

## Purpose

- Use this file as rule, not background reading.
- Humans read it to understand expected agent behavior.
- Agents read it to decide which guidelines, reviews, and commands apply.

## Repo Structure

This repo contains the existing `cve-intelligence` application, the planned viral CVE dashboard app under `de_lekbak/`, and workflow artifacts under `work/`.

- `cve-intelligence/` - Existing CVE intelligence application. Contains the reusable FastAPI backend, NVD ingestion, PostgreSQL/SQLAlchemy models, and existing React/Vite dashboard.
- `cve-intelligence/app/` - Backend application code.
- `cve-intelligence/app/api/` - FastAPI routers and dependency wiring.
- `cve-intelligence/app/services/` - Backend business logic, including dashboard, CVE query, NVD ingestion, scoring, and presentation services.
- `cve-intelligence/app/repositories/` - Backend data-access layer.
- `cve-intelligence/app/models/` - SQLAlchemy ORM models for CVEs, metrics, references, and ingestion runs.
- `cve-intelligence/app/schemas/` - Pydantic API contracts.
- `cve-intelligence/app/clients/` - External HTTP clients and shared HTTP client lifecycle.
- `cve-intelligence/frontend/` - Existing React/Vite dashboard for NVD-backed CVE intelligence.
- `cve-intelligence/tests/` - Existing backend tests.
- `de_lekbak/` - Planned separate Vite app for the viral CVE dashboard. It should consume viral CVE endpoints from the reused `cve-intelligence` backend.
- `work/backlog/` - Durable story state. New scoped implementation work should be recorded here before delivery.
- `work/ideas/` - Exploratory idea capture.
- `work/adr/` - Architecture decision records.

## Output Rules

- Prefer concise, repo-grounded responses.
- Clearly separate verified repository facts from proposals or assumptions.
- Cite relevant file paths when making claims about existing code.
- Treat files in `work/` as the durable source of truth for workflow decisions and story state.

## Domain Rules

### Existing NVD CVE Intelligence

- Purpose: ingest, store, enrich, search, and display NVD-backed CVE data.
- Backend patterns: `cve-intelligence/app/api/`, `cve-intelligence/app/services/`, `cve-intelligence/app/repositories/`, `cve-intelligence/app/models/`, `cve-intelligence/app/schemas/`.
- Frontend patterns: `cve-intelligence/frontend/src/api/`, `cve-intelligence/frontend/src/hooks/`, `cve-intelligence/frontend/src/components/`, `cve-intelligence/frontend/src/pages/`.
- Keywords: CVE, NVD, CVSS, dashboard, ingestion, enrichment, severity, vendor, product.

### Viral CVE Dashboard

- Purpose: rank currently popular CVEs based on public source mentions.
- Initial sources: Reddit, Mastodon, and The Hacker News RSS.
- The Hacker News RSS is the selected news source for the first version because it is structured, accessible, cybersecurity-focused, and includes explicit CVE IDs in feed content.
- The viral dashboard must be a separate Vite app located in `de_lekbak/`, while reusing current backend infrastructure as much as possible.
- NVD data should enrich viral CVEs when available, but viral rankings must function without local NVD matches.
- Manual refresh is acceptable for the first hackathon version; background scheduling is deferred.
- Virality score inputs are mention count, distinct source count, and source type. Exact source-type weights are intentionally deferred.
- Keywords: viral, virality, social, Reddit, Mastodon, The Hacker News, RSS, mention count, source count, source type, manual refresh.

## Technology Rules

- Backend:
  - Python with `uv`.
  - FastAPI async application.
  - SQLAlchemy 2.0 async ORM.
  - PostgreSQL via `asyncpg`.
  - Alembic for migrations.
  - Pydantic and pydantic-settings for schemas/configuration.
  - `httpx` for async external HTTP requests.
  - Ruff for linting.
  - Existing shared HTTP client lifecycle is in `cve-intelligence/app/clients/http.py`.
  - Existing rate limiter utility is in `cve-intelligence/app/services/ingestion/rate_limiter.py`.
- Frontend:
  - React 19.
  - Vite.
  - TypeScript.
  - TanStack Query.
  - Tailwind CSS.
- Existing API style:
  - Backend routes should follow the existing router/service/repository/schema layering.
  - Frontend API calls should follow the existing client/hook/component pattern where practical.

## Review Rules

- For backend changes, review consistency with the existing FastAPI dependency, service, repository, schema, and async database-session patterns.
- For frontend changes, review consistency with the existing Vite/React/Tailwind/TanStack Query component and data-fetching patterns.
- For source ingestion changes, review external-source reliability, rate limiting, graceful failure, and whether the dashboard still works with partial source availability.
- For viral scoring changes, review whether score factors remain explainable in the UI and whether source-type weights are isolated/configurable.
- For NVD enrichment changes, review that NVD data remains optional and missing enrichment does not block viral ranking display.

## Loading Rules

### Always Load

- `AGENTS.md`
- `work/project-config.md`

### Analysis

- Start with `work/project-config.md`.
- For story shaping, inspect existing source files only enough to ground current behavior and identify reusable patterns.
- Prefer targeted lookups over broad scans.
- Treat backlog stories as the source of truth for scoped work.

### Implementation

- Before implementation, identify affected domain(s): existing NVD CVE intelligence, viral CVE dashboard, backend API, frontend dashboard, ingestion/source fetching, or scoring.
- Follow existing backend layering when adding backend behavior.
- Follow existing frontend API/hook/component conventions when adding frontend behavior.
- Keep NVD enrichment optional for viral dashboard work.
- Keep virality scoring weights easy to revise because exact weighting is not yet finalized.

### Validation

- Validate backend behavior with the relevant existing test patterns under `cve-intelligence/tests/` when backend code is affected.
- Validate frontend behavior with the applicable Vite/TypeScript build or lint commands when frontend code is affected.
- For viral dashboard work, validate that rankings still display when NVD enrichment is absent.
- For source fetching work, validate partial failure handling for unavailable sources.

## Command Rules

- No repo-level validation command is currently mandatory for all changes.
- Existing backend test configuration is defined in `cve-intelligence/pyproject.toml` with `pytest` test paths under `tests`.
- Existing frontend scripts are defined in `cve-intelligence/frontend/package.json`:
  - `npm run build`
  - `npm run lint`
  - `npm run dev`
- Use targeted validation appropriate to affected files and scope.

## Agent Usage Rule

- Read this file first when you need repo structure, guideline loading rules, review triggers, or repo-level command rules.
- Load only the guideline files that match the current task.
- Do not invent rules outside this file, `AGENTS.md`, and the loaded guideline files.
