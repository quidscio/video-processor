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
from datetime import timedelta, datetime
from pathlib import Path

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

def transcribe_to_srt(
    input_path: str,
    model_name: str = WHISPER_MODEL,
    debug: bool = False,
) -> str:
    """
    Transcribe the given media file and return an SRT-formatted string.
    """
    # Prepare ffmpeg conversion to mono WAV for full-length decoding
    if shutil.which("ffmpeg") is None:
        raise RuntimeError(
            "ffmpeg not found in PATH; please install ffmpeg for transcription"
        )
    # Timestamp prefix for debug artifacts
    ts = datetime.now().strftime("%Y%m%d_%H%M%S") if debug else None
    stem = Path(input_path).stem
    wav_name = f"{ts}_{stem}.wav" if debug else None
    tmp_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    tmp_wav.close()
    try:
        cmd = ["ffmpeg", "-y", "-i", input_path, "-ac", "1", "-ar", "16000", "-vn", tmp_wav.name]
        if debug:
            print(f"__ Running ffmpeg conversion: {' '.join(cmd)}")
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        model = load_model(model_name)
        result = model.transcribe(tmp_wav.name, verbose=debug)
    finally:
        if debug:
            # preserve intermediate WAV for inspection
            dest = Path.cwd() / wav_name
            shutil.move(tmp_wav.name, dest)
            print(f"__ Saved intermediate audio to {dest}")
        else:
            try:
                os.remove(tmp_wav.name)
            except OSError:
                pass
    # Build SRT from Whisper segments
    subtitles = []
    for i, seg in enumerate(result.get("segments", []), start=1):
        start = timedelta(seconds=seg["start"])
        end = timedelta(seconds=seg["end"])
        content = seg.get("text", "").strip()
        subtitle = srt.Subtitle(index=i, start=start, end=end, content=content)
        subtitles.append(subtitle)
    srt_text = srt.compose(subtitles)
    if debug:
        # save SRT for debugging
        srt_file = Path.cwd() / f"{ts}_{stem}.srt"
        srt_file.write_text(srt_text, encoding='utf-8')
        print(f"__ Saved intermediate SRT to {srt_file}")
    return srt_text