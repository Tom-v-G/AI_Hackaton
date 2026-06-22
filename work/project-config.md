# Project Config

This file is the canonical, human-readable source of truth for repo structure, guideline loading, review triggers, and repo-level command rules.

If another repo document conflicts with this file, follow this file.

## Purpose

- Use this file as rule, not background reading.
- Humans read it to understand expected agent behavior.
- Agents read it to decide which guidelines, reviews, and commands apply.
- Treat `de_lekbak/` as the primary product in this repository.
- Treat `cve-intelligence/` as first inspiration and prior art only, not as a runtime dependency for `de_lekbak/`.

## Repo Structure

This repo is centered on `de_lekbak/`, a standalone viral CVE dashboard with its own backend and frontend. The older `cve-intelligence/` project may be consulted for implementation ideas, but `de_lekbak/` must not import from, depend on, run against, or require `cve-intelligence/` at runtime.

```text
de_lekbak/
├── README.md
├── backend/
│   ├── README.md
│   ├── pyproject.toml
│   ├── uv.lock
│   ├── de_lekbak_backend/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       ├── health.py
│   │   │       ├── router.py
│   │   │       └── viral_cves.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   └── config.py
│   │   ├── repositories/
│   │   │   ├── __init__.py
│   │   │   └── viral_cve_repository.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   └── viral_cve.py
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── scoring.py
│   │       └── viral_cve_service.py
│   └── tests/
│       ├── conftest.py
│       └── test_app.py
└── frontend/
    ├── package.json
    ├── package-lock.json
    ├── index.html
    ├── vite.config.ts
    ├── tsconfig.json
    ├── tsconfig.app.json
    ├── tsconfig.node.json
    ├── tailwind.config.js
    ├── postcss.config.js
    ├── eslint.config.js
    └── src/
        ├── App.tsx
        ├── main.tsx
        ├── index.css
        ├── vite-env.d.ts
        ├── api/
        │   ├── client.ts
        │   └── viralCves.ts
        ├── components/
        │   ├── ViralDashboard.tsx
        │   └── common/
        │       ├── EmptyState.tsx
        │       ├── ErrorState.tsx
        │       └── LoadingState.tsx
        ├── hooks/
        │   └── useViralCves.ts
        └── types/
            └── viralCve.ts
```

- `de_lekbak/` - Primary standalone viral CVE dashboard product.
- `de_lekbak/backend/` - Independent FastAPI backend for viral CVE rankings, refresh actions, scoring, schemas, repositories, and tests.
- `de_lekbak/frontend/` - Independent Vite/React dashboard for viral CVE rankings.
- `cve-intelligence/` - Prior application and first inspiration only; useful for patterns, not runtime integration.
- `work/backlog/` - Durable story state. New scoped implementation work should be recorded here before delivery.
- `work/ideas/` - Exploratory idea capture.
- `work/adr/` - Architecture decision records.
- `artifacts/` - Validation artifacts such as browser screenshots, logs, traces, and videos.

## Output Rules

- Prefer concise, repo-grounded responses.
- Clearly separate verified repository facts from proposals or assumptions.
- Cite relevant file paths when making claims about existing code.
- Treat files in `work/` as the durable source of truth for workflow decisions and story state.
- Do not describe `cve-intelligence/` as an active backend, shared package, or required service for `de_lekbak/`.

## Domain Rules

### De Lekbak Viral CVE Dashboard

- Purpose: rank currently popular CVEs based on public source mentions.
- Primary app: `de_lekbak/`.
- Initial sources: Reddit, Mastodon, and The Hacker News RSS.
- The Hacker News RSS is the selected news source for the first version because it is structured, accessible, cybersecurity-focused, and includes explicit CVE IDs in feed content.
- `de_lekbak/` must remain a standalone app with its own backend and frontend.
- `de_lekbak/` may copy or reimplement useful ideas from `cve-intelligence/`, but copied code becomes owned by `de_lekbak/`.
- `de_lekbak/` must not import from, depend on, run against, or require `cve-intelligence/` at runtime.
- NVD data should enrich viral CVEs when available within `de_lekbak`'s own backend/data model, but viral rankings must function without local NVD matches.
- Manual refresh is acceptable for the first hackathon version; background scheduling is deferred.
- Virality score inputs are mention count, distinct source count, and source type. Exact source-type weights are intentionally deferred.
- Keywords: `de_lekbak`, viral, virality, social, Reddit, Mastodon, The Hacker News, RSS, mention count, source count, source type, manual refresh, standalone.

