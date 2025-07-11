"""
Configuration for video_processor package.
"""
import os
from pathlib import Path

# Load any per-project .env (for secrets like API keys)
try:
    from dotenv import load_dotenv, find_dotenv

    # First search relative to this file (project tree)
    _dotenv_path = find_dotenv()

    # Then search from the current working directory
    if not _dotenv_path:
        _dotenv_path = find_dotenv(usecwd=True)

    # Finally check ~/.env as a fallback
    if not _dotenv_path:
        home_env = Path.home() / ".env"
        if home_env.exists():
            _dotenv_path = str(home_env)

    if _dotenv_path:
        load_dotenv(_dotenv_path, override=False)
except ImportError:
    pass

# Parse optional project-local config.toml (for defaults)
try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

# Configuration precedence: user-wide (~/.config/video-processor/config.toml), then project-local (./config.toml)
_cfg = {}
# User-wide config via XDG_CONFIG_HOME or fallback to ~/.config
_xdg = Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config"))
_user_cfg = _xdg / "video-processor" / "config.toml"
if _user_cfg.exists():
    with open(_user_cfg, "rb") as f:
        _cfg = tomllib.load(f)

# Project-local config overrides user-wide settings
_cfg_path = Path.cwd() / "config.toml"
if _cfg_path.exists():
    with open(_cfg_path, "rb") as f:
        proj = tomllib.load(f)
        _cfg.update(proj)

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

# LLM model name
MODEL = os.getenv("LLM_MODEL", _cfg.get("model", "claude-opus-4"))
# Token limit for LLM
TOKEN_LIMIT = int(os.getenv("TOKEN_LIMIT", _cfg.get("token_limit", 10000)))