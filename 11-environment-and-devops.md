# 11 — Environment and DevOps
**Project:** Interview Ninja — AI-Powered Mock Interview Assistant  
**Version:** 1.0

---

## 1. Overview

This document covers all environment configuration, local setup, and deployment procedures for Interview Ninja. Two environments are defined: **Development** (local machine) and **Production** (single Ubuntu server). A third **Test** environment runs inside the development setup using pytest fixtures.

---

## 2. System Prerequisites

From the source project documentation, the minimum hardware and software requirements are:

### 2.1 Hardware (Minimum — per source document)

| Component | Minimum | Recommended |
|---|---|---|
| CPU | 4-core | 8-core |
| RAM | 8 GB | 16 GB |
| Storage | 50 GB | 200 GB |
| Webcam | Required | Required |
| Microphone | Required | Required |
| Internet | Required (STT API) | Broadband |

### 2.2 Software Prerequisites

| Dependency | Version | Install |
|---|---|---|
| Python | 3.10+ | `sudo apt install python3.10` |
| pip | Latest | `pip install --upgrade pip` |
| ffmpeg | Any recent | `sudo apt install ffmpeg` |
| Git | 2.x+ | `sudo apt install git` |
| Chrome | 90+ | Required for browser testing |

---

## 3. Development Environment Setup

### 3.1 Clone and Create Virtual Environment

```bash
git clone https://github.com/<org>/interview_ninja.git
cd interview_ninja

python3 -m venv venv
source venv/bin/activate          # Linux / macOS
# venv\Scripts\activate           # Windows

pip install -r requirements.txt
```

### 3.2 Install System Dependencies

```bash
# Ubuntu / Debian
sudo apt-get update
sudo apt-get install -y ffmpeg

# macOS
brew install ffmpeg

# Verify
ffmpeg -version
```

### 3.3 Download NLP Models

```bash
# spaCy English model
python -m spacy download en_core_web_sm

# sentence-transformers + DeepFace models are auto-downloaded on first run
# Trigger warm-up manually:
python -c "
from app import create_app
app = create_app()
with app.app_context():
    from services.model_registry import warm_all_models
    warm_all_models()
print('Models loaded successfully')
"
```

Expected downloads:
- DeepFace FER weights: ~100MB (stored in `~/.deepface/`)
- Sentence-BERT `all-MiniLM-L6-v2`: ~80MB (stored in `~/.cache/torch/`)

### 3.4 Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env`:
```
SECRET_KEY=your-random-secret-key-here
FLASK_ENV=development
GOOGLE_STT_API_KEY=         # optional; leave blank to use Whisper fallback
DATABASE_URL=               # leave blank for SQLite in development
```

### 3.5 Initialize Database

```bash
python -c "from app import create_app; app = create_app(); \
           __import__('models').db.create_all.__module__"
# OR simply run the app — db.create_all() is called in app factory
```

### 3.6 Start Development Server

```bash
chmod +x start.sh
./start.sh
```

Or directly:
```bash
export FLASK_ENV=development
flask run --host=0.0.0.0 --port=5000
```

Application available at: `http://localhost:5000`

### 3.7 `start.sh` Script

```bash
#!/bin/bash
set -e

echo "=== Interview Ninja: Pre-flight Checks ==="

# Check ffmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "ERROR: ffmpeg is not installed. Run: sudo apt install ffmpeg"
    exit 1
fi
echo "✅ ffmpeg found: $(ffmpeg -version 2>&1 | head -1)"

# Check Python version
PYTHON_VER=$(python3 --version 2>&1)
echo "✅ Python: $PYTHON_VER"

# Check virtualenv
if [ ! -d "venv" ]; then
    echo "WARNING: No virtualenv found. Creating..."
    python3 -m venv venv
fi
source venv/bin/activate

# Check key packages
python -c "import flask, cv2, mediapipe, deepface" 2>/dev/null || {
    echo "ERROR: Required Python packages missing. Run: pip install -r requirements.txt"
    exit 1
}
echo "✅ Python packages OK"

# Load .env
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Initialize DB
python -c "from app import create_app; app = create_app()"
echo "✅ Database initialized"

echo "=== Starting Interview Ninja on port 5000 ==="
flask run --host=0.0.0.0 --port=5000
```

---

## 4. Environment Variables Reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `SECRET_KEY` | ✅ in production | `dev-insecure-key` | Flask session signing key. Must be a long random string in production. |
| `FLASK_ENV` | No | `development` | Set to `production` to disable debug mode. |
| `DATABASE_URL` | ✅ in production | SQLite file | PostgreSQL connection string: `postgresql://user:pass@host:5432/dbname` |
| `GOOGLE_STT_API_KEY` | No | None | If absent, Whisper offline model is used for STT. |
| `WEIGHT_EMOTION` | No | `0.20` | Override emotion score weight in overall score calculation. |
| `WEIGHT_VOICE` | No | `0.30` | Override voice score weight. |
| `WEIGHT_POSTURE` | No | `0.15` | Override posture score weight. |
| `WEIGHT_ANSWER` | No | `0.35` | Override answer quality weight. |
| `MAX_RECORDING_SECONDS` | No | `90` | Maximum per-question recording time. |
| `ANALYSIS_TIMEOUT_SECONDS` | No | `600` | Kill analysis job after N seconds. |