### Prior Art: CVE Intelligence

- Purpose in this repo: first inspiration and reference implementation only.
- Consult only when useful for implementation patterns such as FastAPI app setup, router/service/repository/schema layering, HTTP client lifecycle, rate limiting, NVD enrichment concepts, React/Vite dashboard structure, API clients, hooks, loading/error/empty states, Tailwind styling, and TanStack Query usage.
- Do not add direct imports from `cve-intelligence/` into `de_lekbak/`.
- Do not require the `cve-intelligence` backend or frontend to be running for `de_lekbak/` validation or demo flows.
- Do not extend `cve-intelligence` endpoints as the primary delivery path for viral CVE dashboard work.
- Keywords: prior art, inspiration, reference, copy, reimplement, no runtime dependency.

## Technology Rules

- Backend:
  - Python with `uv`.
  - FastAPI async application.
  - Pydantic and pydantic-settings for schemas/configuration.
  - `httpx` for async external HTTP requests when source fetching is added.
  - Ruff for linting.
  - Follow router → service → repository/schema layering within `de_lekbak/backend/de_lekbak_backend/`.
  - Keep source-type weighting isolated/configurable in a scoring service.
  - Keep NVD enrichment optional and owned inside `de_lekbak/` if implemented.
- Frontend:
  - React 19.
  - Vite.
  - TypeScript.
  - TanStack Query.
  - Tailwind CSS.
  - Follow API client → hook → component flow within `de_lekbak/frontend/src/`.

## Review Rules

- For backend changes, review consistency with `de_lekbak` FastAPI routing, service, repository, schema, settings, and test patterns.
- For frontend changes, review consistency with `de_lekbak` Vite/React/Tailwind/TanStack Query component and data-fetching patterns.
- For source ingestion changes, review external-source reliability, rate limiting, graceful failure, and whether the dashboard still works with partial source availability.
- For viral scoring changes, review whether score factors remain explainable in the UI and whether source-type weights are isolated/configurable.
- For NVD enrichment changes, review that NVD data remains optional and missing enrichment does not block viral ranking display.
- For dependency changes, review that `de_lekbak/` remains independent from `cve-intelligence/`.

## Loading Rules

### Always Load

- `AGENTS.md`
- `work/project-config.md`

### Analysis

- Start with `work/project-config.md`.
- Treat backlog stories as the source of truth for scoped work.
- For story shaping, inspect existing `de_lekbak/` source files enough to ground current behavior and identify reusable local patterns.
- Consult `cve-intelligence/` only when the story explicitly asks for prior-art comparison or when a local `de_lekbak/` pattern does not yet exist.
- Prefer targeted lookups over broad scans.

### Implementation

- Before implementation, identify affected `de_lekbak` domain(s): backend API, frontend dashboard, ingestion/source fetching, scoring, enrichment, tests, or docs.
- Implement first inside `de_lekbak/` unless the story explicitly concerns workflow artifacts or docs.
- Follow existing `de_lekbak` backend layering when adding backend behavior.
- Follow existing `de_lekbak` frontend API/hook/component conventions when adding frontend behavior.
- Keep NVD enrichment optional for viral dashboard work.
- Keep virality scoring weights easy to revise because exact weighting is not yet finalized.
- Preserve the no-runtime-dependency boundary from `cve-intelligence/`.

### Validation

- Validate backend behavior with commands from `de_lekbak/backend/pyproject.toml`.
- Validate frontend behavior with scripts from `de_lekbak/frontend/package.json`.
- For viral dashboard work, validate that rankings still display when NVD enrichment is absent.
- For source fetching work, validate partial failure handling for unavailable sources.
- For dependency-boundary changes, validate that `de_lekbak/` does not import from or require running `cve-intelligence/`.

## Command Rules

- No repo-level validation command is currently mandatory for all changes.
- Backend commands are run from `de_lekbak/backend/`:
  - `uv run pytest`
  - `uv run ruff check .`
  - `uv run uvicorn de_lekbak_backend.main:app --reload`
- Frontend scripts are run from `de_lekbak/frontend/`:
  - `npm run build`
  - `npm run lint`
  - `npm run dev`
- Use targeted validation appropriate to affected files and scope.

## Agent Usage Rule

- Read this file first when you need repo structure, guideline loading rules, review triggers, or repo-level command rules.
- Load only the guideline files that match the current task.
- Do not invent rules outside this file, `AGENTS.md`, and the loaded guideline files.
