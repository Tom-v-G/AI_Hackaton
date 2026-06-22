import React, { useRef, useEffect } from 'react';

/**
 * @typedef {Object} Vuln
 * @property {number}  rank          1..N — bepaalt volgorde + visuele hiërarchie
 * @property {string}  cveId         bijv. "CVE-2026-1234"
 * @property {string} [name]         bekende/branded naam, bijv. "CoffeeLeak"
 * @property {number}  buzz          composite 0..100 ("hoe heet is dit")
 * @property {'rising'|'cooling'|'stable'} trend
 * @property {number}  news          aantal mainstream nieuws-outlets
 * @property {number}  social        aantal posts/mentions
 * @property {number}  researchers   aantal bekende onderzoekers
 * @property {number} [source]       bronnen totaal (optioneel)
 * @property {'CRITICAL'|'HIGH'|'MEDIUM'|'LOW'} severity
 * @property {string[]} [flags]      bijv. ["KEV","PoC"]
 * @property {string}  summary       1–2 zinnen plain-language uitleg
 * @property {string}  riskFor       wie loopt risico
 * @property {number[]} [spark]      ~7 datapunten mentions laatste 7 dagen
 */

const TREND = {
  rising:  { sym: '▲', label: 'rising',  color: 'var(--tp-rising)' },
  cooling: { sym: '▼', label: 'cooling', color: 'var(--tp-cooling)' },
  stable:  { sym: '→', label: 'stable',  color: 'var(--tp-stable)' },
};

const SEV = {
  CRITICAL: 'var(--tp-critical)',
  HIGH:     'var(--tp-high)',
  MEDIUM:   'var(--tp-medium)',
  LOW:      'var(--tp-medium)',
};

/** 2400 -> "2,4k", 900 -> "900" (NL-notatie met komma) */
function fmtCount(n) {
  return n >= 1000 ? (Math.round(n / 100) / 10).toString().replace('.', ',') + 'k' : String(n);
}

