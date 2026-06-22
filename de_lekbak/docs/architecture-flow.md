# De Lekbak prototype architecture flow

Use this Mermaid diagram in the prototype demo to explain how De Lekbak turns public CVE chatter into the ThreadPulse dashboard.

```mermaid
flowchart LR
    presenter[Demo presenter]
    browser[Browser\nThreadPulse React dashboard]
    query[TanStack Query hooks\nuseViralCves / useRefreshViralCves]
    client[Frontend API client\n/api/v1]

    subgraph Backend[De Lekbak backend]
        rankings[FastAPI viral CVE endpoints\nGET /api/v1/viral-cves\nPOST /api/v1/viral-cves/refresh]
        ranking_service[ViralCveService\nlist + manual refresh]
        in_memory[Prototype ranking cache\nViralCveRepository]

        reddit_api[Reddit endpoint\n/api/v1/reddit/trending]
        reddit_service[RedditService]
        reddit_scraper[RedditScraper\nCVE extraction + fallback seeds]
        reddit_repo[RedditCveRepository]

        bluesky_api[Bluesky analytics endpoints\n/api/v1/bluesky/*]
        bluesky_ingest[BlueskyThreatIntelService\nsearch + CVE extraction]
        bluesky_provider[BlueskySearchProvider\napi.bsky.app]
        bluesky_repo[BlueskyMentionRepository]
    end

    subgraph Storage[App-owned storage]
        postgres[(Postgres\nreddit_cves + bluesky_mentions\noptional NVD tables)]
    end

    subgraph Sources[Public sources]
        reddit[(Reddit subreddits\nnetsec / cybersecurity / cve / sysadmin)]
        bluesky[(Bluesky search\nCVE, exploit, RCE, 0day)]
        nvd[(NVD enrichment\noptional, non-blocking)]
    end

    presenter --> browser --> query --> client --> rankings
    rankings --> ranking_service --> in_memory
    in_memory --> ranking_service --> rankings --> client --> query --> browser

    reddit_api --> reddit_service --> reddit_scraper --> reddit
    reddit_scraper --> reddit_repo --> postgres

    bluesky_ingest --> bluesky_provider --> bluesky
    bluesky_ingest --> bluesky_repo --> postgres
    bluesky_api --> bluesky_repo
    bluesky_repo -. enrich when present .-> nvd
```

## Demo narration

- The browser shows **ThreadPulse**, the React/Vite frontend for De Lekbak.
- TanStack Query loads `/api/v1/viral-cves` and updates the page after a manual refresh.
- FastAPI owns the prototype API boundary; CORS is configured for the local Vite dev server.
- The current dashboard flow uses `ViralCveService` and a prototype in-memory ranking repository.
- Source-ingestion building blocks already live in the backend:
  - Reddit scraping extracts CVE IDs from selected cybersecurity subreddits and persists aggregates in Postgres.
  - Bluesky ingestion searches public posts, extracts CVE IDs, computes engagement, and persists mentions in Postgres.
  - Bluesky analytics can read trending CVEs, top posts, post counts, active authors, and optional NVD enrichment.
- NVD enrichment is optional: viral CVE discovery and display are designed to work even when enrichment is missing.

## Prototype boundaries to call out

- `de_lekbak/` is standalone and does not depend on `cve-intelligence` at runtime.
- Manual refresh is intentional for the hackathon demo; background scheduling is deferred.
- The visible dashboard currently reads the `/viral-cves` ranking endpoint; the Reddit and Bluesky data paths are available as backend prototype capabilities to connect into the ranking service next.
