"""
Orchestrator
Runs the 4-agent pipeline with concurrent workers:

  1. Data Agent   → bulk-fetch all employees
  2. ThreadPool   → per-employee: Math → GitHub+AI → Update DB
     Each thread operates on its own employee dict (no shared mutable state).
     Thread-safe counters use threading.Lock.
     On DB-write failure the employee's ranking/roi are NOT committed,
     so a partial run is safe to re-run.
"""

import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List

from agents import data_agent, math_agent, github_agent, update_agent

logger = logging.getLogger(__name__)

MAX_WORKERS = 10  # stay well within GitHub's secondary rate-limit


def _process_employee(emp: Dict[str, Any], index: int, total: int) -> Dict[str, Any]:
    """Run math → github → update for a single employee. Returns a summary dict.
    Each invocation works on its own `emp` dict — no shared state."""
    name = emp.get("name", "Unknown")
    logger.info("── [%d/%d] Processing: %s ──", index, total, name)

    # Snapshot original values so we can revert on error
    orig_ranking = emp.get("ranking")
    orig_roi = emp.get("roi")
    orig_github_score = emp.get("github_score")
    orig_report_id = emp.get("report_id")

    try:
        # Step 2: Math Agent — pure computation, no I/O
        math_agent.compute_ranking(emp)

        # Step 3: GitHub Agent — HTTP + LLM (I/O-bound, benefits from threading)
        github_agent.run(emp)

        # Step 4: Update Agent — persist to DB
        update_agent.run(emp)

        logger.info("  ✓ %s done (ranking=%.4f, roi=%.4f)",
                     name, emp.get("ranking", 0), emp.get("roi", 0))
        return {
            "id": emp.get("id"),
            "name": name,
            "ranking": emp.get("ranking"),
            "roi": emp.get("roi"),
            "github_score": emp.get("github_score"),
            "status": "success",
        }

    except Exception as exc:
        # Revert in-memory values so the dict stays clean
        emp["ranking"] = orig_ranking
        emp["roi"] = orig_roi
        emp["github_score"] = orig_github_score
        emp["report_id"] = orig_report_id
        logger.error("  ✗ %s FAILED (reverted): %s", name, exc)
        return {
            "id": emp.get("id"),
            "name": name,
            "ranking": None,
            "roi": None,
            "github_score": None,
            "status": f"failed: {exc}",
        }


def run_pipeline() -> Dict[str, Any]:
    """Execute the full agentic pipeline and return a result summary."""
    t0 = time.time()
    results: Dict[str, Any] = {
        "status": "running",
        "total": 0,
        "processed": 0,
        "failed": 0,
        "skipped": 0,
        "employees": [],
    }

    # ── Step 1: Bulk data collection ─────────────────────────────────────
    logger.info("═══ Step 1: Data Agent — fetching all employees ═══")
    employees = data_agent.run()
    results["total"] = len(employees)

    if not employees:
        logger.warning("No employees found — pipeline aborted.")
        results["status"] = "empty"
        return results

    logger.info("═══ Processing %d employees with %d workers ═══",
                len(employees), MAX_WORKERS)

    # ── Step 2-4: Concurrent per-employee processing ─────────────────────
    lock = threading.Lock()
    employee_summaries: List[Dict[str, Any]] = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {
            pool.submit(_process_employee, emp, i, len(employees)): emp
            for i, emp in enumerate(employees, 1)
        }

        for future in as_completed(futures):
            summary = future.result()  # _process_employee never raises
            with lock:
                employee_summaries.append(summary)
                if summary["status"] == "success":
                    results["processed"] += 1
                else:
                    results["failed"] += 1

    results["employees"] = employee_summaries
    elapsed = round(time.time() - t0, 2)
    results["status"] = "completed"
    results["elapsed_seconds"] = elapsed

    logger.info("═══ Pipeline finished in %.2fs — %d/%d processed, %d failed ═══",
                elapsed, results["processed"], results["total"], results["failed"])
    return results
