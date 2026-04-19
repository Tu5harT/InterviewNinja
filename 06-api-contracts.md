# 06 — API Contracts
**Project:** Interview Ninja — AI-Powered Mock Interview Assistant  
**Version:** 1.0

---

## 1. Conventions

| Convention | Value |
|---|---|
| Base URL | `http://localhost:5000/api/v1` |
| Content-Type (default) | `application/json` |
| Content-Type (file upload) | `multipart/form-data` |
| Auth (MVP) | Server-side Flask session cookie |
| Date format | ISO 8601: `2026-04-01T14:32:00Z` |

### Standard Response Envelope

**Success:**
```json
{
  "error": false,
  "data": { }
}
```

**Error:**
```json
{
  "error": true,
  "code": "ERROR_CODE",
  "message": "Human-readable message.",
  "details": { }
}
```

### Standard Error Codes

| Code | HTTP Status | Meaning |
|---|---|---|
| `INVALID_FILE_TYPE` | 422 | File not PDF or DOCX |
| `FILE_TOO_LARGE` | 413 | File exceeds 10MB |
| `PARSE_FAILED` | 422 | Resume text could not be extracted |
| `SESSION_NOT_FOUND` | 404 | session_id does not exist |
| `NO_SESSION` | 401 | No active session cookie |
| `ANALYSIS_NOT_READY` | 409 | Report requested before analysis complete |
| `UPLOAD_FAILED` | 500 | Media blob could not be saved |
| `VALIDATION_ERROR` | 422 | Request body failed schema validation |

---

## 2. Resume Endpoints

### `POST /api/v1/resume/upload`

Upload and parse a candidate resume. Creates a `candidates` record and returns extracted data.

**Request:** `multipart/form-data`

| Field | Type | Required | Notes |
|---|---|---|---|
| `file` | Binary | ✅ | PDF or DOCX; max 10MB |

**Response 200 — Success:**
```json
{
  "error": false,
  "data": {
    "candidate_id": 42,
    "name": "Aditya Arote",
    "skills": [
      {"skill": "Python", "category": "language"},
      {"skill": "Machine Learning", "category": "domain"},
      {"skill": "OpenCV", "category": "library"},
      {"skill": "Flask", "category": "framework"},
      {"skill": "TensorFlow", "category": "library"}
    ],
    "skills_count": 5,
    "education": "B.E. in AI & Data Science, A.C. Patil College, 2026",
    "resume_filename": "aditya_resume.pdf"
  }
}
```

**Response 422 — Invalid file type:**
```json
{
  "error": true,
  "code": "INVALID_FILE_TYPE",
  "message": "Only PDF and DOCX files are accepted. Received: .jpg"
}
```

**Response 413 — File too large:**
```json
{
  "error": true,
  "code": "FILE_TOO_LARGE",
  "message": "File exceeds the 10MB limit. Uploaded file: 14.3MB"
}
```

**Response 422 — Parse failed:**
```json
{
  "error": true,
  "code": "PARSE_FAILED",
  "message": "Could not extract text from this resume. Try a different format.",
  "details": {"fallback": "generic_questions_will_be_used"}
}
```

---

## 3. Session Endpoints

### `POST /api/v1/session/start`

Create a new interview session for a candidate. Generates questions based on extracted skills.

**Request Body:**
```json
{
  "candidate_id": 42
}
```

**Response 201 — Created:**
```json
{
  "error": false,
  "data": {
    "session_id": 7,
    "status": "in_progress",
    "questions": [
      {
        "id": 101,
        "sequence": 1,
        "text": "Explain the difference between supervised and unsupervised learning.",
        "category": "technical",
        "skill_tag": "Machine Learning"
      },
      {
        "id": 102,
        "sequence": 2,
        "text": "Describe a project where you used Python for data processing.",
        "category": "technical",
        "skill_tag": "Python"
      },
      {
        "id": 103,
        "sequence": 3,
        "text": "Tell me about a time you had to work under a tight deadline.",
        "category": "behavioral",
        "skill_tag": null
      }
    ],
    "total_questions": 10,
    "max_response_seconds": 90
  }
}
```

