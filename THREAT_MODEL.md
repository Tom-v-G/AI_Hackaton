# Threat Model: AI_Hackaton CVE Intelligence Workspace

## 1. System context

This checkout contains a hackathon workspace for CVE trend intelligence. The active product is `de_lekbak/`, a standalone FastAPI backend and Vite/React frontend that ranks CVEs gaining attention on public sources such as Reddit and Bluesky, stores social-source mentions in PostgreSQL, and exposes JSON APIs for dashboard views. The repository also retains `cve-intelligence/`, a fuller FastAPI/PostgreSQL/React NVD ingestion and CVE browsing platform used as prior art, plus `threatpulse/` React component code and `.opencode/` local automation definitions.

The code is mostly Python 3.11+ with FastAPI, SQLAlchemy async, httpx, Alembic, PostgreSQL, and React 19/Vite/TanStack Query. It is designed for local development and hackathon demo use, with local Docker Compose databases and browser-facing dev servers. No authentication, authorization, tenant separation, or production deployment hardening is visible in the source reviewed.

## 2. Assets

| asset | description | sensitivity |
|---|---|---|
| CVE trend integrity | Ranking, score, mention count, enrichment, and prioritization data presented to users | high |
| Ingested external content | Reddit posts, Bluesky posts, NVD records, raw NVD JSON, author handles, URLs, and references stored or displayed | medium |
| PostgreSQL data stores | `de_lekbak` and `cve_intelligence` databases, including raw vulnerability records and social mention tables | high |
| Backend service availability | FastAPI processes, background ingestion, DB connection pools, outbound HTTP quota, and local demo responsiveness | high |
| Operator/developer environment | Local machine, `.env` files, API keys such as `NVD_API_KEY`, OpenCode state, browser/session artifacts, and local Docker services | critical |
| Source and dependency integrity | Python/npm lockfiles, package manifests, migrations, `.opencode` agents/skills/commands, zip/html artifacts, and build/install instructions | high |
| Public API consumers | Browsers and tools consuming `/api/v1` JSON responses | medium |

## 3. Entry points & trust boundaries

| entry_point | description | trust_boundary | reachable_assets |
|---|---|---|---|
| De Lekbak FastAPI API | Unauthenticated `/api/v1/health`, `/api/v1/viral-cves`, `/api/v1/viral-cves/refresh`, `/api/v1/reddit/trending`, and `/api/v1/bluesky/*` routes | unauthenticated network -> application logic | CVE trend integrity, Ingested external content, PostgreSQL data stores, Backend service availability, Public API consumers |
| Reddit scraping refresh | `/api/v1/reddit/trending` accepts optional subreddit query values, calls `https://www.reddit.com/r/{subreddit}/new.json`, parses JSON, extracts CVEs, and upserts rows | unauthenticated network -> outbound public web -> parser -> database | CVE trend integrity, Ingested external content, PostgreSQL data stores, Backend service availability |
| Bluesky ingestion and analytics | `BlueskySearchProvider` fetches `https://api.bsky.app/xrpc/app.bsky.feed.searchPosts`; analytics routes expose persisted posts, handles, text, engagement, and NVD enrichment | public social platform -> parser/database -> unauthenticated API consumers | CVE trend integrity, Ingested external content, PostgreSQL data stores, Public API consumers |
| CVE Intelligence API | Retained prior-art FastAPI app exposes unauthenticated CVE query routes and `/api/v1/ingestion/nvd/delta` background ingestion from NVD | unauthenticated network -> background job -> NVD API/database | Ingested external content, PostgreSQL data stores, Backend service availability, Public API consumers |
| Browser frontend configuration | Vite/React clients use `VITE_API_BASE_URL` or dev proxy `/api` and render API-provided content in browser components | public API JSON -> browser UI | Public API consumers, CVE trend integrity, Ingested external content |
| Local PostgreSQL containers | Docker Compose exposes Postgres 16 on host port `5432` with documented default usernames and passwords | local/adjacent network -> database listener | PostgreSQL data stores, Operator/developer environment |
| Local automation and agent definitions | `.opencode/agent`, `.opencode/commands`, `.opencode/skills`, scripts, and instructions can influence developer-agent behavior and local command execution | repository content -> AI/tooling control plane -> developer environment | Operator/developer environment, Source and dependency integrity |
| Dependency and artifact intake | `pyproject.toml`, `uv.lock`, `package-lock.json`, `pnpm-lock.yaml`, `.venv` directories, `design-boilerplate.zip`, and checked-in HTML/files are consumed by developers and tooling | supply chain/artifact files -> install/build/dev tooling | Source and dependency integrity, Operator/developer environment, Backend service availability |

