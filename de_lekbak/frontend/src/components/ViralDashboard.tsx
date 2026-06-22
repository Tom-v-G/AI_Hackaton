import { ApiError } from "@/api/client";
import { EmptyState } from "@/components/common/EmptyState";
import { ErrorState } from "@/components/common/ErrorState";
import { LoadingState } from "@/components/common/LoadingState";
import { useRefreshViralCves, useViralCves } from "@/hooks/useViralCves";
import type { ViralCveItem } from "@/types/viralCve";

function formatTimestamp(value: string | null): string {
  if (!value) return "Not refreshed yet";
  return new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(
    new Date(value),
  );
}

function sourceLabel(sourceType: string): string {
  return sourceType.replace("_", " ");
}

function ViralCveRow({ item, rank }: { item: ViralCveItem; rank: number }) {
  return (
    <article className="rounded-xl border border-surface-border bg-surface-raised p-5 shadow-lg shadow-black/20">
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-accent">Rank #{rank}</p>
          <h2 className="mt-2 text-2xl font-bold text-white">{item.cve_id}</h2>
          <p className="mt-2 text-sm text-slate-400">
            {item.nvd?.description ?? "No NVD enrichment available yet."}
          </p>
        </div>
        <div className="rounded-lg bg-surface px-4 py-3 text-right">
          <p className="text-xs text-slate-400">Virality score</p>
          <p className="text-3xl font-bold text-accent">{item.virality_score}</p>
        </div>
      </div>
      <dl className="mt-5 grid gap-3 text-sm sm:grid-cols-3">
        <div>
          <dt className="text-slate-500">Mentions</dt>
          <dd className="font-semibold text-slate-100">{item.mention_count}</dd>
        </div>
        <div>
          <dt className="text-slate-500">Distinct sources</dt>
          <dd className="font-semibold text-slate-100">{item.distinct_source_count}</dd>
        </div>
        <div>
          <dt className="text-slate-500">First seen</dt>
          <dd className="font-semibold text-slate-100">{formatTimestamp(item.first_seen_at)}</dd>
        </div>
      </dl>
      <div className="mt-4 flex flex-wrap gap-2">
        {item.source_types.map((sourceType) => (
          <span key={sourceType} className="rounded-full bg-sky-400/10 px-3 py-1 text-xs text-sky-200">
            {sourceLabel(sourceType)}
          </span>
        ))}
      </div>
    </article>
  );
}

export function ViralDashboard() {
  const rankings = useViralCves();
  const refresh = useRefreshViralCves();
  const data = rankings.data;

  const errorMessage =
    rankings.error instanceof ApiError || rankings.error instanceof Error
      ? rankings.error.message
      : "Could not load viral CVE rankings.";

  return (
    <main className="mx-auto flex min-h-screen max-w-6xl flex-col gap-8 px-6 py-8">
      <header className="flex flex-col gap-5 rounded-2xl border border-surface-border bg-surface-raised/80 p-6 shadow-2xl shadow-black/30 md:flex-row md:items-center md:justify-between">
        <div>
          <p className="text-sm font-medium uppercase tracking-[0.35em] text-accent">De Lekbak</p>
          <h1 className="mt-3 text-4xl font-black text-white md:text-5xl">Viral CVE Dashboard</h1>
          <p className="mt-3 max-w-2xl text-slate-300">
            Standalone dashboard shell for ranking CVEs mentioned on Reddit, Mastodon, and The
            Hacker News RSS.
          </p>
        </div>
        <button
          type="button"
          onClick={() => refresh.mutate()}
          disabled={refresh.isPending}
          className="rounded-lg bg-accent px-5 py-3 font-semibold text-slate-950 transition hover:bg-sky-300 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {refresh.isPending ? "Refreshing…" : "Manual refresh"}
        </button>
      </header>

      {refresh.isError ? (
        <ErrorState
          title="Refresh failed"
          message={refresh.error instanceof Error ? refresh.error.message : "Unable to refresh rankings."}
        />
      ) : null}

      <section className="grid gap-4 rounded-xl border border-surface-border bg-surface-raised/40 p-5 md:grid-cols-3">
        <div>
          <p className="text-sm text-slate-400">Last refreshed</p>
          <p className="mt-1 font-semibold text-slate-100">
            {formatTimestamp(data?.last_refreshed_at ?? null)}
          </p>
        </div>
        <div>
          <p className="text-sm text-slate-400">Tracked CVEs</p>
          <p className="mt-1 font-semibold text-slate-100">{data?.items.length ?? "—"}</p>
        </div>
        <div>
          <p className="text-sm text-slate-400">Data state</p>
          <p className="mt-1 font-semibold text-slate-100">
            {data?.is_stale ? "Stale / awaiting first refresh" : "Fresh"}
          </p>
        </div>
      </section>

      {rankings.isLoading ? <LoadingState label="Loading viral CVE rankings…" /> : null}
      {rankings.isError ? (
        <ErrorState message={errorMessage} onRetry={() => void rankings.refetch()} />
      ) : null}
      {data && data.items.length === 0 ? (
        <EmptyState
          title="No viral CVEs detected yet"
          description="Use manual refresh after source ingestion is connected. CVEs can still appear here without NVD enrichment."
        />
      ) : null}
      {data && data.items.length > 0 ? (
        <section className="grid gap-4">
          {data.items.map((item, index) => (
            <ViralCveRow key={item.cve_id} item={item} rank={index + 1} />
          ))}
        </section>
      ) : null}
    </main>
  );
}
