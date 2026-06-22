import argparse
import asyncio
import re
from collections.abc import Sequence

import httpx

from de_lekbak_backend.core.config import Settings
from de_lekbak_backend.services.threat_intel import BlueskySearchProvider, ThreatIntelPost

CVE_PATTERN = re.compile(r"CVE-\d{4}-\d+", re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch and print Bluesky threat-intel posts without storing them."
    )
    parser.add_argument(
        "--terms",
        help="Comma-separated search terms. Defaults to DE_LEKBAK_BLUESKY_SEARCH_TERMS.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum number of matching posts to print. Defaults to 20.",
    )
    parser.add_argument(
        "--include-no-cve",
        action="store_true",
        help="Also print posts that do not contain a CVE ID.",
    )
    parser.add_argument(
        "--text-width",
        type=int,
        default=280,
        help="Maximum post text characters to print. Defaults to 280.",
    )
    return parser.parse_args()


def parse_terms(raw_terms: str | None, settings: Settings) -> list[str]:
    if raw_terms is None:
        return settings.bluesky_search_terms
    return [term.strip() for term in raw_terms.split(",") if term.strip()]


def extract_cves(text: str) -> list[str]:
    return sorted({match.upper() for match in CVE_PATTERN.findall(text)})


def engagement_score(post: ThreatIntelPost, settings: Settings) -> float:
    return (
        post.like_count * settings.bluesky_like_weight
        + post.reply_count * settings.bluesky_reply_weight
        + post.repost_count * settings.bluesky_repost_weight
        + post.quote_count * settings.bluesky_quote_weight
    )


def deduplicate_posts(posts: Sequence[ThreatIntelPost]) -> list[ThreatIntelPost]:
    by_uri: dict[str, ThreatIntelPost] = {}
    for post in posts:
        by_uri.setdefault(post.post_uri, post)
    return list(by_uri.values())


def truncate_text(text: str, width: int) -> str:
    normalized = " ".join(text.split())
    if width <= 0 or len(normalized) <= width:
        return normalized
    return f"{normalized[: width - 1]}…"


def print_post(post: ThreatIntelPost, cves: list[str], settings: Settings, text_width: int) -> None:
    print("-" * 80)
    print(f"uri: {post.post_uri}")
    print(f"author: {post.author_handle or '-'} ({post.display_name or '-'})")
    print(f"created_at: {post.created_at.isoformat()}")
    print(f"indexed_at: {post.indexed_at.isoformat()}")
    print(f"cves: {', '.join(cves) if cves else '-'}")
    print(
        "engagement: "
        f"score={engagement_score(post, settings):.1f}, "
        f"likes={post.like_count}, replies={post.reply_count}, "
        f"reposts={post.repost_count}, quotes={post.quote_count}"
    )
    print(f"text: {truncate_text(post.text, text_width)}")


async def run() -> None:
    args = parse_args()
    settings = Settings()
    terms = parse_terms(args.terms, settings)

    if not terms:
        raise SystemExit("No Bluesky search terms configured.")

    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0), follow_redirects=True) as client:
        provider = BlueskySearchProvider(client)
        posts = deduplicate_posts(await provider.fetch_posts(terms))

    matching_posts: list[tuple[ThreatIntelPost, list[str]]] = []
    for post in posts:
        cves = extract_cves(post.text)
        if cves or args.include_no_cve:
            matching_posts.append((post, cves))

    matching_posts.sort(key=lambda item: item[0].indexed_at, reverse=True)

    print("Bluesky preview fetch completed")
    print(f"terms: {', '.join(terms)}")
    print(f"fetched_unique_posts: {len(posts)}")
    print(f"printable_posts: {len(matching_posts)}")
    print(f"limit: {args.limit}")

    for post, cves in matching_posts[: args.limit]:
        print_post(post, cves, settings, args.text_width)


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
