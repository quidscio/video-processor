"""
Configuration for video_processor package.
"""
import os

# Whisper model configuration
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")
# Device for Whisper (e.g. 'cuda' or 'cpu')
DEVICE = os.getenv("DEVICE", "cuda")

# Ollama server URL for Claude Opus 4 (if used later)
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")