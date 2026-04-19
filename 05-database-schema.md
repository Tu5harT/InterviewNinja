# 05 — Database Schema
**Project:** Interview Ninja — AI-Powered Mock Interview Assistant  
**Version:** 1.0

---

## 1. Overview

Interview Ninja uses a relational database (SQLite for development, PostgreSQL for production). The schema models six core entities that map directly to the system's five pipeline stages: candidate ingestion, session management, question generation, response capture, AI analysis, and reporting.

All tables use SQLAlchemy ORM definitions and are compatible with both SQLite (development) and PostgreSQL (production). The JSONB type falls back to TEXT in SQLite.

---

## 2. Entity Relationship Diagram

```
CANDIDATES (1)
    │
    └──< SESSIONS (1)
              │
              ├──< QUESTIONS
              │
              └──< RESPONSES (1) ──< ANALYSIS_RESULTS
              │
              └──< REPORTS
```

**Cardinalities:**
- One candidate → many sessions (future; one in MVP)
- One session → many questions
- One session → many responses (one per question answered)
- One response → one analysis result
- One session → one report

---

## 3. Table Definitions

### 3.1 `candidates`

Stores candidate profile and parsed resume data.

```sql
CREATE TABLE candidates (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(255) NOT NULL,
    email           VARCHAR(255),
    resume_filename VARCHAR(255) NOT NULL,
    -- sanitized original filename stored for display purposes only
    resume_path     VARCHAR(512) NOT NULL,
    -- absolute server-side path; never exposed to client
    skills_raw      TEXT,
    -- comma-separated raw token output from NER pipeline
    skills_json     JSONB,
    -- structured: [{"skill": "Python", "category": "language"}, ...]
    resume_text     TEXT,
    -- full extracted text from PDF/DOCX; retained for re-generation
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_candidates_email ON candidates(email);
```

| Column | Type | Notes |
|---|---|---|
| `id` | SERIAL PK | Auto-increment |
| `name` | VARCHAR(255) | Extracted from resume; candidate-editable on review screen |
| `email` | VARCHAR(255) | Optional; not required for MVP |
| `resume_filename` | VARCHAR(255) | Display only; sanitized |
| `resume_path` | VARCHAR(512) | Server path to uploaded file |
| `skills_raw` | TEXT | Raw comma-separated output |
| `skills_json` | JSONB | Structured skill objects |
| `resume_text` | TEXT | Full text for re-processing |
| `created_at` | TIMESTAMP | Auto-set on insert |

---

### 3.2 `sessions`

One row per mock interview session.

```sql
CREATE TABLE sessions (
    id                      SERIAL PRIMARY KEY,
    candidate_id            INTEGER NOT NULL
                            REFERENCES candidates(id) ON DELETE CASCADE,
    status                  VARCHAR(50) DEFAULT 'created',
    -- values: created | in_progress | completed | analyzing | analyzed | failed
    question_count          INTEGER DEFAULT 0,
    started_at              TIMESTAMP,
    completed_at            TIMESTAMP,
    analysis_started_at     TIMESTAMP,
    analysis_completed_at   TIMESTAMP,
    created_at              TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_sessions_candidate_id ON sessions(candidate_id);
CREATE INDEX idx_sessions_status ON sessions(status);
```

| Column | Type | Notes |
|---|---|---|
| `id` | SERIAL PK | Unique session identifier; used in all URLs |
| `candidate_id` | FK | References `candidates.id` |
| `status` | VARCHAR(50) | Drives UI state machine and analysis pipeline |
| `question_count` | INTEGER | Set after question generation |
| `started_at` | TIMESTAMP | Set when candidate clicks "Start Recording" on Q1 |
| `completed_at` | TIMESTAMP | Set on "Submit Interview" |
| `analysis_started_at` | TIMESTAMP | Set when async job starts |
| `analysis_completed_at` | TIMESTAMP | Set when report is generated |

**Valid status transitions:**
```
created → in_progress → completed → analyzing → analyzed
                                              └→ failed
```

---

### 3.3 `questions`

Interview questions generated for a specific session.

```sql
CREATE TABLE questions (
    id          SERIAL PRIMARY KEY,
    session_id  INTEGER NOT NULL
                REFERENCES sessions(id) ON DELETE CASCADE,
    sequence    INTEGER NOT NULL,
    -- 1-based display order
    text        TEXT NOT NULL,
    category    VARCHAR(50),
    -- 'technical' | 'behavioral'
    skill_tag   VARCHAR(100),
    -- e.g., 'Python', 'Machine Learning', 'Teamwork'
    source      VARCHAR(50) DEFAULT 'bank',
    -- 'bank' | 'generated'
    created_at  TIMESTAMP DEFAULT NOW(),
    UNIQUE (session_id, sequence)
);

CREATE INDEX idx_questions_session_id ON questions(session_id);
```

