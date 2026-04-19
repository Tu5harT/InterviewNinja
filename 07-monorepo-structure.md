# 07 — Monorepo Structure
**Project:** Interview Ninja — AI-Powered Mock Interview Assistant  
**Version:** 1.0

---

## 1. Overview

Interview Ninja is a single-repository (monorepo) Python web application. There is no separate frontend build toolchain — templates are Jinja2 HTML served by Flask, with static JS/CSS files. The repository is organized by layer and responsibility: routes, services (business logic), AI modules, data models, templates, and static assets.

---

## 2. Full Directory Tree

```
interview_ninja/
│
├── app.py                          # Flask application factory; model warm-up
├── config.py                       # Configuration classes (Dev / Prod)
├── requirements.txt                # All Python dependencies
├── .env.example                    # Environment variable template
├── .gitignore
├── README.md
├── start.sh                        # Development startup script
│
├── models.py                       # SQLAlchemy ORM model definitions
│
├── routes/                         # Flask Blueprint route handlers
│   ├── __init__.py
│   ├── resume.py                   # POST /api/v1/resume/upload
│   ├── session.py                  # POST /api/v1/session/start
│   │                               # POST /api/v1/session/upload-response
│   │                               # POST /api/v1/session/complete
│   ├── analysis.py                 # GET  /api/v1/analysis/status/{id}
│   └── report.py                   # GET  /api/v1/report/{id}
│                                   # GET  /api/v1/report/{id}/pdf
│
├── services/                       # Business logic and AI pipeline
│   ├── __init__.py
│   ├── resume_parser.py            # PDF/DOCX extraction + spaCy NER
│   ├── question_generator.py       # Resume → question bank selection
│   ├── media_handler.py            # Save WebM, extract WAV via ffmpeg
│   ├── emotion_analyzer.py         # DeepFace frame-level emotion analysis
│   ├── voice_analyzer.py           # STT + librosa + filler word detection
│   ├── posture_analyzer.py         # MediaPipe pose landmark scoring
│   ├── answer_quality_analyzer.py  # sentence-transformers semantic scoring
│   ├── score_aggregator.py         # Weighted score computation
│   ├── report_builder.py           # HTML + PDF report generation
│   └── model_registry.py           # Singleton model loader (warm-up cache)
│
├── data/                           # Static data files (not user uploads)
│   ├── question_bank.json          # Categorized question bank by skill
│   ├── behavioral_questions.json   # Fixed behavioral question pool
│   ├── skills_taxonomy.json        # Canonical skill → category mappings
│   └── filler_words.json           # Filler word list + metadata
│
├── models_weights/                 # Pre-trained AI model files (gitignored)
│   ├── .gitkeep
│   └── README.md                   # Instructions to download weights
│
├── templates/                      # Jinja2 HTML templates
│   ├── base.html                   # Shared layout, head, nav
│   ├── index.html                  # Screen 1: Resume upload
│   ├── review.html                 # Screen 2: Resume review + confirmation
│   ├── interview.html              # Screen 3: Interview session
│   ├── analysis_wait.html          # Screen 4: Analysis progress
│   ├── report.html                 # Screen 5: Performance report
│   └── partials/
│       ├── question_card.html      # Reusable question display component
│       ├── score_card.html         # Reusable score display widget
│       └── suggestion_card.html    # Reusable improvement suggestion card
│
├── static/
│   ├── css/
│   │   ├── main.css                # Global styles
│   │   ├── interview.css           # Interview session screen styles
│   │   └── report.css              # Report screen styles
│   ├── js/
│   │   ├── media_capture.js        # MediaRecorder + getUserMedia wrapper
│   │   ├── interview_session.js    # Question flow, timer, upload logic
│   │   ├── analysis_poller.js      # Polls /api/v1/analysis/status every 5s
│   │   └── report_charts.js        # Chart.js emotion distribution chart
│   └── img/
│       └── logo.svg
│
├── uploads/                        # Candidate resume uploads (gitignored)
│   └── .gitkeep
│
├── recordings/                     # Session video/audio recordings (gitignored)
│   └── .gitkeep
│
├── reports_output/                 # Generated PDF reports (gitignored)
│   └── .gitkeep
│
└── tests/
    ├── __init__.py
    ├── conftest.py                  # pytest fixtures (Flask test client, DB)
    ├── unit/
    │   ├── test_resume_parser.py
    │   ├── test_question_generator.py
    │   ├── test_voice_analyzer.py
    │   ├── test_posture_analyzer.py
    │   ├── test_score_aggregator.py
    │   └── test_report_builder.py
    ├── integration/
    │   └── test_full_pipeline.py   # End-to-end upload → report
    └── fixtures/
        ├── sample_resume.pdf       # Standard test resume
        ├── sample_resume.docx
        ├── test_video_calm.webm    # Calm candidate test recording
        ├── test_video_nervous.webm # Nervous candidate test recording
        └── test_audio_fillers.wav  # Audio with known filler word count
```

---

## 3. Key File Descriptions

### `app.py` — Application Factory

```python
from flask import Flask
from config import DevelopmentConfig
from models import db
from services.model_registry import warm_all_models

def create_app(config=DevelopmentConfig):
    app = Flask(__name__)
    app.config.from_object(config)
    
    db.init_app(app)
    
    # Register blueprints
    from routes.resume import resume_bp
    from routes.session import session_bp
    from routes.analysis import analysis_bp
    from routes.report import report_bp
    
    app.register_blueprint(resume_bp, url_prefix='/api/v1')
    app.register_blueprint(session_bp, url_prefix='/api/v1')
    app.register_blueprint(analysis_bp, url_prefix='/api/v1')
    app.register_blueprint(report_bp, url_prefix='/api/v1')
    
    with app.app_context():
        db.create_all()
        warm_all_models()  # Load all AI models into memory once
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
```

