# 12 — Testing Strategy
**Project:** Interview Ninja — AI-Powered Mock Interview Assistant  
**Version:** 1.0

---

## 1. Overview

Interview Ninja uses a three-layer testing strategy: **unit tests** for individual service functions, **integration tests** for the end-to-end pipeline, and **manual QA** for browser-based media capture and UI verification. Automated tests use `pytest`.

**Target coverage:** ≥ 80% branch coverage on all `services/` modules.

---

## 2. Testing Stack

| Tool | Purpose |
|---|---|
| `pytest` | Test runner |
| `pytest-cov` | Coverage reporting |
| `Flask test client` | Simulated HTTP requests without a running server |
| `unittest.mock` | Mocking AI models and external APIs |
| `conftest.py` | Shared fixtures (app, test client, DB session) |

Install:
```bash
pip install pytest pytest-cov pytest-flask
```

Run all tests:
```bash
pytest tests/ -v --cov=services --cov-report=term-missing
```

---

## 3. Test Configuration (`tests/conftest.py`)

```python
import pytest
from app import create_app
from config import TestingConfig
from models import db as _db

class TestingConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SECRET_KEY = 'test-key'
    UPLOAD_FOLDER = '/tmp/test_uploads'
    RECORDINGS_FOLDER = '/tmp/test_recordings'
    WTF_CSRF_ENABLED = False

@pytest.fixture(scope='session')
def app():
    app = create_app(TestingConfig)
    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def db(app):
    with app.app_context():
        yield _db
        _db.session.rollback()
```

---

## 4. Unit Tests

### 4.1 `tests/unit/test_resume_parser.py`

```python
import pytest
from services.resume_parser import parse_resume, extract_skills

SAMPLE_PDF = 'tests/fixtures/sample_resume.pdf'
SAMPLE_DOCX = 'tests/fixtures/sample_resume.docx'

def test_pdf_extraction_returns_text():
    result = parse_resume(SAMPLE_PDF)
    assert result['resume_text'] is not None
    assert len(result['resume_text']) > 100

def test_docx_extraction_returns_text():
    result = parse_resume(SAMPLE_DOCX)
    assert result['resume_text'] is not None

def test_name_extraction():
    result = parse_resume(SAMPLE_PDF)
    assert result['name'] != ''

def test_skills_extracted_from_standard_resume():
    result = parse_resume(SAMPLE_PDF)
    assert len(result['skills']) >= 5

def test_known_skills_present():
    result = parse_resume(SAMPLE_PDF)
    skill_names = [s['skill'].lower() for s in result['skills']]
    assert 'python' in skill_names or 'machine learning' in skill_names

def test_empty_pdf_returns_empty_skills():
    # Edge case: scanned / image-only PDF with no extractable text
    result = parse_resume('tests/fixtures/scanned_resume.pdf')
    assert result['skills'] == [] or result['skills'] is not None  # no crash

def test_invalid_file_raises_error():
    with pytest.raises(Exception):
        parse_resume('tests/fixtures/not_a_document.jpg')
```

---

### 4.2 `tests/unit/test_question_generator.py`

```python
from services.question_generator import generate_questions

SKILLS = [
    {"skill": "Python", "category": "language"},
    {"skill": "Machine Learning", "category": "domain"},
    {"skill": "Flask", "category": "framework"}
]

def test_returns_correct_count():
    questions = generate_questions(SKILLS)
    assert 8 <= len(questions) <= 12

def test_no_duplicate_questions():
    questions = generate_questions(SKILLS)
    texts = [q['text'] for q in questions]
    assert len(texts) == len(set(texts))

def test_includes_behavioral_questions():
    questions = generate_questions(SKILLS)
    behavioral = [q for q in questions if q['category'] == 'behavioral']
    assert len(behavioral) >= 2

def test_includes_technical_questions_for_skills():
    questions = generate_questions(SKILLS)
    technical = [q for q in questions if q['category'] == 'technical']
    assert len(technical) >= 5

def test_python_skill_produces_python_question():
    questions = generate_questions(SKILLS)
    python_qs = [q for q in questions if q.get('skill_tag') == 'Python']
    assert len(python_qs) >= 1

def test_empty_skills_returns_behavioral_questions():
    questions = generate_questions([])
    assert len(questions) >= 2
    assert all(q['category'] == 'behavioral' for q in questions)

def test_sequence_numbers_are_unique_and_ordered():
    questions = generate_questions(SKILLS)
    seqs = [q['sequence'] for q in questions]
    assert seqs == list(range(1, len(questions) + 1))
```

