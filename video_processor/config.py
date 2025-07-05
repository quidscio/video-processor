"""
Configuration for video_processor package.
"""
import os

# Whisper model configuration
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")
# Device for Whisper (e.g. 'cuda' or 'cpu')
DEVICE = os.getenv("DEVICE", "cuda")

# Ollama server URL for Claude Opus 4 (if used later)
# Default Ollama URL for Claude Opus 4 (if used later).
# - Default: localhost:11434
# - If OLLAMA_URL has no scheme, assume http://
# - If OLLAMA_URL has no port, default to :11434
_raw_ollama = os.getenv("OLLAMA_URL", "localhost:11434")
if not _raw_ollama.startswith(("http://", "https://")):
    # Ensure host:port is present
    hostport = _raw_ollama
    if ":" not in hostport:
        hostport = f"{hostport}:11434"
    _raw_ollama = "http://" + hostport
OLLAMA_URL = _raw_ollama