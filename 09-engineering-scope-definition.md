# 09 — Engineering Scope Definition
**Project:** Interview Ninja — AI-Powered Mock Interview Assistant  
**Version:** 1.0

---

## 1. Purpose

This document defines the precise engineering boundary for the MVP build. It translates product requirements into a concrete list of what will be built, what will not be built, what engineering assumptions are made, and what third-party dependencies are accepted.

---

## 2. In-Scope Engineering Work

### 2.1 Backend (Flask / Python)

| Module | What Gets Built |
|---|---|
| `resume_parser.py` | PDF and DOCX text extraction; spaCy NER pipeline; skill taxonomy matching; structured JSON output |
| `question_generator.py` | Question bank loader (JSON); skill-to-question mapping; behavioral question injection; ordered list output (8–12 Qs) |
| `media_handler.py` | WebM blob receiver; filesystem save; ffmpeg audio extraction (WAV); path storage in DB |
| `emotion_analyzer.py` | OpenCV frame extractor (2 fps); DeepFace inference; per-frame aggregation; emotion score derivation |
| `voice_analyzer.py` | Google STT / Whisper transcription; filler word regex; librosa WPM computation; clarity score formula |
| `posture_analyzer.py` | MediaPipe Pose landmark detection (1 fps); shoulder alignment + head position scoring |
| `answer_quality_analyzer.py` | Sentence-BERT semantic similarity; keyword coverage check; answer quality score |
| `score_aggregator.py` | Module score averaging; weighted overall score; confidence score; session-level aggregation |
| `report_builder.py` | Jinja2 HTML rendering; suggestion rule engine; WeasyPrint PDF export |
| `model_registry.py` | Singleton model cache; startup warm-up for all AI models |
| Flask routes (5 files) | `/resume/upload`, `/session/start`, `/session/upload-response`, `/session/complete`, `/analysis/status`, `/report/{id}`, `/report/{id}/pdf` |
| `models.py` | SQLAlchemy ORM: 6 tables (candidates, sessions, questions, responses, analysis_results, reports) |
| Config + App factory | `config.py`, `app.py` with blueprint registration and DB initialization |
| Async analysis trigger | `concurrent.futures.ThreadPoolExecutor` for post-session analysis jobs |

### 2.2 Frontend (HTML/CSS/JS)

| File | What Gets Built |
|---|---|
| `templates/index.html` | Resume upload form; file type/size validation |
| `templates/review.html` | Extracted skills display; confirm + start button |
| `templates/interview.html` | Question display; webcam preview; recording controls; countdown timer; upload progress |
| `templates/analysis_wait.html` | Progress bar; module status list; polling trigger |
| `templates/report.html` | Score dashboard; per-question breakdown; emotion chart (Chart.js); suggestions; PDF download button |
| `static/js/media_capture.js` | `getUserMedia()` wrapper; `MediaRecorder` control; blob upload |
| `static/js/interview_session.js` | Question sequencing; timer; upload coordination |
| `static/js/analysis_poller.js` | 5-second polling loop; auto-redirect on completion |
| `static/js/report_charts.js` | Chart.js emotion distribution bar/pie chart |

### 2.3 Data Files

| File | What Gets Built |
|---|---|
| `data/question_bank.json` | Curated questions for: Python, ML, Flask, OpenCV, TensorFlow, Data Structures, SQL, general CS |
| `data/behavioral_questions.json` | 10–15 behavioral questions covering teamwork, deadlines, communication |
| `data/skills_taxonomy.json` | Canonical skill list with category mappings |
| `data/filler_words.json` | Filler word list with metadata |

### 2.4 Infrastructure / Scripts

| Item | What Gets Built |
|---|---|
| `start.sh` | Pre-flight checks (ffmpeg, Python packages); virtualenv activation; DB init; Flask start |
| `requirements.txt` | Pinned dependency versions |
| `.env.example` | Template for environment variables |
| `README.md` | Setup, prerequisites, run instructions |

---

## 3. Explicitly Out of Scope (Not Built in MVP)

| Feature | Engineering Reason |
|---|---|
| User authentication (register/login/JWT) | Adds significant complexity; not needed for single-user local tool |
| Real-time AI analysis during recording | CPU inference latency prevents real-time operation; deferred to v2 with GPU |
| LLM-based answer quality scoring (GPT/Claude API) | API cost + latency; keyword + SBERT sufficient for MVP validation |
| Multi-session history and candidate dashboard | Requires user accounts; deferred |
| Mobile browser support | `MediaRecorder` inconsistencies on iOS Safari; desktop Chrome only |
| Admin panel for question bank management | Manual JSON editing sufficient for MVP |
| Cloud object storage (S3/MinIO) | Local filesystem sufficient; cloud migration is v2 scope |
| Celery + Redis task queue | ThreadPoolExecutor sufficient for single-user MVP load |
| Resume-to-job-description comparison | Not in source project requirements |
| Video playback in report | Large file serving complexity; text report sufficient |
| HR recruiter view / multi-user | Secondary user; future version |
| Non-English resume parsing | English-only; scope risk |
| Automated storage purge jobs | Manual for MVP; scheduled task in v2 |
| GPU inference support | Hardware constraint in source doc (8GB RAM, CPU minimum) |
| Whisper fallback (unless STT fails) | Implemented only as a fallback, not primary |

