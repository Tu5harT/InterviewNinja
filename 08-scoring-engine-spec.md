# 08 — Scoring Engine Specification
**Project:** Interview Ninja — AI-Powered Mock Interview Assistant  
**Version:** 1.0

---

## 1. Overview

The scoring engine aggregates outputs from four independent AI analysis modules into a unified set of scores per question and per session. The output feeds the performance report and drives the improvement suggestion engine.

All scores are integers in the range **0–100**. Higher is always better. Scores are never negative or above 100.

---

## 2. Score Architecture

```
Per Question:
┌─────────────────────────────────────────────────────────┐
│  QUESTION RESPONSE                                      │
│                                                         │
│  Emotion Analyzer  ──▶  emotion_score     (0-100)       │
│  Voice Analyzer    ──▶  clarity_score     (0-100)       │
│  Posture Analyzer  ──▶  posture_score     (0-100)       │
│  Answer Analyzer   ──▶  relevance_score   (0-100)       │
│                                                         │
│  Confidence Score ← f(emotion_score, voice energy)      │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼ (averaged across all questions)
Per Session:
┌─────────────────────────────────────────────────────────┐
│  session_emotion_score  = avg(emotion_score per Q)      │
│  session_voice_score    = avg(clarity_score per Q)      │
│  session_posture_score  = avg(posture_score per Q)      │
│  session_answer_score   = avg(relevance_score per Q)    │
│  session_confidence     = avg(confidence_score per Q)   │
│                                                         │
│  OVERALL SCORE (weighted):                              │
│  = emotion  × 0.20                                      │
│  + voice    × 0.30                                      │
│  + posture  × 0.15                                      │
│  + answer   × 0.35                                      │
└─────────────────────────────────────────────────────────┘
```

---

## 3. Module 1: Emotion Score

### 3.1 Input
- Per-frame emotion probability vectors from DeepFace
- Format: `[{"neutral": 62.3, "happy": 15.1, "sad": 5.2, "angry": 2.1, "surprised": 8.0, "fearful": 7.3}, ...]`

### 3.2 Frame Aggregation
Average each emotion class across all analyzed frames:
```python
def aggregate_emotion_frames(frames: list[dict]) -> dict:
    if not frames:
        return {}
    keys = frames[0].keys()
    return {k: sum(f[k] for f in frames) / len(frames) for k in keys}
```

### 3.3 Score Derivation
Each emotion class is weighted by how "composed" it signals the candidate is:

```python
EMOTION_COMPOSURE_WEIGHTS = {
    'neutral':   1.0,   # most desirable
    'happy':     0.9,   # positive, confident
    'surprised': 0.5,   # neutral-to-negative
    'sad':       0.3,
    'disgusted': 0.2,
    'angry':     0.2,
    'fearful':   0.1    # least desirable
}

def compute_emotion_score(distribution: dict) -> int:
    raw = sum(
        distribution.get(emotion, 0) * weight
        for emotion, weight in EMOTION_COMPOSURE_WEIGHTS.items()
    )
    return min(100, max(0, round(raw)))
```

### 3.4 Dominant Emotion
The emotion with the highest average percentage across all frames.

### 3.5 Output

| Field | Type | Range | Notes |
|---|---|---|---|
| `emotion_dominant` | string | — | e.g., "neutral" |
| `emotion_scores` | dict | 0–100 per key | Distribution percentages |
| `emotion_score` | integer | 0–100 | Composure score |

### 3.6 Failure Handling
- If no face detected across all frames: `emotion_score = null`, `emotion_status = "failed"`
- If < 5 frames analyzed: `emotion_score = null`, `emotion_status = "low_confidence"`

---

## 4. Module 2: Voice / Clarity Score

### 4.1 Input
- Audio file (16kHz mono WAV)
- Speech-to-text transcript string

