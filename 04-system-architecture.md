# 04 — System Architecture
**Project:** Interview Ninja — AI-Powered Mock Interview Assistant  
**Version:** 1.0

---

## 1. Executive Summary

Interview Ninja is built on a **four-tier layered monolithic architecture** with a clearly separated AI inference pipeline. The design operates within academic hardware constraints (minimum 8GB RAM, CPU-only inference) while maintaining a clean upgrade path to a microservices model as scale demands grow.

The five principal pipeline stages, derived directly from the source architecture block diagram, are:

```
Resume Upload → Question Generation → Interview Session (Camera + Mic)
    → AI Analysis (Emotion + Speech + Posture) → Performance Feedback
```

---

## 2. Architectural Style and Patterns

### 2.1 Primary: Layered N-Tier Architecture

```
┌──────────────────────────────────────────────┐
│           PRESENTATION TIER                  │
│  (Browser UI — HTML/CSS/JS, Chart.js,        │
│   Jinja2 Templates or React frontend)        │
├──────────────────────────────────────────────┤
│           APPLICATION / API TIER             │
│  (Flask — REST endpoints, session mgmt,      │
│   request routing, Werkzeug middleware)      │
├──────────────────────────────────────────────┤
│           AI INFERENCE TIER                  │
│  (Emotion Analyzer, Voice Analyzer,          │
│   Posture Analyzer, NLP Answer Scorer,       │
│   Score Aggregator, Report Builder)          │
├──────────────────────────────────────────────┤
│           DATA TIER                          │
│  (SQLite dev / PostgreSQL prod,              │
│   SQLAlchemy ORM, Filesystem storage)        │
└──────────────────────────────────────────────┘
```

### 2.2 Secondary: Pipeline Pattern (AI Processing)

```
Raw Media (Video + Audio)
    → Frame Extraction (OpenCV)
    → Parallel Analysis: [Emotion] [Voice] [Posture] [NLP]
    → Score Aggregation
    → Report Generation
```

### 2.3 Supporting Design Patterns

| Pattern | Application |
|---|---|
| Repository | Data access layer; all DB operations abstracted from business logic |
| Strategy | Interchangeable AI model backends (TensorFlow vs. PyTorch) |
| Observer | Analysis job completion events trigger report generation |
| Factory | Question generation: different factories per resume domain |
| Template Method | Standardized report structure with per-session customization |
| Singleton | AI model instances loaded once at startup; shared across requests |

---

## 3. System Component Map

```
Browser (Chrome 90+, Desktop)
    │
    │  HTTP REST / WebSocket (Flask-SocketIO)
    ▼
┌──────────────────────────────────────────────────────────────┐
│                    FLASK APPLICATION                         │
│                                                              │
│  ┌────────────────┐    ┌──────────────────────────────────┐  │
│  │ Resume Parser  │───▶│ Question Generator               │  │
│  │ (PyMuPDF +     │    │ (Static bank + spaCy mapping)    │  │
│  │  spaCy NER)    │    └──────────────────────────────────┘  │
│  └────────────────┘                                          │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Media Handler                                        │   │
│  │ (Save WebM per question → extract WAV via ffmpeg)    │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ AI Analysis Pipeline (Async — ThreadPoolExecutor)    │   │
│  │  ┌──────────────┐ ┌──────────────┐ ┌─────────────┐  │   │
│  │  │ Emotion      │ │ Voice        │ │ Posture     │  │   │
│  │  │ Analyzer     │ │ Analyzer     │ │ Analyzer    │  │   │
│  │  │ (DeepFace /  │ │ (STT +       │ │ (MediaPipe  │  │   │
│  │  │  TensorFlow) │ │  librosa)    │ │  Pose)      │  │   │
│  │  └──────────────┘ └──────────────┘ └─────────────┘  │   │
│  │  ┌──────────────────────────────────────────────┐    │   │
│  │  │ Answer Quality (sentence-transformers / NLP) │    │   │
│  │  └──────────────────────────────────────────────┘    │   │
│  │  ┌──────────────────────────────────────────────┐    │   │
│  │  │ Score Aggregator + Report Builder            │    │   │
│  │  └──────────────────────────────────────────────┘    │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────┐  ┌──────────────────────┐
│  SQLite (dev) / PostgreSQL (prod)│  │ Filesystem           │
│  (candidates, sessions,          │  │ /uploads/  /recordings/
│   questions, responses,          │  │ /models/   /reports/ │
│   analysis_results, reports)     │  └──────────────────────┘
└──────────────────────────────────┘
```

---

## 4. Component Descriptions

### 4.1 Frontend Module

| Sub-component | Responsibility |
|---|---|
| Resume Upload Widget | File input; validates type and size before submission |
| Interview Dashboard | Displays questions one-by-one; manages session state |
| Media Capture Controller | `MediaDevices.getUserMedia()` wrapper; controls `MediaRecorder` |
| Feedback Report Viewer | Renders scores, charts, transcripts, suggestions |