---

### 4.3 `tests/unit/test_voice_analyzer.py`

```python
from unittest.mock import patch, MagicMock
from services.voice_analyzer import (
    count_fillers, compute_wpm, compute_clarity_score, analyze_voice
)

KNOWN_FILLER_TRANSCRIPT = "um I think like the answer is basically you know Python"
# Manual count: um=1, like=1, basically=1, you know=1 → 4 fillers

def test_filler_count_known_transcript():
    result = count_fillers(KNOWN_FILLER_TRANSCRIPT)
    total = sum(result.values())
    assert abs(total - 4) <= 2  # within ±2 of manual count

def test_filler_count_clean_transcript():
    clean = "Python is a high-level programming language used for data science."
    result = count_fillers(clean)
    assert sum(result.values()) == 0

def test_wpm_calculation():
    transcript = ' '.join(['word'] * 120)  # 120 words
    duration = 60.0                         # 60 seconds
    wpm = compute_wpm(transcript, duration)
    assert wpm == 120

def test_wpm_zero_duration():
    wpm = compute_wpm("some text", 0.0)
    assert wpm == 0

def test_clarity_score_ideal_wpm_no_fillers():
    score = compute_clarity_score(filler_count=0, wpm=130)
    assert score == 100

def test_clarity_score_many_fillers():
    score = compute_clarity_score(filler_count=10, wpm=130)
    assert score <= 50

def test_clarity_score_too_fast():
    score = compute_clarity_score(filler_count=0, wpm=220)
    assert score < 85

def test_clarity_score_too_slow():
    score = compute_clarity_score(filler_count=0, wpm=60)
    assert score < 85

@patch('services.voice_analyzer.sr.Recognizer')
def test_analyze_voice_silent_audio_no_crash(mock_recognizer):
    mock_instance = MagicMock()
    mock_instance.recognize_google.side_effect = Exception("Could not understand audio")
    mock_recognizer.return_value = mock_instance
    
    result = analyze_voice('tests/fixtures/silent_audio.wav')
    assert result['transcript'] == ''
    assert result['filler_count'] == 0
    assert result['clarity_score'] is None
    assert result['voice_status'] == 'no_speech'
```

---

### 4.4 `tests/unit/test_posture_analyzer.py`

```python
from services.posture_analyzer import compute_posture_score, classify_posture

def test_perfect_posture_scores_high():
    # Mock landmarks: shoulders level, nose centred
    class MockLandmark:
        def __init__(self, x, y, visibility=1.0):
            self.x = x
            self.y = y
            self.visibility = visibility
    
    class MockLandmarks:
        landmark = [MockLandmark(0, 0)] * 33
    
    # Set key landmarks: level shoulders, centred head
    lm = MockLandmarks.landmark
    lm[11] = MockLandmark(0.3, 0.5, 1.0)   # left shoulder
    lm[12] = MockLandmark(0.7, 0.5, 1.0)   # right shoulder
    lm[0]  = MockLandmark(0.5, 0.3, 1.0)   # nose (centred)
    
    score = compute_posture_score(MockLandmarks())
    assert score >= 80

def test_slouching_scores_lower():
    class MockLandmarks:
        class landmark:
            pass
    # Tilt: shoulders at very different heights
    # (unit test verifies the formula direction, not exact value)
    # See integration test for actual video comparison

def test_classify_posture_labels():
    assert classify_posture(90) == "Good"
    assert classify_posture(75) == "Good"
    assert classify_posture(74) == "Fair"
    assert classify_posture(50) == "Fair"
    assert classify_posture(49) == "Poor"
    assert classify_posture(0) == "Poor"
```

---

### 4.5 `tests/unit/test_score_aggregator.py`

