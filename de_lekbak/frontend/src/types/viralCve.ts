export type SourceType = "reddit" | "bluesky" | "mastodon" | "hacker_news";

export interface SourceLink {
  source_type: SourceType;
  title: string;
  url: string;
  observed_at: string | null;
}

export interface NvdEnrichment {
  severity: string | null;
  description: string | null;
  affected_vendors: string[];
  affected_products: string[];
  published_at: string | null;
  modified_at: string | null;
}

export interface ViralCveItem {
  cve_id: string;
  virality_score: number;
  mention_count: number;
  distinct_source_count: number;
  source_types: SourceType[];
  first_seen_at: string | null;
  last_seen_at: string | null;
  representative_links: SourceLink[];
  nvd: NvdEnrichment | null;
}

export interface ViralCveRankingResponse {
  items: ViralCveItem[];
  last_refreshed_at: string | null;
  is_stale: boolean;
}

export interface ViralCveRefreshResponse {
  rankings: ViralCveRankingResponse;
  message: string;
}

export type ThreadPulseTrend = "rising" | "cooling" | "stable";

export type ThreadPulseSeverity = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "UNKNOWN";

export interface ThreadPulseVulnerability {
  rank: number;
  cveId: string;
  name?: string;
  buzz: number;
  trend: ThreadPulseTrend;
  news: number;
  social: number;
  researchers: number;
  source: number;
  sourceTypes: SourceType[];
  sourceLabel: string;
  severity: ThreadPulseSeverity;
  flags: string[];
  summary: string;
  riskFor: string;
  spark: number[];
  firstSeenAt: string | null;
  lastSeenAt: string | null;
}
