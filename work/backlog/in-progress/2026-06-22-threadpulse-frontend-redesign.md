# ThreadPulse Frontend Redesign

## Type

feature

## Context

De Lekbak heeft al een React/Vite frontend voor het viral CVE dashboard en een FastAPI backend met basis-endpoints voor viral CVE rankings. Er staat daarnaast een los ThreadPulse-design in `threatpulse/ThreatPulse.jsx` en `threatpulse/threatpulse.css` dat als visuele richting voor de hackathon-frontend moet dienen.

Voor de hackathon moet de frontend simpel blijven: geen SSR, geen backend-contractuitbreiding als vereiste, en geen extra infrastructuurwerk. De bestaande backend response blijft leidend. Velden die het ThreadPulse-design nodig heeft maar die nog niet uit de backend komen, mogen tijdelijk in de frontend worden aangevuld via mock/derived view-data.

## Functional Requirements

- Vervang het huidige dashboardgevoel door het ThreadPulse-design: matrix-achtige achtergrond, cyberpunk/groene styling, hero-kaart voor de hoogste ranking en compacte kaarten voor de overige CVEs.
- Toon viral CVE rankings op basis van de bestaande backend response.
- Behoud manual refresh-functionaliteit voor de gebruiker.
- Behoud gebruikersvriendelijke loading-, error- en empty-states.
- Render rankings ook wanneer NVD enrichment ontbreekt.
- Toon voor elke CVE minimaal de CVE-id, rank, virality/buzz-score, mention/social-signaal, broninformatie en een korte samenvatting wanneer beschikbaar.
- Gebruik frontend mock/derived data voor ThreadPulse-velden die nog niet door de backend worden geleverd.

## Technical Requirements

- Behoud de bestaande Vite SPA-aanpak; SSR wordt bewust geskipt voor de hackathon.
- Behoud de bestaande frontend flow: API client → hook → component.
- Gebruik de bestaande backend endpoints als primaire data source:
  - `GET /api/v1/viral-cves`
  - `POST /api/v1/viral-cves/refresh`
- Introduceer of gebruik een frontend-only ThreadPulse view model dat los staat van het backend DTO-contract.
- Voeg een adapterlaag toe die backend `ViralCveItem` omzet naar ThreadPulse view-data.
- Gebruik deze mapping als basis:
  - `cve_id` → `cveId`
  - ranking index → `rank`
  - `virality_score` → `buzz`
  - `mention_count` → `social`
  - `distinct_source_count` en `source_types` → bron/signaalinformatie
  - `nvd.severity` → `severity` wanneer beschikbaar
  - `nvd.description` → `summary` wanneer beschikbaar
- Vul ontbrekende ThreadPulse-velden in de frontend tijdelijk aan met mock/derived data, zoals:
  - `trend`
  - `news`
  - `researchers`
  - `flags`
  - `riskFor`
  - `spark`
  - optionele display `name`
- Maak de mock-aanvulling duidelijk frontend-only en vervangbaar zodra backendvelden beschikbaar komen.
- Geen backend-wijzigingen zijn vereist voor deze story.
- Geen migratie naar SSR-framework of server-rendering-entrypoint in deze story.
- Volg bestaande React/Vite/Tailwind/TanStack Query conventies binnen `de_lekbak/frontend/src/`.

## Acceptance Criteria

- De De Lekbak frontend gebruikt het ThreadPulse-design als primaire dashboard UI.
- De applicatie blijft een Vite SPA zonder SSR.
- Rankings worden geladen via de bestaande frontend API/hook-flow.
- Backend response is leidend; ontbrekende ThreadPulse-displayvelden worden in de frontend aangevuld.
- Manual refresh werkt nog en update de getoonde rankings.
- Loading-, error- en empty-states zijn zichtbaar en passen visueel bij de nieuwe frontend.
- CVEs zonder NVD enrichment worden zonder crash getoond met passende fallbacktekst.
- De adapter/mock-aanvulling is geïsoleerd genoeg om later door echte backendvelden vervangen te worden.
- De frontend vereist geen runtime dependency op `cve-intelligence/`.

## Analysis

### Likely Impact

- Primary implementation lane: `de_lekbak/frontend/src/api/viralCves.ts` existing endpoints -> `de_lekbak/frontend/src/hooks/useViralCves.ts` query/mutation flow -> `de_lekbak/frontend/src/components/ViralDashboard.tsx` ThreadPulse-style view model + UI.
- `de_lekbak/frontend/src/components/ViralDashboard.tsx` - current dashboard already owns rendering, manual refresh, loading/error/empty states, rank calculation, and NVD fallbacks; this is the main replacement point for hero/card layout and ThreadPulse presentation.
- `de_lekbak/frontend/src/types/viralCve.ts` - backend DTO types are already isolated here; likely add a frontend-only ThreadPulse view type here or in a nearby adapter file rather than changing backend DTO shape.
- Inference: add a small adapter module under `de_lekbak/frontend/src/` (for example `types`/`components` adjacent) to map `ViralCveItem` to ThreadPulse view-data and keep mock/derived fields replaceable.

### Possible Adjacent Touchpoints

