"""
cli.py

Command-line interface for video-processor.
"""
import click
import os
import sys
import subprocess
import re
import shutil
import time
import glob
from pathlib import Path
from datetime import datetime
import importlib.resources as pkg_resources
from .config import WHISPER_MODEL

# Package version for --version flag
try:
    from importlib.metadata import version, PackageNotFoundError
    _pkg_version = version("video-processor")
except Exception:
    _pkg_version = "dev"

# Global timestamp for consistent naming across all artifacts
_global_timestamp = None

def get_global_timestamp() -> str:
    """Get the global timestamp for this execution (set once at start)"""
    global _global_timestamp
    if _global_timestamp is None:
        _global_timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return _global_timestamp

def generate_timestamp_suffix(backend: str, model: str) -> str:
    """Generate timestamp suffix using global timestamp: _backend_model_yyyymmdd-hhmmss"""
    timestamp = get_global_timestamp()
    return f"_{backend}_{model}_{timestamp}"

# Custom command class to include version header in help output
class VersionedHelpCommand(click.Command):
    def format_help(self, ctx, formatter):
        formatter.write_text(f"{ctx.info_name} {_pkg_version}")
        formatter.write_text("")
        super().format_help(ctx, formatter)
        # Example invocations
        formatter.write_text("")
        formatter.write_text("Examples:")
        formatter.write_text(
            "  video-processor -o= -w medium -b ollama -l deepseek-r1:7b -d -y https://www.youtube.com/watch?v=VIDEO"
        )
        formatter.write_text(
            "  video-processor -o= -w medium -b anthropic -l claude-opus-4-20250514 -d -y https://www.youtube.com/watch?v=VIDEO"
        )