**Response 404 — Candidate not found:**
```json
{
  "error": true,
  "code": "SESSION_NOT_FOUND",
  "message": "Candidate with id 42 not found."
}
```

---

### `POST /api/v1/session/upload-response`

Upload a recorded video blob for a specific question in a session.

**Request:** `multipart/form-data`

| Field | Type | Required | Notes |
|---|---|---|---|
| `session_id` | Integer | ✅ | |
| `question_id` | Integer | ✅ | |
| `video` | Binary | ✅ | `.webm` blob from MediaRecorder |
| `duration_sec` | Float | Optional | Client-reported duration |

**Response 200 — Saved:**
```json
{
  "error": false,
  "data": {
    "response_id": 55,
    "session_id": 7,
    "question_id": 101,
    "video_path": "recordings/7/q1.webm",
    "audio_extracted": true,
    "audio_path": "recordings/7/q1.wav",
    "upload_status": "uploaded",
    "next_question_sequence": 2
  }
}
```

**Response 500 — Upload failed:**
```json
{
  "error": true,
  "code": "UPLOAD_FAILED",
  "message": "Failed to save response for question 101. Please retry."
}
```

---

### `POST /api/v1/session/complete`

Mark the session as complete and trigger the async AI analysis pipeline.

**Request Body:**
```json
{
  "session_id": 7
}
```

**Response 202 — Accepted (analysis started):**
```json
{
  "error": false,
  "data": {
    "session_id": 7,
    "status": "analyzing",
    "responses_submitted": 10,
    "estimated_duration_seconds": 180,
    "poll_url": "/api/v1/analysis/status/7"
  }
}
```

**Response 409 — Not all responses uploaded:**
```json
{
  "error": true,
  "code": "VALIDATION_ERROR",
  "message": "Cannot complete session. 3 of 10 questions have no response recorded.",
  "details": {"missing_question_sequences": [4, 7, 9]}
}
```

---

## 4. Analysis Endpoints

### `GET /api/v1/analysis/status/{session_id}`

Poll the AI analysis pipeline status. Called every 5 seconds by the frontend.

**Response 200 — In progress:**
```json
{
  "error": false,
  "data": {
    "session_id": 7,
    "status": "analyzing",
    "progress_percent": 60,
    "modules_complete": ["emotion", "posture"],
    "modules_pending": ["voice", "answer_quality"],
    "modules_failed": [],
    "elapsed_seconds": 87
  }
}
```

**Response 200 — Complete:**
```json
{
  "error": false,
  "data": {
    "session_id": 7,
    "status": "analyzed",
    "progress_percent": 100,
    "modules_complete": ["emotion", "voice", "posture", "answer_quality"],
    "modules_failed": [],
    "report_url": "/api/v1/report/7"
  }
}
```

**Response 200 — Partial failure:**
```json
{
  "error": false,
  "data": {
    "session_id": 7,
    "status": "analyzed",
    "progress_percent": 100,
    "modules_complete": ["emotion", "posture", "answer_quality"],
    "modules_failed": ["voice"],
    "report_url": "/api/v1/report/7",
    "warnings": ["Voice analysis failed. Transcript and clarity scores unavailable."]
  }
}
```

**Response 200 — Full failure:**
```json
{
  "error": false,
  "data": {
    "session_id": 7,
    "status": "failed",
    "message": "Analysis timed out. Please contact support or retry."
  }
}
```

---

## 5. Report Endpoints

### `GET /api/v1/report/{session_id}`

Retrieve the full performance report as JSON.

