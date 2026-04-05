"""
Agent 1 - Data Collection Agent
Fetches all employee records from InsForge DB via REST API
(name, level, apr, pip, gh_username, roi) for downstream processing.
"""

import logging
from typing import Any, Dict, List

from insforge_client import list_rows

logger = logging.getLogger(__name__)


def run() -> List[Dict[str, Any]]:
    """Fetch all employees from the InsForge database via REST API.

    Returns a list of dicts, each containing:
        id, name, level, apr (jsonb), pip, gh_username, joiningdate, roi, ranking
    """
    logger.info("[DataAgent] Fetching all employees from InsForge REST API...")

    rows = list_rows("users")

    employees = []
    for r in rows:
        employees.append({
            "id": str(r.get("id", "")),
            "name": r.get("name", ""),
            "level": r.get("level"),
            "apr": r.get("apr") or r.get(" apr"),  # DB column has leading space
            "pip": r.get("pip", 0),
            "gh_username": r.get("gh_username"),
            "joiningdate": r.get("joiningdate", ""),
            "roi": r.get("roi"),
            "ranking": r.get("ranking"),
            "report_id": r.get("report_id"),
        })

    logger.info("[DataAgent] Fetched %d employees.", len(employees))
    return employees
