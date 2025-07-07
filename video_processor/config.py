"""
Configuration for video_processor package.
"""
import os
from pathlib import Path

# Load any per-project .env (for secrets like API keys)
try:
    from dotenv import load_dotenv, find_dotenv

    _dotenv_path = find_dotenv(usecwd=True)
    if _dotenv_path:
        load_dotenv(_dotenv_path, override=False)
except ImportError:
    pass

# Parse optional project-local config.toml (for defaults)
try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

_cfg = {}
_cfg_path = Path.cwd() / "config.toml"
if _cfg_path.exists():
    with open(_cfg_path, "rb") as f:
        _cfg = tomllib.load(f)

# LLM backend (ollama or anthropic)
BACKEND = os.getenv("LLM_BACKEND", _cfg.get("backend", "ollama")).lower()

# Ollama server URL (default http://localhost:11434)
_raw = os.getenv("OLLAMA_URL", _cfg.get("ollama_host", "localhost:11434"))
if not _raw.startswith(("http://", "https://")):
    hostport = _raw
    if ":" not in hostport:
        hostport = f"{hostport}:11434"
    _raw = "http://" + hostport
OLLAMA_URL = _raw

# Whisper defaults
WHISPER_MODEL = os.getenv("WHISPER_MODEL", _cfg.get("whisper_model", "base"))
# Device for Whisper (e.g. 'cuda' or 'cpu')
DEVICE = os.getenv("DEVICE", _cfg.get("device", "cuda"))