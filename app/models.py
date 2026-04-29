from pydantic import BaseModel
from typing import Optional


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    tool_calls: list[str] = []


class IntakeRequest(BaseModel):
    mrn: str
    first_name: str
    last_name: str
    dob: str
    age: int
    biological_sex: str
    phone: str
    address: str
    language: str = "English"
    chief_complaint: str
    esi_level: int
    arrival_mode: str
    arrival_date: str
    arrival_time: str
    triage_nurse: str = "Triage RN"
    disposition: str = "Main ED — Bay assignment"


class IntakeResponse(BaseModel):
    success: bool
    patient_id: Optional[int] = None
    triage_id: Optional[int] = None
    error: Optional[str] = None
