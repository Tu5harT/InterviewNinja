# 03 — Information Architecture
**Project:** Interview Ninja — AI-Powered Mock Interview Assistant  
**Version:** 1.0

---

## 1. Overview

This document defines the information architecture (IA) of Interview Ninja — how the application is structured from a navigational, content, and state perspective. It covers the page/screen hierarchy, user flow, data hierarchy, and content model for each screen.

---

## 2. Site Map

```
Interview Ninja
│
├── [1] Home / Landing Page
│       └── Resume Upload Form
│
├── [2] Resume Review Screen
│       └── Extracted Skills Confirmation
│
├── [3] Interview Session Screen
│       ├── Question Display
│       ├── Webcam Preview
│       ├── Recording Controls (Start / Stop)
│       └── Question Progress Indicator
│
├── [4] Analysis Wait Screen
│       └── Progress Indicator / Status Polling
│
└── [5] Report Screen
        ├── Score Dashboard
        ├── Per-Question Breakdown
        ├── Emotion Chart
        ├── Filler Word Summary
        ├── Improvement Suggestions
        └── PDF Export Button
```

---

## 3. User Flow (Linear)

The application follows a strictly linear, wizard-style flow. There is no lateral navigation — each screen advances only on successful completion of the prior step.

```
[START]
   │
   ▼
[1] Home — Upload Resume
   │  ✅ File valid (PDF/DOCX, ≤10MB)
   ▼
[2] Resume Review — Confirm Extracted Skills
   │  ✅ Candidate confirms → Session created → Questions generated
   ▼
[3] Interview Session
   │  Loop: For each question (1 to N):
   │    a. Display question text
   │    b. Candidate reads → clicks "Start Recording"
   │    c. Live webcam + countdown timer active
   │    d. Candidate clicks "Stop" or timer hits 0
   │    e. Video uploaded and acknowledged
   │    f. Advance to next question
   │  ✅ All questions answered → Candidate clicks "Submit Interview"
   ▼
[4] Analysis Wait — AI Pipeline Running
   │  System polls /api/analysis/status/{session_id} every 5s
   │  ✅ status = "analyzed"
   ▼
[5] Report — View and Download Results
   │  [Optional] Download PDF
   ▼
[END]
```

---

## 4. Screen-by-Screen Content Model

### Screen 1: Home / Resume Upload

**Purpose:** Entry point. Collect resume.

**Content Elements:**

| Element | Type | Notes |
|---|---|---|
| Application name + tagline | Heading / Hero | "Interview Ninja — Practice Smarter" |
| Resume upload widget | File input | Accepts PDF, DOCX; 10MB max |
| File format guidance | Helper text | "Upload your resume in PDF or DOCX format (max 10MB)" |
| Submit button | CTA | "Upload Resume" — disabled until file is selected |
| Error message area | Conditional | Shown on invalid file type or size |
| Permission disclosure | Informational | Note that webcam/mic will be required in the next step |

---

### Screen 2: Resume Review

**Purpose:** Let the candidate verify that their skills were correctly extracted before questions are generated.

**Content Elements:**

| Element | Type | Notes |
|---|---|---|
| Candidate name (extracted) | Display field | Editable if extraction is wrong |
| Extracted skills list | Tag/chip list | Editable — candidate can remove incorrect tags |
| Skills count summary | Body text | "We found 7 skills in your resume" |
| Confirm & Start button | CTA | "Generate My Questions" |
| Back button | Secondary action | Returns to upload screen |

**Data displayed:**
- `candidate.name`
- `candidate.skills_json[]` — each skill as a tag/chip

---

### Screen 3: Interview Session

**Purpose:** Conduct the mock interview. One question at a time.

**Content Elements:**

| Element | Type | Notes |
|---|---|---|
| Question number indicator | Progress bar / label | "Question 3 of 10" |
| Question category badge | Label | "Technical" or "Behavioral" |
| Question text | Large body text | Full question displayed |
| Webcam preview | Video element | Live feed; always visible |
| Recording indicator | Status badge | "● REC" — visible only when recording |
| Countdown timer | Numeric display | 90 → 0; colour changes at 30s |
| Start Recording button | Primary CTA | Replaced by Stop Recording when active |
| Stop Recording button | Primary CTA | Visible during recording only |
| Upload progress indicator | Loading bar | Shown after stop; before next question loads |

**State machine for this screen:**

```
[ready_to_read]
      │ Candidate clicks "Start Recording"
      ▼
[recording]
      │ Candidate clicks "Stop" OR timer = 0
      ▼
[uploading]
      │ Upload acknowledged by server
      ▼
[ready_to_read]  ← next question loaded
      │ Last question uploaded
      ▼
[all_done] → "Submit Interview" button appears
```

---