- `de_lekbak/frontend/src/index.css` - global body/root styling is minimal today; may need ThreadPulse theme/base background/font treatment if Tailwind classes alone are not enough.
- `de_lekbak/frontend/src/components/common/LoadingState.tsx`, `ErrorState.tsx`, `EmptyState.tsx` - current dashboard imports these for state handling; either restyle via wrapper/classes in `ViralDashboard.tsx` or lightly adjust only if reusable state components clash with the cyberpunk UI.
- `de_lekbak/frontend/src/App.tsx` - currently only renders `ViralDashboard`; should not need more than import/name churn unless the dashboard is split into new components.

### Existing Patterns / Prior Art

- `de_lekbak/frontend/src/api/viralCves.ts` + `de_lekbak/frontend/src/hooks/useViralCves.ts` - existing API client -> TanStack Query hook flow for `GET /viral-cves` and `POST /viral-cves/refresh`; preserve this rather than introducing new data-fetching paths.
- `de_lekbak/frontend/src/components/ViralDashboard.tsx` - existing manual refresh mutation writes returned rankings back into the `viral-cves` query cache and already renders without NVD enrichment using fallback text.
- `threatpulse/ThreatPulse.jsx` and `threatpulse/threatpulse.css` - closest visual prior art: matrix canvas background, hero for rank #1, compact cards for the rest, trend/severity/buzz/signal display, and reduced-motion handling.
- `threatpulse/sampleVulns.js` - concrete shape for frontend-only ThreadPulse fields (`trend`, `news`, `researchers`, `flags`, `riskFor`, `spark`, optional `name`) that can guide derived/mock defaults.

### Layer Boundaries

- Touch first: frontend dashboard component(s), frontend-only adapter/view model, and possibly local CSS/Tailwind styling under `de_lekbak/frontend/src/`.
- Avoid unless evidence emerges: `de_lekbak/backend/` endpoints/schemas/services, new SSR/server entrypoints, runtime imports from `cve-intelligence/`, and broad API contract changes.

### Verification Plan

Repo-configured command checks are handled by implementation/validation via `work/project-config.md`.

**Unit Tests**:

- Adapter/view-model mapping covers backend items with and without `nvd`, preserves rank/buzz/social/source fields, and supplies deterministic frontend-only defaults.

**E2E / Manual Validation**:

- In the Vite app, confirm initial load, empty, error/retry, no-NVD fallback, rank #1 hero, compact lower-ranked cards, and manual refresh updating displayed rankings.

**Additional Checks (as applicable)**:

- Confirm no runtime dependency/import from `cve-intelligence/` and no SSR framework/server-rendering entrypoint was introduced.

## Implementation feedback (2026-06-22 13:22)

* Gate result: FAIL.
* Adapter/view-model unit tests required by the verification plan are missing; no `de_lekbak/frontend/src/**/*.{test,spec}.{ts,tsx}` files cover mapping with/without `nvd`, rank/buzz/social/source preservation, or deterministic frontend-only defaults.
* Story-required browser/manual proof is missing for the Vite UI flows: initial load, empty state, error/retry, no-NVD fallback rendering, rank #1 hero, compact lower-ranked cards, and manual refresh updating displayed rankings.
* Automated checks that were run passed: `npm run build` and `npm run lint` from `de_lekbak/frontend/`.
* Code inspection found the API client → hook → component flow preserved, no backend/codegen impact, no SSR entrypoint signals, and no `cve-intelligence/` runtime import signal in `de_lekbak/frontend/src/`.

## Implementation update (2026-06-22 13:35)

- Addressed: added adapter/view-model unit tests for with-NVD mapping, no-NVD deterministic fallbacks, rank/buzz/social/source preservation, and clamped display values.
- Addressed: generated UI proof artifacts for initial load, rank #1 hero, compact lower-ranked cards, no-NVD fallback, manual refresh update, empty state, and error/retry at `artifacts/e2e/threadpulse-frontend-redesign-2026-06-22/proof.md`.
- Not addressed: none.
- Status: done

## Validation update (2026-06-22 13:34)

* Validation passed with no regressions found.
* Gate result: PASS.
* Baseline checks passed: `npm run test`, `npm run lint`, and `npm run build` from `de_lekbak/frontend/`.
* Touched-scope coverage: no material regression; adapter/view-model mapping is covered by `de_lekbak/frontend/src/adapters/threadPulse.test.ts` for with-NVD, no-NVD fallback, rank/order, buzz/social/source preservation, deterministic mock defaults, and clamped display values.
* Security review: completed; frontend-only display adapter and React rendering introduce no auth/token/secret/file/redirect/external-call risk, preserve API client → hook → component flow, and no `cve-intelligence/` or SSR runtime import signals were found in `de_lekbak/frontend/src/`.
* Retained exploratory artifacts: `artifacts/e2e/threadpulse-frontend-redesign-2026-06-22/proof.md`, `initial-hero-compact-no-nvd.png`, `manual-refresh-updates-rankings.png`, `empty-state.png`, `error-retry-state.png`.
* Validated checklist items: ThreadPulse primary UI; Vite SPA/no SSR; existing backend API/hook flow; frontend-only adapter/mock data; manual refresh proof; loading/error/empty UI proof; no-NVD fallback proof; isolated adapter tests; no `cve-intelligence/` runtime dependency.
* Providers covered: default Vite frontend with mocked `/api/v1/viral-cves` responses for UI proof.
