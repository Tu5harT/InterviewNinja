# 10 — Development Phases
**Project:** Interview Ninja — AI-Powered Mock Interview Assistant  
**Version:** 1.0

---

## 1. Overview

The MVP build is structured across **5 sequential phases** plus a buffer phase. Each phase has clear entry and exit criteria so that progress is unambiguous and each phase can be validated independently before the next begins.

Total estimated effort: **3–4 weeks** (small team or solo developer).

---

## 2. Phase Summary

| Phase | Name | Duration | Primary Deliverable |
|---|---|---|---|
| Phase 1 | Foundation | 1–2 days | Running Flask app, DB schema, project scaffold |
| Phase 2 | Input Pipeline | 3–5 days | Resume upload + parsing + question generation working end-to-end |
| Phase 3 | Interview Session | 3–5 days | Browser recording + server storage + session flow |
| Phase 4 | AI Analysis | 7–10 days | All 4 AI modules integrated and producing scores |
| Phase 5 | Report & Polish | 3–5 days | Report generation, PDF export, UI polish |
| Buffer | Testing & Bug Fixes | 2–3 days | QA, edge cases, documentation |

---

## 3. Phase 1 — Foundation

**Duration:** 1–2 days  
**Goal:** Get the project skeleton running. Nothing works end-to-end yet, but the structure is correct and the database initializes cleanly.

### Tasks

| # | Task | Output |
|---|---|---|
| 1.1 | Initialize Git repository with `.gitignore` | Clean repo |
| 1.2 | Create virtualenv and `requirements.txt` | Reproducible Python env |
| 1.3 | Build `app.py` application factory with blueprint stubs | Flask server starts on port 5000 |
| 1.4 | Write `config.py` with `DevelopmentConfig` | Config system working |
| 1.5 | Define all 6 SQLAlchemy models in `models.py` | DB schema defined |
| 1.6 | Run `db.create_all()` — verify all tables created in SQLite | Schema verified |
| 1.7 | Create directory structure: `/uploads`, `/recordings`, `/reports_output`, `/data` | Dirs in place |
| 1.8 | Write stub JSON files: `question_bank.json`, `skills_taxonomy.json` | Data files present |
| 1.9 | Write `start.sh` with pre-flight checks | One-command startup |
| 1.10 | Write `README.md` skeleton | Documentation started |

### Exit Criteria
- [ ] `./start.sh` starts Flask without errors
- [ ] `GET http://localhost:5000/` returns a 200 response
- [ ] `interview_ninja_dev.db` exists and contains all 6 tables
- [ ] All route files exist with stub `pass` handlers returning `{"status": "stub"}`

---

## 4. Phase 2 — Input Pipeline

**Duration:** 3–5 days  
**Goal:** A candidate can upload a resume and receive a set of generated questions.

### Tasks

| # | Task | Output |
|---|---|---|
| 2.1 | Build `resume_parser.py`: PDF extraction via PyMuPDF | Raw text from PDF |
| 2.2 | Build `resume_parser.py`: DOCX extraction via python-docx | Raw text from DOCX |
| 2.3 | Integrate spaCy NER: extract name, skills, education | Structured JSON |
| 2.4 | Build skills taxonomy matcher: JSON lookup + matching | Skills list |
| 2.5 | Populate `question_bank.json` with 5–10 Qs per skill (Python, ML, Flask, OpenCV, TF, SQL, DSA) | 60–100 questions total |
| 2.6 | Populate `behavioral_questions.json` with 10–15 questions | Behavioral bank |
| 2.7 | Build `question_generator.py`: skill → question selection | 8–12 ordered questions |
| 2.8 | Build `POST /api/v1/resume/upload` route | Working endpoint |
| 2.9 | Build `POST /api/v1/session/start` route | Session + questions created in DB |
| 2.10 | Build `templates/index.html` (upload form) | Browser-accessible upload |
| 2.11 | Build `templates/review.html` (skills review screen) | Skills display |
| 2.12 | Write `tests/unit/test_resume_parser.py` | Unit tests pass |
| 2.13 | Write `tests/unit/test_question_generator.py` | Unit tests pass |