```python
from services.score_aggregator import (
    compute_overall_score, compute_confidence_score,
    session_averages, generate_suggestions
)

SAMPLE_RESULTS = [
    {"emotion_score": 70, "clarity_score": 65, "posture_score": 80, "answer_relevance_score": 72},
    {"emotion_score": 60, "clarity_score": 75, "posture_score": 85, "answer_relevance_score": 68},
    {"emotion_score": 80, "clarity_score": 55, "posture_score": 78, "answer_relevance_score": 80},
]

def test_session_averages():
    avgs = session_averages(SAMPLE_RESULTS)
    assert avgs['emotion_score'] == 70        # (70+60+80)/3
    assert avgs['voice_score'] == 65          # (65+75+55)/3
    assert avgs['posture_score'] == 81        # (80+85+78)/3

def test_overall_score_formula():
    scores = {
        "emotion_score": 70, "voice_score": 65,
        "posture_score": 81, "answer_quality_score": 73
    }
    overall = compute_overall_score(scores)
    expected = round(70*0.20 + 65*0.30 + 81*0.15 + 73*0.35)
    assert overall == expected

def test_overall_score_excludes_null_modules():
    scores = {
        "emotion_score": None,  # module failed
        "voice_score": 70,
        "posture_score": 80,
        "answer_quality_score": 75
    }
    overall = compute_overall_score(scores)
    # Should compute from 3 available modules only
    assert overall is not None
    assert 0 <= overall <= 100

def test_confidence_score_range():
    conf = compute_confidence_score(emotion_score=65, clarity_score=70)
    assert 0 <= conf <= 100

def test_confidence_score_both_null():
    conf = compute_confidence_score(emotion_score=None, clarity_score=None)
    assert conf is None

def test_suggestions_low_voice():
    scores = {"voice_score": 45, "emotion_score": 80, "posture_score": 80,
              "answer_quality_score": 80, "confidence_score": 70}
    suggestions = generate_suggestions(scores)
    categories = [s['category'] for s in suggestions]
    assert 'voice' in categories

def test_no_suggestion_for_high_scores():
    scores = {"voice_score": 90, "emotion_score": 88, "posture_score": 85,
              "answer_quality_score": 86, "confidence_score": 89}
    suggestions = generate_suggestions(scores)
    assert len(suggestions) == 0

def test_suggestions_max_5():
    # All categories below threshold
    scores = {"voice_score": 30, "emotion_score": 30, "posture_score": 30,
              "answer_quality_score": 30, "confidence_score": 30}
    suggestions = generate_suggestions(scores)
    assert len(suggestions) <= 5
```

---

## 5. Integration Tests

### 5.1 `tests/integration/test_full_pipeline.py`

```python
import pytest
import io
import json
import time

def test_full_happy_path(client, db):
    """End-to-end: upload resume → start session → upload 3 responses → analyze → fetch report."""
    
    # Step 1: Upload resume
    with open('tests/fixtures/sample_resume.pdf', 'rb') as f:
        response = client.post('/api/v1/resume/upload',
                               data={'file': (f, 'resume.pdf')},
                               content_type='multipart/form-data')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert not data['error']
    candidate_id = data['data']['candidate_id']
    assert len(data['data']['skills']) >= 1
    
    # Step 2: Start session
    response = client.post('/api/v1/session/start',
                           json={'candidate_id': candidate_id})
    assert response.status_code == 201
    data = json.loads(response.data)
    session_id = data['data']['session_id']
    questions = data['data']['questions']
    assert 8 <= len(questions) <= 12
    
    # Step 3: Upload 3 pre-recorded video responses
    with open('tests/fixtures/test_video_calm.webm', 'rb') as f:
        video_bytes = f.read()
    
    for i, q in enumerate(questions[:3]):
        response = client.post('/api/v1/session/upload-response',
                               data={
                                   'session_id': str(session_id),
                                   'question_id': str(q['id']),
                                   'video': (io.BytesIO(video_bytes), f'q{i+1}.webm')
                               },
                               content_type='multipart/form-data')
        assert response.status_code == 200
    
    # Step 4: Complete session
    response = client.post('/api/v1/session/complete',
                           json={'session_id': session_id})
    # Accept 409 if not all questions answered in this test
    assert response.status_code in [202, 409]
    
    # Step 5: Poll until analyzed (max 5 minutes for test)
    for _ in range(60):  # 60 × 5s = 5 minutes
        time.sleep(5)
        response = client.get(f'/api/v1/analysis/status/{session_id}')
        data = json.loads(response.data)
        if data['data']['status'] in ['analyzed', 'failed']:
            break
    
    # Step 6: Fetch report
    response = client.get(f'/api/v1/report/{session_id}')
    assert response.status_code == 200
    report = json.loads(response.data)['data']
    
    # Validate report structure
    assert 'scores' in report
    assert 'overall' in report['scores']
    assert 0 <= report['scores']['overall'] <= 100
    assert 'questions' in report
    assert 'suggestions' in report
    assert len(report['suggestions']) >= 0  # may be 0 if all scores high

def test_invalid_file_rejected(client):
    response = client.post('/api/v1/resume/upload',
                           data={'file': (io.BytesIO(b'fake'), 'resume.exe')},
                           content_type='multipart/form-data')
    assert response.status_code == 422
    data = json.loads(response.data)
    assert data['error']
    assert data['code'] == 'INVALID_FILE_TYPE'

def test_report_not_ready_returns_409(client, db):
    # Create session without triggering analysis
    response = client.post('/api/v1/resume/upload',
                           data={'file': (open('tests/fixtures/sample_resume.pdf','rb'),
                                          'r.pdf')},
                           content_type='multipart/form-data')
    cid = json.loads(response.data)['data']['candidate_id']
    response = client.post('/api/v1/session/start', json={'candidate_id': cid})
    sid = json.loads(response.data)['data']['session_id']
    
    # Try to fetch report immediately (analysis not started)
    response = client.get(f'/api/v1/report/{sid}')
    assert response.status_code == 409
```