### 4.2 Filler Word Detection
```python
FILLER_WORDS = {
    'um', 'uh', 'like', 'basically', 'you know',
    'right', 'so', 'actually', 'literally', 'kind of'
}

def count_fillers(transcript: str) -> dict:
    words = transcript.lower().split()
    found = {}
    for word in words:
        if word in FILLER_WORDS:
            found[word] = found.get(word, 0) + 1
    return found  # {"um": 3, "like": 2}
```

### 4.3 Speaking Rate (WPM)
```python
def compute_wpm(transcript: str, duration_sec: float) -> int:
    if duration_sec <= 0:
        return 0
    word_count = len(transcript.split())
    return round((word_count / duration_sec) * 60)
```

**Ideal range:** 120–150 WPM (conversational interview pace).

### 4.4 Clarity Score Formula

```python
def compute_clarity_score(filler_count: int, wpm: int) -> int:
    # Filler word penalty: -5 points per filler word (max -50)
    filler_penalty = min(50, filler_count * 5)
    
    # WPM penalty: deviation from ideal range 120-150 WPM
    if 120 <= wpm <= 150:
        wpm_penalty = 0
    elif wpm < 120:
        wpm_penalty = (120 - wpm) * 0.4     # too slow
    else:
        wpm_penalty = (wpm - 150) * 0.3     # too fast
    wpm_penalty = min(30, wpm_penalty)
    
    score = 100 - filler_penalty - wpm_penalty
    return max(0, min(100, round(score)))
```

### 4.5 Voice Tone Label

| Clarity Score | Label |
|---|---|
| 75–100 | Confident |
| 50–74 | Moderate |
| 0–49 | Nervous |

### 4.6 Output

| Field | Type | Range | Notes |
|---|---|---|---|
| `transcript` | string | — | Full STT output |
| `filler_count` | integer | ≥ 0 | Total filler words |
| `filler_words_found` | dict | — | Per-word counts |
| `wpm` | integer | 0–250 | Words per minute |
| `clarity_score` | integer | 0–100 | Voice clarity score |
| `voice_tone_label` | string | — | Confident / Moderate / Nervous |

### 4.7 Failure Handling
- Silent audio (no speech): `clarity_score = null`, `voice_status = "no_speech"`
- STT API failure (all retries exhausted): `clarity_score = null`, `voice_status = "failed"`

---

## 5. Module 3: Posture Score

### 5.1 Input
- Video file; frames extracted at 1 fps
- MediaPipe Pose landmark output (33 3D keypoints per frame)

### 5.2 Key Landmarks Used

| Landmark Index | Name | Used For |
|---|---|---|
| 0 | NOSE | Head forward lean |
| 11 | LEFT_SHOULDER | Shoulder alignment |
| 12 | RIGHT_SHOULDER | Shoulder alignment |
| 23 | LEFT_HIP | Torso reference |
| 24 | RIGHT_HIP | Torso reference |

### 5.3 Scoring Algorithm

```python
def compute_posture_score(landmarks) -> int:
    lm = landmarks.landmark
    
    # --- SHOULDER ALIGNMENT ---
    # Both shoulders should be at similar y-coordinate (horizontal level)
    shoulder_diff = abs(lm[11].y - lm[12].y)
    # Normalized: diff of 0.0 = perfect, diff > 0.2 = severe tilt
    shoulder_score = max(0, 100 - (shoulder_diff * 500))
    
    # --- HEAD POSITION ---
    # Nose x-coordinate should align with mid-shoulder x-coordinate
    mid_shoulder_x = (lm[11].x + lm[12].x) / 2
    head_lean = abs(lm[0].x - mid_shoulder_x)
    head_score = max(0, 100 - (head_lean * 400))
    
    # --- VISIBILITY CHECK ---
    # Penalize if key landmarks are not clearly visible
    visibility_penalty = 0
    if lm[11].visibility < 0.5 or lm[12].visibility < 0.5:
        visibility_penalty = 20
    
    combined = (shoulder_score * 0.5 + head_score * 0.5) - visibility_penalty
    return max(0, min(100, round(combined)))
```

