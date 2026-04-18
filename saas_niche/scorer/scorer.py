"""Formula-based pain point scoring."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from statistics import mean
from typing import Any

from saas_niche.db.client import fetch_pain_points, save_scored_posts

WTP_SCORES = {
    "strong": 1.0,
    "weak": 0.5,
    "none": 0.0,
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _truncate_title(title: str, limit: int = 50) -> str:
    title = title.strip()
    if len(title) <= limit:
        return title
    return f"{title[: limit - 3]}..."


def _clamp_score(score: float) -> float:
    return max(1.0, min(100.0, round(score, 1)))


def _compute_score(
    post: dict[str, Any],
    max_upvotes: int,
    category_profession_counts: Counter[tuple[str, str]],
    max_frequency: int,
) -> float:
    intensity = int(post.get("intensity", 1) or 1)
    intensity_score = (intensity - 1) / 4

    wtp_signal = str(post.get("wtp_signal", "none"))
    wtp_score = WTP_SCORES.get(wtp_signal, 0.0)

    upvotes = int(post.get("upvotes", 0) or 0)
    upvote_score = min(1.0, (upvotes / max_upvotes) if max_upvotes else 0.0)

    key = (
        str(post.get("category", "other")),
        str(post.get("profession", "general")),
    )
    frequency_count = category_profession_counts.get(key, 0)
    frequency_score = min(1.0, (frequency_count / max_frequency) if max_frequency else 0.0)

    score = (
        wtp_score * 0.45
        + intensity_score * 0.30
        + frequency_score * 0.15
        + upvote_score * 0.10
    ) * 100
    if wtp_signal == "none":
        score = min(score, 40.0)
    return _clamp_score(score)


def _build_scored_record(
    post: dict[str, Any],
    score: float,
) -> dict[str, Any]:
    return {
        "id": post.get("id"),
        "subreddit": post.get("subreddit", ""),
        "title": post.get("title", ""),
        "body": post.get("body", ""),
        "url": post.get("url", ""),
        "upvotes": int(post.get("upvotes", 0) or 0),
        "category": post.get("category", "other"),
        "profession": post.get("profession", "general"),
        "wtp_signal": post.get("wtp_signal", "none"),
        "intensity": int(post.get("intensity", 1) or 1),
        "score": score,
        "scored_at": _utc_now(),
    }


def run() -> None:
    """Score all classified pain points and persist the results."""

    pain_points = fetch_pain_points()
    if not pain_points:
        print("No pain points found.")
        return

    max_upvotes = max(int(post.get("upvotes", 0) or 0) for post in pain_points)
    category_profession_counts: Counter[tuple[str, str]] = Counter(
        (
            str(post.get("category", "other")),
            str(post.get("profession", "general")),
        )
        for post in pain_points
    )
    max_frequency = max(category_profession_counts.values(), default=0)

    scored_posts: list[dict[str, Any]] = []

    for post in pain_points:
        score = _compute_score(post, max_upvotes, category_profession_counts, max_frequency)
        scored_posts.append(_build_scored_record(post, score))
        print(f'[score] "{_truncate_title(str(post.get("title", "")))}" → {score}')

    save_scored_posts(scored_posts)

    average_score = round(mean(post["score"] for post in scored_posts), 1)
    top_five = sorted(scored_posts, key=lambda item: item["score"], reverse=True)[:5]

    print(f"Total scored: {len(scored_posts)}")
    print(f"Average score: {average_score}")
    print("Top 5 highest scoring pain points:")
    for post in top_five:
        print(f'  {post["score"]} | {post["category"]} | {_truncate_title(str(post["title"]))}')
