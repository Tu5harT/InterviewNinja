# Interview Ninja — Development Roadmap

**Project:** AI-Powered Mock Interview Assistant  
**Version:** 1.0  
**Total Phases:** 5  
**Build Duration:** 3–4 weeks

---

## Phase Overview

| Phase | Name              | Duration  | Goal                                            | Status          |
| ----- | ----------------- | --------- | ----------------------------------------------- | --------------- |
| 1     | Foundation        | 1–2 days  | Running Flask app, DB schema, project scaffold  | **📋 Planning** |
| 2     | Input Pipeline    | 3–5 days  | Resume upload + parsing + question generation   | **📋 Planning** |
| 3     | Interview Session | 3–5 days  | Browser recording, server storage, session flow | **📋 Planning** |
| 4     | AI Analysis       | 7–10 days | All 4 AI modules integrated, producing scores   | **📋 Planning** |
| 5     | Report & Polish   | 3–5 days  | Report generation, PDF export, UI polish        | **📋 Planning** |

---

## Phase 1: Foundation

**Duration:** 1–2 days

**Goal:** Get the project skeleton running. Nothing works end-to-end yet, but the structure is correct and the database initializes cleanly.

**Requirements:** FR-01 (partial: file handling setup), setup infrastructure

**Plans:**

- [ ] 01-01-PLAN.md — Git + virtualenv + Flask app factory + DB models + startup script

**Entry Criteria:**

- Repository initialized
- Development environment ready

**Exit Criteria:**

- [ ] `./start.sh` starts Flask without errors
- [ ] `GET http://localhost:5000/` returns a 200 response
- [ ] `interview_ninja_dev.db` exists and contains all 6 tables
- [ ] All route files exist with stub `pass` handlers returning `{"status": "stub"}`

---

## Phase 2: Input Pipeline

**Duration:** 3–5 days

**Goal:** A candidate can upload a resume and receive a set of generated questions.

**Requirements:** FR-01 (Resume upload), FR-02 (Question generation), US-01, US-02

**Plans:**

- [x] 02-01-PLAN.md — Resume parsing (PDF + DOCX) + skills extraction via spaCy NER
- [ ] 02-02-PLAN.md — Question bank population + question generator + API endpoints + UI

**Entry Criteria:**

- Phase 1 infrastructure complete and tested
- Flask app running
- Database schema validated

**Exit Criteria:**

- [ ] Upload `sample_resume.pdf` via browser form → skills list displayed on review screen
- [ ] API returns a valid question list with 8–12 questions
- [ ] At least 70% of questions are relevant to skills in the sample resume
- [ ] Unit tests for resume parser and question generator pass
- [ ] Non-PDF file upload rejected with correct error message

---

## Phase 3: Interview Session

**Duration:** 3–5 days

**Goal:** The full interview session flow works in the browser — webcam captures responses, server saves files.

**Requirements:** FR-03 (Recording), FR-04 (Time management), FR-05 (Graceful recovery), US-03, US-04, US-05

**Plans:**

- [ ] 03-01-PLAN.md — Browser media capture (webcam, microphone, MediaRecorder) + countdown timer
- [ ] 03-02-PLAN.md — Server media handling (save WebM, extract WAV via ffmpeg) + session flow + async trigger

**Entry Criteria:**

- Phase 2 input pipeline complete
- Question flow tested and validated
- Database queries tested

**Exit Criteria:**

- [ ] Browser requests webcam/mic permission on interview screen
- [ ] Live webcam feed renders within 2 seconds
- [ ] Recording indicator visible while recording is active
- [ ] Timer counts down from 90 to 0
- [ ] After session, `recordings/{session_id}/q{n}.webm` and `q{n}.wav` exist for each question
- [ ] "Submit Interview" triggers analysis_wait screen
- [ ] Polling endpoint returns valid JSON without crashing

---

## Phase 4: AI Analysis

**Duration:** 7–10 days

**Goal:** All four AI modules run, produce scores, and persist results to the database.

**Requirements:** FR-06 (Emotion analysis), FR-07 (Voice analysis), FR-08 (Posture analysis), FR-09 (Answer quality), US-09, US-10

**Plans:**

- [ ] 04-01-PLAN.md — Emotion analyzer (DeepFace frame extraction + inference + composure score)
- [ ] 04-02-PLAN.md — Voice analyzer (STT transcription + filler word detection + WPM + clarity score)
- [ ] 04-03-PLAN.md — Posture analyzer (MediaPipe landmark extraction + scoring)
- [ ] 04-04-PLAN.md — Answer quality analyzer (keyword coverage + semantic similarity + relevance score)
- [ ] 04-05-PLAN.md — Score aggregator + suggestion rule engine + DB persistence

