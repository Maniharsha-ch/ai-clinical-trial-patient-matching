
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .models import Patient, MatchResponse
from .ai_service import extract_patient
from .matcher import match_trials
from .diversity import analyze_diversity

app = FastAPI(
    title="TrialMatch AI",
    version="1.0.0",
    description="Explainable AI-assisted clinical trial recruitment prototype."
)

app.add_middleware(
    CORSMiddleware,
     allow_origins=[
        "http://localhost:5173",
        "https://ai-clinical-trial-patient-matching.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health():
    return {"status": "ok", "service": "TrialMatch AI"}

@app.post("/api/match", response_model=MatchResponse)
def match(patient: Patient):
    extracted = extract_patient(patient)
    matches = match_trials(extracted)
    eligible = sum(m.status == "ELIGIBLE" for m in matches)
    review = sum(m.status == "REVIEW REQUIRED" for m in matches)
    high = sum(m.confidence == "HIGH" for m in matches)
    return MatchResponse(
        patient=extracted,
        matches=matches,
        metrics={
            "trials_evaluated": len(matches),
            "eligible": eligible,
            "review_required": review,
            "high_confidence": high,
            "top_score": matches[0].match_score if matches else 0
        }
    )


@app.get("/api/recruitment/diversity")
def recruitment_diversity():
    return analyze_diversity()