## 4. Threats

| id | threat | actor | surface | asset | impact | likelihood | status | controls | evidence |
|---|---|---|---|---|---|---|---|---|---|
| T1 | Secrets added by developers to `.env`, browser automation state, or local config can be committed or exposed through local workflow artifacts. | insider | Local automation and agent definitions, Dependency and artifact intake | Operator/developer environment, Source and dependency integrity | critical | rare | partially_mitigated | `.env.example` only contains placeholders; `.gitignore` files exist; no secret scanner or pre-commit policy found | |
| T2 | An unauthenticated user can trigger refresh or ingestion workflows to consume backend workers, database connections, outbound HTTP quota, or third-party API allowance. | remote_unauth | De Lekbak FastAPI API, Reddit scraping refresh, CVE Intelligence API | Backend service availability, PostgreSQL data stores | high | likely | unmitigated | Query limits exist on some read endpoints; Reddit fetch timeout is 10 seconds; NVD client has rate limiting; no auth or per-client rate limit found | |
| T3 | A public-source actor can manipulate social posts or NVD-like content to distort CVE rankings and drive false prioritization decisions. | remote_unauth | Reddit scraping refresh, Bluesky ingestion and analytics, CVE Intelligence API | CVE trend integrity, Ingested external content | high | likely | partially_mitigated | Strict CVE regex normalization; duplicate Reddit URL suppression; some engagement scoring is deterministic; no source reputation, abuse filtering, or provenance scoring found | |
| T4 | A local or adjacent-network actor can access development PostgreSQL databases through exposed port `5432` and well-known default credentials. | adjacent_network | Local PostgreSQL containers | PostgreSQL data stores, Operator/developer environment | high | possible | unmitigated | Docker Compose uses named volumes; credentials are documented defaults; no network binding restriction or secret override requirement found | |
| T5 | A supply-chain actor can compromise the developer environment or application behavior through package installs, retained virtualenvs, zipped artifacts, or workflow automation files. | supply_chain | Dependency and artifact intake, Local automation and agent definitions | Operator/developer environment, Source and dependency integrity | high | possible | partially_mitigated | Lockfiles exist for npm/uv; `.gitignore` files exist; no signature verification, dependency audit policy, or artifact quarantine policy found | |
| T6 | A repository contributor can alter `.opencode` agents, skills, or commands to steer AI tooling into unsafe file edits, command execution, or credential exposure. | insider | Local automation and agent definitions | Operator/developer environment, Source and dependency integrity | high | possible | partially_mitigated | `AGENTS.md` and `work/project-config.md` define workflow rules; no mandatory review or permission boundary for agent/control-plane changes found | |
| T7 | An attacker can exfiltrate or overexpose raw vulnerability records, social post text, author handles, and reference URLs through unauthenticated analytics and CVE detail APIs. | remote_unauth | De Lekbak FastAPI API, Bluesky ingestion and analytics, CVE Intelligence API | Ingested external content, Public API consumers | medium | possible | unmitigated | Data appears public-source oriented; `include_raw` defaults false in one CVE detail route; no access control or field-level disclosure policy found | |
| T8 | Untrusted external content rendered by the frontend can mislead users or become script/content-injection risk if future rendering switches from React escaping to raw HTML/markdown. | remote_unauth | Browser frontend configuration, Bluesky ingestion and analytics, CVE Intelligence API | Public API consumers, Ingested external content | medium | possible | partially_mitigated | Current React rendering escapes strings by default; no `dangerouslySetInnerHTML` found in active frontend search; no explicit sanitization policy found | |
| T9 | User-controlled query parameters can drive expensive database scans or large result processing even when values are type-validated. | remote_unauth | De Lekbak FastAPI API, CVE Intelligence API | Backend service availability, PostgreSQL data stores | medium | possible | partially_mitigated | FastAPI/Pydantic validation constrains limits on several endpoints; SQLAlchemy binding is used for most queries; no global rate limit, query timeout, or pagination cap on all analytics endpoints found | |
| T10 | A hostile or compromised public source can cause ingestion correctness failures through malformed, duplicated, deleted, or rapidly changing posts and payloads. | remote_unauth | Reddit scraping refresh, Bluesky ingestion and analytics | CVE trend integrity, Backend service availability | medium | possible | partially_mitigated | Reddit parser skips malformed children and failures; Bluesky provider validates basic post shapes; no cross-source reconciliation, retry isolation, or dead-letter visibility found | |
| T11 | Retained prior-art code can be accidentally run as a production service despite being outside the active product boundary, exposing broader unauthenticated NVD ingestion and raw data APIs. | local_admin | CVE Intelligence API, Dependency and artifact intake | Backend service availability, PostgreSQL data stores, Source and dependency integrity | medium | possible | partially_mitigated | `work/project-config.md` marks `cve-intelligence/` as prior art only; runnable README and Docker config remain present | |
| T12 | Public endpoints can perform actions without attributable audit records, making abuse of refresh, ingestion, and analytics hard to investigate. | remote_unauth | De Lekbak FastAPI API, Reddit scraping refresh, CVE Intelligence API | Backend service availability, CVE trend integrity | medium | possible | unmitigated | Some application logging exists in `cve-intelligence`; no request identity, audit log, or abuse correlation strategy found | |
| T13 | A malicious API base URL or dev proxy configuration can redirect browser clients to an unintended backend and leak usage patterns or serve forged data. | local_user | Browser frontend configuration | Public API consumers, CVE trend integrity | medium | rare | partially_mitigated | `VITE_API_BASE_URL` is build-time configuration and dev proxy defaults to localhost; no runtime origin pinning or environment validation found | |