| Column | Type | Notes |
|---|---|---|
| `sequence` | INTEGER | 1-based; UNIQUE per session to prevent duplicates |
| `category` | VARCHAR | "technical" or "behavioral" |
| `skill_tag` | VARCHAR | Skill the question tests (for report attribution) |
| `source` | VARCHAR | "bank" = static question bank; "generated" = LLM-produced |

---

### 3.4 `responses`

One row per question answered in a session.

```sql
CREATE TABLE responses (
    id                      SERIAL PRIMARY KEY,
    session_id              INTEGER NOT NULL
                            REFERENCES sessions(id) ON DELETE CASCADE,
    question_id             INTEGER NOT NULL
                            REFERENCES questions(id) ON DELETE CASCADE,
    video_path              VARCHAR(512),
    -- absolute path to .webm file
    audio_path              VARCHAR(512),
    -- absolute path to extracted .wav file
    recording_duration_sec  FLOAT,
    file_size_bytes         BIGINT,
    upload_status           VARCHAR(50) DEFAULT 'pending',
    -- 'pending' | 'uploaded' | 'failed'
    recorded_at             TIMESTAMP DEFAULT NOW(),
    UNIQUE (session_id, question_id)
);

CREATE INDEX idx_responses_session_id ON responses(session_id);
CREATE INDEX idx_responses_question_id ON responses(question_id);
```

---

### 3.5 `analysis_results`

One row per response; stores all AI module outputs.

```sql
CREATE TABLE analysis_results (
    id                  SERIAL PRIMARY KEY,
    response_id         INTEGER NOT NULL
                        REFERENCES responses(id) ON DELETE CASCADE UNIQUE,

    -- EMOTION ANALYSIS
    emotion_dominant    VARCHAR(50),
    -- e.g., 'neutral', 'fearful', 'happy'
    emotion_scores      JSONB,
    -- {"neutral": 62.3, "happy": 15.1, "sad": 5.2,
    --  "angry": 2.1, "surprised": 8.0, "fearful": 7.3}
    emotion_score       INTEGER,
    -- 0-100 derived composite score
    emotion_status      VARCHAR(20) DEFAULT 'pending',
    -- 'pending' | 'complete' | 'failed'

    -- VOICE ANALYSIS
    transcript          TEXT,
    filler_count        INTEGER,
    filler_words_found  JSONB,
    -- [{"word": "um", "count": 3, "positions": [12, 45, 88]}]
    wpm                 INTEGER,
    clarity_score       INTEGER,
    -- 0-100
    voice_tone_label    VARCHAR(50),
    -- 'Confident' | 'Moderate' | 'Nervous'
    voice_status        VARCHAR(20) DEFAULT 'pending',

    -- POSTURE ANALYSIS
    posture_score       INTEGER,
    -- 0-100
    posture_label       VARCHAR(20),
    -- 'Good' | 'Fair' | 'Poor'
    posture_frames_analyzed INTEGER,
    posture_status      VARCHAR(20) DEFAULT 'pending',

    -- ANSWER QUALITY
    answer_relevance_score INTEGER,
    -- 0-100
    keywords_found      JSONB,
    -- ["Python", "supervised learning"]
    keywords_expected   JSONB,
    -- ["machine learning", "model", "training data"]
    answer_status       VARCHAR(20) DEFAULT 'pending',

    -- COMPOSITE
    confidence_score    INTEGER,
    -- 0-100
    confidence_label    VARCHAR(20),
    -- 'High' | 'Moderate' | 'Low'

    analyzed_at         TIMESTAMP DEFAULT NOW()
);
```

**Status columns per module:** Allow partial analysis. Each module writes its own status independently so pipeline failures in one do not block others.

---

### 3.6 `reports`

One final compiled report per session.

```sql
CREATE TABLE reports (
    id                  SERIAL PRIMARY KEY,
    session_id          INTEGER NOT NULL
                        REFERENCES sessions(id) ON DELETE CASCADE UNIQUE,

    -- AGGREGATE SCORES
    overall_score       INTEGER,
    emotion_score       INTEGER,
    voice_score         INTEGER,
    posture_score       INTEGER,
    answer_quality_score INTEGER,
    confidence_score    INTEGER,
    confidence_label    VARCHAR(20),

    -- SUGGESTIONS
    suggestions_json    JSONB,
    -- [{"category": "voice", "priority": 1,
    --   "message": "Reduce filler words..."}]

    -- STORAGE
    report_html         TEXT,
    -- full rendered HTML; cached for re-display
    report_pdf_path     VARCHAR(512),
    -- absolute path to saved PDF file

    generated_at        TIMESTAMP DEFAULT NOW()
);
```

---

## 4. Index Strategy

| Table | Index | Purpose |
|---|---|---|
| `candidates` | `email` | Future user lookup by email |
| `sessions` | `candidate_id` | Retrieve all sessions for a candidate |
| `sessions` | `status` | Filter sessions by pipeline state |
| `questions` | `session_id` | Retrieve all questions for a session |
| `responses` | `session_id` | Retrieve all responses for a session |
| `responses` | `question_id` | Join responses to questions |

---

## 5. SQLAlchemy ORM Models (Python)

