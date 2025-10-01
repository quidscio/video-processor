# video-processor

Command-line tool to transcribe and summarize video or audio files using Whisper and Claude Opus  4. Best used under Linux/WSL. 

See `readme_rmh.md` for full specifications and design.

## Installation

```bash
# Recommended: use a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install latest release from PyPI
pip install video-processor

# (or, install from this source tree for development / upgrade to latest local changes)
pip install -U .
```

## Prerequisites

- `yt-dlp` must be installed and on your PATH if you plan to use `--youtube`.
  ```bash
  pip install yt-dlp
  ```

  Note: As of Debian 12, the package version is years out of date. So symlink to the dev venv
  ```bash
  ln -s /mnt/c/q/arc/projects/video-processor/.venv/bin/yt-dlp /home/user/bin/yt-dlp
  ```

  To upgrade `yt-dlp`: 
  ```bash 
source .venv/bin/activate
python -m pip install --upgrade yt-dlp
```


- `ffmpeg` must be installed and on your PATH for Whisper transcription to decode the full audio track.
  ```bash
  # Debian/Ubuntu
  apt install ffmpeg
  ```

## Usage

### First Time 

#### Bootstrapping a default config file

Rather than manually editing both project-local and user configs, the CLI can do it all in one step:

```bash
# Copy the internal template (if needed) into ./config.toml
# then symlink it into ~/.config/video-processor/config.toml
video-processor --init-config
``` 

#### Symlink the CLI into ~/bin

Once the CLI is installed or available on your current PATH, you can install its entrypoint into
`~/bin` with one command (no venv activation required thereafter):

```bash
video-processor --symlink-cli
```

> **Tip:** if you ever need to customize or relocate the link yourself:
>
> ```bash
> mkdir -p ~/.config/video-processor
> ln -sf "$(pwd)/config.toml" ~/.config/video-processor/config.toml
> ```

### Favorite Backends and Models 

```bash
# Download YouTube, transcribe, and summarize locally
video-processor -o= -w medium -b ollama -l deepseek-r1:7b  -y https://www.youtube.com/watch?v=BaETCQTnr8k

# Same but use Anthropic for Summarization 
video-processor -o= -w medium -b anthropic -l claude-opus-4-20250514     -y https://www.youtube.com/watch?v=BaETCQTnr8k
video-processor -o= -w medium -b anthropic -l claude-sonnet-4-20250514   -y https://www.youtube.com/watch?v=BaETCQTnr8k

# Transcribe a local media file:
video-processor my_video.mp4

# Download captions from YouTube and process:
video-processor --youtube https://youtu.be/VIDEO_ID

# Enable debug logging for downloader and LLM interactions:
video-processor --youtube --debug https://youtu.be/VIDEO_ID

# See full option list:
video-processor --help

```
### Developing Hints 
```bash
# All in project folder 
cd project_folder 

# build 
pip install -U .          # Install to be used from anywhere by user freezing production version vs edits 
pip install -e .          # Install to be executed from dev area allowing ongoing edits 

# execute modules directly (alternative to `pip install -e`)
python3 -m video_processor.cli --help
```

# Examples of writing output to file:
```bash
# default filename (uses video title, no spaces): use `-o=` or `-o =` (equals/magic token)
video-processor -o= -y https://youtu.be/VIDEO_ID
# custom filename
video-processor -o my_summary.md  -y https://youtu.be/VIDEO_ID
```
# One-off backend/host override (does not require editing config.toml):
```bash
# override LLM backend
video-processor --backend anthropic | ollama [OTHER_OPTIONS] SOURCE
# override Ollama host
video-processor --ollama-host 192.168.1.68:11434 [OTHER_OPTIONS] SOURCE

```

### If install fails under PEP   668 environments

Some systems (e.g. Debian/Ubuntu PEP   668) prevent `pip install .` in the current Python interpreter.
In that case, you can run directly from the source tree without installing the package,
but you need to install the dependencies manually:
```bash
# Install dependencies manually when `pip install .` is blocked by PEP   668
pip install openai-whisper srt click requests anthropic python-dotenv tomli yt-dlp
python3 -m video_processor.cli [OPTIONS] SOURCE
```

## Ollama setup

Make sure your Ollama server is running and that you have pulled your desired model:

```bash
ollama pull MODEL
ollama serve --listen 0.0.0.0:11434
```

## WSL2 GPU Setup (for Whisper GPU acceleration)

To let Whisper load models on your Windows GPU under WSL2, install NVIDIA's WSL2 CUDA driver on Windows and a matching CUDA-enabled PyTorch wheel in WSL:

**On Windows (PowerShell as Administrator):**
```powershell
wsl --update
wsl --shutdown
# Install NVIDIA CUDA on WSL driver from https://developer.nvidia.com/cuda/wsl
```

**In WSL (inside your virtualenv):**
```bash
pip install --upgrade \
  torch torchvision torchaudio \
  --index-url https://download.pytorch.org/whl/cu121
python3 - << 'EOF'
import torch
print('CUDA available:', torch.cuda.is_available(), 'CUDA version:', torch.version.cuda)
EOF
```
## WSL Access to Ollama on Windows 

```powershell 
New-NetFirewallRule -DisplayName "Allow Ollama on port 11434" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 11434
Set-NetFirewallRule -DisplayName "Allow Ollama on port 11434" -EdgeTraversalPolicy Allow
```

## Anthropic setup

To use Anthropic Cloud, first install the Anthropic SDK:
```bash
pip install anthropic>=0.3.0
```
Create a `.env` file in your project root with your API key. The CLI
first searches this project tree, then the directory you run from, and
finally falls back to `~/.env` if no project file is found:
```ini
ANTHROPIC_API_KEY=<your_anthropic_api_key_here>
```
You must set `LLM_BACKEND=anthropic` (via CLI flag or project config) to use Anthropic Cloud.

This CLI will automatically fallback to the new Anthropic Messages API for models that no longer support the legacy Completions endpoint.
```bash
video-processor [OPTIONS] SOURCE
```

## Configuration

You can specify defaults in a user-wide or project-local `config.toml`. Values in the project-local file override the user-wide settings unless you utilized the symlink option. Then, they are identical. 

### User-wide configuration

There is a CLI option to symlink a `config.toml` under your XDG config directory (default `~/.config/video-processor/config.toml`):

```toml
# Default LLM backend: "ollama" or "anthropic"
backend     = "ollama"
# Ollama server host (host[:port], defaults to port 11434)
ollama_host = "192.168.1.68"

# Whisper defaults:
whisper_model = "medium"    # or base or small 
device        = "cuda"      # or "cpu"
```

### Project-local configuration

Create `config.toml` in your project root to override the user-wide settings:

```toml
# Per-project overrides (same syntax as above)
backend     = "anthropic"
ollama_host = "localhost:11434"
```

# Known Issues
1. Specifying a new whisper model causes HuggingFace download on first run...ready delay. Afterwards, it loads from a cache.  