/** Bouwt een SVG polyline-points string uit ~7 datapunten. */
function sparkPoints(spark, w, h) {
  if (!spark || spark.length < 2) return '';
  const mn = Math.min(...spark), mx = Math.max(...spark), pad = 2.5;
  return spark
    .map((val, i) => {
      const x = (i / (spark.length - 1)) * w;
      const t = mx === mn ? 0.5 : (val - mn) / (mx - mn);
      const y = (h - pad) - t * (h - 2 * pad);
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(' ');
}

/** Maxima per signaal over de hele lijst — voor relatieve balkbreedtes. */
function getMaxes(vulns) {
  return {
    news: Math.max(1, ...vulns.map(v => v.news || 0)),
    social: Math.max(1, ...vulns.map(v => v.social || 0)),
    researchers: Math.max(1, ...vulns.map(v => v.researchers || 0)),
  };
}

function prefersReducedMotion() {
  return typeof window !== 'undefined'
    && window.matchMedia
    && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

/* ---------- Matrix-rain achtergrond (canvas) ---------- */
function MatrixRain({ color = 'rgba(45,210,110,0.5)', highlight = '#d6ffe5' }) {
  const ref = useRef(null);
  useEffect(() => {
    const canvas = ref.current;
    const parent = canvas && canvas.parentElement;
    if (!canvas || !parent) return;
    const ctx = canvas.getContext('2d');
    const fs = 14;
    const glyphs = 'アカサタナハマヤラワ0123456789ABCDEF<>=/\\$#*+｜:'.split('');
    let cols = 0, drops = [];

    const fit = () => {
      canvas.width = parent.offsetWidth;
      canvas.height = parent.offsetHeight;
      cols = Math.floor(canvas.width / fs) || 1;
      drops = Array(cols).fill(0).map(() => Math.random() * -60);
    };
    fit();

    if (prefersReducedMotion()) {
      // statisch, rustig frame i.p.v. animatie
      ctx.font = `${fs}px monospace`;
      ctx.fillStyle = color;
      for (let i = 0; i < cols; i++) {
        for (let j = 0; j < canvas.height / fs; j += 3) {
          if (Math.random() < 0.15) ctx.fillText(glyphs[(Math.random() * glyphs.length) | 0], i * fs, j * fs);
        }
      }
      return;
    }

    let raf, last = 0;
    const step = (t) => {
      raf = requestAnimationFrame(step);
      if (t - last < 58) return;
      last = t;
      ctx.fillStyle = 'rgba(2,6,4,0.16)';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.font = `${fs}px monospace`;
      for (let i = 0; i < cols; i++) {
        const ch = glyphs[(Math.random() * glyphs.length) | 0];
        const x = i * fs, y = drops[i] * fs;
        ctx.fillStyle = Math.random() < 0.035 ? highlight : color;
        ctx.fillText(ch, x, y);
        if (y > canvas.height && Math.random() > 0.975) drops[i] = 0;
        drops[i]++;
      }
    };
    raf = requestAnimationFrame(step);

    const ro = new ResizeObserver(fit);
    ro.observe(parent);
    return () => { cancelAnimationFrame(raf); ro.disconnect(); };
  }, [color, highlight]);

  return <canvas ref={ref} className="tp__matrix" aria-hidden="true" />;
}

/* ---------- kleine bouwstenen ---------- */
function Sparkline({ spark, color, w = 160, h = 30 }) {
  const pts = sparkPoints(spark, w, h);
  if (!pts) return null;
  return (
    <svg className="tp-spark" viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none" aria-hidden="true">
      <polyline points={pts} fill="none" stroke={color} strokeWidth="2.4" strokeLinejoin="round" strokeLinecap="round" />
    </svg>
  );
}

function Metric({ label, value, unit, pct }) {
  return (
    <div>
      <div className="tp-metric__label">{label}</div>
      <div className="tp-metric__value">{value}</div>
      {unit && <div className="tp-metric__unit">{unit}</div>}
      <div className="tp-bar"><div className="tp-bar__fill" style={{ width: `${pct}%` }} /></div>
    </div>
  );
}

/* ---------- hero ---------- */
function VulnHero({ v, maxes }) {
  const trend = TREND[v.trend] || TREND.stable;
  return (
    <article className="tp-hero">
      <div className="tp-hero__top">
        <span className="tp-tag">#{v.rank} · HOTTEST</span>
        <span className="tp-trend" style={{ color: trend.color }}>{trend.sym} {trend.label}</span>
        <span className="tp-hero__cve">{v.cveId}</span>
      </div>

      <h2 className="tp-hero__name">{v.name || v.cveId}</h2>
      <p className="tp-hero__meta">
        <b style={{ color: SEV[v.severity] }}>{v.severity}</b>
        {v.flags && v.flags.length ? ` · ${v.flags.join(', ')}` : ''}
      </p>

      <p className="tp-hero__summary">{v.summary}</p>
      <p className="tp-hero__risk">risico voor — {v.riskFor}</p>

      <div className="tp-metrics">
        <Metric label="NEWS" value={v.news} unit="outlets" pct={Math.round(v.news / maxes.news * 100)} />
        <Metric label="SOCIAL" value={fmtCount(v.social)} unit="mentions" pct={Math.round(v.social / maxes.social * 100)} />
        <Metric label="RESEARCHERS" value={v.researchers} unit="namen" pct={Math.round(v.researchers / maxes.researchers * 100)} />
        <div className="tp-metric tp-metric--buzz">
          <div className="tp-metric__label">BUZZ</div>
          <div className="tp-metric__row">
            <span className="tp-metric__value">{v.buzz}</span>
            <span className="tp-metric__unit">/100</span>
          </div>
          <Sparkline spark={v.spark} color="var(--tp-green)" />
        </div>
      </div>
    </article>
  );
}

/* ---------- compacte kaart ---------- */
function VulnCard({ v }) {
  const trend = TREND[v.trend] || TREND.stable;
  return (
    <article className="tp-card">
      <div className="tp-card__top">
        <span className="tp-card__rank">#{v.rank}</span>
        <span style={{ color: trend.color }} title={trend.label}>{trend.sym}</span>
      </div>
      <div className="tp-card__cve">{v.cveId}</div>
      <div className="tp-card__name">{v.name || v.cveId}</div>
      <p className="tp-card__summary">{v.summary}</p>
      <div className="tp-card__footer">
        <span className="tp-card__signals">📰{v.news} 💬{fmtCount(v.social)} 🎓{v.researchers}</span>
        <span className="tp-card__buzz">buzz <b>{v.buzz}</b></span>
      </div>
    </article>
  );
}

/**
 * ThreatPulse — "polshoogte van wat er nu speelt in cybersecurityland".
 * Toont de heetste kwetsbaarheid als hero + de rest als kaarten.
 *
 * @param {Object}  props
 * @param {Vuln[]}  props.vulns          gesorteerd op rank/buzz (index 0 = hero)
 * @param {string} [props.title]         merknaam in de header
 * @param {string} [props.tagline]
 * @param {string} [props.statusLabel]   bijv. "ONLINE"
 * @param {string} [props.updatedLabel]  bijv. "09:14 · 22-06-2026"
 * @param {boolean}[props.matrix]        matrix-rain achtergrond aan/uit (default true)
 */
export function ThreatPulse({
  vulns = [],
  title = 'THREATPULSE',
  tagline = 'Polshoogte van wat er nu speelt in cybersecurityland',
  statusLabel = 'ONLINE',
  updatedLabel,
  matrix = true,
}) {
  const sorted = [...vulns].sort((a, b) => (a.rank ?? 99) - (b.rank ?? 99));
  const [hero, ...rest] = sorted;
  const maxes = getMaxes(sorted.length ? sorted : [{ news: 1, social: 1, researchers: 1 }]);

  return (
    <section className="tp">
      {matrix && <MatrixRain />}
      <div className="tp__vignette" />
      <div className="tp__inner">
        <header className="tp__header">
          <div>
            <h1 className="tp__brand">{title}</h1>
            <p className="tp__tagline">// {tagline}</p>
          </div>
          <div className="tp__status">
            <div className="tp__live"><span className="tp__live-dot" />{statusLabel}</div>
            {updatedLabel && <div>{updatedLabel}</div>}
          </div>
        </header>

        {hero ? (
          <>
            <VulnHero v={hero} maxes={maxes} />
            {rest.length > 0 && (
              <div className="tp-cards">
                {rest.map((v) => <VulnCard key={v.cveId} v={v} />)}
              </div>
            )}
          </>
        ) : (
          <div className="tp-empty">
            <div className="tp-empty__title">Rustig in cybersecurityland ☕</div>
            <div className="tp-empty__sub">Geen noemenswaardige kwetsbaarheden om je druk om te maken. Kom straks terug.</div>
          </div>
        )}
      </div>
    </section>
  );
}

export default ThreatPulse;