### Exit Criteria
- [ ] Upload `sample_resume.pdf` via browser form → skills list displayed on review screen
- [ ] API returns a valid question list with 8–12 questions
- [ ] At least 70% of questions are relevant to skills in `sample_resume.pdf`
- [ ] Unit tests for resume parser and question generator pass
- [ ] Non-PDF file upload rejected with correct error message

---

## 5. Phase 3 — Interview Session

**Duration:** 3–5 days  
**Goal:** The full interview session flow works in the browser — webcam captures responses, server saves files.

### Tasks

| # | Task | Output |
|---|---|---|
| 3.1 | Build `templates/interview.html` layout | Interview screen UI |
| 3.2 | Write `static/js/media_capture.js`: `getUserMedia()` + live preview | Webcam feed in browser |
| 3.3 | Write `static/js/media_capture.js`: `MediaRecorder` start/stop + blob collection | Recording works |
| 3.4 | Write countdown timer (90s) in `interview_session.js` | Timer visible; auto-stops |
| 3.5 | Write upload logic: blob → FormData POST → `/upload-response` | Upload on stop |
| 3.6 | Build `media_handler.py`: receive blob, save `.webm`, extract `.wav` via ffmpeg | Files on disk |
| 3.7 | Build `POST /api/v1/session/upload-response` route | DB `responses` row created |
| 3.8 | Build `POST /api/v1/session/complete` route | Session status → "analyzing" |
| 3.9 | Implement async analysis trigger via `ThreadPoolExecutor` | Background job starts |
| 3.10 | Build `templates/analysis_wait.html` with polling JS | Status display works |
| 3.11 | Build `GET /api/v1/analysis/status/{session_id}` route (stub returns "analyzing") | Polling works |
| 3.12 | Build question sequencing: advance to next question after upload acknowledged | Full session flow |

### Exit Criteria
- [ ] Browser requests webcam/mic permission on interview screen
- [ ] Live webcam feed renders within 2 seconds
- [ ] Recording indicator visible while recording is active
- [ ] Timer counts down from 90 to 0
- [ ] After session, `recordings/{session_id}/q{n}.webm` and `q{n}.wav` exist for each question
- [ ] "Submit Interview" triggers analysis_wait screen
- [ ] Polling endpoint returns valid JSON without crashing

---

## 6. Phase 4 — AI Analysis Pipeline

**Duration:** 7–10 days  
**Goal:** All four AI modules run, produce scores, and persist results to the database.

### Tasks

| # | Task | Output |
|---|---|---|
| 4.1 | Build `emotion_analyzer.py`: OpenCV frame extractor | Frames list per video |
| 4.2 | Build `emotion_analyzer.py`: DeepFace inference + aggregation | Emotion distribution dict |
| 4.3 | Build `emotion_analyzer.py`: composure score formula | `emotion_score` int |
| 4.4 | Build `voice_analyzer.py`: Google STT transcription + fallback Whisper | Transcript string |
| 4.5 | Build `voice_analyzer.py`: filler word regex counter | Filler count + per-word dict |
| 4.6 | Build `voice_analyzer.py`: librosa WPM computation | WPM int |
| 4.7 | Build `voice_analyzer.py`: clarity score formula | `clarity_score` int |
| 4.8 | Build `posture_analyzer.py`: MediaPipe landmark extraction | Landmark list per frame |
| 4.9 | Build `posture_analyzer.py`: shoulder + head position scoring | `posture_score` int |
| 4.10 | Build `answer_quality_analyzer.py`: keyword coverage check | Coverage float |
| 4.11 | Build `answer_quality_analyzer.py`: sentence-BERT similarity | Similarity float |
| 4.12 | Build `answer_quality_analyzer.py`: answer quality score formula | `relevance_score` int |
| 4.13 | Build `score_aggregator.py`: session-level averages | Averaged scores dict |
| 4.14 | Build `score_aggregator.py`: weighted overall score | `overall_score` int |
| 4.15 | Build `score_aggregator.py`: confidence score + label | `confidence_score`, label |
| 4.16 | Build `score_aggregator.py`: suggestion rule engine | Suggestions list |
| 4.17 | Persist all results to `analysis_results` table per response | DB rows populated |
| 4.18 | Update `GET /analysis/status` to read from DB and report real progress | Live status |
| 4.19 | Write `tests/unit/test_voice_analyzer.py` | Unit tests pass |
| 4.20 | Write `tests/unit/test_score_aggregator.py` | Unit tests pass |

