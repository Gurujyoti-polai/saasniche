"""Low-volume Reddit crawler using public JSON endpoints."""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from saas_niche.db.client import save_raw_posts

BASE_URL = "https://www.reddit.com"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
}
REQUEST_TIMEOUT = 15.0
SUBREDDIT_SLEEP_SECONDS = 5
RETRY_SLEEP_SECONDS = 60
POST_LIMIT = 25
HOT_POST_LIMIT = 50
BODY_MAX_CHARS = 800
MIN_CONTENT_CHARS = 30
CLASSIFIER_COST_PER_POST = 0.0001
STATE_FILE = Path(__file__).with_name("crawl_state.json")

SUBREDDITS = [
    # Founders & builders
    "entrepreneur", "indiehackers", "startups", "smallbusiness", "SideProject",
    # Developers & DevOps
    "webdev", "devops", "programming", "softwaredevelopment", "sysadmin", "aws",
    # Freelance & agencies
    "freelance", "freelancers", "webdesign",
    # Marketing & content
    "marketing", "content_marketing", "socialmedia", "SEO",
    # Productivity & PM tools
    "productivity", "notion", "clickup", "projectmanagement",
    # Finance & legal
    "accounting", "legaladvice", "personalfinance",
    # Niche high-WTP
    "msp", "ecommerce", "shopify", "humanresources", "recruitinghell",
]

TEST_SUBREDDITS = ["entrepreneur", "webdev", "indiehackers", "productivity", "freelance"]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _today_utc() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _load_crawl_state() -> dict[str, str]:
    if not STATE_FILE.exists():
        return {}
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def _save_crawl_state(state: dict[str, str]) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")


def _subreddits_for_run(test_mode: bool) -> tuple[list[str], dict[str, str]]:
    if test_mode:
        return TEST_SUBREDDITS, {}

    state = _load_crawl_state()
    today = _today_utc()
    pending = [subreddit for subreddit in SUBREDDITS if state.get(subreddit) != today]
    return pending, state


def _truncate_body(body: str) -> str:
    return body[:BODY_MAX_CHARS].strip()


def _is_valid_post(post: dict[str, Any], seen_ids: set[str]) -> bool:
    post_id = post.get("id")
    if not post_id or post_id in seen_ids:
        return False

    if bool(post.get("stickied")):
        return False

    body = (post.get("selftext") or "").strip()
    if not body or body in {"[removed]", "[deleted]"}:
        return False

    title = (post.get("title") or "").strip()
    if len(f"{title}{body}") < MIN_CONTENT_CHARS:
        return False

    return True


def _normalize_post(post: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": post["id"],
        "subreddit": str(post.get("subreddit", "")).lower(),
        "title": (post.get("title") or "").strip(),
        "body": _truncate_body((post.get("selftext") or "").strip()),
        "top_comments": [],
        "upvotes": int(post.get("score", 0) or 0),
        "num_comments": int(post.get("num_comments", 0) or 0),
        "url": post.get("url") or "",
        "fetched_at": _utc_now(),
        "sort_type": "new",
    }


def _fetch_listing(client: httpx.Client, subreddit: str, url: str) -> dict[str, Any] | None:

    for attempt in range(2):
        try:
            response = client.get(url, headers=HEADERS)
        except httpx.HTTPError:
            response = None
        else:
            if response.status_code == 200:
                return response.json()
            if response.status_code not in {403, 429}:
                break

        if attempt == 0:
            time.sleep(RETRY_SLEEP_SECONDS)
            continue

    print(f"[skip] r/{subreddit}")
    return None


def _crawl_subreddit(
    client: httpx.Client,
    subreddit: str,
    seen_ids: set[str],
) -> tuple[list[dict[str, Any]], int]:
    saved: list[dict[str, Any]] = []
    skipped = 0
    endpoints = [
        f"{BASE_URL}/r/{subreddit}/hot.json?limit={HOT_POST_LIMIT}&raw_json=1",
        f"{BASE_URL}/r/{subreddit}/new.json?limit={POST_LIMIT}&raw_json=1",
    ]

    for url in endpoints:
        payload = _fetch_listing(client, subreddit, url)
        if not isinstance(payload, dict):
            continue

        children = payload.get("data", {}).get("children", [])
        for child in children:
            post = child.get("data", {})
            if not _is_valid_post(post, seen_ids):
                skipped += 1
                continue

            saved.append(_normalize_post(post))
            seen_ids.add(post["id"])

    return saved, skipped


def run(test_mode: bool = False) -> None:
    """Crawl one low-volume daily batch of subreddit posts."""

    subreddit_names, crawl_state = _subreddits_for_run(test_mode)
    seen_ids: set[str] = set()
    total_saved = 0
    total_skipped = 0
    crawled_today = 0
    today = _today_utc()

    with httpx.Client(timeout=REQUEST_TIMEOUT, follow_redirects=True) as client:
        for subreddit in subreddit_names:
            started_at = time.perf_counter()
            posts, skipped = _crawl_subreddit(client, subreddit, seen_ids)
            if posts:
                save_raw_posts(posts)
                total_saved += len(posts)
            total_skipped += skipped
            crawled_today += 1

            if not test_mode:
                crawl_state[subreddit] = today

            duration = int(time.perf_counter() - started_at)
            print(f"[crawl] r/{subreddit} | {len(posts)} saved | {skipped} skipped | {duration}s")
            time.sleep(SUBREDDIT_SLEEP_SECONDS)

    if not test_mode:
        _save_crawl_state(crawl_state)

    remaining = 0 if test_mode else sum(
        1 for subreddit in SUBREDDITS if crawl_state.get(subreddit) != today
    )
    estimated_cost = total_saved * CLASSIFIER_COST_PER_POST
    print(f"Total saved: {total_saved}")
    print(f"Total skipped: {total_skipped}")
    print(f"Subreddits crawled today: {crawled_today}")
    print(f"Subreddits remaining for tomorrow: {remaining}")
    print(f"Estimated classifier cost: ${estimated_cost:.4f}")
