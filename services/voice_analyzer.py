"""
Voice Analyzer — Google STT + Audio Preprocessing + Filler Word Detection
Transcribes audio using Google Speech Recognition with amplitude normalization
to ensure reliable recognition across varying recording volumes.
"""
import os
import wave
import io
import numpy as np

# Filler words from 08-scoring-engine-spec.md
FILLER_WORDS = {
    'um', 'uh', 'like', 'basically', 'you know',
    'right', 'so', 'actually', 'literally', 'kind of'
}


def _normalize_audio(wav_path: str, target_rms: int = 10000) -> io.BytesIO:
    """
    Read a WAV file and amplify it so the RMS reaches target_rms.
    Returns an in-memory BytesIO WAV buffer ready for SpeechRecognition.
    Gain is capped at 20x to avoid distortion on genuinely quiet files.
    """
    with wave.open(wav_path, 'r') as wf:
        params = wf.getparams()
        raw = wf.readframes(wf.getnframes())

    data = np.frombuffer(raw, dtype=np.int16).astype(np.float32)
    current_rms = np.sqrt(np.mean(data ** 2))

    if current_rms > 1:
        gain = min(target_rms / current_rms, 20.0)
        data = np.clip(data * gain, -32768, 32767)

    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setparams(params)
        wf.writeframes(data.astype(np.int16).tobytes())
    buf.seek(0)
    return buf


def analyze_voice(wav_path: str) -> dict:
    """
    Analyze voice from a WAV audio file using Google STT.

    Args:
        wav_path: Path to the WAV file extracted from the interview recording.

    Returns:
        dict with transcript, filler_count, wpm, clarity_score, voice_tone_label
    """
    if not os.path.exists(wav_path):
        return _failure_result('Audio file not found')

    try:
        import speech_recognition as sr
    except ImportError:
        return _failure_result('SpeechRecognition not installed')

    # Get audio duration from the raw file
    try:
        with wave.open(wav_path, 'r') as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            duration_sec = frames / float(rate)
    except Exception as e:
        return _failure_result(f'Cannot read audio file: {e}')

    if duration_sec < 0.5:
        return _failure_result('Audio too short for analysis')

    # Normalize audio volume before sending to Google STT
    try:
        audio_buf = _normalize_audio(wav_path, target_rms=10000)
    except Exception as e:
        return _failure_result(f'Audio normalization failed: {e}')

    recognizer = sr.Recognizer()
    # Low fixed threshold — normalization handles the actual level
    recognizer.energy_threshold = 50
    recognizer.dynamic_energy_threshold = False

    transcript = None

    # First attempt: full audio
    try:
        with sr.AudioFile(audio_buf) as source:
            audio = recognizer.record(source)
        transcript = recognizer.recognize_google(audio, language='en-US')
    except sr.UnknownValueError:
        pass
    except sr.RequestError as e:
        return _failure_result(f'Google STT API error: {e}')
    except Exception as e:
        return _failure_result(f'Transcription failed: {e}')

    # Second attempt: try en-IN (Indian English) if first attempt failed
    if not transcript:
        try:
            audio_buf.seek(0)
            with sr.AudioFile(audio_buf) as source:
                audio = recognizer.record(source)
            transcript = recognizer.recognize_google(audio, language='en-IN')
        except sr.UnknownValueError:
            pass
        except Exception:
            pass

    # Third attempt: try en-GB if still no result
    if not transcript:
        try:
            audio_buf.seek(0)
            with sr.AudioFile(audio_buf) as source:
                audio = recognizer.record(source)
            transcript = recognizer.recognize_google(audio, language='en-GB')
        except sr.UnknownValueError:
            pass
        except Exception:
            pass

    if not transcript or not transcript.strip():
        return _failure_result('Speech not recognizable — audio may be too quiet or unclear')

    # Filler word detection
    words = transcript.lower().split()
    filler_found = {}
    for word in words:
        clean = word.strip('.,!?;:')
        if clean in FILLER_WORDS:
            filler_found[clean] = filler_found.get(clean, 0) + 1

    # Check two-word fillers
    for i in range(len(words) - 1):
        bigram = f"{words[i].strip('.,!?')} {words[i+1].strip('.,!?')}"
        if bigram in FILLER_WORDS:
            filler_found[bigram] = filler_found.get(bigram, 0) + 1

    filler_count = sum(filler_found.values())

    # WPM calculation
    word_count = len(words)
    wpm = round((word_count / duration_sec) * 60) if duration_sec > 0 else 0

    # Clarity score
    clarity_score = compute_clarity_score(filler_count, wpm)

    # Voice tone label
    if clarity_score >= 75:
        tone_label = 'Confident'
    elif clarity_score >= 50:
        tone_label = 'Moderate'
    else:
        tone_label = 'Nervous'

    return {
        'status': 'success',
        'transcript': transcript,
        'filler_count': filler_count,
        'filler_words': filler_found,
        'wpm': wpm,
        'word_count': word_count,
        'duration_sec': round(duration_sec, 2),
        'clarity_score': clarity_score,
        'voice_tone_label': tone_label
    }


def compute_clarity_score(filler_count: int, wpm: int) -> int:
    """
    Compute voice clarity score (from 08-scoring-engine-spec.md).
    Penalizes filler words and deviation from ideal 120-150 WPM range.
    """
    filler_penalty = min(50, filler_count * 5)

    if 120 <= wpm <= 150:
        wpm_penalty = 0
    elif wpm < 120:
        wpm_penalty = (120 - wpm) * 0.4
    else:
        wpm_penalty = (wpm - 150) * 0.3
    wpm_penalty = min(30, wpm_penalty)

    score = 100 - filler_penalty - wpm_penalty
    return max(0, min(100, round(score)))


def _failure_result(reason: str) -> dict:
    return {
        'status': 'failed',
        'transcript': None,
        'filler_count': 0,
        'filler_words': {},
        'wpm': 0,
        'clarity_score': None,
        'voice_tone_label': None,
        'reason': reason
    }