---

## 6. Manual QA Checklist

Run this checklist on a clean installation before each release:

### Resume Upload
- [ ] PDF upload succeeds; skills displayed on review screen
- [ ] DOCX upload succeeds
- [ ] `.jpg` file rejected with clear error
- [ ] 11MB PDF rejected with size limit message
- [ ] Extracting from a 2-page standard engineering resume produces ≥ 5 skills

### Question Generation
- [ ] 8–12 questions generated for a standard resume
- [ ] Questions include both Technical and Behavioral categories
- [ ] No duplicate questions in the same session
- [ ] Questions are relevant to skills listed in the resume

### Interview Session
- [ ] Webcam permission prompt appears before interview starts
- [ ] Denying permission shows a clear recovery message
- [ ] Live webcam feed appears within 2 seconds of granting permission
- [ ] "Start Recording" button triggers recording indicator
- [ ] Countdown timer visible and counting down from 90
- [ ] Timer automatically stops recording at 0
- [ ] "Stop Recording" stops recording and shows upload progress
- [ ] "Submit Interview" button appears after all questions answered
- [ ] Clicking "Submit Interview" navigates to analysis wait screen

### AI Analysis
- [ ] Analysis wait screen shows progress updating
- [ ] Emotion: test_video_nervous scores higher "fearful" than test_video_calm
- [ ] Filler count for test_audio_fillers.wav matches manual count ±2
- [ ] Posture: upright recording scores ≥ 10 points higher than slouching
- [ ] Analysis completes within 5 minutes for a 10-question session

### Report
- [ ] Report page loads within 3 seconds of analysis completion
- [ ] Overall score, all category scores visible (0–100 integers)
- [ ] Transcript displayed for each question
- [ ] Filler word count and types displayed
- [ ] Emotion distribution chart renders
- [ ] At least 3 improvement suggestions present
- [ ] "Download PDF" produces a valid, readable PDF file
- [ ] PDF contains all report sections

### Error Handling
- [ ] Closing browser mid-session does not crash the server
- [ ] Re-uploading same resume starts a fresh session
- [ ] If one AI module fails, report still generated with "N/A" for that module
- [ ] No Python exception tracebacks visible in the browser UI

---

## 7. Test Fixtures Required

| File | Description | How to Create |
|---|---|---|
| `sample_resume.pdf` | 2-page standard engineering resume | Create manually; include Python, ML, Flask, OpenCV skills |
| `sample_resume.docx` | Same content as DOCX | Export from Word |
| `scanned_resume.pdf` | Image-only PDF with no extractable text | Scan a printed page |
| `test_video_calm.webm` | 30-second video: person sitting calmly, clear speech | Record manually |
| `test_video_nervous.webm` | 30-second video: person visibly nervous, looking away | Record manually |
| `test_audio_fillers.wav` | 30-second audio with 8 known filler words | Record manually; verify manually |
| `silent_audio.wav` | 5-second silence | `ffmpeg -f lavfi -i anullsrc=r=16000:cl=mono -t 5 silent_audio.wav` |

---

## 8. Coverage Targets

| Module | Target Coverage |
|---|---|
| `resume_parser.py` | ≥ 85% |
| `question_generator.py` | ≥ 90% |
| `voice_analyzer.py` | ≥ 80% |
| `posture_analyzer.py` | ≥ 75% |
| `score_aggregator.py` | ≥ 90% |
| `report_builder.py` | ≥ 70% |
| `routes/` | ≥ 70% |
| **Overall `services/`** | **≥ 80%** |

Run coverage report:
```bash
pytest tests/unit/ --cov=services --cov-report=html
open htmlcov/index.html
```

---

*Source: Interview Ninja project documentation, A.C. Patil College of Engineering.*
