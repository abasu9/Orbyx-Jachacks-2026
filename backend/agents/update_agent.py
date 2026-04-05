"""
Agent 4 - Update Agent
1. Stores each employee's full report (GitHub summary, ranking, ROI, details)
   as a JSON file in local object storage.
2. Writes ranking + roi back to the InsForge DB via REST API in one PATCH.
3. Waits for write success before returning.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict

from insforge_client import update_row

logger = logging.getLogger(__name__)

STORAGE_PATH = os.getenv("STORAGE_PATH", os.path.join(os.path.dirname(__file__), "..", "storage"))


def _ensure_storage() -> Path:
    p = Path(STORAGE_PATH)
    p.mkdir(parents=True, exist_ok=True)
    return p


def _store_report(employee: Dict[str, Any], storage_dir: Path) -> str:
    """Write the full report to a JSON file. Returns the file path."""
    filename = f"{employee['id']}.json"
    filepath = storage_dir / filename

    payload = {
        "id": employee["id"],
        "name": employee["name"],
        "level": employee.get("level"),
        "ranking": employee.get("ranking"),
        "roi": employee.get("roi"),
        "github_score": employee.get("github_score"),
        "github_reasoning": employee.get("github_reasoning", ""),
        "math_details": employee.get("_math_details", {}),
        "roi_details": employee.get("_roi_details", {}),
    }

    filepath.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return str(filepath)


def run(employee: Dict[str, Any]) -> Dict[str, Any]:
    """
    Persist a single employee's results:
    - Save full report to local storage
    - PATCH ranking + roi to InsForge DB
    - Raises on failure so caller knows the write failed.
    """
    row_id = employee.get("id")
    name = employee.get("name", "Unknown")

    if not row_id:
        logger.warning("[UpdateAgent] Employee has no id — skipped.")
        return employee

    # ── Save report to local storage ─────────────────────────────────────
    storage_dir = _ensure_storage()
    path = _store_report(employee, storage_dir)
    employee["report_path"] = path
    logger.info("[UpdateAgent] Report saved: %s", path)

    # ── PATCH ranking + roi to InsForge DB ───────────────────────────────
    patch_data: Dict[str, Any] = {}
    if employee.get("ranking") is not None:
        patch_data["ranking"] = employee["ranking"]
    if employee.get("roi") is not None:
        patch_data["roi"] = employee["roi"]
    if employee.get("report_id") is not None:
        patch_data["report_id"] = employee["report_id"]

    if patch_data:
        try:
            update_row("users", row_id, patch_data)
            logger.info("[UpdateAgent] DB updated for %s: %s", name, patch_data)
            employee["db_write_status"] = "success"
        except Exception as exc:
            logger.error("[UpdateAgent] DB write FAILED for %s: %s", name, exc)
            employee["db_write_status"] = f"failed: {exc}"
            raise  # propagate so orchestrator knows
    else:
        logger.info("[UpdateAgent] Nothing to patch for %s.", name)
        employee["db_write_status"] = "skipped"

    return employee
