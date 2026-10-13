
# TrialMatch AI

AI-assisted clinical trial recruitment prototype.

## Architecture

Patient/EHR → AI clinical extraction → semantic relevance → deterministic eligibility engine → ranked matches → evidence/explanation → researcher review.

## Run

### Backend

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r backend/requirements.txt
copy backend\.env.example backend\.env
python -m uvicorn backend.main:app --reload --port 8000
```

If using macOS/Linux, activate with:
```bash
source .venv/bin/activate
```
Then run:
```bash
python -m uvicorn backend.main:app --reload --port 8000
```

Add your API key to `.env` for LLM extraction and embeddings. The application still runs with deterministic fallback logic if no key is supplied.

### Frontend

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

## Important

The included records are synthetic. This is a research/hackathon prototype, not a medical decision system. Final recruitment decisions must remain with qualified researchers.
