# De Lekbak Backend Data Flow

This package gathers public CVE mentions from Bluesky and Reddit, stores the
normalized mentions in the backend database, and exposes views that can be
joined with NVD-backed vulnerability data when that data is available.

## Bluesky collection

- `services/threat_intel.py` defines `BlueskySearchProvider`, which calls the
  public Bluesky appview search endpoint:
  `https://api.bsky.app/xrpc/app.bsky.feed.searchPosts`.
- Search terms come from `Settings.bluesky_search_terms` in `core/config.py`.
  The default terms include CVE-oriented security language such as `CVE`,
  `CVE-`, `vulnerability`, `exploit`, `0day`, `RCE`, and `PoC`.
- Each search result is normalized into a `ThreatIntelPost` with author data,
  timestamps, post text, and engagement counters.
- `services/bluesky_threat_intel_service.py` extracts CVE IDs from post text
  with the pattern `CVE-YYYY-NNNN...` and ignores posts without a CVE ID.
- Engagement score is calculated from likes, replies, reposts, and quotes using
  configurable weights from `core/config.py`.
- `repositories/bluesky_mention_repository.py` upserts each CVE-bearing post
  into the `bluesky_mentions` table keyed by `post_uri`.
- Bluesky analytics endpoints are exposed under `/api/v1/bluesky`, including
  trending CVEs, top posts, per-CVE post counts, active authors, and enriched
  CVEs.

## Reddit collection

- `scrapers/reddit.py` fetches subreddit listing JSON from
  `https://www.reddit.com/r/{subreddit}/new.json` with a De Lekbak user agent.
- `services/reddit_service.py` uses `DEFAULT_TRENDING_SUBREDDITS` unless the API
  caller provides subreddit names through the request query.
- The scraper looks at posts from the last seven days and scans the title plus
  self text for CVE IDs using the pattern `CVE-YYYY-NNNN...`.
- Mentions are aggregated per CVE with:
  - `mention_count`
  - `first_seen`
  - `last_seen`
  - source post URLs
- Duplicate Reddit post URLs are counted once.
- If live scraping yields no CVE mentions, seeded fallback aggregates from public
  NVD/vendor/advisory links are returned so the dashboard still has data.
- `repositories/reddit_cve_repository.py` upserts aggregates into the
  `reddit_cves` table keyed by `cve_number`.
- Reddit trending data is exposed under `/api/v1/reddit/trending`.

## NVD enrichment

- NVD enrichment is optional: viral and social rankings are designed to work
  even when no matching NVD record exists.
- Bluesky enrichment is implemented by
  `BlueskyMentionRepository.build_enriched_cves_query()`.
- The query first unnests CVE IDs from `bluesky_mentions`, counts mentions, and
  calculates the latest mention time and top engagement score.
- It then left joins the mentioned CVEs to NVD-backed tables:
  - `cves`
  - `cve_metrics`
  - `cve_references`
- When a match is present, the enriched response includes fields such as:
  - NVD source identifier and vulnerability status
  - severity, base score, vector string, and metric type
  - English description
  - published, modified, ingested, created, and updated timestamps
  - CWE IDs
  - affected vendors and products
  - references, metrics, and raw NVD payload
- The `/api/v1/bluesky/enriched-cves` endpoint returns both social mention data
  and the optional `nvd` object. Use `nvd_only=true` to filter to CVEs that have
  matching NVD data.

## End-to-end shape

1. Source fetchers gather public posts from Bluesky or Reddit.
2. Text is scanned for CVE identifiers.
3. CVE-bearing posts or aggregates are persisted with source and timing data.
4. API queries rank CVEs by mention activity and engagement.
5. Where available, NVD tables enrich the social CVE records without blocking
   display of CVEs that have not yet been matched to NVD data.
