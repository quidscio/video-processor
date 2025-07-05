"""
converter.py

Transcribe video/audio files to SRT using OpenAI Whisper.
"""
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
    model = load_model(model_name)
    result = model.transcribe(input_path, verbose=False)
    subtitles = []
    for i, seg in enumerate(result.get("segments", []), start=1):
        start = timedelta(seconds=seg["start"])
        end = timedelta(seconds=seg["end"])
        content = seg.get("text", "").strip()
        subtitle = srt.Subtitle(index=i, start=start, end=end, content=content)
        subtitles.append(subtitle)
    return srt.compose(subtitles)