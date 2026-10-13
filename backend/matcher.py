
import json
import math
import os
import re
from pathlib import Path
from typing import Any

from .models import ExtractedPatient, TrialMatch, CriterionResult

DATA = Path(__file__).parent / "data" / "trials.json"

def load_trials():
    return json.loads(DATA.read_text(encoding="utf-8"))

def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", " ", s.lower()).strip()

def condition_match(patient_conditions, trial_conditions):
    p = [norm(x) for x in patient_conditions]
    t = [norm(x) for x in trial_conditions]
    for pc in p:
        for tc in t:
            if pc == tc or pc in tc or tc in pc:
                return True
    return False

def semantic_similarity(patient: ExtractedPatient, trial: dict) -> float:
    # Real embedding similarity when an API key is available.
    key = os.getenv("OPENAI_API_KEY")
    text_a = " ".join([
        *patient.conditions,
        *patient.medications,
        patient.medical_history,
        patient.summary
    ])
    text_b = " ".join([
        trial["title"], trial["condition"],
        " ".join(trial["inclusion"]["conditions"])
    ])

    if key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=key)
            model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
            result = client.embeddings.create(model=model, input=[text_a, text_b])
            a, b = result.data[0].embedding, result.data[1].embedding
            dot = sum(x*y for x, y in zip(a,b))
            na = math.sqrt(sum(x*x for x in a))
            nb = math.sqrt(sum(x*x for x in b))
            return max(0.0, min(1.0, dot/(na*nb))) if na and nb else 0.0
        except Exception:
            pass

    a = set(norm(text_a).split())
    b = set(norm(text_b).split())
    stop = {"the","and","with","of","to","a","for","in","on","patient"}
    a -= stop
    b -= stop
    if not a or not b:
        return 0.0
    return len(a & b) / max(1, len(a | b))

