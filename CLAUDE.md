# ED AI Agent — Adviava Regional Medical Center

## Project Overview

AI-powered clinical decision support web app for Emergency Department staff. Staff can query patient records, review critical cases, and submit intake forms through a natural language chat interface backed by a LangGraph ReAct agent.

**Live deployment**: AWS EC2 at `http://18.224.64.93:8000`

## Architecture

```
Frontend (vanilla HTML/CSS/JS)
    ↓ POST /api/chat
FastAPI (app/main.py)
    ↓ agent_session()
LangGraph ReAct Agent (app/agent.py)
    ↓ MCP stdio subprocess
MCP Server (mcp_server/server.py)
    ↓ SQLite queries
data/ed_database.db
```

- Each `/api/chat` request spawns a fresh MCP subprocess — stateless by design.
- The agent uses Claude Sonnet 4.6 via `langchain-anthropic` with `temperature=0`.
- Nine MCP tools expose the SQLite database to the agent.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11+, FastAPI, Uvicorn |
| AI agent | LangChain, LangGraph (ReAct), Claude Sonnet 4.6 |
| Tool protocol | MCP (Model Context Protocol) via `mcp` + `langchain-mcp-adapters` |
| Database | SQLite (`data/ed_database.db`) |
| Frontend | HTML5 / CSS3 / Vanilla JS (no build step) |
| PDF generation | ReportLab |

## Key Files

| File | Purpose |
|---|---|
| `app/agent.py` | Agent setup, `SYSTEM_PROMPT`, `agent_session()` context manager |
| `app/main.py` | FastAPI routes — `/`, `/chat`, `/intake`, `/business-case`, `/api/chat`, `/api/intake` |
| `app/models.py` | Pydantic models: `ChatRequest`, `ChatResponse`, `IntakeRequest`, `IntakeResponse` |
| `app/database.py` | `init_database()` — creates tables and seeds sample data |
| `mcp_server/server.py` | Nine MCP tools exposed to the agent via stdio |
| `frontend/` | Static HTML pages served directly by FastAPI |
| `data/ed_database.db` | SQLite database (auto-created on first run) |
| `.env` | `ANTHROPIC_API_KEY`, `HOST`, `PORT` (copy from `.env.example`) |

## Database Schema

Tables: `patients`, `triage_records`, `vital_signs`, `allergies`, `medications`, `medical_history`, `emergency_contacts`

Sample data: 10 patients, triage records dated `2025-04-28`.

ESI levels 1–5 (1 = most critical). Abnormal vitals thresholds used by the agent:
- HR > 100 or < 60
- SBP < 90 or > 180
- SpO2 < 95%
- Temp > 38.3°C or < 36°C

## MCP Tools (mcp_server/server.py)

| Tool | Description |
|---|---|
| `list_tables` | List all DB tables |
| `describe_table` | Schema + row count for a table |
| `execute_query` | Run arbitrary SELECT (no writes) |
| `get_patient_by_mrn` | Look up patient by MRN |
| `search_patients` | Search by name |
| `get_critical_patients` | ESI 1–2 patients |
| `get_today_census` | All patients with triage for a given date |
| `get_patient_full_record` | Complete record: vitals, allergies, meds, history |
| `insert_intake` | Write new patient + triage record |

## Development Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Reset the database (re-seeds sample data)
python -c "from app.database import init_database; init_database()"
```

Required env var: `ANTHROPIC_API_KEY` in `.env`.

## Frontend Pages

| Route | File | Purpose |
|---|---|---|
| `/` | `frontend/index.html` | Dashboard — live census table + ESI chart |
| `/chat` | `frontend/chat.html` | AI chat interface |
| `/intake` | `frontend/intake.html` | Patient registration form |
| `/business-case` | `frontend/business_case.html` | ROI / value analysis |

Static assets are mounted at `/static` → `frontend/`.

## Agent System Prompt

The system prompt lives in `app/agent.py:SYSTEM_PROMPT`. Key behaviors to preserve:
- Flag ESI 1–2 as critical
- Surface allergy warnings when discussing medications
- Use clinical formatting (tables/lists) for multi-patient results
- Remind staff to follow institutional protocols — never make autonomous clinical decisions

## Conventions

- No build step — edit HTML/CSS/JS directly in `frontend/`.
- Database is auto-initialized on startup; never commit `data/ed_database.db`.
- The MCP server runs as a subprocess — do not import it directly from app code.
- Keep the agent stateless; do not add session memory without explicit product approval.
- Model is pinned to `claude-sonnet-4-6`; update in `app/agent.py` when upgrading.
