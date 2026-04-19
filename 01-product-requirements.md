# 01 — Product Requirements
**Project:** Interview Ninja — AI-Powered Mock Interview Assistant  
**Institution:** A.C. Patil College of Engineering, Dept. of AI & Data Science  
**Version:** 1.0

---

## 1. Product Vision

> **Interview Ninja empowers every job-seeking candidate — regardless of access to coaching resources — to practice, receive data-driven feedback, and meaningfully improve their interview performance through AI-powered behavioral and technical analysis.**

The product eliminates dependency on human interviewers for practice, making high-quality mock interview training accessible, repeatable, and objective. It addresses the gap identified across existing research platforms: no prior system simultaneously combines resume-grounded question generation with facial emotion recognition, posture analysis, voice tone evaluation, and filler word detection in a single unified report.

---

## 2. Problem Statement

### 2.1 Core Problems

| Problem | Description |
|---|---|
| Nervousness and low confidence | Anxiety undermines communication even when the candidate knows the answer |
| Poor communication habits | Excessive filler words, unclear speech, inconsistent pace |
| Unaware physical behavior | Slouching, head tilt, distracted posture — candidate cannot self-observe |
| No on-demand practice access | Traditional mock interviews need human interviewers; expensive and hard to schedule |

### 2.2 Gap in Existing Solutions

| Existing System | Strength | Weakness |
|---|---|---|
| Jadhav et al. (2024) — Mock Interview Simulator with AI + Pose | Posture detection, communication feedback | Limited emotion depth; no resume mapping |
| Gomez et al. (2025) — AI-Driven Mock Technical Interviews | Multimodal AI, code analysis | Conversational latency; limited non-verbal tracking |
| Dayal et al. (2025) — AI-Driven Mock Interviews | Speech analysis, feedback on 6,619 interviews | Language only; no facial emotion analysis |
| Amrutha et al. (2024) — Emotion and Confidence in Mock Interviews | CNN/RNN emotion + body language | No resume alignment; no real-time suggestions |

**Interview Ninja's differentiation:** Holistic, multi-modal analysis (emotion + speech + posture + answer quality) combined with resume-personalized question generation — producing a unified, actionable performance report.

---

## 3. Goals

| ID | Goal |
|---|---|
| G1 | Help candidates improve interview confidence and communication skills |
| G2 | Provide data-driven, unbiased interview performance feedback |
| G3 | Simulate real interview conditions through AI |
| G4 | Identify specific weak areas: nervousness, filler words, poor posture, weak answers |

---

## 4. Success Metrics

| Metric | Target |
|---|---|
| End-to-end session completion (no crash) | ≥ 90% |
| Resume skill extraction accuracy | ≥ 80% on standard PDF/DOCX resumes |
| Question relevance (user-rated) | ≥ 70% rated "relevant" |
| Emotion detection directional accuracy | ≥ 80% (nervous vs. calm differentiation) |
| Filler word count accuracy | Within ±2 of manual count |
| Report usefulness (user-rated) | ≥ 75% agree report highlights a real weakness |
| PDF export success rate | 100% |

---

## 5. Target Users

### 5.1 Primary — Job-Seeking Candidate

- Final-year engineering / technical students
- Recent graduates preparing for campus placements
- Working professionals preparing for job switches

**Key needs:** On-demand practice, objective behavioral feedback, specific actionable suggestions.

### 5.2 Secondary — Academic Institution / Training Center *(Future scope, not in MVP)*

- College placement cells, coaching institutes
- Need: batch analytics, HR-ready summaries, progress tracking

---

## 6. Functional Requirements

### FR-01: Resume Upload and Management

| ID | Requirement |
|---|---|
| FR-01.1 | System SHALL accept PDF and DOCX resume files. |
| FR-01.2 | System SHALL reject all other file types with a clear error message. |
| FR-01.3 | System SHALL enforce a 10MB maximum file size. |
| FR-01.4 | System SHALL securely store the resume and associate it with the current session. |
| FR-01.5 | System SHALL extract: candidate name, skills, technologies, projects, education. |
| FR-01.6 | System SHALL display extracted data to the candidate for review before starting the interview. |

