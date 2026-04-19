"""
Emotion Analyzer — OpenCV Haar Cascade + basic emotion heuristics
Detects faces in video frames and estimates emotional composure.
Uses OpenCV's built-in face detection (no TensorFlow dependency).
"""
import cv2
import os
import numpy as np

# Composure weights from 08-scoring-engine-spec.md
EMOTION_COMPOSURE_WEIGHTS = {
    'neutral': 1.0,
    'happy': 0.9,
    'surprise': 0.5,
    'sad': 0.3,
    'disgust': 0.2,
    'angry': 0.2,
    'fear': 0.1
}


def analyze_emotion(video_path: str, fps_sample: int = 2) -> dict:
    """
    Analyze facial emotions from a video file using OpenCV.

    Uses Haar cascade for face detection and basic brightness/contrast
    heuristics for a preliminary emotion estimate. For production,
    replace with a dedicated emotion model.

    Args:
        video_path: Path to the .webm video file
        fps_sample: Frames per second to sample (default 2)

    Returns:
        dict with emotion_dominant, emotion_scores, emotion_score (0-100)
    """
    if not os.path.exists(video_path):
        return _failure_result("Video file not found")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return _failure_result("Cannot open video file")

    video_fps = cap.get(cv2.CAP_PROP_FPS) or 30
    frame_interval = max(1, int(video_fps / fps_sample))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    )
    smile_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + 'haarcascade_smile.xml'
    )

    emotion_frames = []
    face_sizes = []
    frame_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx % frame_interval == 0:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(60, 60))

            if len(faces) > 0:
                # Take the largest face
                x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
                face_roi = gray[y:y+h, x:x+w]
                face_sizes.append(w * h)

                # Detect smile in face region
                smiles = smile_cascade.detectMultiScale(
                    face_roi, 1.7, 15, minSize=(25, 25)
                )
                has_smile = len(smiles) > 0

                # Compute face brightness and contrast
                brightness = float(np.mean(face_roi))
                contrast = float(np.std(face_roi))

                # Heuristic emotion estimation based on face metrics
                emotions = _estimate_emotions(has_smile, brightness, contrast)
                emotion_frames.append(emotions)

        frame_idx += 1

    cap.release()

    if len(emotion_frames) < 1:
        return _failure_result("No face detected in any frame")

    # Aggregate emotion distributions across all frames
    aggregated = {}
    keys = emotion_frames[0].keys()
    for key in keys:
        aggregated[key] = round(
            sum(f.get(key, 0) for f in emotion_frames) / len(emotion_frames), 2
        )

    # Dominant emotion
    dominant = max(aggregated, key=aggregated.get)

    # Composure score (from spec)
    raw_score = sum(
        aggregated.get(emotion, 0) * weight
        for emotion, weight in EMOTION_COMPOSURE_WEIGHTS.items()
    )
    composure_score = min(100, max(0, round(raw_score)))

    # Face consistency bonus: steady face size = more composed
    if len(face_sizes) > 1:
        size_variance = np.std(face_sizes) / (np.mean(face_sizes) + 1)
        if size_variance < 0.1:  # Very stable
            composure_score = min(100, composure_score + 5)

    return {
        'status': 'success',
        'emotion_dominant': dominant,
        'emotion_scores': aggregated,
        'emotion_score': composure_score,
        'frames_analyzed': len(emotion_frames),
        'total_frames': total_frames
    }


def _estimate_emotions(has_smile: bool, brightness: float, contrast: float) -> dict:
    """
    Estimate emotion distribution from face features.
    This is a heuristic approach using smile detection and face metrics.
    For production, replace with a proper CNN emotion classifier.
    """
    if has_smile:
        # Smiling: likely happy or neutral
        return {
            'neutral': 25.0,
            'happy': 55.0,
            'surprise': 8.0,
            'sad': 2.0,
            'disgust': 2.0,
            'angry': 3.0,
            'fear': 5.0
        }
    elif brightness > 130 and contrast > 40:
        # Well-lit, high contrast: engaged/neutral
        return {
            'neutral': 60.0,
            'happy': 15.0,
            'surprise': 8.0,
            'sad': 5.0,
            'disgust': 2.0,
            'angry': 5.0,
            'fear': 5.0
        }
    elif brightness < 90:
        # Dark face region: could indicate looking down or tension
        return {
            'neutral': 35.0,
            'happy': 5.0,
            'surprise': 5.0,
            'sad': 20.0,
            'disgust': 5.0,
            'angry': 10.0,
            'fear': 20.0
        }
    else:
        # Default: neutral-leaning
        return {
            'neutral': 50.0,
            'happy': 10.0,
            'surprise': 10.0,
            'sad': 10.0,
            'disgust': 3.0,
            'angry': 7.0,
            'fear': 10.0
        }


def _failure_result(reason: str) -> dict:
    return {
        'status': 'failed',
        'emotion_dominant': None,
        'emotion_scores': {},
        'emotion_score': None,
        'reason': reason,
        'frames_analyzed': 0
    }
