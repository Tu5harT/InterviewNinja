# Interview Ninja — AI-Powered Mock Interview Assistant

**Version:** 1.0  
**Institution:** A.C. Patil College of Engineering, Dept. of AI & Data Science  
**Build Duration:** 3–4 weeks (solo developer)

---

## Project Vision

> **Interview Ninja empowers every job-seeking candidate — regardless of access to coaching resources — to practice, receive data-driven feedback, and meaningfully improve their interview performance through AI-powered behavioral and technical analysis.**

The product eliminates dependency on human interviewers for practice by providing:

- Resume-grounded question generation (8–12 questions tailored to skills)
- Facial emotion recognition and composure scoring
- Posture and body language analysis
- Voice tone, filler word, and clarity assessment
- Actionable performance reports with PDF export

---

## Success Criteria

| Metric                                   | Target                                        |
| ---------------------------------------- | --------------------------------------------- |
| End-to-end session completion (no crash) | ≥ 90%                                         |
| Resume skill extraction accuracy         | ≥ 80% on standard PDF/DOCX resumes            |
| Question relevance (user-rated)          | ≥ 70% rated "relevant"                        |
| Emotion detection directional accuracy   | ≥ 80% (nervous vs. calm differentiation)      |
| Filler word detection accuracy           | Within ±2 of manual count                     |
| Report usefulness (user-rated)           | ≥ 75% agree report highlights a real weakness |
| PDF export success rate                  | 100%                                          |

---

## Tech Stack

| Layer          | Technology                                                    |
| -------------- | ------------------------------------------------------------- |
| Backend        | Flask 3.0+, SQLAlchemy ORM                                    |
| Frontend       | HTML5, Jinja2 templates, vanilla JS (MediaRecorder), Chart.js |
| Database       | SQLite (dev), PostgreSQL (production)                         |
| AI: Emotion    | DeepFace, TensorFlow/Keras                                    |
| AI: Voice      | Google Cloud Speech-to-Text (+ Whisper fallback), librosa     |
| AI: Posture    | MediaPipe Pose, OpenCV                                        |
| AI: NLP        | sentence-transformers, spaCy NER                              |
| Resume Parsing | PyMuPDF, python-docx, spaCy                                   |
| Media          | FFmpeg, MediaRecorder API, WebM codec                         |
| Async          | ThreadPoolExecutor (core concurrency)                         |
| Deployment     | Vercel (frontend) or standalone Flask on Ubuntu 22.04         |
| PDF Export     | WeasyPrint or ReportLab                                       |

---

## MVP Scope

**In Scope (5 phases):**

- Single-user mock interview session
- Resume upload (PDF/DOCX)
- Generated questions (technical + behavioral)
- Video/audio recording and uploading
- Real-time analysis (emotion, speech, posture, answer quality)
- Performance report with PDF export
- End-to-end system validation

**Out of Scope (Future):**

- User authentication and multi-user sessions
- Batch candidate analytics for schools/HR
- Question customization by HR teams
- Longitudinal progress tracking
- Recursive mock interview scheduling
- Mobile app

---

## Development Phases

| Phase | Name              | Duration  | Primary Deliverable                                              |
| ----- | ----------------- | --------- | ---------------------------------------------------------------- |
| 1     | Foundation        | 1–2 days  | Running Flask app, DB schema, project scaffold                   |
| 2     | Input Pipeline    | 3–5 days  | Resume upload + parsing + question generation working end-to-end |
| 3     | Interview Session | 3–5 days  | Browser recording + server storage + session flow                |
| 4     | AI Analysis       | 7–10 days | All 4 AI modules integrated and producing scores                 |
| 5     | Report & Polish   | 3–5 days  | Report generation, PDF export, UI polish                         |

**Total estimate:** 3–4 weeks

---

## Key Resources

**Documentation located in root:**

- `01-product-requirements.md` — Functional requirements, FR-01 through FR-08
- `02-user-stories-and-acceptance-criteria.md` — User stories US-01 through US-12
- `03-information-architecture.md` — Screen flow and navigation model
- `04-system-architecture.md` — N-tier architecture, pipeline pattern, design patterns
- `05-database-schema.md` — SQLAlchemy model definitions (6 entities)
- `06-api-contracts.md` — REST endpoint specifications
- `07-monorepo-structure.md` — Directory organization
- `08-scoring-engine-spec.md` — Formulas for composure, clarity, posture, relevance, confidence
- `09-engineering-scope-definition.md` — BOM, edge cases, assumptions
- `10-development-phases.md` — Phase breakdown (detailed task lists)
- `11-environment-and-devops.md` — Setup, deployment, CI/CD strategy
- `12-testing-strategy.md` — Unit, integration, UAT approach

---

## Decision Log

**D-01:** Use Flask (not FastAPI) for MVP (simpler async with ThreadPoolExecutor; easier to upgrade to async later)  
**D-02:** Store all models as singletons in memory (app.py initialization) — no reload needed per request  
**D-03:** Use CPU-only inference initially; no GPU acceleration (supports academic hardware constraints, ≥8GB RAM)  
**D-04:** SQLite for development; PostgreSQL for production (schema compatible via SQLAlchemy)  
**D-05:** Streaming WebRTC not required for MVP — chunked upload POST after recording complete  
**D-06:** No user authentication in Phase 1-5 MVP; single-session testing only  
**D-07:** Report PDF via WeasyPrint (pure Python, no external binary dependencies like wkhtmltopdf)

---

## Risks and Mitigations

| Risk                                     | Impact | Mitigation                                                                       |
| ---------------------------------------- | ------ | -------------------------------------------------------------------------------- |
| Google Speech-to-Text quota/cost         | High   | Implement Whisper fallback in `voice_analyzer.py`; local transcription if needed |
| OpenCV/MediaPipe installation on Windows | Medium | Pre-test on target OS; provide Docker setup alternative                          |
| AI model weight downloads on first run   | Low    | Cache weights in git-lfs or download with progress indicator in Phase 4          |
| Async job hangs during analysis          | Medium | Add timeout watchdog; fail gracefully with partial results                       |
| Large resume PDF parsing (>20MB)         | Low    | Enforce 10MB file size limit in FR-01.3; reject oversized                        |
| Browser compatibility (getUserMedia)     | Low    | Test on Chrome 90+, Firefox 88+, Safari 14.1+; document requirements             |

---

## Success Definition

Project is complete when:

- [ ] Phase 5 implementation passes UAT (Phase 5 user stories)
- [ ] All success metrics met or documented with rationale
- [ ] PDF export works on 100% of generated reports
- [ ] No crashes during end-to-end session (candidate upload → analysis → report download)
- [ ] Code follows architecture patterns (4-tier, pipeline, repository, factory patterns)
- [ ] Tests pass for all 4 AI modules + resume parser + question generator
- [ ] README and deployment guide complete
- [ ] One successful deployment to production environment (or staging)
