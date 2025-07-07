"""
converter.py

Transcribe video/audio files to SRT using OpenAI Whisper.
"""
import os
import shutil
import subprocess
import tempfile
import whisper
import srt
from datetime import timedelta

from .config import WHISPER_MODEL, DEVICE

_model = None

def load_model(model_name: str = WHISPER_MODEL, device: str = DEVICE):
    """
    Load and cache the Whisper model on the specified device.
    """
    global _model
    if _model is None:
        _model = whisper.load_model(model_name, device=device)
    return _model

def transcribe_to_srt(input_path: str, model_name: str = WHISPER_MODEL) -> str:
    """
    Transcribe the given media file and return an SRT-formatted string.
    """
    # Convert input to mono WAV via ffmpeg for reliable full-length decoding
    if shutil.which("ffmpeg") is None:
        raise RuntimeError(
            "ffmpeg not found in PATH; please install ffmpeg for transcription"
        )
    tmp_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    tmp_wav.close()
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", input_path, "-ac", "1", "-ar", "16000", "-vn", tmp_wav.name],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        model = load_model(model_name)
        result = model.transcribe(tmp_wav.name, verbose=False)
    finally:
        try:
            os.remove(tmp_wav.name)
        except OSError:
            pass
    subtitles = []
    for i, seg in enumerate(result.get("segments", []), start=1):
        start = timedelta(seconds=seg["start"])
        end = timedelta(seconds=seg["end"])
        content = seg.get("text", "").strip()
        subtitle = srt.Subtitle(index=i, start=start, end=end, content=content)
        subtitles.append(subtitle)
    return srt.compose(subtitles)