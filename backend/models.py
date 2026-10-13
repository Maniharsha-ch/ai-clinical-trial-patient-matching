
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class LabResults(BaseModel):
    HbA1c: Optional[float] = None
    BMI: Optional[float] = None
    eGFR: Optional[float] = None

class Patient(BaseModel):
    patient_id: str = "P001"
    age: int
    sex: str
    location: str = ""
    conditions: List[str] = []
    medications: List[str] = []
    labs: LabResults = Field(default_factory=LabResults)
    medical_history: str = ""

class ExtractedPatient(Patient):
    summary: str = ""
    risk_flags: List[str] = []
    missing_information: List[str] = []

class CriterionResult(BaseModel):
    criterion: str
    status: str
    evidence: str

class TrialMatch(BaseModel):
    trial_id: str
    title: str
    phase: str
    location: str
    sponsor: str
    match_score: float
    status: str
    confidence: str
    semantic_score: float
    eligibility_score: float
    passed: List[CriterionResult]
    failed: List[CriterionResult]
    missing: List[CriterionResult]
    explanation: str

class MatchResponse(BaseModel):
    patient: ExtractedPatient
    matches: List[TrialMatch]
    metrics: Dict[str, int | float]
