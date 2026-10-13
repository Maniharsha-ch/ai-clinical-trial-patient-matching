
import os
from typing import Optional
from dotenv import load_dotenv
from .models import Patient, ExtractedPatient, LabResults

load_dotenv()

def _fallback(patient: Patient) -> ExtractedPatient:
    flags = []
    history = patient.medical_history.lower()
    if "renal" in history and ("severe" in history or "kidney failure" in history):
        flags.append("Severe renal disease")
    if "cardiac event" in history or "myocardial infarction" in history:
        flags.append("Recent cardiac event")

    missing = []
    if patient.labs.eGFR is None:
        missing.append("eGFR / kidney function")
    if patient.labs.HbA1c is None:
        missing.append("HbA1c")
    if patient.labs.BMI is None:
        missing.append("BMI")

    conditions = [c.strip() for c in patient.conditions if c.strip()]
    summary = (
        f"{patient.age}-year-old {patient.sex.lower()} with "
        f"{', '.join(conditions) if conditions else 'no structured conditions recorded'}."
    )
    return ExtractedPatient(
        **patient.model_dump(),
        summary=summary,
        risk_flags=flags,
        missing_information=missing
    )

def extract_patient(patient: Patient) -> ExtractedPatient:
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        return _fallback(patient)

    try:
        from openai import OpenAI
        client = OpenAI(api_key=key)
        model = os.getenv("OPENAI_MODEL", "gpt-5.1")

        prompt = f"""
You are a clinical information extraction assistant for a research prototype.
Do not diagnose, treat, or invent facts. Normalize the supplied synthetic patient
record into structured information. Preserve values exactly when present.
Identify missing information and explicit risk flags only when supported by the text.

Patient record:
{patient.model_dump_json(indent=2)}
"""
        response = client.responses.parse(
            model=model,
            input=prompt,
            text_format=ExtractedPatient
        )
        parsed = response.output_parsed
        if parsed:
            return parsed
    except Exception:
        pass

    return _fallback(patient)
