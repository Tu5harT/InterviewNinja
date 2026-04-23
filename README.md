# Interview Ninja

AI-powered interview practice platform with real-time feedback on your responses.

## Features

- Resume upload & skill extraction
- AI-generated interview questions based on your skills
- Video recording of responses
- AI analysis: emotion, voice, posture, answer quality
- Detailed performance report

## Prerequisites

- Python 3.10+ (Python 3.11 recommended)
- Webcam & microphone
- Internet connection (for AI model downloads)

## Quick Setup

### 1. Clone/Download the Project

```bash
cd interviewNinja-leetcode-v.1
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS/Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Download AI Models

```bash
# Download spaCy English model
python -m spacy download en_core_web_sm

# Download MediaPipe Pose model (if not already in data/)
# The pose_landmarker_lite.task should be in the data/ folder
```

### 5. Create Data Directories

```bash
mkdir -p data uploads recordings instance
```

### 6. Run the Application

```bash
python app.py
```

### 7. Open in Browser

```
http://localhost:5000
```

## First-Time Setup Notes

On first run, several AI models will be downloaded automatically:
- `all-MiniLM-L6-v2` (sentence-transformers) - for answer quality analysis
- MediaPipe models - for posture analysis
- DeepFace models - for emotion analysis

This may take 5-10 minutes depending on your internet connection.

## Project Structure

```
interviewNinja/
├── app.py              # Main Flask application
├── models.py           # Database models
├── requirements.txt    # Python dependencies
├── routes/             # API endpoints
│   ├── resume.py      # Resume upload & parsing
│   └── session.py     # Interview session management
├── services/           # AI analysis services
│   ├── resume_parser.py
│   ├── question_generator.py
│   ├── emotion_analyzer.py
│   ├── voice_analyzer.py
│   ├── posture_analyzer.py
│   ├── answer_analyzer.py
│   └── score_aggregator.py
├── templates/          # HTML templates
├── static/            # CSS, JS files
├── data/              # Question banks, models
│   ├── question_bank.json
│   ├── behavioral_questions.json
│   ├── skills_taxonomy.json
│   └── pose_landmarker_lite.task
├── uploads/           # Uploaded resumes
├── recordings/        # Video/audio recordings
└── instance/         # SQLite database
```

## Troubleshooting

### `ModuleNotFoundError: No module named 'spacy'`
```bash
pip install spacy
python -m spacy download en_core_web_sm
```

### `MediaPipe model not found`
Ensure `data/pose_landmarker_lite.task` exists. If missing, download from MediaPipe.

### `Permission denied` or webcam not working
- Grant camera/microphone permissions in browser
- Try Chrome or Edge for best compatibility

### `SQLite database error`
Delete `instance/interview_ninja.db` and restart - it will be recreated.

### First-run analysis takes too long
This is normal. AI models (especially sentence-transformers) load slowly on first use. Subsequent runs are faster.

## Development

### Run Tests
```bash
pytest tests/
```

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/resume/upload` | Upload resume PDF |
| GET | `/review/<id>` | View candidate profile |
| POST | `/api/v1/session/start` | Start interview session |
| POST | `/api/v1/session/upload-response` | Upload video response |
| POST | `/api/v1/session/complete` | Complete interview |
| GET | `/api/v1/session/analysis/status/<id>` | Check analysis status |
| GET | `/report?session_id=<id>` | View analysis report |

## License

MIT