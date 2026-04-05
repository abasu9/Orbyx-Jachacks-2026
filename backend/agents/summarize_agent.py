"""
Summarize Agent
Generates a structured AI evaluation report for a single employee:

1. Fetches GitHub org-level metrics (PRs, merge rate, commits, reviews)
2. Sends metrics + user data to OpenAI for a structured evaluation
3. Stores the JSON report in local storage
4. Updates the user's report_id in InsForge DB
5. Returns the evaluation to the caller
"""

import json
import logging
import os
import time
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, Optional

import httpx

from insforge_client import list_rows, update_row

logger = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"
GITHUB_PAT = os.getenv("GITHUB_PAT", "")
OPENAI_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
STORAGE_PATH = os.getenv("STORAGE_PATH", os.path.join(os.path.dirname(__file__), "..", "storage"))


def _gh_headers() -> Dict[str, str]:
    h = {"Accept": "application/vnd.github+json"}
    if GITHUB_PAT:
        h["Authorization"] = f"Bearer {GITHUB_PAT}"
    return h


def _gh_get(url: str, **kwargs) -> Any:
    try:
        r = httpx.get(url, headers=_gh_headers(), timeout=15, **kwargs)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPError as e:
        logger.warning("GitHub API error for %s: %s", url, e)
        return None


def fetch_github_metrics(username: str) -> Dict[str, Any]:
    """Collect org-agnostic GitHub metrics for a user (mirrors the serverless github.ts logic)."""

    # Total PRs authored
    prs_data = _gh_get(
        f"{GITHUB_API}/search/issues",
        params={"q": f"is:pr author:{username}", "per_page": "30"},
    ) or {}
    total_prs = prs_data.get("total_count", 0)
    pr_items = prs_data.get("items", [])

    # Merged PRs
    merged_data = _gh_get(
        f"{GITHUB_API}/search/issues",
        params={"q": f"is:pr author:{username} is:merged", "per_page": "1"},
    ) or {}
    merged_prs = merged_data.get("total_count", 0)
    merge_rate = round(merged_prs / total_prs, 2) if total_prs > 0 else 0

    # Reviews by user
    reviewed_data = _gh_get(
        f"{GITHUB_API}/search/issues",
        params={"q": f"is:pr reviewed-by:{username}", "per_page": "1"},
    ) or {}
    reviewed_prs = reviewed_data.get("total_count", 0)
    review_participation_rate = round(min(reviewed_prs / total_prs, 1), 2) if total_prs > 0 else 0

    # Commits (search API)
    commits_data = _gh_get(
        f"{GITHUB_API}/search/commits",
        params={"q": f"author:{username}", "sort": "author-date", "order": "desc", "per_page": "100"},
    ) or {}
    total_commits = commits_data.get("total_count", 0)
    commit_frequency_per_week = round(total_commits / 52)

    commit_items = commits_data.get("items", [])
    commit_dates = set()
    for item in commit_items:
        try:
            d = item["commit"]["author"]["date"][:10]
            commit_dates.add(d)
        except (KeyError, TypeError):
            pass
    active_days_ratio = round(min(len(commit_dates) / 90, 1), 2)

    # PR detail sampling for size + impact + languages
    total_additions = 0
    high_impact_count = 0
    languages = set()
    sampled = 0

    for pr in pr_items[:10]:
        repo_url = pr.get("repository_url", "")
        if not repo_url:
            continue
        parts = repo_url.rstrip("/").split("/")
        if len(parts) < 2:
            continue
        owner, repo = parts[-2], parts[-1]
        detail = _gh_get(f"{GITHUB_API}/repos/{owner}/{repo}/pulls/{pr['number']}")
        if not detail:
            continue
        sampled += 1
        size = detail.get("additions", 0) + detail.get("deletions", 0)
        total_additions += size
        if size > 500:
            high_impact_count += 1
        lang = (detail.get("base") or {}).get("repo", {}).get("language")
        if lang:
            languages.add(lang)

    avg_pr_size = round(total_additions / sampled) if sampled > 0 else 0
    high_impact_pr_ratio = round(high_impact_count / sampled, 2) if sampled > 0 else 0

    return {
        "total_prs": total_prs,
        "merged_prs": merged_prs,
        "merge_rate": merge_rate,
        "avg_pr_size": avg_pr_size,
        "review_participation_rate": review_participation_rate,
        "commit_frequency_per_week": commit_frequency_per_week,
        "active_days_ratio": active_days_ratio,
        "top_languages": list(languages)[:3],
        "high_impact_pr_ratio": high_impact_pr_ratio,
    }


