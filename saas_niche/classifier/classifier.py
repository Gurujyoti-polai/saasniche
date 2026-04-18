"""Batch pain-point classifier using Ollama and Supabase."""

from __future__ import annotations

import json
import traceback
from collections import Counter
from datetime import datetime, timezone
from typing import Any

import requests
from saas_niche.config import get_settings

from saas_niche.db.client import (
    fetch_unclassified_posts,
    mark_raw_posts_classified,
    save_classified_posts,
)

BATCH_SIZE = 1
MAX_POSTS = 500
VALID_CATEGORIES = {
    "billing",
    "workflow",
    "integration",
    "missing_tool",
    "pricing",
    "automation",
    "communication",
    "reporting",
    "hiring",
    "legal",
    "finance",
    "other",
}
VALID_PROFESSIONS = {
    "developer",
    "lawyer",
    "freelancer",
    "marketer",
    "founder",
    "designer",
    "hr",
    "accountant",
    "general",
}
PROFESSION_MAP = {
    "SWE": "developer",
    "software engineer": "developer",
    "engineer": "developer",
    "founder/developer": "founder",
    "developer/founder": "founder",
    "founder/designer": "founder",
    "designer/developer": "developer",
    "marketer/founder": "marketer",
}
VALID_WTP_SIGNALS = {"strong", "weak", "none"}
SYSTEM_PROMPT = (
    "You are a pain point detector for SaaS ideas. "
    "Analyze Reddit posts and identify genuine software "
    "or workflow pain points — problems people would "
    "pay to have solved. Return only valid JSON, "
    "no explanation, no markdown."
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _batch_items(items: list[dict[str, Any]], size: int) -> list[list[dict[str, Any]]]:
    return [items[index : index + size] for index in range(0, len(items), size)]


def _build_user_prompt(posts: list[dict[str, Any]]) -> str:
    post = posts[0]
    payload = {
        "id": post.get("id"),
        "title": post.get("title", ""),
        "body": post.get("body", ""),
    }
    return (
        "Analyze this Reddit post and return a single \n"
        "JSON object with exactly these fields:\n"
        "  id: the post id\n"
        "  is_pain_point: true or false\n"
        "  category: one of [billing, workflow, integration, \n"
        "    missing_tool, pricing, automation, communication, \n"
        "    reporting, hiring, legal, finance, other]\n"
        "  profession: one of [developer, lawyer, freelancer, \n"
        "    marketer, founder, designer, hr, accountant, \n"
        "    general]\n"
        "  wtp_signal: one of [strong, weak, none]\n"
        "    strong = explicitly says they'd pay, tried tools,\n"
        "             or asking for recommendations\n"
        "    weak = frustrated but no explicit WTP\n"
        "    none = no pain signal\n"
        "  intensity: integer 1 to 5\n"
        "    5 = extremely frustrated, urgent problem\n"
        "    1 = mild complaint\n\n"
        "Post:\n"
        f"{json.dumps(payload, ensure_ascii=True)}\n\n"
        "Return a single JSON object."
    )


def _parse_classification_response(
    raw_text: str,
    posts: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    result = json.loads(raw_text)
    if isinstance(result, dict):
        parsed = [result]
    else:
        parsed = result
    if not isinstance(parsed, list) or len(parsed) != len(posts):
        raise ValueError("Response is not a JSON object matching the input post.")

    expected_ids = [str(post["id"]) for post in posts]
    normalized: list[dict[str, Any]] = []

    for expected_id, item in zip(expected_ids, parsed, strict=True):
        if not isinstance(item, dict):
            raise ValueError("Classification item is not an object.")

        item_id = str(item.get("id", ""))
        if item_id != expected_id:
            raise ValueError("Classification ids do not match input order.")

        category = str(item.get("category", "other"))
        profession = str(item.get("profession", "general"))
        profession = PROFESSION_MAP.get(profession, profession)
        wtp_signal = str(item.get("wtp_signal", "none"))
        intensity = max(1, int(item.get("intensity", 1)))

        if category not in VALID_CATEGORIES:
            category = "other"
        if profession not in VALID_PROFESSIONS:
            profession = "general"
        if wtp_signal not in VALID_WTP_SIGNALS:
            raise ValueError(f"Invalid wtp_signal: {wtp_signal}")

        normalized.append(
            {
                "id": item_id,
                "is_pain_point": bool(item.get("is_pain_point", False)),
                "category": category,
                "profession": profession,
                "wtp_signal": wtp_signal,
                "intensity": intensity,
            }
        )

    return normalized


def _call_ollama(prompt: str, settings: Any) -> str:
    response = requests.post(
        f"{settings.OLLAMA_BASE_URL}/api/generate",
        json={
            "model": settings.OLLAMA_CLASSIFIER_MODEL,
            "prompt": prompt,
            "format": "json",
            "stream": False,
            "options": {"temperature": 0.1, "num_predict": 300},
        },
        timeout=120,
    )
    response.raise_for_status()
    return response.json()["response"]


def _classify_batch(
    posts: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], float]:
    user_prompt = _build_user_prompt(posts)
    prompt = f"{SYSTEM_PROMPT}\n\n{user_prompt}"

    for attempt in range(2):
        try:
            result_text = _call_ollama(prompt, get_settings())
        except Exception:
            if attempt == 0:
                continue
            raise
        print(f"[debug] raw response: {result_text[:500]}")
        cost = 0.0

        try:
            parsed = _parse_classification_response(result_text, posts)
        except (json.JSONDecodeError, ValueError):
            if attempt == 0:
                continue
            raise

        return parsed, cost

    raise RuntimeError("Batch classification failed after retry.")


def _build_classified_records(
    posts: list[dict[str, Any]],
    classifications: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    post_by_id = {str(post["id"]): post for post in posts}
    records: list[dict[str, Any]] = []

    for classification in classifications:
        post = post_by_id[classification["id"]]
        records.append(
            {
                "id": classification["id"],
                "subreddit": post.get("subreddit", ""),
                "title": post.get("title", ""),
                "body": post.get("body", ""),
                "url": post.get("url", ""),
                "upvotes": int(post.get("upvotes", 0) or 0),
                "is_pain_point": classification["is_pain_point"],
                "category": classification["category"],
                "profession": classification["profession"],
                "wtp_signal": classification["wtp_signal"],
                "intensity": classification["intensity"],
                "classified_at": _utc_now(),
            }
        )

    return records


def run() -> None:
    """Classify unprocessed Reddit posts and persist the results."""

    posts = fetch_unclassified_posts(limit=MAX_POSTS)
    if not posts:
        print("No unclassified posts found.")
        return

    batches = _batch_items(posts, BATCH_SIZE)
    total_processed = 0
    total_pain_points = 0
    total_cost = 0.0
    category_counter: Counter[str] = Counter()
    total_posts = len(posts)

    for batch_index, batch in enumerate(batches, start=1):
        try:
            classifications, batch_cost = _classify_batch(batch)
        except Exception as e:
            print(f"[error] batch {batch_index} failed: {str(e)}")
            traceback.print_exc()
            continue

        records = _build_classified_records(batch, classifications)
        save_classified_posts(records)
        mark_raw_posts_classified([record["id"] for record in records])

        batch_pain_points = sum(1 for item in classifications if item["is_pain_point"])
        batch_skipped = len(classifications) - batch_pain_points
        for item in classifications:
            if item["is_pain_point"]:
                category_counter[item["category"]] += 1

        total_processed += len(classifications)
        total_pain_points += batch_pain_points
        total_cost += batch_cost
        classification = classifications[0]
        status_text = "pain point ✓" if classification["is_pain_point"] else "not pain point"
        print(
            f"[classify] post {batch_index}/{total_posts} | {status_text} | ${batch_cost:.4f}"
        )

    print(f"Total posts processed: {total_processed}")
    print(f"Pain points found: {total_pain_points}")
    print(f"Breakdown by category: {dict(category_counter)}")
    print(f"Total API cost: ${total_cost:.4f}")
