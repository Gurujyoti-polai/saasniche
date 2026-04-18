"""Supabase client helpers."""

from __future__ import annotations

from typing import Any

import httpx
from supabase import Client, create_client

from saas_niche.config import get_settings

httpx._config.DEFAULT_TIMEOUT_CONFIG = httpx.Timeout(30.0)


def get_client() -> Client:
    """Create a Supabase client from environment-backed settings."""

    settings = get_settings()
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)


def save_raw_posts(posts: list[dict]) -> None:
    """Upsert raw crawler output into the raw_posts table."""

    if not posts:
        return

    settings = get_settings()
    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        print("[warn] SUPABASE_URL or SUPABASE_KEY missing; skipping raw_posts upsert")
        return

    client = get_client()
    client.table("raw_posts").upsert(posts, on_conflict="id").execute()


def fetch_unclassified_posts(limit: int = 500) -> list[dict[str, Any]]:
    """Fetch up to `limit` unclassified raw posts."""

    settings = get_settings()
    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        print("[warn] SUPABASE_URL or SUPABASE_KEY missing; cannot fetch raw_posts")
        return []

    client = get_client()
    response = (
        client.table("raw_posts")
        .select("*")
        .or_("classified.is.null,classified.eq.false")
        .limit(limit)
        .execute()
    )
    data = response.data or []
    return data if isinstance(data, list) else []


def save_classified_posts(posts: list[dict[str, Any]]) -> None:
    """Upsert classified post records into the classified_posts table."""

    if not posts:
        return

    settings = get_settings()
    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        print("[warn] SUPABASE_URL or SUPABASE_KEY missing; skipping classified_posts upsert")
        return

    client = get_client()
    client.table("classified_posts").upsert(posts, on_conflict="id").execute()


def mark_raw_posts_classified(post_ids: list[str]) -> None:
    """Mark processed raw posts as classified."""

    if not post_ids:
        return

    settings = get_settings()
    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        print("[warn] SUPABASE_URL or SUPABASE_KEY missing; skipping raw_posts classified update")
        return

    client = get_client()
    client.table("raw_posts").update({"classified": True}).in_("id", post_ids).execute()


def fetch_pain_points() -> list[dict[str, Any]]:
    """Fetch all classified pain points from classified_posts."""

    settings = get_settings()
    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        print("[warn] SUPABASE_URL or SUPABASE_KEY missing; cannot fetch classified_posts")
        return []

    client = get_client()
    response = (
        client.table("classified_posts")
        .select("*")
        .eq("is_pain_point", True)
        .execute()
    )
    data = response.data or []
    return data if isinstance(data, list) else []


def save_scored_posts(posts: list[dict[str, Any]]) -> None:
    """Upsert scored post records into the scored_posts table."""

    if not posts:
        return

    settings = get_settings()
    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        print("[warn] SUPABASE_URL or SUPABASE_KEY missing; skipping scored_posts upsert")
        return

    client = get_client()
    client.table("scored_posts").upsert(posts, on_conflict="id").execute()


def fetch_blueprint_candidates() -> list[dict[str, Any]]:
    settings = get_settings()
    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        print("[warn] SUPABASE_URL or SUPABASE_KEY missing; cannot fetch scored_posts")
        return []

    client = get_client()

    # Debug: show wtp_signal distribution for score >= 50
    debug_response = (
        client.table("scored_posts")
        .select("id, title, score, wtp_signal")
        .gte("score", 50)
        .execute()
    )
    debug_data = debug_response.data or []
    print(f"[debug] scored_posts with score>=50: {len(debug_data)}")
    for row in debug_data[:10]:
        print(
            f"  score={row.get('score')} wtp={row.get('wtp_signal')} | "
            f"{str(row.get('title', ''))[:50]}"
        )

    response = (
        client.table("scored_posts")
        .select("*")
        .gte("score", 50)
        .in_("wtp_signal", ["strong", "weak"])
        .execute()
    )
    data = response.data or []
    return data if isinstance(data, list) else []


def fetch_existing_blueprint_ids() -> set[str]:
    """Fetch ids that already exist in the blueprints table."""

    settings = get_settings()
    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        print("[warn] SUPABASE_URL or SUPABASE_KEY missing; cannot fetch blueprints")
        return set()

    client = get_client()
    response = client.table("blueprints").select("id").execute()
    data = response.data or []
    if not isinstance(data, list):
        return set()
    return {str(item["id"]) for item in data if isinstance(item, dict) and item.get("id")}


def save_blueprints(blueprints: list[dict[str, Any]]) -> None:
    """Upsert blueprint records into the blueprints table."""

    if not blueprints:
        return

    settings = get_settings()
    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        print("[warn] SUPABASE_URL or SUPABASE_KEY missing; skipping blueprints upsert")
        return

    client = get_client()
    client.table("blueprints").upsert(blueprints, on_conflict="id").execute()
