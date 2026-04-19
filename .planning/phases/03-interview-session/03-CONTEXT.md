# Phase 03: Interview Session - Context

**Gathered:** April 12, 2026  
**Status:** Ready for planning  
**Mode:** Comprehensive full-featured implementation

---

<domain>

## Phase Boundary

Candidate can participate in a complete mock interview session in the browser:

1. Grant webcam + microphone permissions
2. See live preview of themselves
3. Answer 8–12 generated questions one at a time
4. Record each response (video + audio, 90 second max per question)
5. Upload responses to server after each question
6. Submit final interview and proceed to analysis

**Scope:** Browser recording, server storage, session flow UI, error handling, recovery.

**Out of scope:** AI analysis (Phase 4), report generation (Phase 5), multi-user management (future).

</domain>

---

<decisions>

## Implementation Decisions

### Media Capture & Permissions

**D-01: Permission Request Strategy**

- Request **webcam AND microphone simultaneously** in a single browser prompt
- Rationale: Single prompt = simpler UX; dual permission accepted together or rejected together
- Implication: Interview cannot proceed without BOTH permissions

**D-02: Permission Denial Recovery**

- If user denies permissions, interview session STOPS
- Display clear explanation: "Webcam and microphone access required for this session"
- Provide "Try Again" button that re-triggers the permission prompt
- Rationale: No silent failures; user has explicit control and clear path to retry
- Do NOT proceed without both permissions

**D-03: Live Video Preview Placement**

- Fixed preview window: **top-right corner, 320×240 pixels**
- Non-movable, non-resizable (prevents UI clutter)
- Visible throughout entire interview session (all questions)
- Rationale: Candidate maintains posture awareness without distraction; consistent placement

**D-04: Audio Capture Source**