### 5.4 Posture Label

| Score | Label |
|---|---|
| 75–100 | Good |
| 50–74 | Fair |
| 0–49 | Poor |

### 5.5 Per-Frame to Per-Response Aggregation

```python
def aggregate_posture(frame_scores: list[int]) -> dict:
    if not frame_scores:
        return {"posture_score": None, "posture_label": None}
    avg = round(sum(frame_scores) / len(frame_scores))
    label = "Good" if avg >= 75 else "Fair" if avg >= 50 else "Poor"
    return {"posture_score": avg, "posture_label": label,
            "frames_analyzed": len(frame_scores)}
```

### 5.6 Failure Handling
- Zero landmarks detected in all frames: `posture_score = 50` (Fair), `posture_status = "low_confidence"`
- This prevents a missing-camera scenario from penalizing the candidate.

---

## 6. Module 4: Answer Quality Score

### 6.1 Input
- Candidate's transcript (text string)
- Question object with `skill_tag`

### 6.2 Keyword Coverage

Each question in the question bank carries an optional `expected_keywords` list. The answer quality analyzer checks what percentage of expected keywords (or semantically similar terms) appear in the transcript.

```python
def keyword_coverage(transcript: str, expected_keywords: list[str]) -> float:
    transcript_lower = transcript.lower()
    found = sum(1 for kw in expected_keywords if kw.lower() in transcript_lower)
    if not expected_keywords:
        return 0.6  # default 60% if no keywords defined
    return found / len(expected_keywords)
```

### 6.3 Semantic Similarity (Sentence-BERT)

```python
from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer('all-MiniLM-L6-v2')

def semantic_similarity(candidate_answer: str, ideal_answer: str) -> float:
    embeddings = model.encode([candidate_answer, ideal_answer])
    score = util.cos_sim(embeddings[0], embeddings[1]).item()
    return max(0.0, min(1.0, score))
```

**Engineering Assumption:** Ideal answer templates are stored in `question_bank.json` alongside each question. For behavioral questions, a generic rubric answer is used.

### 6.4 Answer Quality Score Formula

```python
def compute_answer_score(keyword_cov: float, semantic_sim: float,
                         response_length_words: int) -> int:
    # Length penalty: < 20 words = too short; > 300 = verbosity penalty
    if response_length_words < 20:
        length_factor = 0.5
    elif response_length_words > 300:
        length_factor = 0.85
    else:
        length_factor = 1.0
    
    raw = (keyword_cov * 0.4 + semantic_sim * 0.6) * 100 * length_factor
    return max(0, min(100, round(raw)))
```

### 6.5 Failure Handling
- Empty transcript (STT failed): `answer_relevance_score = null`, `answer_status = "failed"`
- No ideal answer in question bank: keyword_cov = 0.6 (neutral default), semantic_sim = 0.5

---

## 7. Confidence Score

### 7.1 Derivation

```python
def compute_confidence_score(emotion_score: int, clarity_score: int) -> int:
    # Confidence = weighted blend of emotional composure and vocal clarity
    if emotion_score is None and clarity_score is None:
        return None
    scores = [s for s in [emotion_score, clarity_score] if s is not None]
    weights = [0.55, 0.45][:len(scores)]
    weighted_avg = sum(s * w for s, w in zip(scores, weights))
    total_weight = sum(weights)
    return round(weighted_avg / total_weight)
```

### 7.2 Confidence Label

| Score | Label |
|---|---|
| 75–100 | High |
| 50–74 | Moderate |
| 0–49 | Low |

---

## 8. Session Score Aggregation

### 8.1 Per-Module Session Averages

```python
def session_averages(analysis_results: list) -> dict:
    def safe_avg(values):
        valid = [v for v in values if v is not None]
        return round(sum(valid) / len(valid)) if valid else None
    
    return {
        "emotion_score":       safe_avg([r.emotion_score for r in analysis_results]),
        "voice_score":         safe_avg([r.clarity_score for r in analysis_results]),
        "posture_score":       safe_avg([r.posture_score for r in analysis_results]),
        "answer_quality_score":safe_avg([r.answer_relevance_score for r in analysis_results]),
        "confidence_score":    safe_avg([r.confidence_score for r in analysis_results])
    }
```

