"""Blueprint generation using Ollama and scored pain points."""

from __future__ import annotations

import concurrent.futures
import json
import re
import threading
import time
import traceback
from collections import Counter
from datetime import datetime, timezone
from typing import Any

import requests
from saas_niche.config import get_settings

from saas_niche.db.client import (
    fetch_blueprint_candidates,
    fetch_existing_blueprint_ids,
    save_blueprints,
)

VALID_REVENUE_MODELS = {
    "subscription",
    "usage_based",
    "freemium",
    "one_time",
    "marketplace",
}
VALID_TECH_COMPLEXITIES = {"low", "medium", "high"}
VALID_MARKET_SIZES = {"small", "medium", "large"}
VALID_COMPETITION_LEVELS = {"low", "medium", "high"}
SYSTEM_PROMPT = (
    "You are a SaaS business strategist. Given a Reddit "
    "pain point, generate a concrete monetization blueprint. "
    "Return only a single valid JSON object, no explanation, "
    "no markdown, no code blocks."
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _truncate_body(body: str, limit: int = 500) -> str:
    return body[:limit].strip()


def _build_prompt(post: dict[str, Any]) -> str:
    return (
        "Analyze this specific Reddit pain point and generate \n"
        "a realistic SaaS blueprint. Think carefully about \n"
        "what kind of product actually fits this problem.\n\n"
        f'Title: {post.get("title", "")}\n'
        f'Category: {post.get("category", "")}\n'
        f'Profession: {post.get("profession", "")}\n'
        f'Body: {_truncate_body(str(post.get("body", "")))}\n'
        f'Score: {post.get("score", 0)}\n\n'
        "Rules for each field:\n"
        '- revenue_model: think carefully. \n'
        '  "usage_based" if it involves processing/API calls\n'
        '  "marketplace" if it connects buyers and sellers\n'
        '  "one_time" if it\'s a simple utility tool\n'
        '  "freemium" if network effects matter\n'
        '  "subscription" only if ongoing value is clear\n'
        "  \n"
        '- tech_complexity:\n'
        '  "low" if it\'s forms, dashboards, simple CRUD\n'
        '  "high" if it needs ML, real-time, complex integrations\n'
        '  "medium" for everything else\n'
        "  \n"
        "- pricing: research what similar tools charge.\n"
        "  Simple utilities: $9-19/mo\n"
        "  Workflow tools: $29-79/mo  \n"
        "  Enterprise tools: $99-499/mo\n"
        "  One-time tools: $49-199 lifetime\n"
        "  \n"
        "- mvp_features: be specific to THIS problem.\n"
        '  Not generic features like "dashboard" or "analytics"\n'
        '  Real features like "auto-sync Stripe to QuickBooks"\n'
        "  \n"
        "- landing_copy: must mention the specific pain,\n"
        '  not generic like "manage your workflow better"\n'
        '  Good: "Stop copy-pasting Stripe data into spreadsheets"\n\n'
        "Return a JSON object with exactly these fields:\n"
        "{\n"
        '  "target_audience": "one sentence describing who has this problem and their context",\n'
        '  "problem_summary": "2 sentences explaining the core problem clearly",\n'
        '  "solution": "2-3 sentences describing the SaaS product that solves this",\n'
        '  "revenue_model": one of ["subscription", "usage_based", "freemium", "one_time", "marketplace"],\n'
        '  "pricing": "concrete pricing e.g. $29/mo starter, $79/mo pro, $199/mo agency",\n'
        '  "mvp_features": ["feature 1", "feature 2", "feature 3"] max 4 features,\n'
        '  "tech_complexity": one of ["low", "medium", "high"],\n'
        '  "landing_copy": "one punchy headline for the landing page under 12 words",\n'
        '  "market_size": one of ["small", "medium", "large"],\n'
        '  "competition": one of ["low", "medium", "high"]\n'
        "}\n\n"
        "Return only valid JSON, no explanation."
    )


def _parse_blueprint(raw_text: str) -> dict[str, Any]:
    parsed = json.loads(raw_text)
    if not isinstance(parsed, dict):
        raise ValueError("Blueprint response is not a JSON object.")

    revenue_model = str(parsed.get("revenue_model", ""))
    tech_complexity = str(parsed.get("tech_complexity", ""))
    market_size = str(parsed.get("market_size", ""))
    competition = str(parsed.get("competition", ""))
    mvp_features = parsed.get("mvp_features", [])

    if revenue_model not in VALID_REVENUE_MODELS:
        raise ValueError(f"Invalid revenue_model: {revenue_model}")
    if tech_complexity not in VALID_TECH_COMPLEXITIES:
        raise ValueError(f"Invalid tech_complexity: {tech_complexity}")
    if market_size not in VALID_MARKET_SIZES:
        raise ValueError(f"Invalid market_size: {market_size}")
    if competition not in VALID_COMPETITION_LEVELS:
        raise ValueError(f"Invalid competition: {competition}")
    if not isinstance(mvp_features, list) or len(mvp_features) > 4:
        raise ValueError("mvp_features must be a list with at most 4 entries.")

    return {
        "target_audience": str(parsed.get("target_audience", "")).strip(),
        "problem_summary": str(parsed.get("problem_summary", "")).strip(),
        "solution": str(parsed.get("solution", "")).strip(),
        "revenue_model": revenue_model,
        "pricing": str(parsed.get("pricing", "")).strip(),
        "mvp_features": [str(item).strip() for item in mvp_features],
        "tech_complexity": tech_complexity,
        "landing_copy": str(parsed.get("landing_copy", "")).strip(),
        "market_size": market_size,
        "competition": competition,
    }


def _call_ollama(prompt: str, settings: Any) -> str:
    response = requests.post(
        f"{settings.OLLAMA_BASE_URL}/api/generate",
        json={
            "model": settings.OLLAMA_BLUEPRINT_MODEL,
            "prompt": prompt,
            "format": "json",
            "stream": False,
            "options": {"temperature": 0.2, "num_predict": 1500},
        },
        timeout=300,
    )
    response.raise_for_status()
    return response.json()["response"]


def _generate_blueprint(post: dict[str, Any]) -> dict[str, Any] | None:
    user_prompt = _build_prompt(post)
    prompt = f"{SYSTEM_PROMPT}\n\n{user_prompt}"

    for attempt in range(2):
        try:
            result_text = _call_ollama(prompt, get_settings())
            print(f"[debug] blueprint raw response: {result_text[:800]}")
            time.sleep(6)
            raw = result_text.strip()
            if raw.startswith("```"):
                raw = re.sub(r"^```[a-z]*\n?", "", raw)
                raw = re.sub(r"\n?```$", "", raw.strip())
            blueprint_data = json.loads(raw)
            return _parse_blueprint(json.dumps(blueprint_data))
        except Exception as e:
            print(f"[error] blueprint generation failed: {str(e)}")
            traceback.print_exc()
            if attempt == 0:
                continue
            return None

    return None


def _build_record(post: dict[str, Any], blueprint: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": post.get("id"),
        "title": post.get("title", ""),
        "category": post.get("category", ""),
        "profession": post.get("profession", ""),
        "score": post.get("score", 0),
        "target_audience": blueprint["target_audience"],
        "problem_summary": blueprint["problem_summary"],
        "solution": blueprint["solution"],
        "revenue_model": blueprint["revenue_model"],
        "pricing": blueprint["pricing"],
        "mvp_features": blueprint["mvp_features"],
        "tech_complexity": blueprint["tech_complexity"],
        "landing_copy": blueprint["landing_copy"],
        "market_size": blueprint["market_size"],
        "competition": blueprint["competition"],
        "generated_at": _utc_now(),
    }


def _chunk_posts(posts: list[dict[str, Any]], num_chunks: int) -> list[list[dict[str, Any]]]:
    chunks: list[list[dict[str, Any]]] = [[] for _ in range(num_chunks)]
    for index, post in enumerate(posts):
        chunks[index % num_chunks].append(post)
    return [chunk for chunk in chunks if chunk]


def _process_chunk(
    worker_id: int,
    posts: list[dict[str, Any]],
    write_lock: threading.Lock,
) -> tuple[int, Counter[str], Counter[str]]:
    generated_count = 0
    revenue_counter: Counter[str] = Counter()
    complexity_counter: Counter[str] = Counter()

    for post in posts:
        blueprint = _generate_blueprint(post)
        if blueprint is None:
            continue

        record = _build_record(post, blueprint)
        with write_lock:
            save_blueprints([record])
        generated_count += 1
        revenue_counter[record["revenue_model"]] += 1
        complexity_counter[record["tech_complexity"]] += 1
        print(f'[worker-{worker_id}] "{post.get("title", "")}" → done')

    return generated_count, revenue_counter, complexity_counter


def run() -> None:
    """Generate SaaS blueprints for high-scoring pain points."""

    candidates = fetch_blueprint_candidates()
    if not candidates:
        print("No blueprint candidates found.")
        return

    existing_ids = fetch_existing_blueprint_ids()
    pending_posts = [
        post for post in candidates if str(post.get("id", "")) not in existing_ids
    ]
    if not pending_posts:
        print("No new blueprint candidates found.")
        return

    revenue_counter: Counter[str] = Counter()
    complexity_counter: Counter[str] = Counter()
    generated_count = 0
    write_lock = threading.Lock()
    chunks = _chunk_posts(pending_posts, 1)

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        futures = [
            executor.submit(_process_chunk, worker_id, chunk, write_lock)
            for worker_id, chunk in enumerate(chunks, start=1)
        ]
        for future in concurrent.futures.as_completed(futures):
            chunk_generated, chunk_revenue, chunk_complexity = future.result()
            generated_count += chunk_generated
            revenue_counter.update(chunk_revenue)
            complexity_counter.update(chunk_complexity)

    print(f"Total blueprints generated: {generated_count}")
    print(f"Revenue model breakdown: {dict(revenue_counter)}")
    print(f"Tech complexity breakdown: {dict(complexity_counter)}")