## 5. Deprioritized

| threat | reason |
|---|---|
| Direct SQL injection in reviewed repository queries | Most dynamic values observed are SQLAlchemy-bound or constrained; the one raw SQL path only interpolates a fixed boolean-derived clause and binds `limit`. This should be revisited if free-form SQL clauses are added. |
| Arbitrary host SSRF through Reddit refresh | The reviewed scraper constructs requests against a fixed Reddit base URL rather than accepting arbitrary URLs. Path/query abuse remains a lower availability/integrity concern, not broad SSRF. |
| Credential theft from production user accounts | No user account system or production authentication flow is visible in the active product. |
| Server-side template injection | The active APIs return JSON and React renders on the client; no server-side templating surface was found. |
| File upload parser compromise | No runtime file-upload endpoint was found. Checked-in zip/html artifacts are covered under supply-chain/artifact intake instead. |

## 6. Open questions

- Is `de_lekbak/` intended to remain localhost-only, or will any API be exposed to a LAN, tunnel, demo server, or public internet?
- Should `/viral-cves/refresh`, `/reddit/trending`, and `cve-intelligence` ingestion endpoints require authentication or an operator token?
- What is the acceptable abuse budget for Reddit, Bluesky, and NVD calls, and are there provider terms or API quotas that need enforcement?
- Should social post text, handles, and raw NVD JSON be considered public enough for unauthenticated redistribution?
- Will the retained `cve-intelligence/` app be deployed anywhere, or should it be marked non-runnable/archived to reduce accidental exposure?
- Are `.opencode` agents and skills trusted code requiring code-owner review before use?
- Should local Docker databases bind only to localhost and require developer-specific credentials outside the repo defaults?
- Are checked-in `.venv` directories, `design-boilerplate.zip`, and saved HTML intentional repository assets or accidental artifacts?
- Is there a desired audit trail for manual refresh and ingestion operations?
- Are dependency vulnerability scans, secret scans, or lockfile update policies required before demo or deployment?

## 7. Provenance

- mode: bootstrap
- date: 2026-06-22
- target: /home/defaultuser/Documents/hackathon/code-hackathon/AI_Hackaton @ df4e503eefafef781a8b31036e98a57292ab652b
- inputs: git-log + docs mined
- owner: unset

## 8. Recommended mitigations

| mitigation | threat_ids | closes_class | effort |
|---|---|---|---|
| Require an operator token or local-only guard for refresh and ingestion endpoints, and reject unsafe deployment when unset. | T2, T7, T11, T12 | partial | S |
| Add per-client and per-endpoint rate limits plus cooldowns for external fetch and background ingestion actions. | T2, T9, T12 | partial | M |
| Bind development databases to localhost and require non-default credentials via environment overrides before shared demos. | T4 | partial | S |
| Add source reputation, deduplication, and provenance signals to ranking calculations so social manipulation is visible and dampened. | T3, T10 | partial | M |
| Keep external content rendered as text-only and add a sanitization policy/test for any future HTML, markdown, or rich-link rendering. | T8 | yes | S |
| Add secret scanning, dependency auditing, and artifact quarantine rules for lockfiles, `.venv`, zip/html files, and `.opencode` control-plane changes. | T1, T5, T6 | partial | M |
| Make `cve-intelligence/` explicitly non-deployable or move it outside the active product tree if it remains prior art only. | T11 | partial | S |
| Add structured audit logs for refresh/ingestion calls including caller address, parameters, result counts, duration, and external failures. | T2, T12 | partial | M |