---

## 4. Engineering Assumptions

All assumptions are labeled `[EA-##]` and are referenced in relevant documents.

| ID | Assumption | Impact if Wrong |
|---|---|---|
| EA-01 | `ffmpeg` is installed on the host machine and available in PATH | Audio extraction fails; voice analysis blocked |
| EA-02 | Google STT API has acceptable accuracy for Indian English accents | Transcripts inaccurate; filler count and clarity score degraded |
| EA-03 | Pre-trained FER emotion model works without fine-tuning on target demographic | Emotion scores may be directionally inaccurate |
| EA-04 | Resumes are standard text-based PDFs or DOCX files | Skills extraction may fail or be incomplete on graphical resumes |
| EA-05 | Interview sessions occur in adequately lit environments | DeepFace face detection may fail in dark video |
| EA-06 | Candidate speaks clearly in a quiet environment | STT accuracy degrades in noisy conditions |
| EA-07 | `all-MiniLM-L6-v2` sentence transformer is sufficient for answer quality scoring | Answer quality scores less accurate than GPT-based scoring |
| EA-08 | A candidate completes the session in one sitting without closing the browser | Partial sessions not fully recoverable without auth |
| EA-09 | Score weights (emotion 20%, voice 30%, posture 15%, answer 35%) reflect fair assessment | Scores may not align with human evaluator judgment |
| EA-10 | The question bank covers the main technology domains in the target candidate population | Gaps in question bank lead to generic questions for niche skills |

---

## 5. Third-Party Dependencies and Risks

| Dependency | Type | Risk Level | Mitigation |
|---|---|---|---|
| Google Speech-to-Text API | External API | Medium | Fallback to offline Whisper model |
| DeepFace | Python library | Low | Mature; pre-trained weights auto-download |
| MediaPipe | Python library | Low | Google-maintained; CPU-optimized |
| sentence-transformers | Python library | Low | HuggingFace; auto-downloads weights |
| spaCy `en_core_web_sm` | NLP model | Low | Must be downloaded manually (`python -m spacy download`) |
| ffmpeg | System tool | Medium | Must be pre-installed; documented as prerequisite |
| WeasyPrint | Python library | Low | HTML-to-PDF; may fail on complex CSS |
| Chart.js | JS library (CDN) | Low | Served via CDN; offline fallback not implemented |

---

## 6. Dependency Download Checklist

Run this once after cloning the repository:

```bash
# 1. Python dependencies
pip install -r requirements.txt --break-system-packages

# 2. spaCy language model
python -m spacy download en_core_web_sm

# 3. System: ffmpeg
# Ubuntu/Debian:
sudo apt-get install ffmpeg
# macOS:
brew install ffmpeg
# Windows:
# Download from https://ffmpeg.org/download.html and add to PATH

# 4. AI model warm-up (downloads weights on first run)
python -c "from app import create_app; app = create_app(); app.app_context().push()"
# DeepFace will auto-download FER weights (~100MB)
# Sentence-BERT will auto-download all-MiniLM-L6-v2 (~80MB)
```

---

## 7. Performance Targets (Engineering Contracts)

These are internal engineering targets (not user-facing SLAs) for the MVP build:

| Operation | Max Acceptable Duration |
|---|---|
| Resume upload + parse (2-page PDF) | 10 seconds |
| Question generation | 5 seconds |
| WebM blob upload per question | 5 seconds (90-second max recording) |
| Audio extraction via ffmpeg | 15 seconds per question |
| Emotion analysis per question (CPU, 180 frames) | 45 seconds |
| Voice analysis per question | 20 seconds |
| Posture analysis per question (90 frames) | 30 seconds |
| Answer quality analysis per question | 10 seconds |
| Total analysis for 10-question session | ≤ 5 minutes |
| Report HTML generation | 3 seconds |
| PDF export | 10 seconds |

---

## 8. Definition of Done (Engineering)

A feature is engineering-complete when:

1. **Code written** — implementation exists in the correct module/file per the monorepo structure
2. **Unit tested** — at least one unit test exists; core logic has ≥ 80% branch coverage
3. **Integration verified** — feature works end-to-end in the happy-path flow
4. **Edge cases handled** — known failure modes (empty input, file corruption, API failure) are caught without unhandled exceptions
5. **Docstrings present** — all public functions have docstrings
6. **No hardcoded secrets** — all secrets/configs use environment variables or `config.py`

---

*Source: Interview Ninja project documentation, A.C. Patil College of Engineering.*