**Technologies:** HTML5, CSS3, JavaScript ES6+, Chart.js, Jinja2 templates.

---

### 4.2 Flask API Layer

Handles all HTTP routing, session management, and orchestration.

| Module | Endpoint Group | Role |
|---|---|---|
| Resume | `/api/resume/*` | Upload, parse, extract |
| Questions | `/api/questions/*` | Generate and retrieve |
| Session | `/api/session/*` | Start, record, terminate |
| Analysis | `/api/analysis/*` | Trigger and poll jobs |
| Report | `/api/report/*` | Retrieve and export |

**Technologies:** Python 3.10+, Flask, Flask-RESTful, Flask-Session, Werkzeug.

---

### 4.3 Resume Parser

1. Accept PDF/DOCX → extract raw text (`PyMuPDF` / `python-docx`)
2. Run spaCy NER (`en_core_web_sm`) → entities: names, orgs, dates
3. Match extracted tokens against skills taxonomy JSON
4. Output structured `{name, skills[], education, projects[]}` JSON

**Engineering Assumption:** Skill taxonomy is maintained as a curated JSON lookup file. Scanned/image PDFs fall back to generic questions.

---

### 4.4 Question Generator

- Maps extracted skills to categorized question bank (`question_bank.json`)
- Selects 1–2 questions per detected skill
- Adds 2–3 fixed behavioral questions
- Returns ordered list of 8–12 question objects

---

### 4.5 Media Handler

- Receives chunked `.webm` video blob from browser via POST
- Assembles and saves to `recordings/{session_id}/q{n}.webm`
- Invokes `ffmpeg` subprocess to extract mono 16kHz `.wav` audio
- Records file paths in `responses` table

---

### 4.6 AI Analysis Pipeline (Four Modules)

#### Emotion Analyzer
- **Input:** Video frames extracted at 2 fps via OpenCV
- **Model:** DeepFace (wraps FER/VGG-Face pre-trained weights)
- **Output:** Per-frame 7-class emotion probabilities → dominant emotion + distribution

#### Voice Analyzer
- **Input:** `.wav` audio per question
- **Process:** Google STT / Whisper → transcript → filler word regex → librosa for WPM + acoustic features
- **Output:** Transcript, filler count, WPM, clarity score (0–100), tone label

#### Posture Analyzer
- **Input:** Video frames at 1 fps
- **Model:** MediaPipe Pose (33 body landmarks)
- **Scoring:** Shoulder alignment + head position → posture score (0–100) + label

#### Answer Quality Analyzer
- **Input:** Transcript text per question
- **Process:** Sentence-BERT embeddings → cosine similarity vs. ideal answer → keyword coverage check
- **Output:** Relevance score (0–100), keywords found/expected

---

### 4.7 Score Aggregator

```
Overall Score =
  (Emotion Score    × 0.20) +
  (Voice Score      × 0.30) +
  (Posture Score    × 0.15) +
  (Answer Quality   × 0.35)
```

Weights configurable by admin. Confidence score = f(emotion distribution, voice pace variance).

---

### 4.8 Report Builder

- Collects all analysis outputs from `analysis_results` table
- Renders Jinja2 HTML template with Chart.js data
- Generates improvement suggestions via rule-based engine (score range → template text)
- Exports PDF via `WeasyPrint.HTML(string=html).write_pdf(path)`

---

## 5. Data Flow Diagrams

### 5.1 Resume Upload → Question Generation

```
[Browser] ──POST /resume/upload──▶ [Flask] ──parse()──▶ [ResumeParser]
                                                               │
                                                        extract_skills()
                                                               │
                                            [QuestionGenerator]
                                                               │
                                                         select_from_bank()
                                                               │
                                            [DB: candidates + sessions + questions]
                                                               │
                                            [Browser: Interview Dashboard]
```

### 5.2 AI Analysis Pipeline

```
[All recordings saved]
        │
        ▼
[OpenCV: Frame Extraction]
        │
        ├────────────────────────────────────┐
        ▼                                    ▼
[DeepFace: Emotion]              [MediaPipe: Posture]
        │                                    │
        └──────────────┬─────────────────────┘
                       ▼
              [ffmpeg → WAV]
                       │
        ┌──────────────┴──────────────┐
        ▼                             ▼
[Google STT / Whisper]      [librosa: Acoustic]
        │                             │
[Filler Word Regex]        [WPM + Tone Label]
        │
[sentence-transformers: Answer Quality]
        │
        └──── All Outputs ────▶ [Score Aggregator]
                                        │
                                [Report Builder]
                                        │
                              [DB: reports table]
                                        │
                              [Browser: Report Screen]
```

---

## 6. Technology Stack

