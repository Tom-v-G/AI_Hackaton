# Handover — Slidedeck "ThreatPulse"

> **Voor:** de designer-agent die de slidedeck bouwt.
> **Van:** engineering, na de hackathon-dag (2026-06-22).
> **Doel van dit document:** je genoeg concept-, inhoud- én visuele richting geven om een
> overtuigende hackathon-presentatie te maken die past bij het product. Lees dit volledig
> voordat je begint; alle feiten hieronder zijn geverifieerd tegen de codebase.

---

## 1. Het project in één zin

**ThreatPulse** is een *viral CVE radar*: een dashboard dat laat zien welke beveiligingslekken
(CVE's) op dít moment heet zijn in de cybersecurity-community — gemeten aan de buzz op publieke
bronnen, niet alleen aan hun formele ernstscore.

> **Naam:** het product heet **ThreatPulse** (met een **T** — "Threat"). "De Lekbak" was de
> werktitel en is vervallen; gebruik die naam *niet* meer in de deck. (In de codebase heet de
> map nog `de_lekbak/` — dat is alleen een interne folder, geen productnaam.)

**Subtitel/tagline:** **"De hype-hartslag van CVE's"** (definitief — gebruik deze op de titel-slide en in de footer).

---

## 2. Elevator pitch (gebruik dit als rode draad van de deck)

Er worden elke dag tientallen tot honderden CVE's gepubliceerd. Securityteams verzuipen erin.
De gangbare tools sorteren op **CVSS-severity** — maar "kritiek" zegt niets over wat er
*nu echt toe doet*. Een CVE met een exploit die viraal gaat op Reddit/Bluesky is vaak urgenter
dan een formeel "critical" lek waar niemand het over heeft.

**Inzicht:** sociale buzz is een vroeg signaal. Waar de community over praat, daar zit beweging
(PoC's, actief misbruik, paniek).

**Oplossing:** ThreatPulse verzamelt CVE-vermeldingen over publieke discussiebronnen, berekent
een **virality/buzz-score**, verrijkt elk lek met officiële NVD-data (severity, omschrijving,
getroffen leveranciers/producten), en toont de heetste paar in een Matrix-achtig dashboard:
één grote hero-kaart + compacte kaarten, met buzz, trend (rising/cooling/stable) en een
plain-language "risico voor — …".

**De kicker:** alles in één hackathon-dag gebouwd, end-to-end, met een AI-agent-gedreven
workflow.

---

## 2a. Subtitel / tagline

**Definitief: "De hype-hartslag van CVE's"** — gebruik deze consistent op de titel-slide en
in de footer. Sluit aan op de naam (*Pulse* = hartslag).

Verworpen alternatieven (alleen ter context, niet gebruiken):
Niet de ernstigste — de heetste CVE's · Realtime hype-radar voor kwetsbaarheden ·
De polsslag van het dreigingslandschap.

Sterke **pitch-regel** voor slide 2 (los van de subtitel):
*"Severity vertelt je wat erg is. ThreatPulse vertelt je wat heet is."*

> Zodra de subtitel gekozen is, gebruik die consistent op de titel-slide en in de footer.

---

## 3. Het concept in detail (probleem → inzicht → oplossing)

**Probleem**
- Volume: NVD publiceert continu nieuwe CVE's. Triage is een hooiberg.
- Severity ≠ urgentie: CVSS is statisch en zegt niet of iets *nu* speelt of misbruikt wordt.
- Signaal zit verspreid: het echte "is dit heet?"-signaal leeft op Reddit, Bluesky, Mastodon,
  securitynieuws — niet in één dashboard.

**Inzicht**
- Cross-source buzz = vroege waarschuwing. Hoe meer onafhankelijke bronnen + hoe meer
  vermeldingen, hoe waarschijnlijker dat een CVE er nu toe doet.

**Oplossing — ThreatPulse**
- Aggregeer CVE-vermeldingen per CVE over meerdere publieke bronnen.
- Scoor de "viraliteit" (zie §5).
- Verrijk met NVD (officiële severity/omschrijving/impact) wanneer beschikbaar — maar
  rankings werken óók zonder NVD-match.
- Presenteer de top als een snel leesbaar "radar"-dashboard met buzz, trend en
  mensentaal-samenvatting.

---

## 4. Hoe het werkt (architectuur — voor de "how it works"-slide)

```
Publieke bronnen        Ingestion            Opslag            API                Dashboard
┌───────────────┐   ┌──────────────┐   ┌────────────┐   ┌──────────────┐   ┌─────────────────┐
│ Reddit        │──▶│ scrapers +    │──▶│ PostgreSQL │──▶│ FastAPI       │──▶│ React + Vite     │
│ Bluesky       │   │ CVE-extractie │   │ (mentions, │   │ /viral-cves   │   │ "ThreatPulse"    │
│ (NVD verrijkt)│   │ + scoring     │   │  NVD)      │   │ + scoring     │   │ matrix-dashboard │
└───────────────┘   └──────────────┘   └────────────┘   └──────────────┘   └─────────────────┘
```

- Per CVE worden vermeldingen uit **Reddit** + **Bluesky** samengevoegd, gescoord, en met
  NVD-data verrijkt; daarna gesorteerd op viraliteit en als ranking teruggegeven.
- Manual refresh-knop herbouwt de ranking uit de laatste brondata (geen scheduler nodig voor
  de demo).

---

## 5. De virality/buzz-score (1 slide waard — het "slimme" deel)

- Inputs (bewust simpel en uitlegbaar gehouden): **mention count**, **distinct source count**,
  en **source type** (elk brontype heeft een gewicht).
- Bluesky weegt ook **engagement** mee: `likes + replies×1.5 + reposts×2 + quotes×2`.
- Ontwerpprincipe: de score moet **uitlegbaar** blijven in de UI (geen black box) en de
  bron-gewichten zijn configureerbaar.
- In de UI wordt `virality_score` getoond als **buzz (0–100)**, plus een **trend**-indicator
  (rising ▲ / cooling ▼ / stable →) en per-bron signalen (news / social / researchers).

> Eerlijk kader voor de deck: de exacte gewichten zijn bewust nog niet "af" — dat is een
> feature, geen bug. Het is een hackathon-MVP met een helder, uitbreidbaar scoremodel.

---

## 6. Wat er écht gebouwd is (scope & status — wees eerlijk in de deck)

**Werkt end-to-end:**
- FastAPI-backend (async) met `/api/v1/viral-cves` ranking-endpoint, op Postgres aangesloten.
- Datamodel + migraties (Alembic) voor `reddit_cves`, `bluesky_mentions`, en NVD-tabellen
  (`cves`, `cve_metrics`, `cve_references`).
- Reddit CVE-scraper en Bluesky-ingestie (publieke Bluesky API) met CVE-extractie.
- Virality-scoring service + NVD-verrijking (optioneel, degradeert netjes).
- React/Vite "ThreatPulse" dashboard met hero + kaarten, manual refresh, en
  loading/error/empty/stale states.

**Demo draait op mock/seed-data:** 3 trending CVE's, elk in zowel Reddit als Bluesky:
| CVE | Onderwerp | NVD-severity |
|---|---|---|
| CVE-2026-20253 | Splunk Enterprise pre-auth RCE | CRITICAL |
| CVE-2026-20245 | Cisco SD-WAN privilege escalation | HIGH |
| CVE-2026-50656 | Microsoft-lek (RoguePlanet) | HIGH |

**Vizie / niet-af (roadmap-slide):** extra bronnen (Mastodon, The Hacker News RSS stonden in
het oorspronkelijke concept), automatische/scheduled ingestion, en verfijning van de
score-gewichten. Live bron-fetching i.p.v. seed-data.

---

## 7. Tech stack (1 slide / footer-strip)

- **Backend:** Python, FastAPI (async), SQLAlchemy 2.0, Pydantic, Alembic, PostgreSQL, `uv`.
- **Frontend:** React 19, Vite, TypeScript, Tailwind CSS, TanStack Query.
- **Bronnen:** Reddit, Bluesky (ATProto public API), NVD-verrijking.
- **Werkwijze (meta, sterk verhaal voor een hackathon):** AI-agent-gedreven, artifact-based
  workflow — backlog-stories, ADR's en agent-definities in `work/` als "source of truth".
  Het hele product is in één dag met agents geleverd.

---

## 8. Publiek & doel van de deck

- **Context:** hackathon-eindpresentatie (kort, energiek, demo-gedreven).
- **Publiek:** mede-deelnemers, jury/organisatie, technisch onderlegd maar niet per se security-experts.
- **Doel:** in ~5–8 slides het probleem laten voelen, het inzicht verkopen, het product laten
  zien (screenshots/live demo), en de "in één dag gebouwd met AI-agents"-twist landen.

---

## 9. Voorgestelde slide-structuur (skelet — pas gerust aan)

1. **Titel** — woordmerk **THREATPULSE** + de gekozen subtitel (§2a).
   Matrix-rain achtergrond. Woordmerk in neon-groen met glow.
2. **Het probleem** — honderden CVE's/dag; severity ≠ urgentie; signaal zit verspreid.
   (Visueel: overweldigende lijst vs. één highlight.)
3. **Het inzicht** — buzz op de community is een vroeg signaal. Eén sterke zin + bron-iconen
   (Reddit, Bluesky).
4. **De oplossing** — wat ThreatPulse doet, in 3 stappen: verzamel → scoor → toon.
   (Visueel: de architectuur-flow uit §4, gestileerd.)
5. **Het dashboard** — productscreenshot(s): hero-kaart + compacte kaarten. Laat buzz/trend zien.
   (Assets: §11. Overweeg een live demo hier i.p.v. statisch.)
6. **De buzz-score** — uitlegbaar scoremodel (mention count × bronnen × bron-gewicht +
   engagement). Benadruk "geen black box".
7. **Hoe gebouwd** — tech stack + de AI-agent/artifact-workflow twist (in één dag, end-to-end).
8. **Roadmap / outro** — meer bronnen, live ingestion, scherpere scoring. Afsluiter + tagline.

> Korter mag: titel → probleem+inzicht → oplossing → demo → "in één dag met agents" → outro.

---

## 10. Visuele richting — MOET matchen met het product ("Matrix / tech")

De deck moet dezelfde identiteit ademen als het dashboard. Dit is de geverifieerde
design-taal uit `threatpulse/threatpulse.css` en de live frontend:

**Kleuren (donker, neon-groen "Matrix"):**
- Achtergrond: bijna-zwart met groene zweem — `#020604` (en panelen `#04120a` / `#07120c`).
- Accent / neon-groen: **`#39ff88`** (hoofdaccent), helder highlight `#d6ffe5` / `#eaffef`.
- Dimmer groen voor secundaire tekst: `#7fc69a` / `#43c476`.
- Severity-/trend-kleuren: critical `#ff5c5c`, high `#ffb02e`, rising `#ff7a45`,
  cooling `#46d3e6` (cyaan), stable/medium `#7fae93`.

**Typografie:**
- **JetBrains Mono** overal (monospace = "tech/terminal"-gevoel). Zware gewichten (800/black)
  voor koppen, met een zachte groene **glow** (`text-shadow` rond het accent).

**Vorm & sfeer:**
- **Scherpe hoeken** (3–6px), géén ronde "soft UI". Strakke, terminal-achtige panelen met
  dunne groene randen en subtiele glow/box-shadow.
- **Matrix-rain**: vallende katakana/hex-glyphs op de achtergrond (groen, met af en toe een
  felle highlight). Subtiel houden achter een vignette zodat tekst leesbaar blijft.
- Algemene vibe: cyberpunk / "security operations center bij nacht". Strak, niet kinderachtig.

**Do / don't:**
- ✅ Donkere slides, neon-groen accent, mono-font, scherpe randen, matrix-motief als rode draad.
- ✅ Veel contrast, weinig tekst per slide, grote cijfers (buzz-scores) als blikvanger.
- ❌ Geen lichte/witte slides, geen ronde bubbels, geen corporate-blauw, geen stockfoto's van
  hangslotjes.

---

## 11. Beschikbare assets

- **Productscreenshots** (echte UI, ThreatPulse-redesign):
  `artifacts/e2e/threadpulse-frontend-redesign-2026-06-22/`
  - `initial-hero-compact-no-nvd.png` — hero + compacte kaarten (hoofdbeeld voor de demo-slide).
  - `manual-refresh-updates-rankings.png` — refresh-flow.
  - `empty-state.png` — lege staat ("Rustig in cybersecurityland").
  - `error-retry-state.png` — foutstaat.
- **Design-referentie / tokens:** `threatpulse/threatpulse.css` (kleuren, glow, radii) en
  `threatpulse/README.md`.
- **Live dashboard:** draait lokaal op de Vite dev-server (de_lekbak/frontend) met de backend
  op poort 8000 — bruikbaar voor verse screenshots of een live demo. Vraag engineering om hem
  op te starten als je nieuwe beelden nodig hebt.
- **Concept/feiten:** dit document + `work/project-config.md` + de backlog-stories in
  `work/backlog/in-progress/` (viral-cve-dashboard, bluesky-datasource, reddit-scraper,
  threadpulse-frontend-redesign).

---

## 12. Belangrijkste boodschappen om te landen (als je niks anders onthoudt)

1. **Severity vertelt je niet wat nu telt — buzz wel.** Dat is de hele pitch.
2. **Cross-source viral-signaal**, uitlegbaar gescoord, verrijkt met officiële NVD-data.
3. **Eén Matrix-achtig "radar"-scherm**: de heetste CVE's in één oogopslag.
4. **In één hackathon-dag end-to-end gebouwd, met een AI-agent-workflow.**

Houd de deck strak, donker en groen — net als het product.
