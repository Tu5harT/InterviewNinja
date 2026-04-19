# Implement Real AI Analysis Pipeline

Replace the fake `time.sleep()` simulation with actual AI-powered analysis using the recorded video/audio files.

## Background

The current `analyze_session_async` in `routes/session.py` uses `time.sleep()` to fake progress. Real `.webm` video and `.wav` audio files **already exist** in `recordings/session_X/` — the media pipeline is working. We just need to process them.

Your project spec (`08-scoring-engine-spec.md`, `04-system-architecture.md`) defines exactly which tools to use:

| Module | Library | Input | Output |
|---|---|---|---|
| Emotion | **DeepFace** (wraps FER) | Video frames via OpenCV | 7-class emotion probabilities → composure score |
| Voice | **SpeechRecognition** (Google STT) | `.wav` audio | Transcript → filler words, WPM, clarity score |
| Posture | **MediaPipe Pose** | Video frames | 33 landmarks → shoulder/head alignment score |
| Answer Quality | **sentence-transformers** (all-MiniLM-L6-v2) | Transcript + question text | Cosine similarity → relevance score |

## User Review Required

> [!IMPORTANT]
> **New dependencies.** This will install ~1.5GB of AI libraries (TensorFlow via DeepFace, MediaPipe, sentence-transformers, torch). First run will also download model weights (~500MB). Ensure you have disk space and a stable connection.

> [!WARNING]
> **Google STT requires internet.** The Voice Analyzer uses Google's free Speech-to-Text API. If you want fully offline, we can swap to Whisper later, but it requires more RAM.

> [!IMPORTANT]
> **Analysis will take 30–90 seconds per question** on CPU. For a 1-question test session, expect ~60 seconds total. This is real AI inference, not simulation.

## Proposed Changes

### 1. Install AI Dependencies

#### [MODIFY] [requirements.txt](file:///d:/code/interviewNinja/interviewNinja-leetcode-v.1/requirements.txt)
Add the following packages:
```
opencv-python==4.9.0.80
deepface==0.0.93
mediapipe==0.10.9
SpeechRecognition==3.10.1
sentence-transformers==2.3.1
tf-keras==2.16.0
```

---

### 2. Create the Four Analysis Modules

Each module is a standalone service file following the spec exactly.

#### [NEW] [services/emotion_analyzer.py](file:///d:/code/interviewNinja/interviewNinja-leetcode-v.1/services/emotion_analyzer.py)
- Extract video frames at 2 fps using OpenCV
- Run DeepFace `analyze(frame, actions=['emotion'])` on each frame
- Aggregate emotion distributions across frames
- Compute composure score using weighted emotion values from `08-scoring-engine-spec.md`
- Return: `emotion_dominant`, `emotion_scores` dict, `emotion_score` (0–100)

#### [NEW] [services/voice_analyzer.py](file:///d:/code/interviewNinja/interviewNinja-leetcode-v.1/services/voice_analyzer.py)
- Load `.wav` file using `speech_recognition.AudioFile`
- Transcribe via Google STT (`recognizer.recognize_google()`)
- Count filler words against the defined set (`um`, `uh`, `like`, `basically`, etc.)
- Calculate WPM from word count / audio duration
- Compute clarity score using the spec formula (filler penalty + WPM penalty)
- Return: `transcript`, `filler_count`, `filler_words`, `wpm`, `clarity_score`, `voice_tone_label`

#### [NEW] [services/posture_analyzer.py](file:///d:/code/interviewNinja/interviewNinja-leetcode-v.1/services/posture_analyzer.py)
- Extract video frames at 1 fps using OpenCV
- Run MediaPipe Pose on each frame to get 33 landmarks
- Compute per-frame posture score (shoulder alignment + head position)
- Average across all frames
- Return: `posture_score` (0–100), `posture_label`, `frames_analyzed`

#### [NEW] [services/answer_analyzer.py](file:///d:/code/interviewNinja/interviewNinja-leetcode-v.1/services/answer_analyzer.py)
- Load sentence-transformers `all-MiniLM-L6-v2` model (singleton)
- Encode candidate transcript + question text
- Compute cosine similarity
- Run keyword coverage check
- Apply length factor
- Return: `relevance_score` (0–100), `keywords_found`, `semantic_similarity`

---

### 3. Create the Score Aggregator

#### [NEW] [services/score_aggregator.py](file:///d:/code/interviewNinja/interviewNinja-leetcode-v.1/services/score_aggregator.py)
- Implement the weighted overall score formula from the spec:
  - Emotion × 0.20 + Voice × 0.30 + Posture × 0.15 + Answer × 0.35
- Implement the suggestion rule engine from `08-scoring-engine-spec.md`
- Compute confidence score from emotion + voice

---

### 4. Wire the Real Pipeline into the Background Worker

#### [MODIFY] [routes/session.py](file:///d:/code/interviewNinja/interviewNinja-leetcode-v.1/routes/session.py)
- Replace `time.sleep()` stubs with real analyzer calls
- For each response in the session:
  1. Run emotion analyzer on the `.webm` file
  2. Run voice analyzer on the `.wav` file
  3. Run posture analyzer on the `.webm` file
  4. Run answer analyzer on the transcript + question text
- Save results to `AnalysisResult` table
- Update session status after each module completes (for progress bar)

---

### 5. Update the Report Route to Use Real Data

#### [MODIFY] [app.py](file:///d:/code/interviewNinja/interviewNinja-leetcode-v.1/app.py)
- Replace `random.randint()` mock scores with actual data from `AnalysisResult` table
- Use the score aggregator to compute final session scores
- Generate dynamic suggestions based on actual scores using the rule engine

---

## Open Questions

> [!IMPORTANT]
> **Internet requirement:** Google STT needs internet. Is that acceptable for your deployment, or do you want me to use OpenAI Whisper (offline but heavier on RAM)?

## Verification Plan

### Automated Tests
1. Run through a complete interview with 1 question
2. Verify `AnalysisResult` row is created with real scores (not null/random)
3. Verify `/report?session_id=X` displays data from the database
4. Check each analyzer module independently with the existing `recordings/session_5/q41.webm`

### Manual Verification
- You will see the progress bars move at different speeds (emotion is slowest due to frame-by-frame processing)
- The report will show your **actual** dominant emotion, real transcript of what you said, and real posture score
- Suggestions will change based on your actual performance
