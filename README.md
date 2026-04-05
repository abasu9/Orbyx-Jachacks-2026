<p align="center">
  <img src="frontend/public/cull-log.jpeg" alt="CULL Logo" width="120" />
</p>

<h1 align="center">CULL — Agentic AI for Employee Analytics</h1>

<p align="center">
  <strong>A social-impact AI platform that evaluates, ranks, and uplifts employee performance using autonomous agents and graph-based pipeline traversal.</strong>
</p>

<p align="center">
  Built at <strong>JacHacks 2026</strong> &nbsp;|&nbsp; MIT License
</p>

---

## The Problem

Organizations struggle to objectively evaluate employee performance. Manual reviews are biased, slow, and inconsistent. High-performing employees go unrecognized while struggling ones miss early intervention. There is no unified system that combines **internal KPIs**, **external contribution signals** (GitHub), and **AI-powered analysis** into a single actionable view.

## Our Solution

**CULL** is an agentic AI platform that autonomously collects, analyzes, and visualizes employee performance data. It combines internal metrics (APR, PIP counts) with real-world engineering contributions from GitHub, processed through a **directed acyclic graph (DAG) of specialized AI agents** to produce fair, evidence-based evaluations.

### Social Impact

- **Upholds high performers** — objective data ensures top contributors are recognized, not overlooked
- **Early intervention** — identifies employees who may need support before formal reviews
- **Removes bias** — AI-driven scoring based on measurable signals, not subjective opinion
- **Transparency** — every ranking and score is traceable back to the data that produced it

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CULL Frontend                            │
│              React + Vite + Chart.js                            │
│   ┌──────────┐  ┌───────────┐  ┌────────────────────────┐      │
│   │  Login   │  │ Dashboard │  │      Analytics          │      │
│   │          │  │ (Trigger) │  │ Heatmap + Table + Modal │      │
│   └──────────┘  └─────┬─────┘  └───────────┬────────────┘      │
└────────────────────────┼────────────────────┼───────────────────┘
                         │ POST /handle       │ POST /summarize/{id}
                         ▼                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI Backend                              │
│                                                                 │
│  ┌──────────────── Agent Pipeline (DAG) ──────────────────┐     │
│  │                                                        │     │
│  │   ┌─────────────┐                                      │     │
│  │   │ Data Agent   │── fetch all employees ──┐            │     │
│  │   └─────────────┘                          │            │     │
│  │                                            ▼            │     │
│  │                              ┌─── ThreadPool (10) ───┐  │     │
│  │                              │                       │  │     │
│  │                              │  ┌──────────────┐     │  │     │
│  │                              │  │  Math Agent   │    │  │     │
│  │                              │  │  (Ranking)    │    │  │     │
│  │                              │  └──────┬───────┘    │  │     │
│  │                              │         ▼            │  │     │
│  │                              │  ┌──────────────┐    │  │     │
│  │                              │  │ GitHub Agent  │    │  │     │
│  │                              │  │ + AI Scoring  │    │  │     │
│  │                              │  └──────┬───────┘    │  │     │
│  │                              │         ▼            │  │     │
│  │                              │  ┌──────────────┐    │  │     │
│  │                              │  │ Update Agent  │    │  │     │
│  │                              │  │ (DB Write)    │    │  │     │
│  │                              │  └──────────────┘    │  │     │
│  │                              │                      │  │     │
│  │                              │  × 46 employees      │  │     │
│  │                              └──────────────────────┘  │     │
│  └────────────────────────────────────────────────────────┘     │
│                                                                 │
│  ┌─────────────────┐                                            │
│  │ Summarize Agent  │── on-demand per employee                  │
│  │ (GitHub Metrics  │                                           │
│  │  + AI Eval)      │                                           │
│  └─────────────────┘                                            │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                    ┌──────────┴──────────┐
                    ▼                     ▼
           ┌──────────────┐     ┌─────────────────┐
           │  InsForge DB  │     │  GitHub REST API │
           │  (PostgreSQL) │     │  + OpenAI API    │
           └──────────────┘     └─────────────────┘
```

---

## Agentic AI — How It Works

CULL implements a **multi-agent pipeline** where each agent is a specialized, autonomous unit with a single responsibility. The agents are composed into a **directed acyclic graph (DAG)** and orchestrated with concurrent execution.

### The 4-Agent Pipeline

| Agent | Role | Input | Output |
|-------|------|-------|--------|
| **Data Agent** | Bulk-fetches all employee records from InsForge DB | — | List of employee dicts |
| **Math Agent** | Computes a normalized ranking (0–1) from APR scores and PIP count | Employee dict | `ranking` field (0–1) |
| **GitHub Agent** | Collects GitHub activity + calls OpenAI for a contribution score | Employee dict + ranking | `github_score`, `roi` fields |
| **Update Agent** | Persists results back to DB, stores JSON report | Employee dict with scores | DB row updated |

### Graph-Based Traversal

The pipeline follows a **DAG traversal pattern**:

```
Data Agent (root)
     │
     ├──→ Math Agent ──→ GitHub Agent ──→ Update Agent   (Employee 1)
     ├──→ Math Agent ──→ GitHub Agent ──→ Update Agent   (Employee 2)
     ├──→ Math Agent ──→ GitHub Agent ──→ Update Agent   (Employee 3)
     │    ...
     └──→ Math Agent ──→ GitHub Agent ──→ Update Agent   (Employee N)