### FR-02: Interview Question Generation

| ID | Requirement |
|---|---|
| FR-02.1 | System SHALL generate 8–12 questions per session based on extracted resume data. |
| FR-02.2 | Questions SHALL include both technical (skill-mapped) and behavioral categories. |
| FR-02.3 | Technical questions SHALL be mapped to skills identified in the resume. |
| FR-02.4 | Behavioral questions SHALL cover confidence, communication, teamwork, and problem-solving. |
| FR-02.5 | Questions SHALL be presented one at a time in sequential order. |
| FR-02.6 | Candidate SHALL have time to read each question before recording begins. |
| FR-02.7 | A countdown timer SHALL be visible during recording (default 90 seconds max). |

### FR-03: Media Capture

| ID | Requirement |
|---|---|
| FR-03.1 | System SHALL request webcam and microphone permissions before interview begins. |
| FR-03.2 | If permission is denied, the session SHALL be blocked with a clear explanation. |
| FR-03.3 | System SHALL display a live webcam preview throughout the interview. |
| FR-03.4 | System SHALL record video and audio simultaneously for each question response. |
| FR-03.5 | A visible recording indicator SHALL be shown while recording is active. |
| FR-03.6 | System SHALL save each question's response as a separate video file. |
| FR-03.7 | System SHALL extract the audio track from each video for independent voice analysis. |

### FR-04: Facial Emotion Analysis

| ID | Requirement |
|---|---|
| FR-04.1 | System SHALL analyze facial expressions from the recorded video of each response. |
| FR-04.2 | System SHALL classify emotions into: Neutral, Happy, Sad, Angry, Surprised, Fearful. |
| FR-04.3 | System SHALL compute a dominant emotion per question response. |
| FR-04.4 | System SHALL compute an emotion distribution (%) across the full session. |
| FR-04.5 | Emotion distribution SHALL feed into the confidence score calculation. |
| FR-04.6 | System SHALL degrade gracefully if no face is detected in a frame (no crash). |

### FR-05: Voice Tone and Speech Clarity Analysis

| ID | Requirement |
|---|---|
| FR-05.1 | System SHALL transcribe each spoken response to text. |
| FR-05.2 | System SHALL count filler words: "um", "uh", "like", "basically", "you know", "right", "so". |
| FR-05.3 | System SHALL calculate speaking rate in Words Per Minute (WPM) per response. |
| FR-05.4 | System SHALL compute a speech clarity score (0–100) from WPM and filler frequency. |
| FR-05.5 | System SHALL assign a voice tone label: Confident / Moderate / Nervous. |
| FR-05.6 | System SHALL handle transcription failures gracefully without blocking analysis. |

### FR-06: Body Posture Detection

| ID | Requirement |
|---|---|
| FR-06.1 | System SHALL analyze candidate posture from recorded video. |
| FR-06.2 | System SHALL evaluate shoulder alignment and head position at minimum. |
| FR-06.3 | System SHALL assign a posture score (0–100) per response. |
| FR-06.4 | System SHALL classify posture as: Good (75–100), Fair (50–74), Poor (0–49). |

### FR-07: Confidence Level Detection

| ID | Requirement |
|---|---|
| FR-07.1 | System SHALL compute a confidence score (0–100) from emotion + voice analysis. |
| FR-07.2 | System SHALL assign a confidence label: High / Moderate / Low. |

### FR-08: Score Aggregation

| ID | Requirement |
|---|---|
| FR-08.1 | System SHALL compute an overall score as a weighted combination: emotion (20%), voice (30%), posture (15%), answer quality (35%). |
| FR-08.2 | All component scores SHALL be individually visible in the report. |
| FR-08.3 | Score weights SHALL be configurable by an administrator. |

### FR-09: Performance Feedback Report

