# 02 — User Stories and Acceptance Criteria
**Project:** Interview Ninja — AI-Powered Mock Interview Assistant  
**Version:** 1.0

---

## 1. User Story Index

| ID | Title | Priority |
|---|---|---|
| US-01 | Resume Upload | Must Have |
| US-02 | Interview Preparation (Question Review) | Must Have |
| US-03 | Recording a Response | Must Have |
| US-04 | Live Webcam Preview | Must Have |
| US-05 | Time Management During Response | Must Have |
| US-06 | Report Review | Must Have |
| US-07 | Improvement Guidance | Must Have |
| US-08 | PDF Export | Must Have |
| US-09 | Emotional Self-Awareness | Must Have |
| US-10 | Filler Word Awareness | Must Have |
| US-11 | Graceful Permission Denial Handling | Should Have |
| US-12 | Partial Analysis Recovery | Should Have |

---

## 2. User Stories

### US-01: Resume Upload

**As a** job-seeking candidate,  
**I want to** upload my resume to the system,  
**So that** the AI can generate interview questions tailored to my specific skills and experience.

**Preconditions:** Candidate has a PDF or DOCX resume file ready.

**Acceptance Criteria:**
- [ ] System accepts PDF files up to 10MB without error.
- [ ] System accepts DOCX files up to 10MB without error.
- [ ] System rejects files that are not PDF or DOCX, displaying a clear error message specifying accepted formats.
- [ ] System rejects files exceeding 10MB, displaying a file size limit message.
- [ ] After successful upload, system displays extracted candidate name and skill list for review.
- [ ] Extracted skills list contains ≥ 5 correctly identified skills for a standard 2-page engineering resume.
- [ ] Upload completes and feedback is shown within 10 seconds.

---

### US-02: Interview Preparation (Question Review)

**As a** candidate,  
**I want to** read each interview question fully before I start recording my response,  
**So that** I can collect my thoughts and structure my answer before speaking.

**Preconditions:** Resume has been successfully uploaded and parsed. Session has been started.

**Acceptance Criteria:**
- [ ] Each question is displayed in full, legible text before the recording starts.
- [ ] A "Start Recording" button is present and must be clicked explicitly — recording does NOT begin automatically.
- [ ] Questions are shown one at a time; the next question is not visible until the current response is submitted.
- [ ] A question category label (Technical / Behavioral) is shown alongside the question text.
- [ ] At least 8 questions are generated per session.
- [ ] For a resume listing Python and Machine Learning, at least 3 generated questions are directly about those topics.
- [ ] At least 2 questions are behavioral (not skill-specific).
- [ ] No two questions in the same session are duplicates.

---

### US-03: Recording a Response

**As a** candidate,  
**I want to** record my verbal response to each interview question via my webcam and microphone,  
**So that** the AI can analyze my voice, facial expressions, and posture.

**Preconditions:** Webcam and microphone permissions have been granted.

**Acceptance Criteria:**
- [ ] Clicking "Start Recording" begins video and audio capture simultaneously.
- [ ] A visible recording indicator (red dot, "REC" label, or equivalent) is shown while recording is active.
- [ ] Recording stops when the candidate clicks "Stop Recording".
- [ ] Recording stops automatically when the timer reaches 0.
- [ ] After stopping, the response is uploaded to the server before moving to the next question.
- [ ] A progress indicator is shown during upload.
- [ ] After a complete session, one `.webm` video file and one `.wav` audio file exist on the server for each answered question.

---

### US-04: Live Webcam Preview

**As a** candidate,  
**I want to** see myself on screen via a live webcam preview during the interview,  
**So that** I am aware of my framing, lighting, and posture in real time.

**Preconditions:** Webcam permission has been granted.

**Acceptance Criteria:**
- [ ] Live webcam feed renders within 2 seconds of permission being granted.
- [ ] Preview is visible throughout the entire interview session (all questions).
- [ ] Preview does not obstruct the question text.
- [ ] Preview continues to display even during recording.

---

### US-05: Time Management During Response

**As a** candidate,  
**I want to** see a countdown timer for each question response,  
**So that** I can pace my answer and know how much time I have remaining.

**Acceptance Criteria:**
- [ ] A countdown timer is visible from the moment "Start Recording" is clicked.
- [ ] Default timer is set to 90 seconds.
- [ ] Timer counts down in whole seconds.
- [ ] When the timer reaches 0, recording stops automatically.
- [ ] Timer does not reset when paused (no pause feature in MVP — recording is continuous).
- [ ] Timer color or visual style changes at the 30-second mark to signal urgency.

---

### US-06: Report Review

**As a** candidate,  
**I want to** receive a detailed performance report after my interview session,  
**So that** I can understand how I performed across multiple dimensions.

**Preconditions:** All question responses have been submitted and the AI analysis pipeline has completed.

**Acceptance Criteria:**
- [ ] System notifies the candidate in-browser when the report is ready.
- [ ] Report page is accessible without re-uploading a resume or restarting the session.
- [ ] Report displays: overall score (0–100), emotion score, voice/clarity score, posture score, answer quality score, confidence score and label.
- [ ] All numeric scores are in the range 0–100.
- [ ] Report displays per-question breakdown: question text, transcript, dominant emotion, filler word count, posture label.
- [ ] Emotion distribution is shown as a chart (bar or pie).
- [ ] Report page loads within 3 seconds of being opened.

---

### US-07: Improvement Guidance

**As a** candidate,  
**I want to** receive specific, actionable improvement suggestions in my report,  
**So that** I know what to focus on when preparing for my next interview.