### 8.2 Overall Score (Weighted)

```python
SCORE_WEIGHTS = {
    "emotion_score":        0.20,
    "voice_score":          0.30,
    "posture_score":        0.15,
    "answer_quality_score": 0.35
}

def compute_overall_score(session_scores: dict) -> int:
    numerator = 0.0
    denominator = 0.0
    for key, weight in SCORE_WEIGHTS.items():
        val = session_scores.get(key)
        if val is not None:
            numerator += val * weight
            denominator += weight
    if denominator == 0:
        return None
    return round(numerator / denominator)
```

> If a module fails for all questions, it is excluded from the overall score calculation. The denominator adjusts accordingly so the result is still a fair 0–100 value.

---

## 9. Score Grade Labels

| Overall Score | Grade Label |
|---|---|
| 90–100 | Exceptional |
| 75–89 | Good |
| 60–74 | Average |
| 45–59 | Needs Improvement |
| 0–44 | Poor |

---

## 10. Suggestion Rule Engine

Suggestions are generated after session scores are computed. Rules are evaluated in priority order. A maximum of 5 suggestions are included in the report.

```python
SUGGESTION_RULES = [
    {
        "condition": lambda s: s.get("voice_score") is not None and s["voice_score"] < 60,
        "category": "voice",
        "priority": 1,
        "template": (
            "Your speech clarity score was {voice_score}/100. "
            "Practice reducing filler words — aim for a pace of 120–150 WPM. "
            "Record yourself and listen back."
        )
    },
    {
        "condition": lambda s: s.get("emotion_score") is not None and s["emotion_score"] < 60,
        "category": "emotion",
        "priority": 2,
        "template": (
            "Your emotional composure score was {emotion_score}/100. "
            "Practice breathing exercises before interviews. "
            "Repeat mock sessions to reduce anxiety through familiarity."
        )
    },
    {
        "condition": lambda s: s.get("posture_score") is not None and s["posture_score"] < 65,
        "category": "posture",
        "priority": 3,
        "template": (
            "Your posture score was {posture_score}/100. "
            "Sit upright with shoulders level. "
            "Keep your head facing the camera directly."
        )
    },
    {
        "condition": lambda s: s.get("answer_quality_score") is not None 
                               and s["answer_quality_score"] < 65,
        "category": "content",
        "priority": 4,
        "template": (
            "Your answer quality score was {answer_quality_score}/100. "
            "Structure answers using the STAR method and ensure you cover "
            "key technical keywords for each topic."
        )
    },
    {
        "condition": lambda s: s.get("confidence_score") is not None 
                               and s["confidence_score"] < 55,
        "category": "confidence",
        "priority": 5,
        "template": (
            "Your overall confidence score was {confidence_score}/100. "
            "Confidence improves with repetition — aim for at least "
            "3 mock interview sessions per week."
        )
    }
]
```

---

## 11. Score Weight Configuration

Score weights are stored in `config.py` and can be overridden by an administrator without code changes:

```python
# config.py
SCORE_WEIGHTS = {
    "emotion_score":        float(os.environ.get('WEIGHT_EMOTION', 0.20)),
    "voice_score":          float(os.environ.get('WEIGHT_VOICE', 0.30)),
    "posture_score":        float(os.environ.get('WEIGHT_POSTURE', 0.15)),
    "answer_quality_score": float(os.environ.get('WEIGHT_ANSWER', 0.35))
}
```

Weights must sum to 1.0. The system validates this at startup:
```python
assert abs(sum(SCORE_WEIGHTS.values()) - 1.0) < 1e-6, "Score weights must sum to 1.0"
```

---

*Source: Interview Ninja project documentation, A.C. Patil College of Engineering.*