@click.command(cls=VersionedHelpCommand)
@click.version_option(_pkg_version, "--version", "-V", prog_name="video-processor", message="%(prog)s %(version)s")
@click.argument("source", type=str, required=False)
@click.option(
    "-y", "--youtube", is_flag=True,
    help="Treat SOURCE as a YouTube URL and download captions via yt-dlp."
)
@click.option(
    "-d", "--download-video", is_flag=True,
    help="Also download the full YouTube video via yt-dlp."
)
@click.option(
    "-D", "--debug",
    is_flag=True,
    help="Show debug output (commands and yt-dlp logs) when downloading captions."
)
@click.option(
    "-w", "--whisper-model",
    default=WHISPER_MODEL, show_default=True,
    help="Whisper model to use for transcription."
)
@click.option(
    "-l", "--llm-model",
    default="claude-opus-4", show_default=True,
    help="LLM model to use for summarization via Ollama."
)
@click.option(
    "-t", "--temperature",
    default=0.0, show_default=True,
    help="Temperature for LLM chat completion."
)
@click.option(
    "--token-limit",
    default=10000, show_default=True, type=int,
    help="Maximum OUTPUT tokens for LLM response generation."
)
@click.option(
    "-b", "--backend",
    type=click.Choice(['ollama', 'anthropic']),
    help="One-off override for LLM backend (ollama or anthropic)."
)
@click.option(
    "--ollama-host",
    default=None, metavar="HOST[:PORT]",
    help="One-off override for Ollama server host (overrides config file and env)."
)
@click.option(
    "--init-config",
    is_flag=True,
    help="Bootstrap project-local config.toml (copy template if missing) and symlink it into XDG config area, then exit."
)
@click.option(
    "--symlink-cli",
    is_flag=True,
    help="Symlink the installed video-processor entrypoint into $HOME/bin and exit."
)
@click.option(
    "-o", "--output",
    default=None, metavar="FILE",
    help="Write summarization to FILE; use -o= to auto-generate from video title (no spaces)."
)
def main(
    youtube: bool,
    download_video: bool,
    whisper_model: str,
    llm_model: str,
    temperature: float,
    token_limit: int,
    backend: str,
    ollama_host: str,
    init_config: bool,
    symlink_cli: bool,
    output: str,
    debug: bool,
    source: str = None,
):
    """
    Transcribe and summarize a video/audio SOURCE (file path or YouTube URL) in Markdown.
    """
    # Program start banner with timestamp
    try:
        from importlib.metadata import version
        ver = version("video-processor")
    except Exception:
        ver = "dev"
    timestamp = get_global_timestamp()
    click.echo(f"== Video Processor {ver} {timestamp} ==")

    # Bootstrap project-local config and symlink into user XDG config area
    if init_config:
        local_cfg = Path.cwd() / 'config.toml'
        if not local_cfg.exists():
            data = pkg_resources.read_text('video_processor', 'config_template.toml')
            local_cfg.write_text(data, encoding='utf-8')
            click.echo(f"Copied template to {local_cfg}")
        else:
            click.echo(f"Local config already exists at {local_cfg}, skipping template copy")

        xdg_dir = Path(os.getenv('XDG_CONFIG_HOME', Path.home() / '.config')) / 'video-processor'
        xdg_file = xdg_dir / 'config.toml'
        xdg_dir.mkdir(parents=True, exist_ok=True)
        if xdg_file.exists() or xdg_file.is_symlink():
            xdg_file.unlink()
        os.symlink(local_cfg, xdg_file)
        click.echo(f"Symlinked {xdg_file} → {local_cfg}")
        return

    # Symlink the CLI entrypoint into ~/bin and exit
    if symlink_cli:
        # Locate the installed script
        script = shutil.which("video-processor")
        if not script:
            raise click.ClickException(
                "Cannot find 'video-processor' executable in PATH; is it installed?"
            )
        dest_dir = Path.home() / 'bin'
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / 'video-processor'
        if dest.exists() or dest.is_symlink():
            dest.unlink()
        os.symlink(script, dest)
        click.echo(f"Symlinked {script} → {dest}")
        return

    # SOURCE argument becomes required for normal operation
    if source is None:
        raise click.UsageError("Missing argument 'SOURCE'.")

    # Determine which backend to use (CLI flag overrides project config)
    from .config import BACKEND as CONFIG_BACKEND
    if backend:
        os.environ['LLM_BACKEND'] = backend
        backend_used = backend
    else:
        backend_used = CONFIG_BACKEND

    if youtube:
        click.echo(f".. Seeking subtitles for {source}")
        if download_video:
            click.echo(f".. Downloading full video for {source}")
            # sanitize title for output basename (slugify like for SRT)
            try:
                title = subprocess.run(
                    ["yt-dlp", "--get-title", "-q", source],
                    check=True, capture_output=True, text=True
                ).stdout.strip()
            except Exception:
                title = None
            if title:
                slug = re.sub(r"[^\w\s-]", "", title).strip()
                slug = re.sub(r"[\s_-]+", "-", slug)
                # Add timestamp suffix to video files
                timestamp_suffix = generate_timestamp_suffix(backend_used, llm_model)
                out_template = f"{slug}{timestamp_suffix}.%(ext)s"
            else:
                # Add timestamp suffix to video files
                timestamp_suffix = generate_timestamp_suffix(backend_used, llm_model)
                out_template = f"%(id)s{timestamp_suffix}.%(ext)s"
            cmd_vid = ["yt-dlp"]
            if not debug:
                cmd_vid += ["-q", "--no-warnings"]
            # Select best single file format (highest resolution) - use "b" to suppress warning
            cmd_vid += ["-f", "b", "-o", out_template, source]
            if debug:
                click.echo(f"__ Running video download: {' '.join(cmd_vid)}", err=True)
            try:
                subprocess.run(cmd_vid, check=True)
                # Update video file modification time to current time for proper sorting
                # Find the downloaded video file(s) that match our pattern
                if title:
                    base_pattern = f"{slug}{timestamp_suffix}.*"
                else:
                    # Get video ID for fallback pattern
                    try:
                        video_id = subprocess.run(
                            ["yt-dlp", "--get-id", "-q", source],
                            check=True, capture_output=True, text=True
                        ).stdout.strip()
                        base_pattern = f"{video_id}{timestamp_suffix}.*"
                    except Exception:
                        base_pattern = f"*{timestamp_suffix}.*"
                
                # Find and update modification time of downloaded video files
                current_time = time.time()
                for video_file in glob.glob(base_pattern):
                    if os.path.isfile(video_file):
                        os.utime(video_file, (current_time, current_time))
                        if debug:
                            click.echo(f"__ Updated modification time for {video_file}", err=True)
            except Exception as e:
                raise click.ClickException(f"Error downloading video: {e}")
        from .downloader import download_srt
        try:
            srt_text = download_srt(source, debug=debug, backend=backend_used, model=llm_model)
        except RuntimeError as err:
            raise click.ClickException(str(err))
    else:
        from .converter import transcribe_to_srt

        srt_text = transcribe_to_srt(source, whisper_model, debug=debug, backend=backend_used, model=llm_model)

    from .srt_parser import srt_to_timestamped_lines
    from .llm_client import load_template, chat

    # CLI override for Ollama host: normalize and override config/env and llm_client
    if ollama_host:
        _raw = ollama_host
        if not _raw.startswith(("http://", "https://")):
            _hp = _raw
            if ":" not in _hp:
                _hp = f"{_hp}:11434"
            _raw = "http://" + _hp
        os.environ["OLLAMA_URL"] = _raw
        from . import llm_client as _lc
        _lc.OLLAMA_URL = _raw
        click.echo(f".. Overriding Ollama URL to {_raw}")

    timestamped = srt_to_timestamped_lines(srt_text)
    template = load_template("transcribe.tpl")
    prompt = template.replace("{{ transcript }}", timestamped)
    # Track if any errors occurred during processing
    has_errors = False
    
    try:
        click.echo(f".. Sending prompt to LLM backend ({backend_used}), model={llm_model}, temp={temperature}, max_tokens={token_limit}")
        md, was_truncated = chat(prompt, model=llm_model, temperature=temperature, debug=debug, max_tokens=token_limit)
        if was_truncated:
            has_errors = True
        click.echo(f".. Received result from LLM (length={len(md)} chars)")
    except Exception as e:
        # Provide a clearer error if the Ollama server returns HTTP errors or is unreachable
        import requests

        if isinstance(e, requests.exceptions.HTTPError):
            resp = e.response
            # Attempt to parse structured Ollama error JSON
            try:
                body = resp.json()
                info = body.get('error', {})
                err_msg = info.get('message', '').strip()
            except Exception:
                body = resp.text
                info = {}
                err_msg = str(body).strip()
            # Debug output for LLM HTTP errors
            if debug:
                click.echo(f"[debug] LLM error response [{resp.status_code}]: {body}", err=True)
            # Detect missing-model error (legacy and new formats)
            if info.get('type') == 'not_found_error' or ('model' in err_msg and 'not found' in err_msg):
                model_name = llm_model
                if backend == 'anthropic':
                    raise click.ClickException(
                        f"Model '{model_name}' not found on Anthropic Cloud."
                        " Please use a valid Anthropic model name, e.g. claude-2, claude-2.1, claude-2-instant, or claude-3."
                    )
                raise click.ClickException(
                    f"Model '{model_name}' not found on Ollama server."
                    f"\nPlease pull it first: `ollama pull {model_name}`"
                )
            msg = f"HTTP {resp.status_code} {resp.reason}: {err_msg}"
        else:
            msg = str(e)
        # Special-case missing Anthropic SDK or API key
        if 'Anthropic SDK is not installed' in msg:
            raise click.ClickException(
                "Anthropic SDK is not installed; please install with:\n"
                "  pip install anthropic>=0.3.0"
            )
        if 'ANTHROPIC_API_KEY is not set' in msg:
            raise click.ClickException(
                "ANTHROPIC_API_KEY is not set; please export your Anthropic API key, e.g.:\n"
                "  export ANTHROPIC_API_KEY=your_api_key_here"
            )
        raise click.ClickException(
            f"Error during chat completion: {msg}\n"
            "Ensure your LLM backend is configured correctly (check LLM_BACKEND, OLLAMA_URL, ANTHROPIC_API_KEY)."
        )
    # Handle output: write to file if requested, else print to stdout
    if output is not None:
        # Determine filename: empty or '=' means auto-generate
        if output in ("", "="):
            try:
                title = subprocess.run(
                    ["yt-dlp", "--get-title", "-q", source],
                    check=True, capture_output=True, text=True
                ).stdout.strip()
            except Exception:
                title = os.path.splitext(os.path.basename(source))[0]
            slug = re.sub(r"[^\w\s-]", "", title).strip()
            slug = re.sub(r"[\s_-]+", "-", slug)
            # Add timestamp suffix to MD files
            timestamp_suffix = generate_timestamp_suffix(backend_used, llm_model)
            filename = slug + timestamp_suffix + ".md"
        else:
            # Add timestamp suffix to custom output filename
            base_name = os.path.splitext(output)[0]
            ext = os.path.splitext(output)[1] or ".md"
            timestamp_suffix = generate_timestamp_suffix(backend_used, llm_model)
            filename = base_name + timestamp_suffix + ext
        # Write summary to file, warning if overwriting
        existed = os.path.exists(filename)
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(md)
        if existed:
            click.echo(f".. Summarization overwritten to {filename}")
        else:
            click.echo(f".. Summarization written to {filename}")
    else:
        click.echo(md)
    
    # Exit with non-zero code if any errors occurred during processing
    if has_errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