- Capture **microphone audio only** (candidate's voice)
- Do NOT capture system audio (questions, background)
- Rationale: Simpler implementation; AI analysis only needs candidate voice
- Implication: Audio transcript will be only what candidate says, not question text

### Recording Control & Indicators

**D-05: Recording Start Behavior**

- Recording does NOT auto-start when question appears
- Candidate must click explicit **"Start Recording" button**
- Rationale: Prevents accidental recordings; gives time to read and think about question
- Question text visible for min 3 seconds before recording allowed

**D-06: Countdown Timer Behavior**

- Default duration: **90 seconds per question**
- Timer visible immediately after recording starts
- Timer **auto-stops at 0** (recording terminates, upload begins)
- Visual urgency signal: color shift (green → yellow at 30 sec, yellow → red at 10 sec)
- Rationale: Enforces structured response time; prevents rambling; no manual stop needed

**D-07: Recording Indicator**

- Animated red dot + "REC" label displayed while recording active
- Indicator location: directly above video preview
- Rationale: Clear, unambiguous visual feedback; candidate always knows recording status

### File Upload & Storage

**D-08: Video File Storage**

- Save each response as WebM file: `recordings/{session_id}/q{n}.webm`
- One file per question per session
- Stored server-side only (not sent to external service for MVP)
- Rationale: WebM is native browser codec (no transcoding); smaller than raw video

**D-09: Audio Extraction**

- After video upload completes, **extract audio to WAV format**
- Output: `recordings/{session_id}/q{n}.wav`
- Extraction triggered async (does not block question flow)
- Tool: FFmpeg command: `ffmpeg -i {webm} -acodec pcm_s16le -ar 16000 {wav}`
- Rationale: WAV is standard for speech-to-text APIs; 16kHz sampling rate matches Google STT spec

**D-10: Upload Async Processing**

- Video chunk upload happens after "Stop Recording" clicked
- Audio extraction happens **in parallel via ThreadPoolExecutor** (no blocking)
- Candidate sees progress indicator during upload
- Store extraction task ID in database so Phase 4 can query status
- Rationale: Interview flow doesn't wait for FFmpeg; better responsiveness

### Session Flow & Navigation

**D-11: Question Navigation**

- **One question at a time, sequential only**
- Next question NOT visible until current response uploaded and confirmed
- No ability to skip or go back to previous questions
- Rationale: Enforces interview linearity; prevents gaming; matches real interview

**D-12: Progress Indicator**

- Top of question area: **"Question 3 of 10"** (updates for each question)
- Optional: progress bar (e.g., 30% complete)
- Rationale: Candidate knows position in interview; reduces anxiety

**D-13: End-of-Interview Flow**

- After final question response uploaded, **"Submit Interview" button appears**
- Clicking triggers redirect to **analysis-wait screen** (showing "Analysis in progress...")
- Polling endpoint checks analysis status; redirects to report when ready
- Rationale: Clear termination; prevents re-answering questions

### Error Handling & Recovery

**D-14: Upload Failure Retry Strategy**

- If video upload fails after recording stops:
  1. Auto-retry 3 times with exponential backoff (1 sec, 2 sec, 4 sec)
  2. If all 3 fail, show **retry button + message**: "Upload failed. [Retry] button"
  3. No "save to disk as backup" option (keep MVP simple)
- Rationale: Production-grade resilience; user controls final retry

**D-15: Mid-Session Browser Crash Recovery**

- Track session state in **browser localStorage**: session_id, current question, uploaded questions list
- Also store on server: session status updated after each upload
- On browser restart/new session start, offer **"Resume previous session"** if data exists
  - Grace period: 2 hours (auto-delete older sessions)
  - Resume skips re-recording already-uploaded questions
  - Continue from next unrecorded question
- Rationale: Candidate doesn't lose work; MVP-friendly (simple recovery, not complex state sync)

**D-16: Video Preview Control**

- Preview displays fixed in top-right corner
- Include **minimize/expand toggle button** (hide to reduce clutter, show to check setup)
- Mirror/flip option: **agent's discretion** (lower priority; can add if simple)
- Rationale: Candidate controls visual clutter; preview always available if needed

</decisions>

---

<canonical_refs>

## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Functional Requirements

- `01-product-requirements.md` — FR-03 (Media Capture), FR-04 (Emotion Analysis), FR-10 (Session Management)
  - FR-03.1-3.7: Recording, permission handling, live preview requirements
  - FR-10.1-10.4: Session tracking, status, timestamps
- `02-user-stories-and-acceptance-criteria.md` — US-03, US-04, US-05, US-11
  - US-03: Recording a Response (start/stop, timer, backend media files)
  - US-04: Live Webcam Preview (render timing, visibility)
  - US-05: Time Management (countdown, default 90 sec, auto-stop)
  - US-11: Permission denial handling (clear message, retry)

### Architecture & Implementation Patterns

- `04-system-architecture.md` — Pipeline pattern, async job handling, multi-tier structure
  - Reference: ThreadPoolExecutor for non-blocking operations (consistent with D-01 from PROJECT.md)
- `05-database-schema.md` — Session, Response models
  - Session: id, candidate_id, question_count, status, created_at
  - Response: id, session_id, question_id, video_path, audio_path, transcript, duration
- `06-api-contracts.md` — Session endpoints
  - POST `/api/v1/session/start` (already implemented Phase 2)
  - POST `/api/v1/session/{session_id}/response` (video upload)
  - GET `/api/v1/session/{session_id}/status` (polling for analysis)

### Frontend Code Context

- `templates/review.html` — Already routes to interview screen
  - Starting point for session interview page; builds from review flow
- `templates/` — base.html Jinja2 extension (for new interview.html template)

### Video & Audio Technical References

- WebM codec support: Natively supported in modern browsers (Chrome 25+, Firefox 26+, Safari 14.1 has limitations)
  - Fallback: MP4 if Safari support needed in MVP
- FFmpeg command for WAV extraction: Audio extraction tool (already in PROJECT.md tech stack)
- MediaRecorder API: Browser standard for capturing audio/video from devices
- Canvas/getUserMedia API: Permission model and stream capture

### Previous Phase Context

- `02-input-pipeline/02-01-SUMMARY.md` — Session model created, questions generated, API endpoints working
  - Interview screen receives session_id, questions list, candidate data
  - Database ready for Response entries

</canonical_refs>

---

<specifics>

## Specific Ideas

### Browser Compatibility Notes

- Chrome 90+: Full MediaRecorder support, WebM/MP4
- Firefox 90+: Full MediaRecorder support, WebM preferred
- Safari 14.1+: MediaRecorder supported but WebM not natively; use MP4 fallback or custom codec
  - **Decision impact:** D-08 specifies WebM; Safari users may see transcoding delay or MP4 alternative

### Recording Quality Targets

- Video bitrate: 1-2 Mbps (balance quality and file size)
- Audio bitrate: 128 kbps, 16 kHz sample rate (matches Google STT requirements)
- File size estimate: 90 sec video ≈ 11–22 MB; 10 questions ≈ 110–220 MB per session

### Network Scenario

- Assuming candidate has stable internet (MVP constraint from PROJECT.md)
- Fallback for poor connection: Chunk-based upload with resume capability
  - **Agent's discretion:** Implement if bandwidth limitations emerge during Phase 3 execution

### UI/UX Edge Cases

- Preview window should NOT obstruct "Start Recording" button or timer
- If candidate has very large webcam resolution, preview scaling to 320×240 should be smooth (CSS or canvas)
- Mobile: OUT OF SCOPE (Phase 3 is desktop only per FR-03 MediaRecorder inconsistencies note)

</specifics>

---

<deferred>

## Deferred Ideas

- **Video playback in report:** Recording playback during Phase 5 report review (complex storage; text report sufficient for MVP)
- **Real-time analysis during recording:** Move to Phase 4+ (CPU constraint; deferred to optimization phase)
- **Multi-camera support:** One camera only for MVP; future enhancement
- **Screen share recording:** Out of scope; interview focuses on candidate presence only
- **Automatic question skip if no response:** Keeping question mandatory; can revisit if UX testing reveals need

</deferred>

---

_Phase: 03-interview-session_  
_Context gathered: April 12, 2026_  
_16 decisions locked for planning and execution_