| ID | Requirement |
|---|---|
| FR-09.1 | System SHALL generate a report after AI analysis completes. |
| FR-09.2 | Report SHALL display: overall score, per-category scores, confidence score and label. |
| FR-09.3 | Report SHALL display full transcript per question. |
| FR-09.4 | Report SHALL display filler word count and list of filler words used per question. |
| FR-09.5 | Report SHALL include an emotion distribution chart. |
| FR-09.6 | Report SHALL display posture score and label. |
| FR-09.7 | Report SHALL include at least 3 personalized improvement suggestions. |
| FR-09.8 | Report SHALL be immediately viewable in the browser after analysis. |
| FR-09.9 | Report SHALL be exportable as a PDF document. |
| FR-09.10 | System SHALL notify the candidate in-browser when the report is ready. |

### FR-10: Session Management

| ID | Requirement |
|---|---|
| FR-10.1 | Each session SHALL have a unique identifier. |
| FR-10.2 | System SHALL track session status: created / in_progress / completed / analyzing / analyzed / failed. |
| FR-10.3 | System SHALL record timestamps for session start and completion. |
| FR-10.4 | All question-response pairs SHALL be stored and associated with the session. |

---

## 7. Non-Functional Requirements

### Performance
- Resume parsing: ≤ 10 seconds for a 2-page PDF
- Question generation: ≤ 5 seconds after parsing
- Recording latency (live preview): < 100ms
- AI analysis pipeline: ≤ 5 minutes for a 10-question session at 90 seconds per response
- Report page load: ≤ 3 seconds after analysis completes

### Reliability
- Individual AI module failures must NOT crash the full pipeline
- All recorded media must be preserved even if analysis fails
- System must be recoverable from unexpected browser closure

### Accuracy
- Filler word detection: within ±2 of manual count
- Emotion analysis: correctly differentiates nervous vs. calm in ≥ 80% of test cases
- Posture scoring: upright candidate scores ≥ 10 points higher than slouching in ≥ 90% of test pairs

### Security
- Uploaded files stored outside web root; filenames sanitized
- CSRF tokens on all form submissions
- Recordings stored in session-scoped directories; not accessible cross-session
- Candidate video NOT transmitted to third parties (audio to Google STT disclosed before session)

### Usability
- Clear instructions at every step
- Permission prompts explain why access is needed in plain language
- Visual feedback during recording, analysis, and report generation
- Functional on Chrome 90+ and Firefox 90+ on desktop

### Hardware Constraints (from source document)
- Minimum 8GB RAM
- Functional webcam required
- Functional microphone required
- Active internet connection required

---

## 8. Out of Scope

| Feature | Reason |
|---|---|
| User account registration / login | Beyond MVP scope |
| Multi-session history and progress tracking | Requires accounts |
| Real-time AI analysis during recording | CPU constraint; deferred to v2 |
| HR / recruiter dashboard | Secondary user; future version |
| Mobile browser support | MediaRecorder inconsistencies; desktop only |
| Non-English language support | English-only for MVP |
| Job description input / role-specific tuning | Not in source feature list |
| Video playback in report | Storage complexity; text report sufficient |
| Proctoring / anti-cheating | Out of scope for self-practice tool |
| Integration with LinkedIn, Naukri, etc. | External dependency; deferred |
| Live human interviewer mode | Antithetical to AI-automation purpose |

---

## 9. Constraints and Assumptions

### Constraints
- Minimum 8GB RAM on host machine
- Webcam and microphone required on candidate's device
- Internet connection required (Google STT API)
- Primary browser: Chrome 90+ on desktop
- Local or single-server deployment only (MVP)

### Assumptions
- Candidates use standard English-language PDF/DOCX resumes
- Sessions occur in reasonably lit environments
- Audio is recorded in reasonably quiet environments
- `ffmpeg` is installed and available on the server host
- Pre-trained FER model is sufficiently accurate for the target demographic

---

*Source: Interview Ninja project presentation, A.C. Patil College of Engineering.*
