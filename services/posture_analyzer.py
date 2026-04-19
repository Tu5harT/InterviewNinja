"""
Posture Analyzer — runs posture_worker.py in an isolated subprocess.

This avoids the oneDNN deadlock that occurs when mediapipe 0.10+ and
TensorFlow 2.x are both loaded in the same process.
"""
import os
import sys
import json
import subprocess
from pathlib import Path

_MODEL_PATH = str(Path(__file__).parent.parent / 'data' / 'pose_landmarker_lite.task')
_WORKER_PATH = str(Path(__file__).parent.parent / 'posture_worker.py')
_PYTHON = sys.executable  # same venv python


def analyze_posture(video_path: str, fps_sample: int = 1) -> dict:
    """
    Analyze posture from a video file.
    Delegates to posture_worker.py in a subprocess to avoid TF/mediapipe deadlock.

    Returns:
        dict with posture_score (0-100), posture_label, frames_analyzed
    """
    if not os.path.exists(video_path):
        return _failure_result('Video file not found')

    if not os.path.exists(_MODEL_PATH):
        return _failure_result(f'Pose model not found: {_MODEL_PATH}')

    if not os.path.exists(_WORKER_PATH):
        return _failure_result(f'posture_worker.py not found: {_WORKER_PATH}')

    try:
        result = subprocess.run(
            [_PYTHON, _WORKER_PATH, video_path, _MODEL_PATH],
            capture_output=True,
            timeout=120,
        )
        stdout = result.stdout.decode('utf-8', errors='ignore').strip()
        if not stdout:
            stderr = result.stderr.decode('utf-8', errors='ignore')[-500:]
            return _failure_result(f'Worker produced no output. stderr: {stderr}')

        # The worker prints one JSON line at the end
        last_line = [l for l in stdout.splitlines() if l.strip()][-1]
        data = json.loads(last_line)
        return data

    except subprocess.TimeoutExpired:
        return _failure_result('Posture analysis timed out (>120s)')
    except json.JSONDecodeError as e:
        return _failure_result(f'Worker returned invalid JSON: {e}')
    except Exception as e:
        return _failure_result(f'Subprocess error: {e}')


def _failure_result(reason: str) -> dict:
    return {
        'status': 'failed',
        'posture_score': None,
        'posture_label': None,
        'frames_analyzed': 0,
        'reason': reason
    }
