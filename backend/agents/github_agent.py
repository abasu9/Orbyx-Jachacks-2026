"""
Agent 3 - GitHub + AI Scoring Agent

1. Fetches GitHub data (repos, commits, PRs, activity) for an employee.
2. Sends the collected data to an LLM (via OpenRouter) with a strict
   scoring prompt that returns a float 0-1 github_score.
3. Calculates ROI combining ranking, github_score, and tenure years.

If there is no gh_username → github_score is skipped and ROI is
calculated from ranking + tenure only.
"""

import asyncio
import json
import logging
import os
from datetime import date, datetime
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

# ─── Config ──────────────────────────────────────────────────────────────────
GITHUB_API = "https://api.github.com"
OPENAI_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
GITHUB_PAT = os.getenv("GITHUB_PAT", "")

MAX_REPOS = 5
MAX_COMMITS_PER_REPO = 5
MAX_PRS = 10

# ROI weights
RANKING_WEIGHT = 0.9       # 90% from performance ranking
GITHUB_WEIGHT = 0.1        # 10% from github contribution


# ─── GitHub data collection ──────────────────────────────────────────────────

def _gh_headers() -> Dict[str, str]:
    h = {"Accept": "application/vnd.github+json"}
    if GITHUB_PAT:
        h["Authorization"] = f"Bearer {GITHUB_PAT}"
    return h


async def _async_get(client: httpx.AsyncClient, url: str, **kwargs) -> Any:
    """Async GET wrapper that returns parsed JSON or fallback."""
    try:
        r = await client.get(url, headers=_gh_headers(), timeout=10, **kwargs)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPError:
        return None


def _collect_github_data(username: str) -> Dict[str, Any]:
    """Collect GitHub data with parallel HTTP calls for speed."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # Already inside an async context (uvicorn) — use nest_asyncio or thread
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, _collect_github_data_async(username)).result()
    else:
        return asyncio.run(_collect_github_data_async(username))


async def _collect_github_data_async(username: str) -> Dict[str, Any]:
    async with httpx.AsyncClient() as client:
        # Phase 1: fetch profile, repos, PRs in parallel
        profile_task = _async_get(client, f"{GITHUB_API}/users/{username}")
        repos_task = _async_get(
            client,
            f"{GITHUB_API}/users/{username}/repos",
            params={"sort": "pushed", "per_page": MAX_REPOS},
        )
        prs_task = _async_get(
            client,
            f"{GITHUB_API}/search/issues",
            params={
                "q": f"author:{username} type:pr",
                "sort": "created",
                "order": "desc",
                "per_page": MAX_PRS,
            },
        )

        profile, repos_raw, prs_raw = await asyncio.gather(
            profile_task, repos_task, prs_task
        )

        profile = profile or {}
        repos = repos_raw if isinstance(repos_raw, list) else []
        prs = (prs_raw or {}).get("items", []) if isinstance(prs_raw, dict) else []

        # Phase 2: fetch commits for all repos in parallel
        async def _get_commits(repo_data):
            owner = repo_data["owner"]["login"]
            name = repo_data["name"]
            data = await _async_get(
                client,
                f"{GITHUB_API}/repos/{owner}/{name}/commits",
                params={"author": username, "per_page": MAX_COMMITS_PER_REPO},
            )
            return repo_data, data if isinstance(data, list) else []

        commit_results = await asyncio.gather(
            *[_get_commits(r) for r in repos]
        )

    total_commits = 0
    repo_summaries = []
    for repo_data, commits in commit_results:
        total_commits += len(commits)
        repo_summaries.append({
            "name": f"{repo_data['owner']['login']}/{repo_data['name']}",
            "language": repo_data.get("language"),
            "description": repo_data.get("description", ""),
            "stars": repo_data.get("stargazers_count", 0),
            "forks": repo_data.get("forks_count", 0),
            "recent_commits": len(commits),
            "last_commit_msgs": [
                c.get("commit", {}).get("message", "").split("\n")[0]
                for c in commits[:5]
            ],
        })

    pr_summaries = []
    for pr in prs[:MAX_PRS]:
        pr_summaries.append({
            "title": pr.get("title", ""),
            "state": pr.get("state", ""),
            "repo": pr.get("repository_url", "").split("/")[-1] if pr.get("repository_url") else "",
            "created_at": pr.get("created_at", "")[:10],
        })

    return {
        "username": username,
        "public_repos": profile.get("public_repos", 0),
        "followers": profile.get("followers", 0),
        "following": profile.get("following", 0),
        "account_created": profile.get("created_at", "")[:10],
        "bio": profile.get("bio", ""),
        "total_recent_commits": total_commits,
        "repos_inspected": len(repo_summaries),
        "repos": repo_summaries,
        "total_prs_found": len(pr_summaries),
        "pull_requests": pr_summaries,
    }


# ─── AI scoring ─────────────────────────────────────────────────────────────

SCORING_PROMPT = """You are an employee GitHub contribution evaluator.