```python
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, BigInteger, \
                       ForeignKey, Timestamp, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app import db

class Candidate(db.Model):
    __tablename__ = 'candidates'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255))
    resume_filename = Column(String(255), nullable=False)
    resume_path = Column(String(512), nullable=False)
    skills_raw = Column(Text)
    skills_json = Column(JSONB)
    resume_text = Column(Text)
    created_at = Column(Timestamp, default=datetime.utcnow)
    sessions = relationship('Session', backref='candidate', lazy=True)

class Session(db.Model):
    __tablename__ = 'sessions'
    id = Column(Integer, primary_key=True)
    candidate_id = Column(Integer, ForeignKey('candidates.id'), nullable=False)
    status = Column(String(50), default='created')
    question_count = Column(Integer, default=0)
    started_at = Column(Timestamp)
    completed_at = Column(Timestamp)
    analysis_started_at = Column(Timestamp)
    analysis_completed_at = Column(Timestamp)
    created_at = Column(Timestamp, default=datetime.utcnow)
    questions = relationship('Question', backref='session', lazy=True)
    responses = relationship('Response', backref='session', lazy=True)

class Question(db.Model):
    __tablename__ = 'questions'
    __table_args__ = (UniqueConstraint('session_id', 'sequence'),)
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('sessions.id'), nullable=False)
    sequence = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    category = Column(String(50))
    skill_tag = Column(String(100))
    source = Column(String(50), default='bank')
    created_at = Column(Timestamp, default=datetime.utcnow)

class Response(db.Model):
    __tablename__ = 'responses'
    __table_args__ = (UniqueConstraint('session_id', 'question_id'),)
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('sessions.id'), nullable=False)
    question_id = Column(Integer, ForeignKey('questions.id'), nullable=False)
    video_path = Column(String(512))
    audio_path = Column(String(512))
    recording_duration_sec = Column(Float)
    file_size_bytes = Column(BigInteger)
    upload_status = Column(String(50), default='pending')
    recorded_at = Column(Timestamp, default=datetime.utcnow)
    analysis = relationship('AnalysisResult', backref='response',
                            uselist=False, lazy=True)

class AnalysisResult(db.Model):
    __tablename__ = 'analysis_results'
    id = Column(Integer, primary_key=True)
    response_id = Column(Integer, ForeignKey('responses.id'),
                         nullable=False, unique=True)
    emotion_dominant = Column(String(50))
    emotion_scores = Column(JSONB)
    emotion_score = Column(Integer)
    emotion_status = Column(String(20), default='pending')
    transcript = Column(Text)
    filler_count = Column(Integer)
    filler_words_found = Column(JSONB)
    wpm = Column(Integer)
    clarity_score = Column(Integer)
    voice_tone_label = Column(String(50))
    voice_status = Column(String(20), default='pending')
    posture_score = Column(Integer)
    posture_label = Column(String(20))
    posture_frames_analyzed = Column(Integer)
    posture_status = Column(String(20), default='pending')
    answer_relevance_score = Column(Integer)
    keywords_found = Column(JSONB)
    keywords_expected = Column(JSONB)
    answer_status = Column(String(20), default='pending')
    confidence_score = Column(Integer)
    confidence_label = Column(String(20))
    analyzed_at = Column(Timestamp, default=datetime.utcnow)

class Report(db.Model):
    __tablename__ = 'reports'
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('sessions.id'),
                        nullable=False, unique=True)
    overall_score = Column(Integer)
    emotion_score = Column(Integer)
    voice_score = Column(Integer)
    posture_score = Column(Integer)
    answer_quality_score = Column(Integer)
    confidence_score = Column(Integer)
    confidence_label = Column(String(20))
    suggestions_json = Column(JSONB)
    report_html = Column(Text)
    report_pdf_path = Column(String(512))
    generated_at = Column(Timestamp, default=datetime.utcnow)
```

---

## 6. Data Retention Policy

| Data | Retention | Rationale |
|---|---|---|
| `resume_path` (file) | Until session analyzed; optional user-controlled deletion | Privacy; large files |
| `video_path` (file) | Until report generated; purge after PDF export | Storage cost (~180MB/session) |
| `audio_path` (file) | Until voice analysis complete; then purge | Audio is smaller; purge after transcription |
| `report_html` (DB column) | Indefinite | Fast re-render without re-running analysis |
| `report_pdf_path` (file) | Indefinite or until user downloads | User may download multiple times |
| `analysis_results` (DB rows) | Indefinite | Required for report re-generation |

**Engineering Assumption:** No automated purge in MVP. Storage is managed manually. A TTL-based cleanup job should be added in v2.

---

## 7. Migration Strategy

The project uses SQLAlchemy's `db.create_all()` for initial setup in development. For production, Flask-Migrate (Alembic) is used:

```bash
flask db init          # one-time
flask db migrate -m "initial schema"
flask db upgrade
```

All schema changes in future versions must go through Alembic migration files — direct table alterations on production are prohibited.

---

*Source: Interview Ninja project documentation, A.C. Patil College of Engineering.*