EVALUATION_PROMPT = """You are an engineering performance analyst.

You are given structured contribution metrics for a software engineer.
Your task is to produce an objective, evidence-based evaluation.
Use third person addressing eg. "John demonstrates a steady pattern of commits..."

User Info: {user_json}
GitHub Metrics: {metrics_json}

STRICT RULES:
- Use ONLY the provided metrics. Do NOT assume or infer missing data.
- If a signal is missing, explicitly acknowledge the limitation.
- Do NOT generalize beyond what the data supports.
- Avoid vague or generic statements.
- Every assessment must be justified using specific metrics.
- Be concise, analytical, and neutral in tone.

EVALUATION DIMENSIONS:
1. Impact — Use: total_prs, merged_prs, merge_rate, high_impact_pr_ratio
2. Code Quality Signals — Use: avg_pr_size, merge_rate
3. Collaboration — Use: review_participation_rate
4. Consistency — Use: commit_frequency_per_week, active_days_ratio
5. Seniority Signal — Infer cautiously from high_impact_pr_ratio, review_participation_rate, merge_rate

Return ONLY valid JSON. No markdown. No extra text. Follow this exact schema:
{{
  "summary": "string",
  "impact_assessment": {{ "level": "low | medium | high", "justification": "string" }},
  "code_quality_signals": {{ "assessment": "string", "risk_flags": ["string"] }},
  "collaboration": {{ "assessment": "string", "review_strength": "low | medium | high" }},
  "consistency": {{ "assessment": "string", "pattern": "sporadic | steady | highly_consistent" }},
  "seniority_signal": {{ "level": "junior | mid | senior | staff", "confidence": 0.0 }},
  "strengths": ["string"],
  "weaknesses": ["string"]
}}"""


def _ai_evaluate(user_data: Dict, metrics: Dict) -> Dict[str, Any]:
    """Call OpenAI for structured evaluation."""
    if not OPENAI_API_KEY:
        return {"summary": "No API key configured", "error": True}

    prompt = EVALUATION_PROMPT.format(
        user_json=json.dumps(user_data, default=str),
        metrics_json=json.dumps(metrics, default=str),
    )

    resp = httpx.post(
        OPENAI_URL,
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": OPENAI_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "max_tokens": 800,
        },
        timeout=60,
    )
    resp.raise_for_status()
    content = resp.json()["choices"][0]["message"]["content"].strip()

    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
        content = content.strip()

    return json.loads(content)


def _store_report(employee_id: str, report: Dict) -> str:
    """Save report JSON to local storage. Returns the report filename."""
    storage = Path(STORAGE_PATH)
    storage.mkdir(parents=True, exist_ok=True)
    filename = f"{employee_id}-{int(time.time() * 1000)}.json"
    (storage / filename).write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    return filename


def run(employee_id: str) -> Dict[str, Any]:
    """Generate a full summary report for a single employee by ID."""

    # 1. Fetch employee from DB
    rows = list_rows("users", params={"id": f"eq.{employee_id}"})
    if not rows:
        raise ValueError(f"Employee {employee_id} not found")
    user = rows[0]

    gh_username = user.get("gh_username")
    if not gh_username:
        raise ValueError(f"Employee {user.get('name')} has no gh_username")

    # 2. Collect GitHub metrics
    logger.info("[SummarizeAgent] Fetching GitHub metrics for %s", gh_username)
    metrics = fetch_github_metrics(gh_username)

    # 3. AI evaluation
    logger.info("[SummarizeAgent] Generating AI evaluation for %s", user.get("name"))
    user_info = {
        "name": user.get("name"),
        "level": user.get("level"),
        "pip": user.get("pip"),
        "joiningdate": user.get("joiningdate"),
        "gh_username": gh_username,
    }
    evaluation = _ai_evaluate(user_info, metrics)

    # 4. Store report
    report = {
        "employee_id": employee_id,
        "name": user.get("name"),
        "generated_at": datetime.now().isoformat(),
        "github_metrics": metrics,
        "evaluation": evaluation,
    }
    report_id = _store_report(employee_id, report)

    # 5. Update DB with new report_id
    update_row("users", employee_id, {"report_id": report_id})

    logger.info("[SummarizeAgent] Report stored: %s", report_id)
    return report