You will receive structured GitHub data about an employee. Based on this data,
assign a **github_score** from 0.0 to 1.0 that reflects their contribution level.

## Scoring Rules (apply consistently to ALL employees):
- **0.0-0.2**: Minimal/no activity — few commits, no PRs, dormant repos
- **0.2-0.4**: Low activity — occasional commits, rare PRs, mostly personal/toy repos
- **0.4-0.6**: Moderate — regular commits, some PRs, involvement in team repos
- **0.6-0.8**: Strong — frequent commits, active PR author/reviewer, meaningful contributions
- **0.8-1.0**: Exceptional — high volume quality commits, many PRs, cross-repo contributions,
               leadership in open-source, significant project impact

## Factors to consider:
1. **Commit frequency** — total recent commits across repos
2. **Pull Requests** — count, merged/open ratio, cross-repo involvement
3. **Repo diversity** — contributing to multiple repos vs just one
4. **Commit quality** — meaningful commit messages vs trivial changes
5. **Project impact** — stars, forks, language diversity
6. **Consistency** — even spread vs burst activity

## Output format:
Return ONLY a valid JSON object with exactly these fields:
{"github_score": <float 0.0-1.0>, "reasoning": "<one sentence justification>"}

Do NOT include any other text before or after the JSON."""


def _ai_score(github_data: Dict[str, Any]) -> Dict[str, Any]:
    """Call OpenRouter LLM to assign a github_score based on collected data."""
    if not OPENAI_API_KEY:
        logger.warning("[GitHubAgent] No OPENAI_API_KEY set — defaulting score to 0.5")
        return {"github_score": 0.5, "reasoning": "No API key configured; default score assigned."}

    user_msg = f"Evaluate this employee's GitHub activity:\n\n{json.dumps(github_data, indent=2, default=str)}"

    try:
        resp = httpx.post(
            OPENAI_URL,
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": OPENAI_MODEL,
                "messages": [
                    {"role": "system", "content": SCORING_PROMPT},
                    {"role": "user", "content": user_msg},
                ],
                "temperature": 0.1,
                "max_tokens": 200,
            },
            timeout=60,
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"].strip()

        # Parse the JSON response from LLM
        # Handle cases where LLM wraps in markdown code block
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        result = json.loads(content)
        score = float(result.get("github_score", 0.5))
        score = min(1.0, max(0.0, score))  # clamp
        return {
            "github_score": round(score, 4),
            "reasoning": result.get("reasoning", ""),
        }
    except Exception as exc:
        logger.error("[GitHubAgent] AI scoring failed: %s", exc)
        return {"github_score": 0.5, "reasoning": f"AI scoring failed: {exc}"}


# ─── ROI calculation ────────────────────────────────────────────────────────

def _tenure_years(joiningdate: str) -> float:
    """Years of tenure from joining date to today."""
    try:
        jd = datetime.strptime(str(joiningdate)[:10], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return 1.0  # default to 1 year if unparseable
    delta = date.today() - jd
    years = delta.days / 365.25
    return max(years, 0.1)  # at least 0.1 to avoid division issues


def calculate_roi(
    ranking: float,
    github_score: Optional[float],
    tenure_years: float,
) -> float:
    """
    Calculate ROI (Return on Investment).

    ROI reflects how much value the employee delivers relative to investment.
    - < 1.0 → underperforming for what the company pays
    - = 1.0 → performing at expected level
    - > 1.0 → overperforming (e.g., 2.0 = 200% return)

    Formula:
    - If github_score available:
        performance = (ranking * 0.9) + (github_score * 0.1)
    - If no github:
        performance = ranking

    ROI = (performance / 0.5) * tenure_factor

    Where:
    - performance / 0.5 normalizes so that ranking=0.5 (satisfactory) → base of 1.0
    - tenure_factor accounts for experience:
        - < 2 years: 0.9 (still ramping up, slight discount)
        - 2-4 years: 1.0 (expected performance)
        - > 4 years: slight boost up to 1.1 (experience premium)
    """
    if github_score is not None:
        performance = (ranking * RANKING_WEIGHT) + (github_score * GITHUB_WEIGHT)
    else:
        performance = ranking

    # Normalize: ranking 0.5 (satisfactory) should map to ROI ~1.0
    base_roi = performance / 0.5

    # Tenure factor
    if tenure_years < 2:
        tenure_factor = 0.9
    elif tenure_years <= 4:
        tenure_factor = 1.0
    else:
        tenure_factor = min(1.1, 1.0 + (tenure_years - 4) * 0.02)

    roi = round(base_roi * tenure_factor, 4)
    return roi


# ─── Main agent entry point ─────────────────────────────────────────────────

def run(employee: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a single employee:
    1. Collect GitHub data (if gh_username exists)
    2. Get AI github_score (if data collected)
    3. Calculate ROI
    Returns the enriched employee dict.
    """
    name = employee.get("name", "Unknown")
    gh_username = employee.get("gh_username")
    ranking = employee.get("ranking", 0.0) or 0.0
    joiningdate = employee.get("joiningdate", "")

    tenure = _tenure_years(joiningdate)
    github_score = None
    github_data = None
    ai_result = None

    # ── GitHub collection + AI scoring ───────────────────────────────────
    if gh_username:
        logger.info("[GitHubAgent] Collecting GitHub data for %s (@%s)...", name, gh_username)
        github_data = _collect_github_data(gh_username)
        employee["github_data"] = github_data

        logger.info("[GitHubAgent] Requesting AI score for %s...", name)
        ai_result = _ai_score(github_data)
        github_score = ai_result["github_score"]
        employee["github_score"] = github_score
        employee["github_reasoning"] = ai_result["reasoning"]

        logger.info("[GitHubAgent] %s: github_score=%.4f (%s)",
                    name, github_score, ai_result["reasoning"])
    else:
        logger.warning("[GitHubAgent] %s has no gh_username — skipping GitHub scoring.", name)
        employee["github_score"] = None
        employee["github_reasoning"] = "No GitHub username configured."
        employee["github_data"] = None

    # ── ROI calculation ──────────────────────────────────────────────────
    roi = calculate_roi(ranking, github_score, tenure)
    employee["roi"] = roi
    employee["_roi_details"] = {
        "ranking": ranking,
        "github_score": github_score,
        "tenure_years": round(tenure, 2),
        "has_github": gh_username is not None,
    }

    logger.info("[GitHubAgent] %s: ROI=%.4f (ranking=%.4f, gh=%.4f, tenure=%.1fy)",
                name, roi, ranking,
                github_score if github_score is not None else 0.0,
                tenure)

    return employee