```

- **Root node** (Data Agent) fans out to N parallel branches
- Each branch is a **linear chain** of 3 agents executed sequentially per employee
- Branches run concurrently via `ThreadPoolExecutor(max_workers=10)`
- Thread safety: each thread operates on its own employee dict — no shared mutable state
- Atomic rollback: if any agent fails, the employee's in-memory values are reverted to their original state

### The 5th Agent — Summarize Agent

A standalone agent triggered on-demand per employee. It:
1. Fetches GitHub org-level metrics (PR merge rate, commit frequency, review participation, impact ratio)
2. Sends metrics to OpenAI with a structured evaluation prompt
3. Returns a comprehensive report: impact assessment, code quality signals, collaboration, consistency, seniority inference, strengths/weaknesses

### AI Scoring

- **Math Agent**: Weighted APR average normalized to 0–1, PIP penalty (0.80^pip), consistency bonus from variance analysis
- **GitHub Agent**: OpenAI `gpt-4o-mini` scores GitHub activity 0–1 based on commit frequency, PR quality, repo diversity
- **ROI Calculation**: `(ranking × 0.9 + github_score × 0.1) / salary_proxy × tenure_factor`

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 19 + Vite 8 + Chart.js (scatter heatmap) |
| **Backend** | Python 3.12 + FastAPI + Uvicorn |
| **Database** | InsForge BaaS (managed PostgreSQL) |
| **AI** | OpenAI GPT-4o-mini (scoring + evaluation) |
| **GitHub Data** | GitHub REST API v3 with PAT auth |
| **Concurrency** | `concurrent.futures.ThreadPoolExecutor` |
| **Serverless** | InsForge Edge Functions (TypeScript + Octokit) |
| **UI Support** | Lovable for rapid component prototyping |

---

## Jac Language — What We Tried

We initially explored using **Jac** (Jaseci's next-gen language) for the entire frontend and agent logic. Jac's walker-based graph traversal model was a natural fit for our agent DAG — each agent could be a node, and walkers would traverse the graph triggering computation.

### Why We Moved Away

- **Chart.js integration**: Jac's frontend capabilities couldn't support the interactive Chart.js scatter heatmap we needed for the analytics visualization
- **Ecosystem maturity**: The React + Vite ecosystem offered faster iteration for the hackathon timeline, with Chart.js, react-chartjs-2, and react-router-dom working out of the box
- **Compromise**: We kept the **graph-based DAG traversal concept** from Jac's architecture and implemented it in Python with ThreadPoolExecutor, preserving the walker-like pattern where each employee "walks" through the agent graph

The Jac-inspired architecture is visible in how our orchestrator fans out from a single root node into parallel per-employee chains — a direct analog of Jac's walker traversal model.

---

## InsForge Usage

CULL uses **InsForge** as its Backend-as-a-Service (BaaS) platform:

- **Database**: Managed PostgreSQL via REST API (`GET/POST/PATCH /api/database/records/{table}`)
- **Auth**: API key-based authentication (`Bearer` token)
- **Storage**: Blob storage bucket (`reports`) for JSON evaluation reports
- **AI Gateway**: `insforge.ai.chat.completions` for proxied LLM calls
- **Edge Functions**: Serverless TypeScript functions for isolated per-user report generation
- **SDK**: `@insforge/sdk` for TypeScript, raw REST for Python

---

## Lovable Usage

**Lovable** was used for rapid UI prototyping and component scaffolding:

- Quick iteration on the dark-theme design system (`#121212` bg, `#ee4f35` primary, `#fafafa` text)
- Layout scaffolding for the Login, Dashboard, and Analytics pages
- Component structure guidance that was then customized and integrated with React Router, Chart.js, and the API layer

---

## Project Structure

```
Jachacks-2026/
├── backend/
│   ├── agents/
│   │   ├── data_agent.py        # Fetches employees from DB
│   │   ├── math_agent.py        # APR + PIP → ranking (0-1)
│   │   ├── github_agent.py      # GitHub + AI → github_score + ROI
│   │   ├── update_agent.py      # Persists results to DB
│   │   ├── summarize_agent.py   # On-demand evaluation reports
│   │   └── orchestrator.py      # DAG orchestrator with ThreadPool
│   ├── insforge_client.py       # REST client for InsForge
│   ├── main.py                  # FastAPI app + endpoints
│   ├── schema.sql               # Database schema
│   └── seed_data.py             # Bulk employee data insert
├── frontend/
│   └── src/
│       ├── pages/
│       │   ├── Login.jsx         # Auth with demo credentials
│       │   ├── Dashboard.jsx     # Pipeline trigger (APR + PIP)
│       │   └── Analytics.jsx     # Heatmap + table + report modal
│       └── App.jsx               # Router
├── serverless/
│   └── user-report-generator/
│       ├── index.ts              # Edge function handler
│       └── github.ts             # GitHub metrics via Octokit
└── storage/                      # Local JSON report storage
```

---

## Getting Started

### Prerequisites

- Python 3.12+
- Node.js 18+
- InsForge account + API key
- GitHub PAT (personal access token)
- OpenAI API key

### Backend Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
cp .env.example .env          # Fill in API keys
python -m uvicorn main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev                   # Starts on http://localhost:5173
```

### Demo Login

```
Email:    emphr@company.in
Password: admin
```

---

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Health check |
| `POST` | `/handle` | Trigger full agent pipeline for all employees |
| `GET` | `/employees` | Fetch all employees for analytics |
| `POST` | `/summarize/{id}` | Generate AI evaluation report for one employee |

---

## Team

Built with ❤️ at **JacHacks 2026**

---

## License

[MIT](LICENSE) — Abhishek Basu, 2026