**Acceptance Criteria:**
- [ ] At least 3 improvement suggestions are present in every report.
- [ ] Each suggestion is linked to a specific performance category (voice, emotion, posture, or answer quality).
- [ ] Suggestions are generated based on the candidate's actual scores — the weakest scoring categories produce the most prominent suggestions.
- [ ] Suggestions are written in plain, actionable language (e.g., "Reduce filler words — you used 'um' 12 times. Practice pausing silently instead.").
- [ ] No suggestion is shown for a category where the candidate scored above 80 ("Good" threshold).

---

### US-08: PDF Export

**As a** candidate,  
**I want to** download my performance report as a PDF file,  
**So that** I can review it offline, archive it, or share it with a mentor or placement coordinator.

**Acceptance Criteria:**
- [ ] A "Download PDF" button is visible on the report page.
- [ ] Clicking the button triggers a file download in the browser.
- [ ] The downloaded file is a valid, readable PDF.
- [ ] PDF contains all report sections: scores, transcripts, emotion summary, posture summary, suggestions.
- [ ] PDF filename includes the session identifier (e.g., `interview_report_7.pdf`).
- [ ] PDF generation succeeds 100% of the time on standard report data.

---

### US-09: Emotional Self-Awareness

**As a** candidate,  
**I want to** see how my emotional state varied across the interview session,  
**So that** I can understand at which points I appeared most nervous or confident.

**Acceptance Criteria:**
- [ ] Report shows dominant emotion per question (e.g., "Q3: Fearful").
- [ ] Report shows an overall emotion distribution chart for the full session.
- [ ] Emotion labels are human-readable: Neutral, Happy, Sad, Angry, Surprised, Fearful.
- [ ] A confidence label (High / Moderate / Low) derived from emotional state is shown prominently.
- [ ] If no face was detected in a response, the report shows "Emotion data unavailable" for that question rather than a default or fabricated score.

---

### US-10: Filler Word Awareness

**As a** candidate,  
**I want to** see which filler words I used and how frequently,  
**So that** I can consciously reduce them in real interviews.

**Acceptance Criteria:**
- [ ] Report shows total filler word count for the session.
- [ ] Report shows per-question filler word count.
- [ ] Specific filler words used are listed (e.g., "um: 4 times, like: 3 times, basically: 1 time").
- [ ] Filler word detection covers at minimum: "um", "uh", "like", "basically", "you know", "right", "so".
- [ ] Filler word count accuracy is within ±2 of a manual count on test recordings.

---

### US-11: Graceful Permission Denial

**As a** candidate who accidentally denies webcam/microphone permission,  
**I want to** receive a clear explanation and recovery path,  
**So that** I understand what to do next without the session crashing silently.

**Acceptance Criteria:**
- [ ] If camera or microphone permission is denied, the interview session does NOT proceed.
- [ ] A clear, non-technical error message is displayed explaining that webcam and microphone access is required.
- [ ] Instructions are provided for how to re-enable permissions in the browser.
- [ ] A "Try Again" button is presented that re-triggers the permission prompt.

---

### US-12: Partial Analysis Recovery

**As a** candidate,  
**I want** the report to be generated even if one AI analysis module fails,  
**So that** a single technical error doesn't cause me to lose all feedback from my session.

**Acceptance Criteria:**
- [ ] If the emotion analysis module fails, voice, posture, and answer quality results are still reported.
- [ ] Failed modules are shown as "N/A — Analysis unavailable" in the report, not as a 0 score.
- [ ] Overall score is computed from available modules only, with a note that one module was excluded.
- [ ] No unhandled exception is surfaced to the candidate; failure is handled gracefully in the backend.

---

## 3. Primary Use Case: End-to-End Mock Interview Session

**Use Case ID:** UC-01  
**Actor:** Candidate  
**Precondition:** PDF resume ready; device has webcam and microphone; Chrome 90+ browser.

### Main Flow

| Step | Actor | Action |
|---|---|---|
| 1 | Candidate | Opens application in Chrome |
| 2 | System | Displays resume upload screen |
| 3 | Candidate | Uploads PDF resume |
| 4 | System | Parses resume; displays extracted skills for review |
| 5 | System | Generates 8–12 questions based on resume |
| 6 | System | Prompts for webcam and microphone permissions |
| 7 | Candidate | Grants permissions; live video preview appears |
| 8 | System | Displays Question 1 |
| 9 | Candidate | Reads question, clicks "Start Recording", responds verbally |
| 10 | Candidate | Clicks "Stop Recording" |
| 11 | System | Saves response, advances to next question |
| 12 | — | Steps 8–11 repeat for all questions |
| 13 | Candidate | Clicks "Submit Interview" after final question |
| 14 | System | Starts AI analysis pipeline; shows progress indicator |
| 15 | System | Generates performance report |
| 16 | System | Redirects candidate to report page |
| 17 | Candidate | Reviews report; optionally downloads PDF |

### Alternate Flows

| ID | Trigger | Handling |
|---|---|---|
| AF-01 | Permission denied at step 6 | Session paused; explanation and retry prompt shown |
| AF-02 | One AI module fails at step 14 | Pipeline continues; failed module marked "N/A" in report |
| AF-03 | Browser closes mid-session | Saved recordings preserved; candidate starts new session |
| AF-04 | Upload fails for one response | Retry prompt shown; session does not advance until upload succeeds |
| AF-05 | STT API unavailable during analysis | Fallback to offline Whisper model; if also unavailable, voice section marked "N/A" |

---

*Source: Interview Ninja project documentation, A.C. Patil College of Engineering.*