def evaluate(patient: ExtractedPatient, trial: dict):
    inc = trial["inclusion"]
    exc = trial["exclusion"]
    passed, failed, missing = [], [], []
    checks = 0
    passed_count = 0

    # Age
    checks += 1
    if patient.age is None:
        missing.append(CriterionResult(
            criterion="Age", status="missing", evidence="Patient age not available."
        ))
    elif inc["age_min"] <= patient.age <= inc["age_max"]:
        passed_count += 1
        passed.append(CriterionResult(
            criterion="Age", status="passed",
            evidence=f"{patient.age} is within {inc['age_min']}–{inc['age_max']}."
        ))
    else:
        failed.append(CriterionResult(
            criterion="Age", status="failed",
            evidence=f"{patient.age} is outside {inc['age_min']}–{inc['age_max']}."
        ))

    # Condition
    checks += 1
    if not patient.conditions:
        missing.append(CriterionResult(
            criterion="Clinical condition", status="missing",
            evidence="No condition is recorded."
        ))
    elif condition_match(patient.conditions, inc["conditions"]):
        passed_count += 1
        passed.append(CriterionResult(
            criterion="Clinical condition", status="passed",
            evidence=f"Patient condition matches {trial['condition']}."
        ))
    else:
        failed.append(CriterionResult(
            criterion="Clinical condition", status="failed",
            evidence=f"Recorded conditions do not directly satisfy {trial['condition']}."
        ))

    # HbA1c
    if "hba1c_min" in inc:
        checks += 1
        value = patient.labs.HbA1c
        if value is None:
            missing.append(CriterionResult(
                criterion="HbA1c", status="missing",
                evidence="HbA1c value is unavailable."
            ))
        elif inc["hba1c_min"] <= value <= inc["hba1c_max"]:
            passed_count += 1
            passed.append(CriterionResult(
                criterion="HbA1c", status="passed",
                evidence=f"{value}% is within {inc['hba1c_min']}–{inc['hba1c_max']}%."
            ))
        else:
            failed.append(CriterionResult(
                criterion="HbA1c", status="failed",
                evidence=f"{value}% is outside {inc['hba1c_min']}–{inc['hba1c_max']}%."
            ))

    # BMI
    if "bmi_min" in inc:
        checks += 1
        value = patient.labs.BMI
        if value is None:
            missing.append(CriterionResult(
                criterion="BMI", status="missing",
                evidence="BMI is unavailable."
            ))
        elif value >= inc["bmi_min"]:
            passed_count += 1
            passed.append(CriterionResult(
                criterion="BMI", status="passed",
                evidence=f"{value} meets minimum BMI {inc['bmi_min']}."
            ))
        else:
            failed.append(CriterionResult(
                criterion="BMI", status="failed",
                evidence=f"{value} is below minimum BMI {inc['bmi_min']}."
            ))

    history = norm(patient.medical_history)

    # Exclusion rules
    exclusion_phrases = {
        "severe_renal_disease": ["severe renal disease", "kidney failure"],
        "severe_heart_failure": ["severe heart failure"],
        "recent_cardiac_event": ["recent cardiac event", "myocardial infarction"]
    }

    for key, phrases in exclusion_phrases.items():
        if not exc.get(key):
            continue
        triggered = any(p in history for p in phrases)
        checks += 1
        if triggered:
            failed.append(CriterionResult(
                criterion=key.replace("_", " ").title(),
                status="failed",
                evidence="Exclusion condition is explicitly present in medical history."
            ))
        else:
            passed_count += 1
            passed.append(CriterionResult(
                criterion=key.replace("_", " ").title(),
                status="passed",
                evidence="No explicit exclusion condition found in the supplied record."
            ))

    if exc.get("pregnancy"):
        checks += 1
        if patient.sex.lower() in {"female", "woman"}:
            if "pregnant" in history or "pregnancy" in history:
                failed.append(CriterionResult(
                    criterion="Pregnancy", status="failed",
                    evidence="Pregnancy is explicitly mentioned."
                ))
            else:
                passed_count += 1
                passed.append(CriterionResult(
                    criterion="Pregnancy", status="passed",
                    evidence="No pregnancy is explicitly recorded."
                ))
        else:
            passed_count += 1
            passed.append(CriterionResult(
                criterion="Pregnancy", status="passed",
                evidence="Not applicable based on supplied sex field."
            ))

    eligibility = (passed_count / checks * 100) if checks else 0
    semantic = semantic_similarity(patient, trial) * 100

    # Hard failures dominate; missing data prevents a high-confidence eligible label.
    if failed:
        status = "NOT ELIGIBLE"
        confidence = "LOW"
    elif missing:
        status = "REVIEW REQUIRED"
        confidence = "MEDIUM"
    else:
        status = "ELIGIBLE"
        confidence = "HIGH"

    # Ranking score rewards both clinical eligibility and semantic relevance.
    score = 0.70 * eligibility + 0.30 * semantic
    if failed:
        score = min(score, 59.0)
    elif missing:
        score = min(score, 84.0)

    if status == "ELIGIBLE":
        explanation = (
            "The patient satisfies the evaluated inclusion/exclusion criteria "
            "and has strong semantic relevance to this trial."
        )
    elif status == "REVIEW REQUIRED":
        explanation = (
            "The candidate is potentially relevant, but one or more required "
            "data points are missing. Researcher verification is required."
        )
    else:
        explanation = (
            "One or more evaluated eligibility criteria are not satisfied. "
            "The candidate should not be treated as eligible without further review."
        )

    return TrialMatch(
        trial_id=trial["id"],
        title=trial["title"],
        phase=trial["phase"],
        location=trial["location"],
        sponsor=trial["sponsor"],
        match_score=round(score, 1),
        status=status,
        confidence=confidence,
        semantic_score=round(semantic, 1),
        eligibility_score=round(eligibility, 1),
        passed=passed,
        failed=failed,
        missing=missing,
        explanation=explanation
    )

def match_trials(patient: ExtractedPatient):
    results = [evaluate(patient, t) for t in load_trials()]
    return sorted(results, key=lambda x: x.match_score, reverse=True)