| Layer | Technology | Justification |
|---|---|---|
| Web Framework | Flask (Python) | Python-native; integrates directly with all AI/ML libs; minimal overhead |
| Frontend | HTML5 / CSS3 / JS + Chart.js | Native browser MediaDevices API for webcam/mic; no build toolchain |
| Computer Vision | OpenCV | Industry standard; free; runs on CPU |
| Deep Learning | TensorFlow / PyTorch | Source doc specifies both; TF for deployment, PyTorch for research |
| Pose Detection | MediaPipe | CPU-optimized; 33 landmarks; no GPU required |
| Speech Recognition | SpeechRecognition + Google STT | Accurate; multi-backend wrapper |
| Audio Analysis | librosa | De facto Python audio feature library |
| NLP | spaCy + sentence-transformers | spaCy for NER; SBERT for semantic answer scoring |
| ORM / DB | SQLAlchemy + PostgreSQL | ORM abstracts DB; PostgreSQL for production reliability |
| Report Export | WeasyPrint | HTML-to-PDF; Jinja2 templates |
| Emotion Analysis | DeepFace | Pre-trained multi-model wrapper; simple API |

---

## 7. Inter-Component Communication

### Synchronous (HTTP REST)
All candidate-facing interactions use HTTP REST with JSON payloads.

### Asynchronous (AI Jobs)
AI analysis runs post-session in a background thread (`ThreadPoolExecutor`) or Celery task (production). Frontend polls `/api/analysis/status/{session_id}` every 5 seconds.

### Real-Time Media
`MediaRecorder` accumulates blobs per question → sent via multipart POST on question completion.

---

## 8. AI Model Registry

| Model | Task | Framework | Input | Output |
|---|---|---|---|---|
| FER / Mini-Xception | Facial Emotion Recognition | TensorFlow/Keras | 48×48 face crop | 7-class probabilities |
| MediaPipe Pose | Body Landmark Detection | MediaPipe | RGB frame | 33 3D keypoints |
| Whisper / Google STT | Speech-to-Text | PyTorch / API | 16kHz WAV | Transcript |
| all-MiniLM-L6-v2 | Semantic Similarity | PyTorch | Sentence string | 384-dim embedding |
| spaCy en_core_web_sm | Named Entity Recognition | spaCy | Resume text | Entity spans |

**Loading strategy:** All models loaded once at Flask startup (singleton). Cold start: ~15–30 seconds. Acceptable for MVP.

---

## 9. Scalability and Fault Tolerance

### Current MVP Targets
- Concurrent users: 1–10 (single instance)
- Storage: ~180MB per session
- Analysis turnaround: < 3 minutes

### Scale-Up Path

| Concern | MVP | Production |
|---|---|---|
| Concurrency | Flask dev server | Gunicorn + 4 workers |
| AI jobs | ThreadPoolExecutor | Celery + Redis |
| Storage | Local filesystem | AWS S3 / MinIO |
| Database | SQLite | PostgreSQL with read replicas |
| Model serving | In-process | TorchServe / TF Serving |

### Fault Tolerance Design
- Each AI module wrapped in try/except; partial results preserved; failed modules flagged as null
- Media uploads use client-side retry; chunks acknowledged before next sent
- Session ID persisted in browser `localStorage` for recovery
- SQLAlchemy connection pool with `pool_pre_ping=True`

---

## 10. Architectural Decisions

| Decision | Choice | Rationale | Trade-off |
|---|---|---|---|
| Monolith vs. Microservices | Monolith | Simpler for academic deployment; team size doesn't justify microservices overhead | Less independent scaling |
| Sync vs. Async AI | Async (post-session) | CPU inference too slow for real-time; pipeline runs after all responses saved | Feedback not instant |
| Resume parsing | Text extraction + NLP | No paid OCR dependency; sufficient for standard resumes | Fails on scanned PDFs |
| Flask vs. Django | Flask | Lightweight; no opinionated ORM/auth; faster AI integration | Must add auth and ORM manually |
| On-device vs. Cloud AI | On-device | No per-inference cost; data privacy; works offline | Slower without GPU |

---

## 11. Security Architecture

- File uploads: whitelist only (PDF, DOCX); `secure_filename()` sanitization; stored outside web root
- CSRF tokens on all form submissions
- Server-side Flask sessions with signed cookies
- Recordings stored in session-scoped directories; not publicly accessible
- Audio to Google STT is the only data leaving the server; disclosed to candidate before session

---

## 12. Deployment Architecture

### Development
```
Laptop (8GB+ RAM)
├── Python 3.10 venv
├── Flask dev server :5000
├── SQLite .db file
└── /recordings/, /models/ local dirs
```

### Production (Single Server)
```
Ubuntu 22.04 LTS
├── Nginx (reverse proxy + static)
├── Gunicorn (4 workers, port 8000)
├── Flask application
├── PostgreSQL (port 5432)
├── Celery worker (AI jobs)
└── Redis (Celery broker, port 6379)
```

### Minimum Hardware (from source document)
| Component | Minimum | Recommended |
|---|---|---|
| CPU | 4-core | 8-core |
| RAM | 8 GB | 16 GB |
| Storage | 50 GB | 200 GB |
| OS | Any | Ubuntu 22.04 LTS |
| Network | Internet required | Broadband |

---

*Source: Interview Ninja project documentation, A.C. Patil College of Engineering.*
