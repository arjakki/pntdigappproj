# ED AI Agent — Mercy Regional Medical Center

A full-stack AI-powered Emergency Department clinical decision-support system. A LangChain ReAct agent backed by Claude Sonnet 4.6 uses the **Model Context Protocol (MCP)** to query a live SQLite patient database. The web interface provides a real-time census dashboard, an AI chat assistant, and a patient intake form.

---

## Table of Contents

1. [Project Architecture](#1-project-architecture)
2. [Application Components](#2-application-components)
3. [Technology Stack](#3-technology-stack)
4. [Prerequisites](#4-prerequisites)
5. [Installation](#5-installation)
6. [Configuration](#6-configuration)
7. [Running the Application](#7-running-the-application)
8. [Using the Application](#8-using-the-application)
9. [API Reference](#9-api-reference)
10. [MCP Tools Reference](#10-mcp-tools-reference)
11. [Database Schema](#11-database-schema)
12. [Generating the Architecture PDF](#12-generating-the-architecture-pdf)

---

## 1. Project Architecture

```
Browser (HTML/JS)
       │
       ▼
┌─────────────────────────────────────────┐
│          FastAPI  (app/main.py)         │
│   GET /          → Dashboard            │
│   GET /chat      → AI Chat              │
│   GET /intake    → Patient Intake Form  │
│   POST /api/chat → AI Agent endpoint    │
│   POST /api/intake → DB write endpoint  │
│   GET /api/stats → Live census stats    │
│   GET /api/patients → Patient list      │
└────────────┬────────────────────────────┘
             │  per-request agent session
             ▼
┌────────────────────────────────────────┐
│      LangChain ReAct Agent             │
│      (LangGraph + Claude Sonnet 4.6)   │
│                                        │
│  Reason → Select Tool → Observe → …   │
└────────────┬───────────────────────────┘
             │  Model Context Protocol (stdio)
             ▼
┌────────────────────────────────────────┐
│      FastMCP Server                    │
│      (mcp_server/server.py)            │
│                                        │
│  9 registered tools (list below)       │
└────────────┬───────────────────────────┘
             │  SQLite queries
             ▼
┌────────────────────────────────────────┐
│      SQLite Database                   │
│      (data/ed_database.db)             │
│                                        │
│  7 tables, 10 patients, sample census  │
└────────────────────────────────────────┘
```

### Request Flow — AI Chat

1. Browser POSTs `{"message": "..."}` to `/api/chat`
2. FastAPI calls `agent_session()` — an async context manager that spawns the MCP subprocess
3. `MultiServerMCPClient` connects to `mcp_server/server.py` over **stdio**
4. `load_mcp_tools()` introspects the MCP server and returns LangChain-compatible tool wrappers
5. `create_react_agent(llm, tools, prompt=SYSTEM_PROMPT)` builds the ReAct loop
6. The agent iterates: **Reason → Call tool → Observe result → Reason again** until it has an answer
7. FastAPI returns `{"response": "...", "tool_calls": [...]}` to the browser

### Request Flow — Patient Intake

1. Browser POSTs form data as JSON to `/api/intake`
2. FastAPI validates the payload with Pydantic (`IntakeRequest`)
3. Database is written directly (upsert patient + insert triage record)
4. `IntakeResponse` is returned with the new `patient_id` and `triage_id`

---

## 2. Application Components

### 2.1 FastAPI Backend — `app/`

| File | Purpose |
|------|---------|
| `app/main.py` | Application entry point; mounts static files, defines all routes, calls `init_database()` on startup |
| `app/agent.py` | Defines `agent_session()` — the per-request context manager that wires together MCP client, tools, LLM, and ReAct agent |
| `app/database.py` | SQLite schema creation and full sample data seed (10 patients, 12 triage records, vitals, allergies, meds, history, contacts) |
| `app/models.py` | Pydantic v2 models for all request/response payloads |

**`app/agent.py` — how the agent is constructed per request:**

```python
@asynccontextmanager
async def agent_session() -> AsyncIterator:
    client = MultiServerMCPClient(_MCP_CONFIG)
    async with client.session("ed_database") as session:
        tools = await load_mcp_tools(session)
        llm = ChatAnthropic(model="claude-sonnet-4-6", temperature=0, max_tokens=2048)
        agent = create_react_agent(llm, tools, prompt=SYSTEM_PROMPT)
        yield agent
```

The MCP subprocess is started per request and cleanly terminated when the context exits. This avoids state leakage between requests.

### 2.2 MCP Server — `mcp_server/server.py`

A standalone Python process that speaks the **Model Context Protocol** over stdio. FastMCP registers each function decorated with `@mcp.tool()` as a callable tool. The agent can discover and call these at runtime.

**9 registered tools:**

| Tool | Description |
|------|-------------|
| `list_tables` | Returns all table names in the database |
| `describe_table` | Returns column schema and row count for a named table |
| `execute_query` | Runs any read-only `SELECT` statement (write operations are blocked) |
| `get_patient_by_mrn` | Full patient record: demographics, allergies, meds, history, last 5 visits |
| `get_todays_patients` | All arrivals on a given date, sorted by ESI level then time |
| `get_triage_statistics` | ESI distribution, arrival mode breakdown, total census |
| `get_critical_patients` | All ESI 1–2 patients with vitals and allergy summary |
| `search_patients` | Fuzzy search by first name, last name, or MRN fragment |
| `insert_patient_intake` | Write a new patient + triage record to the database |

### 2.3 Frontend — `frontend/`

Three single-page HTML files, no build step required — served as static files by FastAPI.

#### `frontend/index.html` — Dashboard

- Fetches `/api/stats` and `/api/patients` on load
- Displays live census counts: total patients, today's census, critical patients (ESI 1–2)
- Renders an ESI distribution bar chart using inline SVG/CSS
- Patient table with color-coded ESI badges and abnormal vital highlighting
- Auto-refreshes every 60 seconds

#### `frontend/chat.html` — AI Chat

- Full-page chat interface with message history
- Sidebar listing 8 quick-query suggestions and all 9 MCP tool names
- Sends POST requests to `/api/chat` and streams the response text
- Displays "thinking..." indicator while agent is reasoning
- Shows tool-call chips (e.g., `get_critical_patients`, `execute_query`) for each response
- Supports markdown-style formatting in responses

#### `frontend/intake.html` — Patient Intake Form (ED-001)

- Complete Emergency Department intake form with all clinical fields:
  - Patient demographics (name, DOB, MRN, sex, language, address, phone)
  - Arrival information (date, time, mode, triage nurse)
  - Clinical fields (chief complaint, ESI level, disposition)
  - Medical/surgical history, allergies, current medications
  - Emergency contact
- Auto-generates MRN (`MRN-YYYY-NNN`) and pre-fills arrival date/time
- Overrides native form submit — POSTs JSON to `/api/intake`
- Shows toast notification on success, redirects to dashboard after 2 seconds

### 2.4 Database — `data/ed_database.db`

SQLite database (MySQL-compatible SQL syntax) created and seeded automatically on first startup.

**Sample data:**

- 10 patients across the Boston metro area
- 12 triage records spanning 3 dates (10 on the sample census date 2025-04-28)
- 12 vital sign sets with realistic clinical values
- 8 allergy records with severity and reaction type
- 19 medication records
- 19 medical history entries (PMH and PSH)
- 10 emergency contacts

### 2.5 Architecture PDF — `generate_pdf.py`

A standalone ReportLab script that generates `ED_AI_Agent_Architecture.pdf` — a 13+ page technical document with:

- Cover page with layered architecture preview diagram
- 5-layer system architecture diagram
- Chat request sequence diagram (7 actors)
- Patient intake data flow with decision logic
- MCP tool chain detail with protocol arrows
- Component-level file dependency map
- Full entity-relationship diagram (7 tables)
- Deployment architecture diagram
- Complete API reference, MCP tools, DB schema, and technology stack tables

---

## 3. Technology Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Language | Python | 3.10+ |
| Web framework | FastAPI | ≥ 0.115 |
| ASGI server | Uvicorn | ≥ 0.32 |
| AI framework | LangChain + LangGraph | ≥ 0.3 / ≥ 0.2 |
| LLM | Claude Sonnet 4.6 (Anthropic) | — |
| LLM client | `langchain-anthropic` | ≥ 0.3 |
| Protocol | Model Context Protocol (MCP) | ≥ 1.3 |
| MCP client | `langchain-mcp-adapters` | ≥ 0.2 |
| MCP server | FastMCP (`mcp.server.fastmcp`) | ≥ 1.3 |
| Database | SQLite (MySQL-compatible SQL) | built-in |
| Data validation | Pydantic v2 | ≥ 2.0 |
| Environment | python-dotenv | ≥ 1.0 |
| PDF generation | ReportLab | ≥ 4.0 |
| Frontend | HTML5 / CSS3 / Vanilla JS | — |

---

## 4. Prerequisites

Before installing, ensure you have the following:

- **Python 3.10 or higher** — [python.org/downloads](https://www.python.org/downloads/)
  ```
  python --version   # must show 3.10+
  ```

- **pip** — included with Python; upgrade if needed:
  ```
  python -m pip install --upgrade pip
  ```

- **Anthropic API Key** — create one at [console.anthropic.com](https://console.anthropic.com)
  - The key must have access to `claude-sonnet-4-6`
  - Starts with `sk-ant-...`

- **Git** — [git-scm.com](https://git-scm.com) (for cloning)

- **Internet access** — required at runtime for Anthropic API calls

---

## 5. Installation

Follow these steps exactly, in order.

### Step 1 — Clone the repository

```bash
git clone https://github.com/arjakki/pntdigappproj.git
cd pntdigappproj
```

### Step 2 — Create a virtual environment

Using a virtual environment keeps the project's dependencies isolated from your system Python.

**Windows:**
```cmd
python -m venv .venv
.venv\Scripts\activate
```

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

You should see `(.venv)` at the start of your terminal prompt after activation.

### Step 3 — Install Python dependencies

```bash
pip install -r requirements.txt
```

This installs the following packages (and their transitive dependencies):

| Package | What it does |
|---------|-------------|
| `fastapi` | Web framework and REST API layer |
| `uvicorn[standard]` | ASGI server with WebSocket and HTTP/2 support |
| `aiofiles` | Async file I/O for static file serving |
| `httpx` | Async HTTP client used internally by FastAPI |
| `python-dotenv` | Loads `.env` file into environment variables |
| `mcp` | Model Context Protocol SDK (includes `FastMCP`) |
| `langchain` | Core LangChain framework |
| `langchain-anthropic` | LangChain integration for Claude models |
| `langchain-mcp-adapters` | Bridges MCP tools into LangChain tool format |
| `langgraph` | ReAct agent runtime and graph execution |
| `anthropic` | Low-level Anthropic API client |
| `pydantic` | Request/response data validation |

Verify the installation:
```bash
pip show fastapi langchain langgraph mcp
```

### Step 4 — Configure your API key

Copy the environment template:

**Windows:**
```cmd
copy .env.example .env
```

**macOS / Linux:**
```bash
cp .env.example .env
```

Open `.env` in any text editor and replace the placeholder:

```env
ANTHROPIC_API_KEY=sk-ant-api03-your-actual-key-here
HOST=0.0.0.0
PORT=8000
```

> **Never commit `.env` to version control.** It is listed in `.gitignore` by default.

### Step 5 — Verify the database path

The database is auto-created on first startup at `data/ed_database.db`. No manual database setup is required. If the `data/` directory doesn't exist, Python will create it.

To confirm the database initialises correctly, you can do a dry run:

```bash
python -c "from app.database import init_database; init_database(); print('OK')"
```

Expected output:
```
Database initialized with 10 patients and sample ED records
OK
```

### Step 6 — (Optional) Install PDF generation dependencies

If you want to re-generate the architecture PDF, install ReportLab:

```bash
pip install reportlab
```

---

## 6. Configuration

All configuration is done via the `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | *(required)* | Your Anthropic API key starting with `sk-ant-` |
| `HOST` | `0.0.0.0` | Interface to bind the server to |
| `PORT` | `8000` | TCP port the server listens on |

To run on a different port:
```env
PORT=9000
```

---

## 7. Running the Application

### Quick start (Windows)

Double-click `start.bat` or run from a terminal:

```cmd
start.bat
```

### Quick start (macOS / Linux)

```bash
chmod +x start.sh
./start.sh
```

### Manual start

With the virtual environment activated:

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The `--reload` flag restarts the server automatically whenever you edit a Python file. Remove it in production.

### Verify the server is running

Open a browser and navigate to:

| URL | Page |
|-----|------|
| `http://localhost:8000` | Census Dashboard |
| `http://localhost:8000/chat` | AI Chat Assistant |
| `http://localhost:8000/intake` | Patient Intake Form |
| `http://localhost:8000/docs` | Interactive API docs (Swagger UI) |
| `http://localhost:8000/redoc` | API docs (ReDoc) |

Expected startup output:
```
INFO:     Database initialized with 10 patients and sample ED records
INFO:     ED AI Agent ready - MCP server will start per-request
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### Stopping the server

Press `Ctrl+C` in the terminal where the server is running.

---

## 8. Using the Application

### Dashboard (`/`)

The dashboard loads automatically on startup. It shows:

- **Total Patients** — all patients in the database
- **Today's Census** — arrivals on the sample date (2025-04-28)
- **Critical Patients** — ESI 1 or ESI 2 patients today
- **ESI Distribution** — bar chart of patients by triage level
- **Patient Table** — all of today's patients with vitals, sorted by ESI level

ESI color coding: ESI 1 (red), ESI 2 (orange), ESI 3 (yellow), ESI 4 (green), ESI 5 (blue).

### AI Chat (`/chat`)

Type any clinical question in natural language. Example queries:

- `Show me all critical patients with their vitals`
- `What are the allergies for patient MRN-2024-001?`
- `Who arrived by ambulance today?`
- `List all patients on warfarin`
- `What is today's ESI distribution?`
- `Search for patients named Johnson`

The agent will select the appropriate MCP tools, query the database, and return a formatted clinical summary. Tool calls used to generate each response are displayed as chips below the message.

### Patient Intake Form (`/intake`)

Fill in the form fields to register a new patient:

1. MRN is auto-generated (you can override it)
2. Arrival date and time are pre-filled to the current timestamp
3. Complete all required fields (marked with an asterisk)
4. Click **Submit Intake** — a success toast appears and the page redirects to the dashboard
5. The new patient is immediately queryable via the AI chat

---

## 9. API Reference

### `POST /api/chat`

Send a message to the AI agent.

**Request:**
```json
{
  "message": "Show me all critical patients"
}
```

**Response:**
```json
{
  "response": "Here are the current ESI 1-2 patients...",
  "tool_calls": ["get_critical_patients", "execute_query"]
}
```

**Error responses:**
- `503` — `ANTHROPIC_API_KEY` not set or invalid
- `500` — Agent or MCP server error

---

### `POST /api/intake`

Submit a new patient intake record.

**Request body fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `mrn` | string | yes | Medical Record Number |
| `first_name` | string | yes | Patient first name |
| `last_name` | string | yes | Patient last name |
| `dob` | string | yes | Date of birth (YYYY-MM-DD) |
| `age` | integer | yes | Age in years |
| `biological_sex` | string | yes | Male / Female / Intersex |
| `phone` | string | no | Contact phone number |
| `address` | string | no | Street address |
| `language` | string | no | Preferred language (default: English) |
| `arrival_date` | string | yes | Arrival date (YYYY-MM-DD) |
| `arrival_time` | string | yes | Arrival time (HH:MM) |
| `arrival_mode` | string | yes | How patient arrived |
| `chief_complaint` | string | yes | Chief complaint verbatim |
| `esi_level` | integer | yes | ESI triage level 1–5 |
| `disposition` | string | yes | Initial disposition |
| `triage_nurse` | string | yes | Triage nurse name |

**Response:**
```json
{
  "success": true,
  "patient_id": 11,
  "triage_id": 13
}
```

---

### `GET /api/stats`

Returns live census statistics for the dashboard.

**Response:**
```json
{
  "total_patients": 10,
  "today_census": 10,
  "critical_patients": 4,
  "esi_distribution": [
    {"esi_level": 1, "count": 1},
    {"esi_level": 2, "count": 4}
  ]
}
```

---

### `GET /api/patients`

Returns all patients for today's census date with their first vital sign reading.

**Response:** Array of patient objects with demographics, triage data, and vitals.

---

## 10. MCP Tools Reference

The MCP server (`mcp_server/server.py`) exposes these tools to the AI agent via the Model Context Protocol. The agent selects and calls these autonomously based on the user's question.

| Tool | Input Parameters | Returns |
|------|-----------------|---------|
| `list_tables` | *(none)* | JSON array of table names |
| `describe_table` | `table_name: str` | Column schema + row count |
| `execute_query` | `sql: str` | Query results as JSON (SELECT only) |
| `get_patient_by_mrn` | `mrn: str` | Full patient record with history |
| `get_todays_patients` | `date: str` (default: `2025-04-28`) | All arrivals sorted by ESI |
| `get_triage_statistics` | `date: str` (optional) | ESI distribution + arrival modes |
| `get_critical_patients` | *(none)* | All ESI 1–2 patients with vitals |
| `search_patients` | `query: str` | Matching patients with visit counts |
| `insert_patient_intake` | 16 fields (see intake API) | `{success, patient_id, triage_id}` |

The MCP server runs as a **child process** of the FastAPI server, communicating over stdin/stdout using the MCP wire protocol. It is spawned per chat request and terminates when the request completes.

---

## 11. Database Schema

Seven tables, all created automatically on first startup:

```
patients                    (root entity)
├── triage_records          (one per ED visit)
│   └── vital_signs         (multiple readings per visit)
├── allergies               (one per allergen)
├── medications             (current meds)
├── medical_history         (PMH / PSH)
└── emergency_contacts      (one per patient)
```

### `patients`

| Column | Type | Notes |
|--------|------|-------|
| `id` | INTEGER PK | Auto-increment |
| `mrn` | TEXT UNIQUE | Medical Record Number |
| `first_name` | TEXT | — |
| `last_name` | TEXT | — |
| `dob` | TEXT | YYYY-MM-DD |
| `age` | INTEGER | — |
| `biological_sex` | TEXT | Male / Female / Intersex |
| `phone` | TEXT | — |
| `address` | TEXT | — |
| `language` | TEXT | Default: English |
| `ssn_last4` | TEXT | Last 4 digits only |
| `created_at` | TEXT | UTC timestamp |

### `triage_records`

| Column | Type | Notes |
|--------|------|-------|
| `id` | INTEGER PK | — |
| `patient_id` | INTEGER FK | References `patients.id` |
| `mrn` | TEXT | Denormalized for fast lookup |
| `arrival_date` | TEXT | YYYY-MM-DD |
| `arrival_time` | TEXT | HH:MM |
| `arrival_mode` | TEXT | EMS / Walk-in / Private Vehicle |
| `chief_complaint` | TEXT | — |
| `esi_level` | INTEGER | 1 (critical) to 5 (non-urgent) |
| `disposition` | TEXT | Resuscitation Room / Bay / Fast Track |
| `triage_nurse` | TEXT | — |
| `triage_note` | TEXT | Full clinical note |
| `isolation_type` | TEXT | None / Droplet / Contact / Airborne |
| `fall_risk` | TEXT | Low / Moderate / High |
| `code_status` | TEXT | Full Code / DNR |
| `created_at` | TEXT | UTC timestamp |

### `vital_signs`

| Column | Type | Notes |
|--------|------|-------|
| `id` | INTEGER PK | — |
| `triage_id` | INTEGER FK | References `triage_records.id` |
| `patient_id` | INTEGER FK | References `patients.id` |
| `reading_number` | INTEGER | 1 = first reading |
| `reading_time` | TEXT | HH:MM |
| `blood_pressure` | TEXT | e.g. `"128/78"` |
| `heart_rate` | INTEGER | bpm |
| `respiratory_rate` | INTEGER | breaths/min |
| `temperature` | REAL | Fahrenheit |
| `spo2` | INTEGER | % oxygen saturation |
| `o2_source` | TEXT | RA / NC / NRB / BiPAP |
| `glucose` | INTEGER | mg/dL |
| `gcs` | INTEGER | Glasgow Coma Scale (3–15) |

Abnormal thresholds used by the agent: HR > 100 or < 60, SBP < 90 or > 180, SpO2 < 95%, Temp > 38.3°C / < 36°C.

### `allergies`

| Column | Type |
|--------|------|
| `id` | INTEGER PK |
| `patient_id` | INTEGER FK |
| `allergen` | TEXT |
| `reaction_type` | TEXT |
| `severity` | TEXT (Mild / Moderate / Severe) |
| `notes` | TEXT |

### `medications`

| Column | Type |
|--------|------|
| `id` | INTEGER PK |
| `patient_id` | INTEGER FK |
| `medication_name` | TEXT |
| `dose` | TEXT |
| `frequency` | TEXT |
| `route` | TEXT (PO / IV / SubQ / Inhaled) |
| `last_taken` | TEXT |

### `medical_history`

| Column | Type |
|--------|------|
| `id` | INTEGER PK |
| `patient_id` | INTEGER FK |
| `condition_name` | TEXT |
| `category` | TEXT (PMH = Past Medical, PSH = Past Surgical) |
| `year_diagnosed` | INTEGER |

### `emergency_contacts`

| Column | Type |
|--------|------|
| `id` | INTEGER PK |
| `patient_id` | INTEGER FK |
| `name` | TEXT |
| `relationship` | TEXT |
| `phone` | TEXT |

---

## 12. Generating the Architecture PDF

The repository includes a pre-generated `ED_AI_Agent_Architecture.pdf`. To regenerate it after making changes:

```bash
# Install ReportLab if not already installed
pip install reportlab

# Run the generator
python generate_pdf.py
```

Output: `ED_AI_Agent_Architecture.pdf` in the project root (~13 pages).

The PDF includes 8 programmatically drawn architecture diagrams:

- Cover page with system overview
- 5-layer system architecture
- Chat request sequence (7 actors)
- Patient intake data flow
- MCP tool chain and protocol detail
- Component-level file dependency graph
- Full ER diagram for all 7 tables
- Deployment architecture

---

## Project Structure

```
pntdigappproj/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI routes and lifespan
│   ├── agent.py         # LangChain agent + MCP session wiring
│   ├── database.py      # SQLite schema + sample data seed
│   └── models.py        # Pydantic request/response models
├── mcp_server/
│   ├── __init__.py
│   └── server.py        # FastMCP server with 9 database tools
├── frontend/
│   ├── index.html       # Census dashboard
│   ├── chat.html        # AI chat interface
│   └── intake.html      # Patient intake form (ED-001)
├── data/
│   └── ed_database.db   # SQLite DB (auto-created, git-ignored)
├── generate_pdf.py      # ReportLab architecture PDF generator
├── ED_AI_Agent_Architecture.pdf
├── requirements.txt
├── .env.example
├── .gitignore
├── start.bat            # Windows one-click startup
└── start.sh             # macOS/Linux one-click startup
```

---

## Troubleshooting

**`503 AI agent unavailable`** — `ANTHROPIC_API_KEY` is missing or still set to the placeholder in `.env`. Open `.env` and add your real key.

**`Address already in use`** on port 8000 — Another process is using the port. Either stop it or change `PORT=9000` in `.env`.

**`ModuleNotFoundError`** — The virtual environment is not activated, or `pip install -r requirements.txt` was not run. Activate the venv and re-run the install step.

**Intake form shows error toast** — Check the terminal for the Python traceback. Most commonly a missing required field or a duplicate MRN.

**Agent response is slow (5–10s)** — Normal. The MCP subprocess starts fresh per request (adds ~2–3s) and each LLM call adds latency. The agent may also make multiple tool calls before answering.
