
import { useState } from "react";
import { Activity, BrainCircuit, CheckCircle2, ChevronRight, FileSearch, ShieldCheck, TriangleAlert, Users } from "lucide-react";

type Criterion = { criterion: string; status: string; evidence: string };
type Match = {
  trial_id: string; title: string; phase: string; location: string; sponsor: string;
  match_score: number; status: string; confidence: string; semantic_score: number;
  eligibility_score: number; passed: Criterion[]; failed: Criterion[]; missing: Criterion[];
  explanation: string;
};
type Diversity = {
  total_candidates: number;
  gender: Record<string, number>;
  age_groups: Record<string, number>;
  locations: Record<string, number>;
  recruitment_gaps: string[];
};
type Result = {
  patient: any; matches: Match[]; metrics: Record<string, number>;
};

const samplePatient = {
  patient_id: "P001", age: 52, sex: "Male", location: "Hyderabad",
  conditions: ["Type 2 Diabetes Mellitus", "Hypertension"],
  medications: ["Metformin", "Atorvastatin"],
  labs: { HbA1c: 8.2, BMI: 28.1, eGFR: 88 },
  medical_history: "No severe renal disease. No recent cardiac event. No pregnancy."
};

function App() {
  const [patient, setPatient] = useState(JSON.stringify(samplePatient, null, 2));
  const [reviewSent, setReviewSent] = useState(false);
  const [result, setResult] = useState<Result | null>(null);
  const [selected, setSelected] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [diversity, setDiversity] = useState<Diversity | null>(null);

  async function analyze() {
    setLoading(true);
    setError("");

    try {
      const parsed = JSON.parse(patient);

      const response = await fetch("http://localhost:8000/api/match", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(parsed)
      });

      if (!response.ok) {
        throw new Error("Backend request failed");
      }

      const matchData = await response.json();

      const diversityResponse = await fetch(
        "http://localhost:8000/api/recruitment/diversity"
      );

      if (!diversityResponse.ok) {
        throw new Error("Diversity analytics request failed");
      }

      const diversityData = await diversityResponse.json();

      setResult(matchData);
      setDiversity(diversityData);
      setSelected(0);
      setReviewSent(false);

    } catch (e: any) {
      setError(e.message || "Could not analyze patient.");
    } finally {
      setLoading(false);
    }
  }

  const current = result?.matches[selected];
  const top = result?.matches[0];


  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <div className="logo"><BrainCircuit size={23} /></div>
          <div><strong>TrialMatch AI</strong><span>Clinical Recruitment Intelligence</span></div>
        </div>
        <div className="status"><span className="dot" /> Researcher Decision Support</div>
      </header>

      <main className="shell">
        <section className="hero">
          <div>
            <p className="eyebrow">AI-POWERED CLINICAL TRIAL MATCHING</p>
            <h1>From patient records to <em>explainable</em> trial matches.</h1>
            <p className="sub">Hybrid AI extraction + semantic relevance + deterministic eligibility verification.</p>
          </div>
          <div className="hero-badge"><ShieldCheck /> Human-in-the-loop</div>
        </section>

        <div className="grid">
          <section className="panel input-panel">
            <div className="panel-title"><FileSearch /> Patient / EHR Record</div>
            <p className="hint">Synthetic patient data for prototype demonstration.</p>
            <textarea value={patient} onChange={e => setPatient(e.target.value)} />
            <button className="primary" onClick={analyze} disabled={loading}>
              {loading ? "Analyzing..." : "Analyze & Find Trials"} <ChevronRight size={18} />
            </button>
            {error && <div className="error">{error}</div>}
          </section>

          <section className="panel profile">
            <div className="panel-title"><Activity /> AI Patient Profile</div>
            {!result ? (
              <div className="empty">Analyze the patient to generate a structured clinical profile.</div>
            ) : (
              <>
                <div className="profile-head">
                  <div><span className="label">PATIENT</span><h2>{result.patient.patient_id}</h2></div>
                  <div className="confidence">AI PROFILE READY</div>
                </div>
                <p className="summary">{result.patient.summary}</p>
                <div className="chips">
                  {result.patient.conditions.map((x: string) => <span key={x}>{x}</span>)}
                  {result.patient.medications.map((x: string) => <span key={x}>{x}</span>)}
                </div>
                <div className="labgrid">
                  <div><span>AGE</span><b>{result.patient.age}</b></div>
                  <div><span>HbA1c</span><b>{result.patient.labs.HbA1c ?? "—"}%</b></div>
                  <div><span>BMI</span><b>{result.patient.labs.BMI ?? "—"}</b></div>
                  <div><span>eGFR</span><b>{result.patient.labs.eGFR ?? "—"}</b></div>
                </div>
              </>
            )}
          </section>
        </div>

        {result && (
          <>
            <section className="metrics">
              <div>
                <span>Trials Evaluated</span>
                <b>{result.metrics.trials_evaluated}</b>
              </div>

              <div>
                <span>Eligible</span>
                <b>{result.metrics.eligible}</b>
              </div>

              <div>
                <span>Potential Matches</span>
                <b>{result.metrics.review_required}</b>
              </div>

              <div>
                <span>Total Candidates</span>
                <b>{diversity?.total_candidates ?? "—"}</b>
              </div>

              <div>
                <span>High Confidence</span>
                <b>{result.metrics.high_confidence}</b>
              </div>

              <div>
                <span>Top Match</span>
                <b>{result.metrics.top_score}%</b>
              </div>
            </section>

            <section className="results">
              <div className="section-head">
                <div><p className="eyebrow">MATCH ENGINE</p><h2>Ranked clinical trials</h2></div>
                <span className="engine-pill">HYBRID AI + RULE ENGINE</span>
              </div>

              <div className="match-layout">
                <div className="trial-list">
                  {result.matches.map((m, i) => (
                    <button className={`trial-card ${i === selected ? "selected" : ""}`} key={m.trial_id} onClick={() => setSelected(i)}>
                      <div className="rank">0{i + 1}</div>
                      <div className="trial-info">
                        <h3>{m.title}</h3>
                        <p>{m.phase} · {m.location} · {m.sponsor}</p>
                        <span className={`tag ${m.status === "ELIGIBLE" ? "green" : m.status === "REVIEW REQUIRED" ? "amber" : "red"}`}>{m.status}</span>
                      </div>
                      <div className="score"><b>{m.match_score}%</b><span>match</span></div>
                    </button>
                  ))}
                </div>


                {current && (
                  <div className="explain">

                    {current.status === "REVIEW REQUIRED" && (
                      <div className="potential-banner">
                        <div className="potential-icon">
                          ⚠
                        </div>

                        <div className="potential-content">
                          <strong>Potential Match — Review Required</strong>
                          <span>
                            This candidate is relevant to the trial, but required clinical
                            information is missing.
                          </span>
                        </div>

                        <div className="potential-score">
                          {current.match_score}%
                          <span>match</span>
                        </div>
                      </div>
                    )}

                    <div className="explain-top">
                      <div><span className="label">MATCH EXPLANATION</span><h2>{current.match_score}% Match</h2></div>
                      <span className={`confidence ${current.confidence.toLowerCase()}`}>{current.confidence} CONFIDENCE</span>
                    </div>
                    <p className="explanation">{current.explanation}</p>

                    <div className="evidence-grid">
                      <div>
                        <h4><CheckCircle2 /> PASSED</h4>
                        {current.passed.map((x, i) => <div className="evidence pass" key={i}><b>{x.criterion}</b><span>{x.evidence}</span></div>)}
                      </div>
                      <div>
                        <h4><TriangleAlert /> REVIEW / FAILED</h4>
                        {current.failed.length === 0 && current.missing.length === 0
                          ? <div className="evidence pass"><b>No blocking criteria</b><span>All evaluated criteria are satisfied.</span></div>
                          : [...current.failed, ...current.missing].map((x, i) => <div className="evidence warn" key={i}><b>{x.criterion}</b><span>{x.evidence}</span></div>)
                        }
                      </div>
                    </div>

                    <div className="scorebar">
                      <div><span>Eligibility verification</span><b>{current.eligibility_score}%</b></div>
                      <div className="bar"><i style={{ width: `${current.eligibility_score}%` }} /></div>
                      <div><span>Semantic relevance</span><b>{current.semantic_score}%</b></div>
                      <div className="bar"><i style={{ width: `${current.semantic_score}%` }} /></div>
                    </div>
                    <button
                      className="review"
                      onClick={() => setReviewSent(true)}
                      disabled={reviewSent}
                    >
                      <Users size={17} />
                      {reviewSent
                        ? "Candidate marked for researcher review"
                        : "Send candidate for researcher review"}
                    </button>

                    {reviewSent && (
                      <div className="review-note">
                        ✓ Researcher review flag added for this candidate.
                      </div>
                    )}
                  </div>
                )}
              </div>
            </section>
            {diversity && (
              <section className="diversity-section">
                <div className="section-head">
                  <div>
                    <p className="eyebrow">RECRUITMENT INTELLIGENCE</p>
                    <h2>Diversity & Recruitment Analytics</h2>
                  </div>

                  <span className="engine-pill">
                    COHORT ANALYTICS
                  </span>
                </div>

                <div className="diversity-total">
                  <div>
                    <span>Total Candidates</span>
                    <b>{diversity.total_candidates}</b>
                  </div>

                  <div>
                    <span>Gender Groups</span>
                    <b>{Object.keys(diversity.gender).length}</b>
                  </div>

                  <div>
                    <span>Age Groups</span>
                    <b>{Object.keys(diversity.age_groups).length}</b>
                  </div>

                  <div>
                    <span>Locations</span>
                    <b>{Object.keys(diversity.locations).length}</b>
                  </div>
                </div>

                <div className="diversity-grid">

                  <div className="analytics-card">
                    <h3>Gender Distribution</h3>

                    {diversity &&
                      Object.entries(diversity.gender).map(([key, value]) => (
                        <div className="analytics-row" key={key}>
                          <span>{key}</span>
                          <b>{value}%</b>
                        </div>
                      ))
                    }
                  </div>

                  <div className="analytics-card">
                    <h3>Age Distribution</h3>

                    {diversity &&
                      Object.entries(diversity.age_groups).map(([key, value]) => (
                        <div className="analytics-row" key={key}>
                          <span>{key}</span>
                          <b>{value}%</b>
                        </div>
                      ))
                    }
                  </div>

                  <div className="analytics-card">
                    <h3>Geographic Distribution</h3>

                    {diversity &&
                      Object.entries(diversity.locations).map(([key, value]) => (
                        <div className="analytics-row" key={key}>
                          <span>{key}</span>
                          <b>{value}%</b>
                        </div>
                      ))
                    }
                  </div>

                </div>

                <div className="recruitment-gaps">
                  <h3>Recruitment Gaps</h3>

                  {diversity?.recruitment_gaps?.length ? (
                    diversity.recruitment_gaps.map((gap, index) => (
                      <div className="gap-warning" key={index}>
                        <TriangleAlert size={19} />
                        <span>{gap}</span>
                      </div>
                    ))
                  ) : (
                    <div className="gap-success">
                      No major recruitment gaps detected.
                    </div>
                  )}
                </div>

                <div className="analytics-grid">

                  <div className="analytics-card">
                    <h3>Gender Distribution</h3>

                    {Object.entries(diversity.gender).map(([key, value]) => (
                      <div className="distribution-row" key={key}>
                        <div className="distribution-label">
                          <span>{key}</span>
                          <b>{value}%</b>
                        </div>

                        <div className="distribution-bar">
                          <i style={{ width: `${value}%` }} />
                        </div>
                      </div>
                    ))}
                  </div>


                  <div className="analytics-card">
                    <h3>Age Distribution</h3>

                    {Object.entries(diversity.age_groups).map(([key, value]) => (
                      <div className="distribution-row" key={key}>
                        <div className="distribution-label">
                          <span>{key}</span>
                          <b>{value}%</b>
                        </div>

                        <div className="distribution-bar">
                          <i style={{ width: `${value}%` }} />
                        </div>
                      </div>
                    ))}
                  </div>


                  <div className="analytics-card locations-card">
                    <h3>Geographic Distribution</h3>

                    {Object.entries(diversity.locations).map(([key, value]) => (
                      <div className="distribution-row" key={key}>
                        <div className="distribution-label">
                          <span>{key}</span>
                          <b>{value}%</b>
                        </div>

                        <div className="distribution-bar">
                          <i style={{ width: `${value}%` }} />
                        </div>
                      </div>
                    ))}
                  </div>


                  <div className="analytics-card gaps-card">
                    <h3>Recruitment Gaps</h3>

                    {diversity.recruitment_gaps.length === 0 ? (
                      <div className="gap-success">
                        <CheckCircle2 size={20} />
                        <div>
                          <b>No major recruitment gaps detected</b>
                          <span>
                            Current candidate distribution is reasonably balanced.
                          </span>
                        </div>
                      </div>
                    ) : (
                      diversity.recruitment_gaps.map((gap, index) => (
                        <div className="gap-warning" key={index}>
                          <TriangleAlert size={19} />
                          <span>{gap}</span>
                        </div>
                      ))
                    )}
                  </div>

                </div>
              </section>
            )}
          </>
        )}

        <footer>
          <span>TrialMatch AI · Prototype</span>
          <span>Uses synthetic data · Not a medical decision system</span>
        </footer>
      </main>
    </div>
  );
}

export default App;
