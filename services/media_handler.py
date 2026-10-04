import os
import shutil
import subprocess
from pathlib import Path


class MediaHandlingError(Exception):
    pass


class MediaHandler:
    def __init__(self, base_recordings_dir: str = 'recordings'):
        self.base_recordings_dir = base_recordings_dir
        os.makedirs(self.base_recordings_dir, exist_ok=True)

    def get_session_dir(self, session_id: int) -> str:
        session_dir = os.path.join(self.base_recordings_dir, f'session_{session_id}')
        os.makedirs(session_dir, exist_ok=True)
        return session_dir

    def save_media(self, blob: bytes, session_id: int, question_number: int) -> dict:
        try:
            session_dir = self.get_session_dir(session_id)
            webm_filename = f'q{question_number}.webm'
            webm_path = os.path.join(session_dir, webm_filename)

            with open(webm_path, 'wb') as out_file:
                out_file.write(blob)

            wav_filename = f'q{question_number}.wav'
            wav_path = os.path.join(session_dir, wav_filename)
            self.extract_audio(webm_path, wav_path)

            return {
                'webm_path': webm_path,
                'wav_path': wav_path,
                'webm_filename': webm_filename,
                'wav_filename': wav_filename,
            }
        except Exception as exc:
            raise MediaHandlingError(f'Failed to save media: {exc}') from exc

    def extract_audio(self, video_path: str, output_audio_path: str, format: str = 'wav') -> str:
        # Try PATH first, then fall back to known winget install location
        ffmpeg_path = shutil.which('ffmpeg')
        if not ffmpeg_path:
            winget_dir = Path(os.environ.get('LOCALAPPDATA', '')) / 'Microsoft' / 'WinGet' / 'Packages'
            matches = sorted(winget_dir.glob('Gyan.FFmpeg*/ffmpeg-*/bin/ffmpeg.exe')) if winget_dir.is_dir() else []
            if matches:
                ffmpeg_path = str(matches[-1])
        if not ffmpeg_path:
            raise MediaHandlingError('ffmpeg not found. Install ffmpeg and ensure it is on the PATH.')

        cmd = [
            ffmpeg_path,
            '-y',
            '-i', video_path,
            '-vn',
            '-acodec', 'pcm_s16le',
            '-ar', '16000',
            '-ac', '1',
            output_audio_path,
        ]

        result = subprocess.run(cmd, capture_output=True, timeout=60)
        if result.returncode != 0:
            stderr = result.stderr.decode('utf-8', errors='ignore')
            raise MediaHandlingError(f'ffmpeg extraction failed: {stderr}')

        return output_audio_path

    def get_media_file_path(self, session_id: int, question_number: int, media_type: str = 'webm') -> str:
        session_dir = self.get_session_dir(session_id)
        ext = 'webm' if media_type == 'webm' else 'wav'
        return os.path.join(session_dir, f'q{question_number}.{ext}')

    def list_session_media(self, session_id: int) -> dict:
        session_dir = self.get_session_dir(session_id)
        files = os.listdir(session_dir)
        return {
            'webm_files': sorted([f for f in files if f.endswith('.webm')]),
            'wav_files': sorted([f for f in files if f.endswith('.wav')]),
        }

    def delete_session_media(self, session_id: int) -> bool:
        session_dir = self.get_session_dir(session_id)
        if os.path.exists(session_dir):
            shutil.rmtree(session_dir)
        return True


media_handler = MediaHandler()


def save_media_for_response(blob: bytes, session_id: int, question_number: int) -> dict:
    return media_handler.save_media(blob, session_id, question_number)
