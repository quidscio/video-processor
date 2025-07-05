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

- If you set a custom Ollama host via `OLLAMA_URL`, you can omit the scheme
  and/or port (11434 is the default):
```bash
export OLLAMA_URL=192.168.1.68
# → http://192.168.1.68:11434

export OLLAMA_URL=http://192.168.1.68:11434
# → same effect
```

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

### If install fails under PEP‑668 environments

Some systems (e.g. Debian/Ubuntu PEP‑668) prevent `pip install .` in the current Python interpreter.
In that case, you can run directly from the source tree without installing the package,
but you need to install the dependencies manually:
```bash
pip install openai-whisper srt click requests anthropic yt-dlp
python3 -m video_processor.cli [OPTIONS] SOURCE
```

## Ollama setup

Make sure your Ollama server is running and that you have pulled your desired model (e.g. claude-opus-4):
```bash
ollama pull claude-opus-4
ollama serve --listen 0.0.0.0:11434
```

## Anthropic setup

To use Anthropic Cloud, first install the Anthropic SDK and set your API key (get your key at https://console.anthropic.com):
```bash
pip install anthropic>=3.0.0
export ANTHROPIC_API_KEY="<your_anthropic_api_key>"
```
You must set `LLM_BACKEND=anthropic` to use Anthropic Cloud; `ANTHROPIC_API_KEY` is also required.

This CLI will automatically fallback to the new Anthropic Messages API for models that no longer support the legacy Completions endpoint.
```bash
video-processor [OPTIONS] SOURCE
```