### Screen 4: Analysis Wait

**Purpose:** Inform the candidate that AI analysis is running; prevent navigation away.

**Content Elements:**

| Element | Type | Notes |
|---|---|---|
| Status message | Heading | "Analysing your interview..." |
| Progress bar | Animated | Driven by poll response `progress_percent` |
| Module status list | Status list | "✅ Emotion analysis", "⏳ Voice analysis", "⌛ Posture analysis" |
| Estimated time | Body text | "This usually takes 2–3 minutes" |
| Do not close warning | Alert | "Please keep this tab open" |

**Polling behavior:** Browser polls `GET /api/v1/analysis/status/{session_id}` every 5 seconds. On `status = "analyzed"`, auto-redirect to Report screen.

---

### Screen 5: Report

**Purpose:** Present the full performance analysis with scores, per-question breakdown, charts, and suggestions.

**Content Sections:**

#### 5.1 Score Dashboard (top of page)

| Element | Type | Notes |
|---|---|---|
| Candidate name | Heading | |
| Session date/time | Subheading | |
| Overall score | Large number + grade ring | 0–100 |
| Emotion score | Score card | 0–100 |
| Voice/Clarity score | Score card | 0–100 |
| Posture score | Score card | 0–100 |
| Answer Quality score | Score card | 0–100 |
| Confidence label | Badge | High / Moderate / Low |

#### 5.2 Per-Question Breakdown

Repeated for each question:

| Element | Type | Notes |
|---|---|---|
| Question number + text | Section header | |
| Transcript | Text block | Full STT transcript |
| Dominant emotion | Badge | e.g., "Neutral" |
| Filler words used | Inline list | "um ×3, like ×2" |
| WPM | Stat | e.g., "112 WPM" |
| Clarity score | Stat | 0–100 |
| Posture label | Badge | Good / Fair / Poor |
| Answer relevance score | Stat | 0–100 |

#### 5.3 Emotion Distribution Chart

- Chart type: Horizontal bar or pie chart
- Data: Average emotion distribution across all responses
- Labels: Neutral, Happy, Sad, Angry, Surprised, Fearful

#### 5.4 Improvement Suggestions

- 3–5 cards, sorted by priority (most impactful first)
- Each card: Category icon + suggestion text

#### 5.5 Actions

| Element | Type | Notes |
|---|---|---|
| Download PDF button | Primary CTA | Triggers PDF download |
| Start New Interview button | Secondary CTA | Returns to home screen |

---

## 5. Navigation Rules

| From | To | Trigger | Blocked If |
|---|---|---|---|
| Home | Resume Review | Valid file uploaded | File invalid or too large |
| Resume Review | Interview Session | "Generate My Questions" clicked | Skills list empty (no skills extracted) |
| Interview Session | Analysis Wait | "Submit Interview" clicked | Not all questions answered |
| Analysis Wait | Report | Analysis status = "analyzed" | Analysis still running |
| Report | Home | "Start New Interview" clicked | Never blocked |

---

## 6. Data Hierarchy (Content Model)

```
Session
├── candidate
│   ├── id
│   ├── name
│   └── skills[]
├── questions[]
│   ├── sequence
│   ├── text
│   ├── category
│   └── skill_tag
├── responses[]
│   ├── question_id
│   ├── video_path
│   ├── audio_path
│   └── transcript
├── analysis_results[]
│   ├── emotion_dominant
│   ├── emotion_scores{}
│   ├── filler_count
│   ├── filler_words[]
│   ├── wpm
│   ├── clarity_score
│   ├── posture_score
│   ├── posture_label
│   └── answer_relevance_score
└── report
    ├── overall_score
    ├── emotion_score
    ├── voice_score
    ├── posture_score
    ├── answer_quality_score
    ├── confidence_score
    ├── confidence_label
    └── suggestions[]
        ├── category
        ├── priority
        └── message
```

---

## 7. Error States

| Screen | Error Condition | User-Facing Message | Recovery Action |
|---|---|---|---|
| Home | File type invalid | "Only PDF and DOCX files are accepted." | Re-upload |
| Home | File too large | "File exceeds 10MB limit." | Re-upload smaller file |
| Home | Parsing fails | "We couldn't extract data from this resume. Try a different format." | Re-upload |
| Interview Session | Webcam permission denied | "Camera access is required. Please allow access in your browser settings." | Retry button |
| Interview Session | Upload failure | "Response upload failed. Please try again." | Retry upload button |
| Analysis Wait | Analysis fails (all modules) | "Analysis encountered an error. Partial results may still be available." | View partial report |
| Report | PDF generation fails | "PDF export unavailable. You can print this page instead." | Print browser page |

---

*Source: Interview Ninja project documentation, A.C. Patil College of Engineering.*
