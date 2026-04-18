"""FastAPI app for browsing scored SaaS ideas and blueprints."""

from __future__ import annotations

from statistics import mean
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from saas_niche.config import get_settings
from saas_niche.db.client import get_client

app = FastAPI(title="SaasNiche API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _fetch_scored_posts() -> list[dict[str, Any]]:
    settings = get_settings()
    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        raise HTTPException(status_code=500, detail="Supabase configuration missing.")

    try:
        response = get_client().table("scored_posts").select("*").execute()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Database error: {exc}") from exc

    data = response.data or []
    return data if isinstance(data, list) else []


def _fetch_blueprints() -> dict[str, dict[str, Any]]:
    settings = get_settings()
    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        raise HTTPException(status_code=500, detail="Supabase configuration missing.")

    try:
        response = get_client().table("blueprints").select("*").execute()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Database error: {exc}") from exc

    data = response.data or []
    if not isinstance(data, list):
        return {}
    return {str(item["id"]): item for item in data if isinstance(item, dict) and item.get("id")}


def _merge_idea(post: dict[str, Any], blueprint: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": post.get("id"),
        "title": post.get("title", ""),
        "subreddit": post.get("subreddit", ""),
        "url": post.get("url", ""),
        "score": post.get("score", 0),
        "category": post.get("category", ""),
        "profession": post.get("profession", ""),
        "wtp_signal": post.get("wtp_signal", ""),
        "blueprint": blueprint,
    }


def _load_joined_ideas() -> list[dict[str, Any]]:
    posts = _fetch_scored_posts()
    blueprints = _fetch_blueprints()

    ideas: list[dict[str, Any]] = []
    for post in posts:
        blueprint = blueprints.get(str(post.get("id", "")))
        if blueprint is None:
            continue
        ideas.append(_merge_idea(post, blueprint))

    ideas.sort(key=lambda item: float(item.get("score", 0) or 0), reverse=True)
    return ideas


def _load_joined_details() -> list[dict[str, Any]]:
    posts = _fetch_scored_posts()
    blueprints = _fetch_blueprints()

    details: list[dict[str, Any]] = []
    for post in posts:
        blueprint = blueprints.get(str(post.get("id", "")))
        if blueprint is None:
            continue

        detail = dict(post)
        detail["blueprint"] = blueprint
        details.append(detail)

    details.sort(key=lambda item: float(item.get("score", 0) or 0), reverse=True)
    return details


@app.get("/")
def health_check() -> dict[str, Any]:
    ideas = _load_joined_ideas()
    return {"status": "ok", "total_ideas": len(ideas)}


@app.get("/ideas")
def list_ideas(
    category: str | None = None,
    profession: str | None = None,
    min_score: float = 0,
    wtp: str | None = None,
    limit: int = Query(default=20, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
) -> list[dict[str, Any]]:
    ideas = _load_joined_ideas()

    filtered = [
        idea
        for idea in ideas
        if (category is None or str(idea.get("category", "")) == category)
        and (profession is None or str(idea.get("profession", "")) == profession)
        and float(idea.get("score", 0) or 0) >= min_score
        and (wtp is None or str(idea.get("wtp_signal", "")) == wtp)
    ]
    return filtered[offset : offset + limit]


@app.get("/ideas/{idea_id}")
def get_idea(idea_id: str) -> dict[str, Any]:
    for idea in _load_joined_details():
        if str(idea.get("id", "")) == idea_id:
            return idea
    raise HTTPException(status_code=404, detail="Idea not found.")


@app.get("/stats")
def get_stats() -> dict[str, Any]:
    ideas = _load_joined_details()
    if not ideas:
        return {
            "total_ideas": 0,
            "avg_score": 0,
            "top_categories": {},
            "top_professions": {},
            "score_distribution": {"0-25": 0, "25-50": 0, "50-75": 0, "75-100": 0},
        }

    categories: dict[str, int] = {}
    professions: dict[str, int] = {}
    score_distribution = {"0-25": 0, "25-50": 0, "50-75": 0, "75-100": 0}

    for idea in ideas:
        category = str(idea.get("category", ""))
        profession = str(idea.get("profession", ""))
        categories[category] = categories.get(category, 0) + 1
        professions[profession] = professions.get(profession, 0) + 1

        score = float(idea.get("score", 0) or 0)
        if score < 25:
            score_distribution["0-25"] += 1
        elif score < 50:
            score_distribution["25-50"] += 1
        elif score < 75:
            score_distribution["50-75"] += 1
        else:
            score_distribution["75-100"] += 1

    ordered_categories = dict(
        sorted(categories.items(), key=lambda item: item[1], reverse=True)
    )
    ordered_professions = dict(
        sorted(professions.items(), key=lambda item: item[1], reverse=True)
    )

    return {
        "total_ideas": len(ideas),
        "avg_score": round(mean(float(idea.get("score", 0) or 0) for idea in ideas), 1),
        "top_categories": ordered_categories,
        "top_professions": ordered_professions,
        "score_distribution": score_distribution,
    }


@app.get("/top")
def top_ideas() -> list[dict[str, Any]]:
    return _load_joined_ideas()[:10]


def run() -> None:
    """Run the local API server."""

    uvicorn.run("saas_niche.api.main:app", host="0.0.0.0", port=8000, reload=True)
