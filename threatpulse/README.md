# ThreatPulse — React boilerplate

> Polshoogte van wat er nu speelt in cybersecurityland.
> Toont de 3–5 heetste kwetsbaarheden van het moment: één hero-kaart + een rij compacte kaarten, met een matrix-rain achtergrond.

Dit is de **Matrix-variant (B)** als herbruikbaar, framework-agnostisch React-component. Drop de map in je project en geef hem een lijst kwetsbaarheden.

## Bestanden

| Bestand | Wat |
|---|---|
| `ThreatPulse.jsx` | Het component (+ `MatrixRain`, hero, kaarten). Geen dependencies behalve React. |
| `threatpulse.css` | Alle styling. Thema's via CSS custom properties op `.tp`. |
| `sampleVulns.js` | Voorbeelddata in het juiste formaat. |

## Gebruik

```jsx
import { ThreatPulse } from './threatpulse/ThreatPulse';
import { sampleVulns } from './threatpulse/sampleVulns';
import './threatpulse/threatpulse.css';

export default function Page() {
  return (
    <ThreatPulse
      vulns={sampleVulns}
      updatedLabel="09:14 · 22-06-2026"
    />
  );
}
```

Het component vult de hoogte van zijn container (`min-height: 100%`). Zet het in een element met hoogte (bijv. een route-pagina of `min-height: 100vh`).

## Props

| Prop | Type | Default | Uitleg |
|---|---|---|---|
| `vulns` | `Vuln[]` | `[]` | Lijst kwetsbaarheden. Index/rank 1 = hero, de rest = kaarten. Leeg → vriendelijke empty-state. |
| `title` | `string` | `"THREATPULSE"` | Merknaam in de header. |
| `tagline` | `string` | `"Polshoogte van wat er nu speelt in cybersecurityland"` | |
| `statusLabel` | `string` | `"ONLINE"` | Tekst naast de live-dot. |
| `updatedLabel` | `string` | — | "laatst bijgewerkt"-regel; verborgen als leeg. |
| `matrix` | `boolean` | `true` | Matrix-rain achtergrond aan/uit. |

## Datamodel (`Vuln`)

| Veld | Type | Verplicht | Voorbeeld |
|---|---|---|---|
| `rank` | number | ✓ | `1` |
| `cveId` | string | ✓ | `"CVE-2026-1234"` |
| `name` | string | – | `"CoffeeLeak"` |
| `buzz` | number (0–100) | ✓ | `87` |
| `trend` | `"rising" \| "cooling" \| "stable"` | ✓ | `"rising"` |
| `news` | number | ✓ | `12` |
| `social` | number | ✓ | `2400` |
| `researchers` | number | ✓ | `8` |
| `source` | number | – | `24` |
| `severity` | `"CRITICAL" \| "HIGH" \| "MEDIUM" \| "LOW"` | ✓ | `"CRITICAL"` |
| `flags` | string[] | – | `["KEV","PoC"]` |
| `summary` | string | ✓ | 1–2 zinnen plain language |
| `riskFor` | string | ✓ | "publieke webservers met …" |
| `spark` | number[] (~7) | – | `[18,26,24,39,55,72,87]` |

De balkbreedtes per signaal (news/social/researchers) zijn **relatief t.o.v. het maximum in de lijst**, zodat je in één oogopslag ziet of iets vooral nieuws- of vooral social-gedreven is.

## Theming

Override de CSS-variabelen op `.tp` (of een ouder-element):

```css
.tp {
  --tp-green: #39ff88;   /* accent + glow */
  --tp-bg:    #020604;   /* achtergrond */
  --tp-rising:  #ff7a45; /* trend-kleuren */
  --tp-cooling: #46d3e6;
  --tp-critical:#ff5c5c; /* severity-kleuren */
  --tp-high:    #ffb02e;
}
```

## Goed om te weten

- **Geen build-magie nodig** — het is gewone React + één CSS-bestand. Werkt in Vite/Next/CRA. In Next: `'use client'` bovenaan je pagina, want het component gebruikt `useEffect`/canvas.
- **Toegankelijkheid** — respecteert `prefers-reduced-motion` (matrix-rain wordt dan een statisch frame i.p.v. animatie). Trend is altijd symbool **én** kleur.
- **Performance** — de rain draait op `requestAnimationFrame` (~17 fps, bewust rustig) en stopt netjes bij unmount. Zet `matrix={false}` voor een statische achtergrond.
- **Lettertype** — `threatpulse.css` importeert JetBrains Mono van Google Fonts. Laadt je app die zelf al? Verwijder dan de `@import` bovenaan.

## Nog te doen (bewust buiten scope)

- Loading-skeletons (de empty-state zit er wel in).
- Hover/expand voor extra detail per kaart.
- Data-fetching / buzz-score-berekening — dit component verwacht kant-en-klare data.
