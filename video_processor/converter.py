"""
converter.py

Transcribe video/audio files to SRT using OpenAI Whisper.
"""
import os
import shutil
import subprocess
import tempfile
import re
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
    backend: str = 'default',
    model: str = 'default',
) -> str:
    """
    Transcribe the given media file and return an SRT-formatted string.
    """
    # Prepare ffmpeg conversion to mono WAV for full-length decoding
    if shutil.which("ffmpeg") is None:
        raise RuntimeError(
            "ffmpeg not found in PATH; please install ffmpeg for transcription"
        )
    # Timestamp suffix for artifact naming and sanitize basename for files
    from .cli import generate_timestamp_suffix
    timestamp_suffix = generate_timestamp_suffix(backend, model_name)
    raw_stem = Path(input_path).stem
    # slugify stem: remove invalid chars and replace spaces/underscores with hyphens
    stem = re.sub(r"[^\w\s-]", "", raw_stem).strip()
    stem = re.sub(r"[\s_-]+", "-", stem)
    if debug:
        wav_name = f"{stem}{timestamp_suffix}.wav"
    else:
        wav_name = None
    tmp_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    tmp_wav.close()
    try:
        cmd = ["ffmpeg", "-y", "-i", input_path, "-ac", "1", "-ar", "16000", "-vn", tmp_wav.name]
        if debug:
            print(f"__ Running ffmpeg conversion: {' '.join(cmd)}")
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if debug:
            # report size of converted WAV
            try:
                size = os.path.getsize(tmp_wav.name)
                n = float(size)
                for unit in ('B','KiB','MiB','GiB'):
                    if n < 1024.0:
                        hr = f"{n:.2f}{unit}"
                        break
                    n /= 1024.0
                else:
                    hr = f"{n:.2f}TiB"
                print(f"____ Converted WAV size: {hr}")
            except Exception:
                pass
        if debug:
            # Confirm Whisper parameters and environment
            ver = getattr(whisper, "__version__", None)
            print(f"__ whisper version: {ver}, model_name={model_name!r}, device={DEVICE!r}")
            try:
                import torch
                print(
                    f"__ torch.cuda.is_available(): {torch.cuda.is_available()}, "
                    f"torch.cuda.device_count(): {torch.cuda.device_count()}"
                )
            except ImportError:
                pass
        if debug: print(f"__ Loading model '{model_name}' for transcription")
        model = load_model(model_name)
        if debug: print(f"____ Model loaded.")
        if debug:
            try:
                print(f"__ Getting model parms")
                dev = next(model.parameters()).device
                print(f"__ Loaded Whisper model parameters on device: {dev}")
            except Exception:
                print("** Failed to get model parameters, using default device")
                pass
        print(f".. Starting transcription of {tmp_wav.name}")
        result = model.transcribe(tmp_wav.name)
        # result = model.transcribe(tmp_wav.name, verbose=debug)
        if debug: print(f"____ Transcription result length: {len(result)}")
    finally:
        if debug:
            print(f"__ Transcription complete")
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
        # save SRT for debugging with timestamp suffix using global timestamp
        srt_file = Path.cwd() / f"{stem}{timestamp_suffix}.srt"
        srt_file.write_text(srt_text, encoding='utf-8')
        if debug:
            print(f"__ Saved intermediate SRT to {srt_file}")
    return srt_text
