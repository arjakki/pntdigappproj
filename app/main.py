import os
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.agent import agent_session
from app.database import DB_PATH, init_database
from app.models import ChatRequest, ChatResponse, IntakeRequest, IntakeResponse

load_dotenv()

FRONTEND = Path(__file__).parent.parent / "frontend"
ROOT = Path(__file__).parent.parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_database()
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key or api_key == "your-anthropic-api-key-here":
        print("WARNING: ANTHROPIC_API_KEY not set — AI chat will return 503")
    else:
        print("ED AI Agent ready - MCP server will start per-request")
    yield


app = FastAPI(title="ED AI Agent", lifespan=lifespan)

# ─── Static files ─────────────────────────────────────────────────────────────

app.mount("/static", StaticFiles(directory=str(FRONTEND)), name="static")


@app.get("/")
async def dashboard():
    return FileResponse(FRONTEND / "index.html")


@app.get("/chat")
async def chat_page():
    return FileResponse(FRONTEND / "chat.html")


@app.get("/intake")
async def intake_page():
    return FileResponse(FRONTEND / "intake.html")


@app.get("/business-case")
async def business_case_page():
    return FileResponse(FRONTEND / "business_case.html")


# ─── API ──────────────────────────────────────────────────────────────────────

@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key or api_key == "your-anthropic-api-key-here":
        raise HTTPException(
            status_code=503,
            detail="AI agent unavailable — set ANTHROPIC_API_KEY in .env and restart",
        )
    try:
        async with agent_session() as agent:
            result = await agent.ainvoke({"messages": [{"role": "user", "content": req.message}]})
        messages = result.get("messages", [])
        tool_calls = [
            m.name
            for m in messages
            if hasattr(m, "name") and m.name and hasattr(m, "type") and m.type == "tool"
        ]
        response_text = messages[-1].content if messages else "No response generated."
        if isinstance(response_text, list):
            response_text = " ".join(
                block.get("text", "") if isinstance(block, dict) else str(block)
                for block in response_text
            )
        return ChatResponse(response=response_text, tool_calls=list(dict.fromkeys(tool_calls)))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/intake", response_model=IntakeResponse)
async def submit_intake(req: IntakeRequest):
    try:
        with sqlite3.connect(str(DB_PATH)) as conn:
            cur = conn.cursor()
            existing = cur.execute(
                "SELECT id FROM patients WHERE mrn = ?", (req.mrn,)
            ).fetchone()
            if existing:
                pid = existing[0]
            else:
                cur.execute(
                    "INSERT INTO patients (mrn,first_name,last_name,dob,age,biological_sex,phone,address,language) VALUES (?,?,?,?,?,?,?,?,?)",
                    (req.mrn, req.first_name, req.last_name, req.dob, req.age, req.biological_sex, req.phone, req.address, req.language),
                )
                pid = cur.lastrowid
            cur.execute(
                "INSERT INTO triage_records (patient_id,mrn,arrival_date,arrival_time,arrival_mode,chief_complaint,esi_level,disposition,triage_nurse) VALUES (?,?,?,?,?,?,?,?,?)",
                (pid, req.mrn, req.arrival_date, req.arrival_time, req.arrival_mode, req.chief_complaint, req.esi_level, req.disposition, req.triage_nurse),
            )
            tid = cur.lastrowid
            conn.commit()
        return IntakeResponse(success=True, patient_id=pid, triage_id=tid)
    except Exception as exc:
        return IntakeResponse(success=False, error=str(exc))


@app.get("/api/stats")
async def get_stats():
    with sqlite3.connect(str(DB_PATH)) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        total = cur.execute("SELECT COUNT(*) AS n FROM patients").fetchone()["n"]
        today = cur.execute(
            "SELECT COUNT(*) AS n FROM triage_records WHERE arrival_date = '2025-04-28'"
        ).fetchone()["n"]
        critical = cur.execute(
            "SELECT COUNT(*) AS n FROM triage_records WHERE esi_level <= 2 AND arrival_date = '2025-04-28'"
        ).fetchone()["n"]
        by_esi = cur.execute(
            "SELECT esi_level, COUNT(*) AS count FROM triage_records WHERE arrival_date = '2025-04-28' GROUP BY esi_level ORDER BY esi_level"
        ).fetchall()
    return {
        "total_patients": total,
        "today_census": today,
        "critical_patients": critical,
        "esi_distribution": [dict(r) for r in by_esi],
    }


@app.get("/api/patients")
async def list_patients():
    with sqlite3.connect(str(DB_PATH)) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        rows = cur.execute(
            """
            SELECT t.mrn, p.first_name, p.last_name, p.age, p.biological_sex,
                   t.arrival_time, t.chief_complaint, t.esi_level,
                   t.disposition, t.triage_nurse,
                   v.blood_pressure, v.heart_rate, v.spo2
            FROM triage_records t
            JOIN patients p ON t.patient_id = p.id
            LEFT JOIN vital_signs v ON t.id = v.triage_id AND v.reading_number = 1
            WHERE t.arrival_date = '2025-04-28'
            ORDER BY t.esi_level ASC, t.arrival_time ASC
            """
        ).fetchall()
    return [dict(r) for r in rows]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=True,
    )
