# video-processor

Command-line tool to transcribe and summarize video or audio files using Whisper and Claude Opus 4.

See `readme_rmh.md` for full specifications and design.

## Installation

```bash
# Recommended: use a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install this package
pip install .
```

## Prerequisites


- `yt-dlp` must be installed and on your PATH if you plan to use `--youtube`.
  ```bash
  pip install yt-dlp
  ```
(or: `apt install yt-dlp` / download the binary from https://github.com/yt-dlp/yt-dlp)


## Usage

```bash
# Transcribe a local media file:
video-processor my_video.mp4

# Download captions from YouTube and process:
video-processor --youtube https://youtu.be/VIDEO_ID

# Enable debug logging for downloader and LLM interactions:
video-processor --youtube --debug https://youtu.be/VIDEO_ID

# See full option list:
video-processor --help

# Development mode (run directly from source, no install):

python3 -m video_processor.cli --help
```

# One-off backend override (does not require editing config.toml):
```bash
video-processor --backend anthropic [OTHER_OPTIONS] SOURCE
```

### If install fails under PEP‑668 environments

Some systems (e.g. Debian/Ubuntu PEP‑668) prevent `pip install .` in the current Python interpreter.
In that case, you can run directly from the source tree without installing the package,
but you need to install the dependencies manually:
```bash
# Install dependencies manually when `pip install .` is blocked by PEP‑668
pip install openai-whisper srt click requests anthropic python-dotenv tomli yt-dlp
python3 -m video_processor.cli [OPTIONS] SOURCE
```

## Ollama setup

Make sure your Ollama server is running and that you have pulled your desired model (e.g. claude-opus-4):
```bash
ollama pull claude-opus-4
ollama serve --listen 0.0.0.0:11434
```

## Anthropic setup

To use Anthropic Cloud, first install the Anthropic SDK:
```bash
pip install anthropic>=0.3.0
```
Then create a `.env` file in your project root with your API key:
```ini
ANTHROPIC_API_KEY=<your_anthropic_api_key_here>
```
You must set `LLM_BACKEND=anthropic` (via CLI flag or project config) to use Anthropic Cloud.

This CLI will automatically fallback to the new Anthropic Messages API for models that no longer support the legacy Completions endpoint.
```bash
video-processor [OPTIONS] SOURCE
```

## Project-local configuration

You can set per-project defaults by creating `config.toml` in your project root:

```toml
# Default LLM backend: "ollama" or "anthropic"
backend = "ollama"

# Host (and optional port) for your Ollama server.
# If you omit scheme/port, code assumes http://<host>:11434
ollama_host = "localhost:11434"

# Whisper defaults:
whisper_model = "base"
device = "cuda"
```

Settings in `config.toml` are loaded automatically when you run `video-processor`.