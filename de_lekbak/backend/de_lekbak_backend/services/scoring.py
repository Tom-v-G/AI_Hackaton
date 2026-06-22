from de_lekbak_backend.schemas.viral_cve import SourceType

SOURCE_TYPE_WEIGHTS: dict[SourceType, float] = {
    SourceType.reddit: 1.0,
    SourceType.bluesky: 1.0,
    SourceType.mastodon: 1.0,
    SourceType.hacker_news: 1.25,
}


def calculate_virality_score(mention_count: int, source_types: set[SourceType]) -> float:
    source_weight = sum(SOURCE_TYPE_WEIGHTS[source_type] for source_type in source_types)
    return round(float(mention_count) + source_weight + len(source_types), 2)