**Validation at startup:**
```python
import os
assert os.environ.get('SECRET_KEY') != 'dev-insecure-key' or \
       os.environ.get('FLASK_ENV') == 'development', \
       "Set a secure SECRET_KEY in production!"
```

---

## 5. Production Deployment

### 5.1 Server Setup (Ubuntu 22.04 LTS)

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install dependencies
sudo apt-get install -y python3.10 python3.10-venv python3-pip \
                        ffmpeg nginx postgresql redis-server git

# Create application user
sudo useradd -m -s /bin/bash interview_ninja
sudo su - interview_ninja

# Clone and setup
git clone https://github.com/<org>/interview_ninja.git /home/interview_ninja/app
cd /home/interview_ninja/app
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn celery
python -m spacy download en_core_web_sm
```

### 5.2 PostgreSQL Setup

```bash
sudo -u postgres psql
CREATE DATABASE interview_ninja_prod;
CREATE USER ninja_user WITH PASSWORD 'strong_password_here';
GRANT ALL PRIVILEGES ON DATABASE interview_ninja_prod TO ninja_user;
\q
```

### 5.3 Environment Configuration (Production)

```bash
cat > /home/interview_ninja/app/.env << 'EOF'
SECRET_KEY=<64-char-random-string>
FLASK_ENV=production
DATABASE_URL=postgresql://ninja_user:strong_password_here@localhost:5432/interview_ninja_prod
GOOGLE_STT_API_KEY=<api-key-if-used>
EOF
chmod 600 .env
```

### 5.4 Gunicorn Service

```ini
# /etc/systemd/system/interview_ninja.service
[Unit]
Description=Interview Ninja Flask Application
After=network.target postgresql.service

[Service]
User=interview_ninja
WorkingDirectory=/home/interview_ninja/app
EnvironmentFile=/home/interview_ninja/app/.env
ExecStart=/home/interview_ninja/app/venv/bin/gunicorn \
          -w 4 \
          -b 127.0.0.1:8000 \
          --timeout 300 \
          --access-logfile /var/log/interview_ninja/access.log \
          --error-logfile /var/log/interview_ninja/error.log \
          "app:create_app()"
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo mkdir -p /var/log/interview_ninja
sudo chown interview_ninja:interview_ninja /var/log/interview_ninja
sudo systemctl enable interview_ninja
sudo systemctl start interview_ninja
```

### 5.5 Nginx Configuration

```nginx
# /etc/nginx/sites-available/interview_ninja
server {
    listen 80;
    server_name your-domain.com;

    client_max_body_size 20M;

    location /static/ {
        alias /home/interview_ninja/app/static/;
        expires 7d;
        add_header Cache-Control "public, immutable";
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 300s;
        proxy_connect_timeout 30s;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/interview_ninja /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 5.6 (Optional) Celery Worker for Production AI Jobs

```ini
# /etc/systemd/system/interview_ninja_celery.service
[Unit]
Description=Interview Ninja Celery Worker
After=network.target redis.service

[Service]
User=interview_ninja
WorkingDirectory=/home/interview_ninja/app
EnvironmentFile=/home/interview_ninja/app/.env
ExecStart=/home/interview_ninja/app/venv/bin/celery \
          -A app.celery worker \
          --concurrency=2 \
          --loglevel=info \
          --logfile=/var/log/interview_ninja/celery.log
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## 6. Directory Permissions (Production)

```bash
# Writable by the application
sudo chown -R interview_ninja:interview_ninja /home/interview_ninja/app/uploads
sudo chown -R interview_ninja:interview_ninja /home/interview_ninja/app/recordings
sudo chown -R interview_ninja:interview_ninja /home/interview_ninja/app/reports_output
sudo chmod 750 /home/interview_ninja/app/uploads
sudo chmod 750 /home/interview_ninja/app/recordings
```

---

## 7. Storage Estimation and Management

| Content | Size per Session | 100 Sessions |
|---|---|---|
| WebM videos (10 × 90s) | ~150 MB | ~15 GB |
| WAV audio (10 × 90s) | ~27 MB | ~2.7 GB |
| PDF report | ~0.5 MB | ~50 MB |
| DB rows (all tables) | Negligible | < 100 MB |
| **Total** | **~178 MB** | **~18 GB** |

**Recommendation:** At 100+ sessions, migrate recordings to object storage (MinIO/S3) and implement a TTL cleanup policy. This is deferred to v2.

---

## 8. Monitoring (MVP Baseline)

| Signal | Method | Production |
|---|---|---|
| App health | `GET /health` → `{"status": "ok"}` | Nginx status |
| Error logs | `/var/log/interview_ninja/error.log` | Tail or Sentry (future) |
| Access logs | `/var/log/interview_ninja/access.log` | Parse for 5xx rate |
| Analysis job failures | Log `analysis_results.*.status = "failed"` | DB query alert |
| Disk usage | `df -h /home/interview_ninja/app/recordings` | Cron alert |

---

## 9. Backup Strategy

```bash
# Daily PostgreSQL backup (add to crontab)
0 2 * * * pg_dump interview_ninja_prod | gzip > \
  /backups/interview_ninja_$(date +\%Y\%m\%d).sql.gz

# Weekly cleanup (keep last 7 days)
0 3 * * 0 find /backups -name "*.sql.gz" -mtime +7 -delete
```

---

*Source: Interview Ninja project documentation, A.C. Patil College of Engineering.*