### Exit Criteria
- [ ] After submitting a test session, all `analysis_results` rows have non-null emotion, voice, and posture scores
- [ ] Emotion analysis: test_video_nervous scores higher in "fearful" than test_video_calm
- [ ] Filler count for test_audio_fillers.wav matches manual count within ±2
- [ ] Posture: upright test recording scores ≥ 10 points higher than slouching recording
- [ ] `analysis/status` returns `"analyzed"` after pipeline completes
- [ ] No unhandled exceptions in the analysis pipeline for the happy-path test case
- [ ] Unit tests for voice analyzer and score aggregator pass

---

## 7. Phase 5 — Report and Polish

**Duration:** 3–5 days  
**Goal:** The full performance report is generated, displayed in the browser, and exportable as PDF. The UI is clean and complete.

### Tasks

| # | Task | Output |
|---|---|---|
| 5.1 | Build `report_builder.py`: collect all `analysis_results` for session | Data object |
| 5.2 | Build `report_builder.py`: populate suggestions from rule engine | Suggestions list |
| 5.3 | Write `templates/report.html`: score dashboard section | Score cards in browser |
| 5.4 | Write `templates/report.html`: per-question breakdown section | Per-Q table |
| 5.5 | Write `static/js/report_charts.js`: Chart.js emotion distribution chart | Chart renders |
| 5.6 | Write `templates/report.html`: suggestions section | Suggestion cards |
| 5.7 | Build `GET /api/v1/report/{session_id}` route | JSON report returned |
| 5.8 | Build report HTML rendering via Jinja2 | HTML report in browser |
| 5.9 | Build `GET /api/v1/report/{session_id}/pdf` via WeasyPrint | PDF downloads |
| 5.10 | Persist `report_html` and `report_pdf_path` to `reports` table | Report cached in DB |
| 5.11 | Update session status to "analyzed" after report generation | Status correct |
| 5.12 | UI polish: responsive layout, loading states, error messages | Clean UX |
| 5.13 | Write `tests/unit/test_report_builder.py` | Unit tests pass |
| 5.14 | Write `tests/integration/test_full_pipeline.py` | End-to-end test passes |

### Exit Criteria
- [ ] Report page renders with all sections: scores, per-question, chart, suggestions
- [ ] All score values are integers 0–100
- [ ] Emotion chart renders correctly for a completed session
- [ ] At least 3 suggestions appear in the report
- [ ] "Download PDF" triggers a PDF file download
- [ ] PDF is readable and contains all report sections
- [ ] Full end-to-end integration test passes on a clean database

---

## 8. Buffer Phase — Testing and Documentation

**Duration:** 2–3 days  
**Goal:** Harden edge cases, complete documentation, and produce a clean, handoff-ready codebase.

### Tasks

| # | Task |
|---|---|
| B.1 | Manual QA run through full happy-path session on a fresh install |
| B.2 | Test edge cases: scanned PDF, blank audio, denied webcam, very short responses |
| B.3 | Verify all unit tests pass (`pytest tests/unit/`) |
| B.4 | Verify integration test passes (`pytest tests/integration/`) |
| B.5 | Complete `README.md`: prerequisites, install steps, run instructions, architecture overview |
| B.6 | Add docstrings to all service modules |
| B.7 | Final code review: remove print statements, hardcoded paths, debug flags |
| B.8 | Tag `v1.0.0-mvp` in Git |

---

## 9. Phase Gate Checklist

Before starting the next phase, confirm all exit criteria of the current phase are met:

```
Phase 1 Gate: Flask runs ✅ | DB tables created ✅ | Stubs return 200 ✅
Phase 2 Gate: Resume parses ✅ | Questions generated ✅ | Unit tests pass ✅
Phase 3 Gate: Webcam captures ✅ | Files saved to disk ✅ | Session submits ✅
Phase 4 Gate: All 4 modules score ✅ | DB rows populated ✅ | Tests pass ✅
Phase 5 Gate: Report renders ✅ | PDF downloads ✅ | E2E test passes ✅
Buffer Gate:  Manual QA ✅ | Docs complete ✅ | Git tagged ✅
```

---

*Source: Interview Ninja project documentation, A.C. Patil College of Engineering.*
