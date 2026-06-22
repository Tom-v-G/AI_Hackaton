import type {
  SourceType,
  ThreadPulseSeverity,
  ThreadPulseTrend,
  ThreadPulseVulnerability,
  ViralCveItem,
} from "@/types/viralCve";

const SOURCE_LABELS: Record<SourceType, string> = {
  reddit: "Reddit",
  mastodon: "Mastodon",
  hacker_news: "The Hacker News",
};

const SEVERITIES: ThreadPulseSeverity[] = ["CRITICAL", "HIGH", "MEDIUM", "LOW"];

// Frontend-only ThreadPulse display enrichment. These derived fields are intentionally
// isolated here so backend-provided equivalents can replace them without changing the UI.

function clampBuzz(score: number): number {
  return Math.max(0, Math.min(100, Math.round(score)));
}

function normalizeSeverity(value: string | null | undefined): ThreadPulseSeverity {
  const severity = value?.toUpperCase();
  return SEVERITIES.includes(severity as ThreadPulseSeverity)
    ? (severity as ThreadPulseSeverity)
    : "UNKNOWN";
}

function deriveTrend(item: ViralCveItem): ThreadPulseTrend {
  if (item.virality_score >= 70 || item.mention_count >= 25) return "rising";
  if (item.virality_score < 30 && item.mention_count < 5) return "cooling";
  return "stable";
}

function deriveNewsCount(item: ViralCveItem): number {
  const newsMentions = item.representative_links.filter(
    (link) => link.source_type === "hacker_news",
  ).length;
  return item.source_types.includes("hacker_news") ? Math.max(1, newsMentions) : 0;
}

function deriveResearchers(item: ViralCveItem): number {
  return Math.max(1, Math.min(12, item.distinct_source_count + Math.floor(item.mention_count / 8)));
}

function deriveFlags(item: ViralCveItem, severity: ThreadPulseSeverity): string[] {
  const flags: string[] = [];
  if (severity === "CRITICAL" || severity === "HIGH") flags.push("watch");
  if (item.source_types.length > 1) flags.push("cross-source");
  if (!item.nvd) flags.push("no-nvd-yet");
  return flags;
}

function deriveRiskFor(item: ViralCveItem): string {
  const products = item.nvd?.affected_products.filter(Boolean) ?? [];
  const vendors = item.nvd?.affected_vendors.filter(Boolean) ?? [];

  if (products.length > 0) return `teams running ${products.slice(0, 2).join(", ")}`;
  if (vendors.length > 0) return `organizations using ${vendors.slice(0, 2).join(", ")} software`;
  return "teams that recognize this CVE in their exposed stack";
}

function deriveSpark(item: ViralCveItem): number[] {
  const buzz = clampBuzz(item.virality_score);
  const base = Math.max(1, Math.round(buzz * 0.35));
  const spread = Math.max(3, Math.round(item.mention_count / 2));
  const trend = deriveTrend(item);

  if (trend === "cooling") {
    return [buzz + spread, buzz, buzz - 3, buzz - 7, buzz - 10, buzz - 12, buzz].map(clampBuzz);
  }

  if (trend === "stable") {
    return [buzz - 4, buzz - 2, buzz + 1, buzz - 1, buzz + 2, buzz - 1, buzz].map(clampBuzz);
  }

  return [base, base + 4, base + spread, buzz - 8, buzz - 3, buzz - 1, buzz].map(clampBuzz);
}

function sourceLabel(sourceTypes: SourceType[]): string {
  if (sourceTypes.length === 0) return "No source signal yet";
  return sourceTypes.map((sourceType) => SOURCE_LABELS[sourceType]).join(" + ");
}

function cveShortName(cveId: string): string {
  return cveId.replace(/^CVE-/, "Signal ");
}

export function toThreadPulseVulnerability(
  item: ViralCveItem,
  index: number,
): ThreadPulseVulnerability {
  const severity = normalizeSeverity(item.nvd?.severity);

  return {
    rank: index + 1,
    cveId: item.cve_id,
    name: cveShortName(item.cve_id),
    buzz: clampBuzz(item.virality_score),
    trend: deriveTrend(item),
    news: deriveNewsCount(item),
    social: item.mention_count,
    researchers: deriveResearchers(item),
    source: item.distinct_source_count,
    sourceTypes: item.source_types,
    sourceLabel: sourceLabel(item.source_types),
    severity,
    flags: deriveFlags(item, severity),
    summary: item.nvd?.description ?? "NVD enrichment is not available yet; ranking is based on public-source mentions and source diversity.",
    riskFor: deriveRiskFor(item),
    spark: deriveSpark(item),
    firstSeenAt: item.first_seen_at,
    lastSeenAt: item.last_seen_at,
  };
}

export function toThreadPulseVulnerabilities(items: ViralCveItem[]): ThreadPulseVulnerability[] {
  return items.map(toThreadPulseVulnerability);
}
