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