**Entry Criteria:**

- Phase 3 interview session complete
- Media files successfully captured and stored
- Analysis pipeline infrastructure in place

**Exit Criteria:**

- [ ] All 4 AI modules produce scores within expected ranges
- [ ] Session-level averages computed and stored
- [ ] Suggestions generated based on low scores
- [ ] Analysis completes within 60 seconds per session (9–10 responses)
- [ ] Unit tests for all analyzers pass
- [ ] No crashes on edge cases (silent videos, corrupted audio)

---

## Phase 5: Report & Polish

**Duration:** 3–5 days

**Goal:** Generate and deliver final performance reports with PDF export, Polish UI, prepare for deployment.

**Requirements:** FR-10 (Report generation), FR-11 (PDF export), US-06, US-07, US-08

**Plans:**

- [ ] 05-01-PLAN.md — Report builder + HTML report template
- [ ] 05-02-PLAN.md — PDF export (WeasyPrint) + asset bundling
- [ ] 05-03-PLAN.md — UI polish + error handling + deployment preparation

**Entry Criteria:**

- Phase 4 AI analysis complete and tested
- All scores and suggestions available in database
- Report infrastructure designed

**Exit Criteria:**

- [ ] HTML report displays all scores, emotion charts, suggestions
- [ ] PDF export generates valid PDF file (100% success rate)
- [ ] Report PDF loads correctly in all browsers
- [ ] All buttons and links functional
- [ ] No broken images or styling
- [ ] End-to-end session completes without errors
- [ ] Deployment guide complete and tested

---

## Overall Success Criteria

**All phases complete when:**

- [ ] All exit criteria for Phase 5 met
- [ ] No open bugs in critical path
- [ ] All acceptance criteria met (≥80% accuracy for key metrics)
- [ ] Code follows architecture patterns and design principles
- [ ] Tests pass for all core modules
- [ ] Documentation complete
- [ ] Deployed to production or staging environment

---

## Key Constraints

**Hardware:** Minimum 8GB RAM, CPU-only inference  
**Browser:** Chrome 90+, Firefox 88+, Safari 14.1+  
**Network:** WebRTC not required; chunked upload acceptable  
**Timeline:** 3–4 weeks estimate for solo developer  
**Tech Stack:** Flask, SQLAlchemy, DeepFace, MediaPipe, librosa, sentence-transformers, WeasyPrint

---

## Decision Log (Project Level)

| ID   | Decision                           | Rationale                                                        |
| ---- | ---------------------------------- | ---------------------------------------------------------------- |
| D-01 | Use Flask, not FastAPI             | Simpler async with ThreadPoolExecutor; easier upgrade path later |
| D-02 | Load models as singletons (app.py) | No per-request reload; faster inference                          |
| D-03 | CPU-only inference; no GPU         | Academic hardware support (≥8GB RAM sufficient)                  |
| D-04 | SQLite dev, PostgreSQL prod        | Easy local dev, production-grade persistence                     |
| D-05 | No real-time streaming             | Simpler MVP; chunked upload after record complete                |
| D-06 | No authentication (MVP)            | Single-user testing focus; auth added in future phase            |
| D-07 | WeasyPrint for PDF export          | Pure Python; no external binary dependencies                     |

---

## Risk Register

| Risk                              | Impact | Probability | Mitigation                                                     |
| --------------------------------- | ------ | ----------- | -------------------------------------------------------------- |
| Google STT quota exhaustion       | High   | Medium      | Implement Whisper fallback; local inference if needed          |
| OpenCV install fails on target OS | Medium | Medium      | Pre-test; provide Docker alternative; document troubleshooting |
| AI model weights > 2GB            | Medium | Low         | Download lazily on phase 4; cache in git-lfs                   |
| Analysis job timeout / hang       | High   | Low         | Add watchdog thread; fail gracefully with partial results      |
| Resume PDF parsing error          | Medium | Low         | Enforce 10MB limit; test with diverse resume formats           |
| Browser compatibility issues      | Low    | Low         | Test on Chrome, Firefox, Safari; document min versions         |

---

## Communication / Feedback Gates

- **Phase 1 ↔ Phase 2:** Validate database schema design; ensure all tables created correctly
- **Phase 2 ↔ Phase 3:** Validate question generation quality; confirm ≥70% relevance
- **Phase 3 ↔ Phase 4:** Validate media capture and storage; confirm files readable by analyzers
- **Phase 4 ↔ Phase 5:** Validate score ranges and suggestion quality; confirm no crashes
- **Phase 5 Exit:** Full end-to-end session (upload → questions → recording → analysis → report → PDF) succeeds 100%