---

### `config.py` — Configuration

```python
import os

class BaseConfig:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-insecure-key')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB upload limit
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
    RECORDINGS_FOLDER = os.path.join(os.getcwd(), 'recordings')
    REPORTS_FOLDER = os.path.join(os.getcwd(), 'reports_output')
    MODELS_FOLDER = os.path.join(os.getcwd(), 'models_weights')
    ALLOWED_EXTENSIONS = {'pdf', 'docx'}
    QUESTION_MIN = 8
    QUESTION_MAX = 12
    MAX_RECORDING_SECONDS = 90
    ANALYSIS_TIMEOUT_SECONDS = 600  # 10 min max

class DevelopmentConfig(BaseConfig):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///interview_ninja_dev.db'

class ProductionConfig(BaseConfig):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Strict'
```

---

### `services/model_registry.py` — Singleton Model Cache

```python
_registry = {}

def get_model(name: str):
    """Return cached model or load and cache it."""
    if name not in _registry:
        _registry[name] = _load(name)
    return _registry[name]

def _load(name: str):
    if name == 'spacy':
        import spacy
        return spacy.load('en_core_web_sm')
    if name == 'pose':
        import mediapipe as mp
        return mp.solutions.pose.Pose(
            static_image_mode=False,
            min_detection_confidence=0.5
        )
    if name == 'sentence_transformer':
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer('all-MiniLM-L6-v2')
    raise ValueError(f"Unknown model: {name}")

def warm_all_models():
    """Pre-load all models at startup."""
    for name in ['spacy', 'pose', 'sentence_transformer']:
        get_model(name)
    # DeepFace auto-loads on first call; trigger here to avoid cold start
    from deepface import DeepFace
    DeepFace.analyze(
        img_path='static/img/warmup_frame.jpg',
        actions=['emotion'],
        enforce_detection=False,
        silent=True
    )
```

---

### `data/question_bank.json` — Structure

```json
{
  "Python": [
    {
      "id": "py_001",
      "text": "What is the difference between a list and a tuple in Python?",
      "difficulty": "beginner"
    },
    {
      "id": "py_002",
      "text": "Explain how Python's GIL affects multi-threaded programs.",
      "difficulty": "intermediate"
    }
  ],
  "Machine Learning": [
    {
      "id": "ml_001",
      "text": "Explain the difference between supervised and unsupervised learning.",
      "difficulty": "beginner"
    }
  ],
  "Flask": [
    {
      "id": "flask_001",
      "text": "How does Flask's request context work?",
      "difficulty": "intermediate"
    }
  ]
}
```

---

### `static/js/media_capture.js` — Core Browser Logic

Responsibilities:
- `initCamera()` — calls `navigator.mediaDevices.getUserMedia()`; renders stream to `<video>` preview
- `startRecording(questionId)` — initialises `MediaRecorder`; collects data chunks
- `stopRecording()` — stops recorder; assembles `Blob`; calls `uploadResponse()`
- `uploadResponse(blob, sessionId, questionId)` — `FormData` POST to `/api/v1/session/upload-response`
- `startTimer(seconds, onExpire)` — countdown display; calls `stopRecording()` on expiry

---

## 4. Naming Conventions

| Scope | Convention | Example |
|---|---|---|
| Python files | `snake_case` | `resume_parser.py` |
| Python classes | `PascalCase` | `ResumeParser`, `AnalysisResult` |
| Python functions | `snake_case` | `extract_skills()` |
| Flask routes | `kebab-case` (URL) | `/upload-response` |
| JS files | `snake_case` | `media_capture.js` |
| CSS classes | `kebab-case` | `.score-card`, `.recording-indicator` |
| DB tables | `snake_case` (plural) | `analysis_results` |
| DB columns | `snake_case` | `candidate_id`, `emotion_dominant` |
| JSON keys | `snake_case` | `"skills_json"`, `"filler_count"` |
| Environment vars | `UPPER_SNAKE_CASE` | `SECRET_KEY`, `DATABASE_URL` |

---

## 5. Git Conventions

### Ignored Paths (`.gitignore`)
```
# Runtime data
uploads/
recordings/
reports_output/
*.db

# AI model weights (large binary files)
models_weights/*.h5
models_weights/*.pt
models_weights/*.pb

# Python
__pycache__/
*.pyc
venv/
.env

# OS
.DS_Store
Thumbs.db
```

### Branch Strategy

| Branch | Purpose |
|---|---|
| `main` | Stable; production-ready code |
| `develop` | Integration branch |
| `feature/resume-parser` | Feature-specific branches |
| `fix/emotion-crash` | Bug fix branches |

### Commit Message Format
```
<type>(<scope>): <short description>

type: feat | fix | docs | test | refactor | chore
scope: resume | session | analysis | report | ui | db | config

Examples:
feat(analysis): add posture scorer using MediaPipe landmarks
fix(voice): handle silent audio without crashing STT
test(resume): add DOCX parser unit tests
```

---

## 6. Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `SECRET_KEY` | ✅ (prod) | `dev-insecure-key` | Flask session signing key |
| `DATABASE_URL` | ✅ (prod) | SQLite | PostgreSQL connection string |
| `GOOGLE_STT_API_KEY` | Optional | None | Falls back to Whisper if absent |
| `FLASK_ENV` | Optional | `development` | `production` disables debug mode |
| `MAX_RECORDING_SECONDS` | Optional | `90` | Override per-question timer |

---

*Source: Interview Ninja project documentation, A.C. Patil College of Engineering.*
