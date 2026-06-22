import { describe, expect, it } from "vitest";

import { toThreadPulseVulnerabilities, toThreadPulseVulnerability } from "@/adapters/threadPulse";
import type { ViralCveItem } from "@/types/viralCve";

const baseItem: ViralCveItem = {
  cve_id: "CVE-2026-0001",
  virality_score: 87.4,
  mention_count: 31,
  distinct_source_count: 3,
  source_types: ["reddit", "hacker_news"],
  first_seen_at: "2026-06-22T08:00:00Z",
  last_seen_at: "2026-06-22T11:00:00Z",
  representative_links: [
    {
      source_type: "hacker_news",
      title: "Critical CVE write-up",
      url: "https://example.test/news/cve-2026-0001",
      observed_at: "2026-06-22T09:00:00Z",
    },
  ],
  nvd: {
    severity: "critical",
    description: "NVD says this vulnerability allows remote code execution.",
    affected_vendors: ["Acme"],
    affected_products: ["Acme Gateway", "Acme Agent"],
    published_at: "2026-06-21T00:00:00Z",
    modified_at: "2026-06-22T00:00:00Z",
  },
};

function item(overrides: Partial<ViralCveItem> = {}): ViralCveItem {
  return {
    ...baseItem,
    ...overrides,
    nvd: overrides.nvd === undefined ? baseItem.nvd : overrides.nvd,
    representative_links: overrides.representative_links ?? baseItem.representative_links,
    source_types: overrides.source_types ?? baseItem.source_types,
  };
}

describe("ThreadPulse adapter", () => {
  it("maps backend fields with NVD enrichment into the frontend view model", () => {
    const vulnerability = toThreadPulseVulnerability(baseItem, 0);

    expect(vulnerability).toMatchObject({
      rank: 1,
      cveId: "CVE-2026-0001",
      name: "Signal 2026-0001",
      buzz: 87,
      social: 31,
      source: 3,
      sourceTypes: ["reddit", "hacker_news"],
      sourceLabel: "Reddit + The Hacker News",
      severity: "CRITICAL",
      summary: "NVD says this vulnerability allows remote code execution.",
      riskFor: "teams running Acme Gateway, Acme Agent",
      firstSeenAt: "2026-06-22T08:00:00Z",
      lastSeenAt: "2026-06-22T11:00:00Z",
    });
    expect(vulnerability.flags).toEqual(["watch", "cross-source"]);
    expect(vulnerability.news).toBe(1);
    expect(vulnerability.researchers).toBe(6);
    expect(vulnerability.trend).toBe("rising");
  });

  it("renders a stable deterministic fallback view model without NVD enrichment", () => {
    const noNvdItem = item({
      cve_id: "CVE-2026-0002",
      virality_score: 42.2,
      mention_count: 7,
      distinct_source_count: 1,
      source_types: ["mastodon"],
      representative_links: [],
      nvd: null,
    });

    const first = toThreadPulseVulnerability(noNvdItem, 4);
    const second = toThreadPulseVulnerability(noNvdItem, 4);

    expect(first).toEqual(second);
    expect(first).toMatchObject({
      rank: 5,
      cveId: "CVE-2026-0002",
      buzz: 42,
      social: 7,
      source: 1,
      sourceLabel: "Mastodon",
      severity: "UNKNOWN",
      trend: "stable",
      news: 0,
      researchers: 1,
      flags: ["no-nvd-yet"],
      summary:
        "NVD enrichment is not available yet; ranking is based on public-source mentions and source diversity.",
      riskFor: "teams that recognize this CVE in their exposed stack",
      spark: [38, 40, 43, 41, 44, 41, 42],
    });
  });

  it("preserves ranking order and clamps buzz/spark display values", () => {
    const vulnerabilities = toThreadPulseVulnerabilities([
      item({ cve_id: "CVE-2026-0100", virality_score: 144, mention_count: 50 }),
      item({
        cve_id: "CVE-2026-0101",
        virality_score: -10,
        mention_count: 0,
        source_types: [],
        distinct_source_count: 0,
        representative_links: [],
      }),
    ]);

    expect(vulnerabilities.map((vulnerability) => [vulnerability.rank, vulnerability.cveId])).toEqual([
      [1, "CVE-2026-0100"],
      [2, "CVE-2026-0101"],
    ]);
    expect(vulnerabilities[0].buzz).toBe(100);
    expect(vulnerabilities[0].spark.every((value) => value >= 0 && value <= 100)).toBe(true);
    expect(vulnerabilities[1].buzz).toBe(0);
    expect(vulnerabilities[1].sourceLabel).toBe("No source signal yet");
  });
});
