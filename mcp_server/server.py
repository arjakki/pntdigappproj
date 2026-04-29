"""
ED MySQL MCP Server
Exposes Emergency Department database tools via the Model Context Protocol (stdio).
Backed by SQLite; same SQL dialect as MySQL for all queries used here.
"""
import json
import sqlite3
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

DB_PATH = Path(__file__).parent.parent / "data" / "ed_database.db"

mcp = FastMCP(
    "ED MySQL MCP Server",
    instructions="Emergency Department database assistant. Use these tools to query patient records, triage data, vitals, medications, and allergies.",
)


def _query(sql: str, params: tuple = ()) -> list[dict]:
    with sqlite3.connect(str(DB_PATH)) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]


def _exec(sql: str, params: tuple = ()) -> int:
    with sqlite3.connect(str(DB_PATH)) as conn:
        cur = conn.cursor()
        cur.execute(sql, params)
        conn.commit()
        return cur.lastrowid


# ─── Tools ────────────────────────────────────────────────────────────────────

@mcp.tool()
def list_tables() -> str:
    """List all tables in the Emergency Department database."""
    rows = _query("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    return json.dumps([r["name"] for r in rows])


@mcp.tool()
def describe_table(table_name: str) -> str:
    """Get schema and row count for a database table.

    Args:
        table_name: One of: patients, triage_records, vital_signs, allergies,
                    medications, medical_history, emergency_contacts
    """
    cols = _query(f"PRAGMA table_info({table_name})")
    cnt = _query(f"SELECT COUNT(*) AS n FROM {table_name}")
    return json.dumps({"columns": cols, "row_count": cnt[0]["n"]})


@mcp.tool()
def execute_query(sql: str) -> str:
    """Run a read-only SQL SELECT query on the ED database.

    Available tables: patients, triage_records, vital_signs, allergies,
    medications, medical_history, emergency_contacts

    Args:
        sql: A SQL SELECT statement
    """
    if not sql.strip().upper().startswith("SELECT"):
        return "Error: Only SELECT queries are permitted."
    try:
        return json.dumps(_query(sql), indent=2, default=str)
    except Exception as exc:
        return f"Query error: {exc}"


@mcp.tool()
def get_patient_by_mrn(mrn: str) -> str:
    """Get the complete record for a patient identified by MRN.

    Returns demographics, allergies, current medications, medical history,
    emergency contact, and the 5 most recent triage visits.

    Args:
        mrn: Medical Record Number, e.g. 'MRN-2024-001'
    """
    rows = _query("SELECT * FROM patients WHERE mrn = ?", (mrn,))
    if not rows:
        return f"No patient found with MRN: {mrn}"
    pid = rows[0]["id"]
    return json.dumps(
        {
            "patient": rows[0],
            "allergies": _query("SELECT * FROM allergies WHERE patient_id = ?", (pid,)),
            "medications": _query("SELECT * FROM medications WHERE patient_id = ?", (pid,)),
            "medical_history": _query(
                "SELECT * FROM medical_history WHERE patient_id = ? ORDER BY category, year_diagnosed",
                (pid,),
            ),
            "emergency_contact": _query(
                "SELECT * FROM emergency_contacts WHERE patient_id = ?", (pid,)
            ),
            "recent_visits": _query(
                """
                SELECT t.*, v.blood_pressure, v.heart_rate, v.temperature, v.spo2, v.gcs
                FROM triage_records t
                LEFT JOIN vital_signs v ON t.id = v.triage_id AND v.reading_number = 1
                WHERE t.patient_id = ?
                ORDER BY t.arrival_date DESC, t.arrival_time DESC
                LIMIT 5
                """,
                (pid,),
            ),
        },
        indent=2,
        default=str,
    )


@mcp.tool()
def get_todays_patients(date: str = "2025-04-28") -> str:
    """Get all patients who arrived on a given date, sorted by ESI level then time.

    Args:
        date: Date in YYYY-MM-DD format (sample census date: 2025-04-28)
    """
    rows = _query(
        """
        SELECT t.id AS triage_id, t.mrn,
               p.first_name, p.last_name, p.age, p.biological_sex,
               t.arrival_time, t.arrival_mode, t.chief_complaint,
               t.esi_level, t.disposition, t.triage_nurse,
               t.fall_risk, t.code_status,
               v.blood_pressure, v.heart_rate, v.temperature, v.spo2
        FROM triage_records t
        JOIN patients p ON t.patient_id = p.id
        LEFT JOIN vital_signs v ON t.id = v.triage_id AND v.reading_number = 1
        WHERE t.arrival_date = ?
        ORDER BY t.esi_level ASC, t.arrival_time ASC
        """,
        (date,),
    )
    return json.dumps(rows, indent=2, default=str)


@mcp.tool()
def get_triage_statistics(date: str = "") -> str:
    """Get ESI distribution, arrival mode breakdown, and total census.

    Args:
        date: Optional date filter YYYY-MM-DD; omit for all-time stats
    """
    where = "WHERE arrival_date = ?" if date else ""
    params: tuple = (date,) if date else ()

    by_level = _query(
        f"SELECT esi_level, COUNT(*) AS count FROM triage_records {where} GROUP BY esi_level ORDER BY esi_level",
        params,
    )
    by_mode = _query(
        f"SELECT arrival_mode, COUNT(*) AS count FROM triage_records {where} GROUP BY arrival_mode ORDER BY count DESC",
        params,
    )
    total = _query(f"SELECT COUNT(*) AS n FROM triage_records {where}", params)
    return json.dumps(
        {"total_visits": total[0]["n"], "by_esi_level": by_level, "by_arrival_mode": by_mode},
        indent=2,
    )


@mcp.tool()
def get_critical_patients() -> str:
    """List all ESI 1 and ESI 2 (critical/emergent) patients with vitals and allergy summary."""
    rows = _query(
        """
        SELECT t.mrn, p.first_name, p.last_name, p.age, p.biological_sex,
               t.arrival_date, t.arrival_time, t.chief_complaint,
               t.esi_level, t.disposition, t.triage_nurse, t.code_status,
               v.blood_pressure, v.heart_rate, v.temperature, v.spo2, v.gcs,
               GROUP_CONCAT(DISTINCT a.allergen) AS known_allergies
        FROM triage_records t
        JOIN patients p ON t.patient_id = p.id
        LEFT JOIN vital_signs v ON t.id = v.triage_id AND v.reading_number = 1
        LEFT JOIN allergies a ON p.id = a.patient_id
        WHERE t.esi_level <= 2
        GROUP BY t.id
        ORDER BY t.esi_level ASC, t.arrival_date DESC, t.arrival_time ASC
        """
    )
    return json.dumps(rows, indent=2, default=str)


@mcp.tool()
def search_patients(query: str) -> str:
    """Search patients by first name, last name, or MRN.

    Args:
        query: Partial name or MRN fragment
    """
    q = f"%{query}%"
    rows = _query(
        """
        SELECT p.mrn, p.first_name, p.last_name, p.age, p.biological_sex, p.phone,
               MAX(t.arrival_date) AS last_visit, COUNT(t.id) AS total_visits
        FROM patients p
        LEFT JOIN triage_records t ON p.id = t.patient_id
        WHERE p.first_name LIKE ? OR p.last_name LIKE ? OR p.mrn LIKE ?
        GROUP BY p.id
        ORDER BY last_visit DESC
        """,
        (q, q, q),
    )
    return json.dumps(rows, indent=2, default=str)


@mcp.tool()
def insert_patient_intake(
    mrn: str,
    first_name: str,
    last_name: str,
    dob: str,
    age: int,
    biological_sex: str,
    phone: str,
    address: str,
    language: str,
    chief_complaint: str,
    esi_level: int,
    arrival_mode: str,
    arrival_date: str,
    arrival_time: str,
    triage_nurse: str = "Triage RN",
    disposition: str = "Main ED — Bay assignment",
) -> str:
    """Insert a new patient intake record (patient + triage) into the database.

    Args:
        mrn: Medical Record Number (e.g. MRN-2024-011)
        first_name: Patient first name
        last_name: Patient last name
        dob: Date of birth YYYY-MM-DD
        age: Patient age in years
        biological_sex: Male / Female / Intersex
        phone: Contact phone number
        address: Street address
        language: Preferred language
        chief_complaint: Patient's chief complaint verbatim
        esi_level: ESI triage level 1-5
        arrival_mode: How patient arrived
        arrival_date: Arrival date YYYY-MM-DD
        arrival_time: Arrival time HH:MM
        triage_nurse: Name of triage nurse
        disposition: Initial disposition decision
    """
    try:
        existing = _query("SELECT id FROM patients WHERE mrn = ?", (mrn,))
        if existing:
            pid = existing[0]["id"]
        else:
            pid = _exec(
                "INSERT INTO patients (mrn,first_name,last_name,dob,age,biological_sex,phone,address,language) VALUES (?,?,?,?,?,?,?,?,?)",
                (mrn, first_name, last_name, dob, age, biological_sex, phone, address, language),
            )
        tid = _exec(
            "INSERT INTO triage_records (patient_id,mrn,arrival_date,arrival_time,arrival_mode,chief_complaint,esi_level,disposition,triage_nurse) VALUES (?,?,?,?,?,?,?,?,?)",
            (pid, mrn, arrival_date, arrival_time, arrival_mode, chief_complaint, esi_level, disposition, triage_nurse),
        )
        return json.dumps({"success": True, "patient_id": pid, "triage_id": tid})
    except Exception as exc:
        return json.dumps({"success": False, "error": str(exc)})


if __name__ == "__main__":
    mcp.run()
