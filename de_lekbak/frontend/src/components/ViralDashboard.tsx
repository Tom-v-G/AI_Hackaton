import { ApiError } from "@/api/client";
import { toThreadPulseVulnerabilities } from "@/adapters/threadPulse";
import { MatrixRain } from "@/components/MatrixRain";
import { EmptyState } from "@/components/common/EmptyState";
import { ErrorState } from "@/components/common/ErrorState";
import { LoadingState } from "@/components/common/LoadingState";
import { useRefreshViralCves, useViralCves } from "@/hooks/useViralCves";
import type { ThreadPulseTrend, ThreadPulseVulnerability } from "@/types/viralCve";

const TREND_STYLE: Record<ThreadPulseTrend, { symbol: string; label: string; className: string }> = {
  rising: { symbol: "▲", label: "rising", className: "text-emerald-300" },
  stable: { symbol: "→", label: "stable", className: "text-cyan-300" },
  cooling: { symbol: "▼", label: "cooling", className: "text-amber-300" },
};

const SEVERITY_STYLE: Record<ThreadPulseVulnerability["severity"], string> = {
  CRITICAL: "text-red-300",
  HIGH: "text-orange-300",
  MEDIUM: "text-yellow-200",
  LOW: "text-emerald-200",
  UNKNOWN: "text-slate-300",
};

function formatTimestamp(value: string | null): string {
  if (!value) return "Not refreshed yet";
  return new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(
    new Date(value),
  );
}

function formatCount(value: number): string {
  return value >= 1000 ? `${(Math.round(value / 100) / 10).toString().replace(".", ",")}k` : String(value);
}

function maxMetrics(vulnerabilities: ThreadPulseVulnerability[]) {
  return {
    news: Math.max(1, ...vulnerabilities.map((item) => item.news)),
    social: Math.max(1, ...vulnerabilities.map((item) => item.social)),
    researchers: Math.max(1, ...vulnerabilities.map((item) => item.researchers)),
  };
}