**Response 200 — Full report:**
```json
{
  "error": false,
  "data": {
    "session_id": 7,
    "candidate_name": "Aditya Arote",
    "generated_at": "2026-04-01T14:32:00Z",
    "scores": {
      "overall": 73,
      "emotion": 68,
      "voice": 70,
      "posture": 82,
      "answer_quality": 75,
      "confidence": 66,
      "confidence_label": "Moderate"
    },
    "questions": [
      {
        "sequence": 1,
        "question_text": "Explain supervised vs unsupervised learning.",
        "category": "technical",
        "skill_tag": "Machine Learning",
        "transcript": "Um, supervised learning is like, when you have labelled data...",
        "emotion_dominant": "fearful",
        "emotion_scores": {
          "neutral": 35.0,
          "fearful": 40.2,
          "happy": 10.1,
          "sad": 8.5,
          "angry": 3.1,
          "surprised": 3.1
        },
        "emotion_score": 52,
        "filler_count": 4,
        "filler_words": [
          {"word": "um", "count": 2},
          {"word": "like", "count": 2}
        ],
        "wpm": 112,
        "clarity_score": 62,
        "voice_tone_label": "Nervous",
        "posture_score": 78,
        "posture_label": "Fair",
        "answer_relevance_score": 70,
        "keywords_found": ["supervised", "labelled", "model"],
        "keywords_expected": ["training data", "labels", "prediction", "classification"]
      }
    ],
    "session_emotion_distribution": {
      "neutral": 48.2,
      "happy": 12.3,
      "sad": 10.1,
      "fearful": 19.8,
      "angry": 5.2,
      "surprised": 4.4
    },
    "suggestions": [
      {
        "category": "voice",
        "priority": 1,
        "message": "You used filler words 18 times across the session. Practice pausing silently instead of saying 'um' or 'like'. Record yourself and listen back."
      },
      {
        "category": "emotion",
        "priority": 2,
        "message": "Your dominant emotion was 'fearful' in 6 of 10 questions. Practice deep breathing before interviews and repeat mock sessions to build familiarity."
      },
      {
        "category": "answer_quality",
        "priority": 3,
        "message": "Your answer quality score was 75/100. Structure answers using the STAR method and ensure you cover key technical keywords."
      }
    ],
    "modules_failed": []
  }
}
```

**Response 409 — Report not ready:**
```json
{
  "error": true,
  "code": "ANALYSIS_NOT_READY",
  "message": "Analysis is still running. Poll /api/v1/analysis/status/7 for updates."
}
```

**Response 404 — Session not found:**
```json
{
  "error": true,
  "code": "SESSION_NOT_FOUND",
  "message": "No session found with id 7."
}
```

---

### `GET /api/v1/report/{session_id}/pdf`

Download the report as a PDF file.

**Response 200:**
```
Content-Type: application/pdf
Content-Disposition: attachment; filename="interview_report_7.pdf"

<binary PDF stream>
```

**Response 503 — PDF generation unavailable:**
```json
{
  "error": true,
  "code": "PDF_UNAVAILABLE",
  "message": "PDF export failed. You can print the report page from your browser."
}
```

---

## 6. API Endpoint Summary

| Method | Endpoint | Purpose | Auth |
|---|---|---|---|
| `POST` | `/api/v1/resume/upload` | Upload and parse resume | None (MVP) |
| `POST` | `/api/v1/session/start` | Create session + generate questions | Session cookie |
| `POST` | `/api/v1/session/upload-response` | Upload question response video | Session cookie |
| `POST` | `/api/v1/session/complete` | Trigger AI analysis | Session cookie |
| `GET` | `/api/v1/analysis/status/{session_id}` | Poll analysis progress | Session cookie |
| `GET` | `/api/v1/report/{session_id}` | Retrieve full report JSON | Session cookie |
| `GET` | `/api/v1/report/{session_id}/pdf` | Download PDF report | Session cookie |

---

## 7. Rate Limiting (Engineering Assumption)

| Endpoint | Limit | Window |
|---|---|---|
| `POST /resume/upload` | 5 requests | Per 10 minutes per IP |
| `POST /session/upload-response` | 30 requests | Per session |
| `GET /analysis/status/*` | 60 requests | Per 5 minutes |
| `GET /report/*/pdf` | 10 requests | Per hour |

---

*Source: Interview Ninja project documentation, A.C. Patil College of Engineering.*
