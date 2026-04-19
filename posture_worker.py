"""
posture_worker.py — Standalone subprocess worker for posture analysis.
Run as: python posture_worker.py <video_path>
Outputs a single JSON line to stdout.

Kept completely separate from the main Flask process so that mediapipe's
oneDNN init does not deadlock with TensorFlow (which runs in the main process).
"""
import sys
import json
import os
import cv2


def compute_posture_score(landmarks) -> int:
    lm = landmarks
    shoulder_diff = abs(lm[11].y - lm[12].y)
    shoulder_score = max(0, 100 - (shoulder_diff * 500))

    mid_shoulder_x = (lm[11].x + lm[12].x) / 2
    head_lean = abs(lm[0].x - mid_shoulder_x)
    head_score = max(0, 100 - (head_lean * 400))

    visibility_penalty = 0
    left_vis = getattr(lm[11], 'visibility', 1.0) or 1.0
    right_vis = getattr(lm[12], 'visibility', 1.0) or 1.0
    if left_vis < 0.5 or right_vis < 0.5:
        visibility_penalty = 20

    combined = (shoulder_score * 0.5 + head_score * 0.5) - visibility_penalty
    return max(0, min(100, round(combined)))


def analyze(video_path: str, model_path: str, fps_sample: int = 1) -> dict:
    import mediapipe as mp
    from mediapipe.tasks.python.vision import PoseLandmarker, PoseLandmarkerOptions
    from mediapipe.tasks.python import vision
    from mediapipe.tasks.python.core import base_options as mp_base

    if not os.path.exists(video_path):
        return {'status': 'failed', 'reason': 'Video file not found',
                'posture_score': None, 'posture_label': None, 'frames_analyzed': 0}

    if not os.path.exists(model_path):
        return {'status': 'failed', 'reason': f'Model not found: {model_path}',
                'posture_score': None, 'posture_label': None, 'frames_analyzed': 0}

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return {'status': 'failed', 'reason': 'Cannot open video',
                'posture_score': None, 'posture_label': None, 'frames_analyzed': 0}

    video_fps = cap.get(cv2.CAP_PROP_FPS) or 30
    frame_interval = max(1, int(video_fps / fps_sample))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    frame_scores = []
    frame_idx = 0

    base_opts = mp_base.BaseOptions(model_asset_path=model_path)
    options = PoseLandmarkerOptions(
        base_options=base_opts,
        running_mode=vision.RunningMode.IMAGE,
        num_poses=1,
        min_pose_detection_confidence=0.5,
        min_pose_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    try:
        with PoseLandmarker.create_from_options(options) as landmarker:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                if frame_idx % frame_interval == 0:
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
                    result = landmarker.detect(mp_image)
                    if result.pose_landmarks:
                        score = compute_posture_score(result.pose_landmarks[0])
                        frame_scores.append(score)
                frame_idx += 1
    finally:
        cap.release()

    if not frame_scores:
        return {
            'status': 'low_confidence',
            'posture_score': 50,
            'posture_label': 'Fair',
            'frames_analyzed': 0,
            'total_frames': total_frames,
            'reason': 'No pose landmarks detected'
        }

    avg_score = round(sum(frame_scores) / len(frame_scores))
    label = 'Good' if avg_score >= 75 else ('Fair' if avg_score >= 50 else 'Poor')

    return {
        'status': 'success',
        'posture_score': avg_score,
        'posture_label': label,
        'frames_analyzed': len(frame_scores),
        'total_frames': total_frames
    }


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(json.dumps({'status': 'failed', 'reason': 'Usage: posture_worker.py <video_path> <model_path>',
                          'posture_score': None, 'posture_label': None, 'frames_analyzed': 0}))
        sys.exit(1)

    video_path = sys.argv[1]
    model_path = sys.argv[2]

    result = analyze(video_path, model_path)
    print(json.dumps(result))