function sparkPoints(spark: number[]): string {
  const width = 160;
  const height = 34;
  const min = Math.min(...spark);
  const max = Math.max(...spark);
  const padding = 3;

  return spark
    .map((value, index) => {
      const x = (index / (spark.length - 1)) * width;
      const scaled = max === min ? 0.5 : (value - min) / (max - min);
      const y = height - padding - scaled * (height - padding * 2);
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
}

function MatrixBackground() {
  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden="true">
      <MatrixRain />
      <div className="absolute inset-0 bg-[radial-gradient(120%_90%_at_50%_0%,rgba(2,6,4,0.05),rgba(2,6,4,0.62)_80%)]" />
    </div>
  );
}

function Metric({ label, value, unit, percent }: { label: string; value: string; unit: string; percent: number }) {
  return (
    <div className="rounded-xl border border-emerald-400/15 bg-black/30 p-4">
      <p className="text-[0.65rem] font-semibold uppercase tracking-[0.3em] text-emerald-200/60">{label}</p>
      <div className="mt-2 flex items-end gap-2">
        <span className="font-mono text-2xl font-black text-emerald-100">{value}</span>
        <span className="pb-1 text-xs uppercase tracking-widest text-slate-500">{unit}</span>
      </div>
      <div className="mt-3 h-1.5 rounded-sm bg-emerald-950/80">
        <div className="h-full rounded-sm bg-emerald-300 shadow-[0_0_16px_rgba(57,255,136,0.85)]" style={{ width: `${percent}%` }} />
      </div>
    </div>
  );
}

function Sparkline({ spark }: { spark: number[] }) {
  return (
    <svg className="h-10 w-full" viewBox="0 0 160 34" preserveAspectRatio="none" aria-hidden="true">
      <polyline
        points={sparkPoints(spark)}
        fill="none"
        stroke="rgb(57 255 136)"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="2.4"
      />
    </svg>
  );
}

function VulnerabilityHero({ item, maxes }: { item: ThreadPulseVulnerability; maxes: ReturnType<typeof maxMetrics> }) {
  const trend = TREND_STYLE[item.trend];

  return (
    <article className="relative overflow-hidden rounded-lg border border-emerald-300/25 bg-[#07120c]/90 p-6 shadow-[0_0_55px_rgba(45,210,110,0.18)] md:p-8">
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-emerald-200 to-transparent" />
      <div className="flex flex-wrap items-center gap-3 text-xs font-bold uppercase tracking-[0.28em]">
        <span className="rounded border border-emerald-300/40 bg-emerald-300/10 px-3 py-1 text-emerald-100">#{item.rank} · hottest</span>
        <span className={trend.className}>{trend.symbol} {trend.label}</span>
        <span className="font-mono text-emerald-200/70">{item.cveId}</span>
      </div>

      <div className="mt-6 grid gap-8 lg:grid-cols-[1.15fr_0.85fr] lg:items-end">
        <div>
          <h2 className="font-mono text-4xl font-black tracking-tight text-emerald-50 [text-shadow:0_0_22px_rgba(57,255,136,0.5)] md:text-6xl">{item.name ?? item.cveId}</h2>
          <p className="mt-3 text-sm uppercase tracking-[0.28em] text-slate-400">
            <span className={SEVERITY_STYLE[item.severity]}>{item.severity}</span>
            {item.flags.length > 0 ? ` · ${item.flags.join(" · ")}` : ""}
          </p>
          <p className="mt-5 max-w-3xl text-lg leading-8 text-slate-200">{item.summary}</p>
          <p className="mt-4 text-sm text-emerald-100/80">risk for — {item.riskFor}</p>
          <p className="mt-3 text-xs uppercase tracking-[0.24em] text-slate-500">sources — {item.sourceLabel}</p>
        </div>

        <div className="rounded-2xl border border-emerald-300/20 bg-black/35 p-5">
          <div className="flex items-end justify-between gap-4">
            <div>
              <p className="text-xs uppercase tracking-[0.32em] text-emerald-200/60">buzz</p>
              <p className="font-mono text-6xl font-black text-emerald-200">{item.buzz}</p>
            </div>
            <span className="pb-3 text-sm text-slate-500">/100</span>
          </div>
          <Sparkline spark={item.spark} />
        </div>
      </div>

      <div className="mt-8 grid gap-3 md:grid-cols-3">
        <Metric label="news" value={String(item.news)} unit="outlets" percent={Math.round((item.news / maxes.news) * 100)} />
        <Metric label="social" value={formatCount(item.social)} unit="mentions" percent={Math.round((item.social / maxes.social) * 100)} />
        <Metric label="researchers" value={String(item.researchers)} unit="names" percent={Math.round((item.researchers / maxes.researchers) * 100)} />
      </div>
    </article>
  );
}

function VulnerabilityCard({ item }: { item: ThreadPulseVulnerability }) {
  const trend = TREND_STYLE[item.trend];

  return (
    <article className="rounded-2xl border border-emerald-300/15 bg-[#07120c]/80 p-5 shadow-[0_0_30px_rgba(45,210,110,0.08)] transition hover:-translate-y-0.5 hover:border-emerald-200/40">
      <div className="flex items-center justify-between gap-3">
        <span className="font-mono text-2xl font-black text-emerald-200">#{item.rank}</span>
        <span className={trend.className} title={trend.label}>{trend.symbol}</span>
      </div>
      <p className="mt-4 font-mono text-lg font-bold text-emerald-50">{item.cveId}</p>
      <p className="mt-1 text-sm uppercase tracking-[0.22em] text-slate-500">{item.name}</p>
      <p className="mt-4 line-clamp-3 min-h-20 text-sm leading-6 text-slate-300">{item.summary}</p>
      <div className="mt-5 flex items-center justify-between gap-3 border-t border-emerald-300/10 pt-4 text-xs text-slate-400">
        <span>📰 {item.news} · 💬 {formatCount(item.social)} · 🎓 {item.researchers}</span>
        <span className="font-mono text-emerald-200">buzz <b>{item.buzz}</b></span>
      </div>
      <p className="mt-3 text-[0.65rem] uppercase tracking-[0.2em] text-slate-600">{item.sourceLabel}</p>
    </article>
  );
}

export function ViralDashboard() {
  const rankings = useViralCves();
  const refresh = useRefreshViralCves();
  const data = rankings.data;
  const vulnerabilities = data ? toThreadPulseVulnerabilities(data.items) : [];
  const [hero, ...rest] = vulnerabilities;
  const metrics = maxMetrics(vulnerabilities);

  const errorMessage =
    rankings.error instanceof ApiError || rankings.error instanceof Error
      ? rankings.error.message
      : "Could not load viral CVE rankings.";

  return (
    <main className="relative min-h-screen overflow-hidden bg-[#020604] px-5 py-6 text-slate-100 md:px-8">
      <MatrixBackground />
      <div className="relative z-10 mx-auto flex max-w-7xl flex-col gap-6">
        <header className="flex flex-col gap-5 rounded-3xl border border-emerald-300/20 bg-black/45 p-5 shadow-[0_0_40px_rgba(45,210,110,0.1)] backdrop-blur md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="font-mono text-4xl font-black tracking-[0.12em] text-emerald-100 [text-shadow:0_0_22px_rgba(57,255,136,0.55)] md:text-6xl">THREADPULSE</h1>
            <p className="mt-2 text-sm uppercase tracking-[0.25em] text-emerald-200/60">// De Lekbak viral CVE radar</p>
          </div>
          <div className="flex flex-col gap-3 md:items-end">
            <div className="flex flex-wrap gap-3 text-xs uppercase tracking-[0.22em] text-slate-400">
              <span className="rounded border border-emerald-300/25 bg-emerald-300/10 px-3 py-1 text-emerald-100">● online</span>
              <span>{formatTimestamp(data?.last_refreshed_at ?? null)}</span>
            </div>
            <button
              type="button"
              onClick={() => refresh.mutate()}
              disabled={refresh.isPending}
              className="rounded border border-emerald-200/50 bg-emerald-300 px-5 py-3 text-sm font-black uppercase tracking-[0.18em] text-[#020604] shadow-[0_0_24px_rgba(57,255,136,0.35)] transition hover:bg-emerald-100 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {refresh.isPending ? "Refreshing…" : "Manual refresh"}
            </button>
          </div>
        </header>

        {refresh.isError ? (
          <ErrorState title="Refresh failed" message={refresh.error instanceof Error ? refresh.error.message : "Unable to refresh rankings."} />
        ) : null}

        <section className="grid gap-3 rounded-2xl border border-emerald-300/15 bg-black/35 p-4 backdrop-blur md:grid-cols-3">
          <Metric label="tracked cves" value={String(data?.items.length ?? "—")} unit="items" percent={100} />
          <Metric
            label="data state"
            value={data ? (data.is_stale ? "stale" : "fresh") : "—"}
            unit="cache"
            percent={data?.is_stale ? 45 : 100}
          />
          <Metric label="source mode" value="api" unit="backend" percent={100} />
        </section>

        {rankings.isLoading ? <LoadingState label="Loading viral CVE rankings…" /> : null}
        {rankings.isError ? <ErrorState message={errorMessage} onRetry={() => void rankings.refetch()} /> : null}
        {data && data.items.length === 0 ? (
          <EmptyState
            title="Rustig in cybersecurityland"
            description="No viral CVEs detected yet. Manual refresh keeps using the backend rankings endpoint when sources are ready."
          />
        ) : null}

        {hero ? (
          <>
            <VulnerabilityHero item={hero} maxes={metrics} />
            {rest.length > 0 ? (
              <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                {rest.map((item) => <VulnerabilityCard key={item.cveId} item={item} />)}
              </section>
            ) : null}
          </>
        ) : null}
      </div>
    </main>
  );
}
