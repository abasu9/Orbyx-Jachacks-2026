import logging
import os
import traceback

from dotenv import load_dotenv

# Ensure .env is loaded from the same directory as this file (backend/)
_this_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_this_dir, ".env"))

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from routes import pipeline
from agents.orchestrator import run_pipeline
from insforge_client import list_rows

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")

app = FastAPI(title="Jachacks-2026")

@app.get("/")
def read_root():
    return {"message": "Welcome to Jachacks-2026 API"}


@app.post("/handle")
def handle():
    """
    Trigger the full agentic pipeline:
    Fetches all employees, processes each one-by-one through
    Data → Math → GitHub+AI → Update agents, waiting for each
    DB write to succeed before moving to the next employee.
    Returns a success summary when all are done.
    """
    try:
        result = run_pipeline()
        return result
    except Exception as exc:
        tb = traceback.format_exc()
        logging.error("Pipeline error:\n%s", tb)
        return JSONResponse(status_code=500, content={"error": str(exc), "traceback": tb})


@app.get("/employees")
def get_employees():
    """Fetch all employees from InsForge DB for the analytics page."""
    try:
        rows = list_rows("users")
        # Normalize the " apr" key (DB column has a leading space)
        for row in rows:
            if " apr" in row:
                row["apr"] = row.pop(" apr")
        return rows
    except Exception as exc:
        return JSONResponse(status_code=500, content={"error": str(exc)})


app.include_router(pipeline.router, prefix="/pipeline", tags=["pipeline"])
