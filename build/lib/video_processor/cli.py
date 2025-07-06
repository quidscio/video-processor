"""
cli.py

Command-line interface for video-processor.
"""
import click
import os
import subprocess
import re
from .config import WHISPER_MODEL


@click.command()
@click.argument("source", type=str)
@click.option(
    "-y", "--youtube", is_flag=True,
    help="Treat SOURCE as a YouTube URL and download captions via yt-dlp."
)
@click.option(
    "-d", "--debug",
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
    "-b", "--backend",
    type=click.Choice(['ollama', 'anthropic']),
    help="One-off override for LLM backend (ollama or anthropic)."
)
@click.option(
    "-o", "--output",
    default=None, metavar="FILE",
    help="Write summarization to FILE; use -o= to auto-generate from video title (no spaces)."
)
def main(
    source: str,
    youtube: bool,
    whisper_model: str,
    llm_model: str,
    temperature: float,
    backend: str,
    output: str,
    debug: bool,
):
    """
    Transcribe and summarize a video/audio SOURCE (file path or YouTube URL) in Markdown.
    """
    # Program start banner
    try:
        from importlib.metadata import version
        ver = version("video-processor")
    except Exception:
        ver = "dev"
    click.echo(f"== Video Processor {ver} ==")

    if youtube:
        click.echo(f".. Seeking subtitles for {source}")
        from .downloader import download_srt
        try:
            srt_text = download_srt(source, debug=debug)
        except RuntimeError as err:
            raise click.ClickException(str(err))
    else:
        from .converter import transcribe_to_srt

        srt_text = transcribe_to_srt(source, whisper_model)

    from .srt_parser import srt_to_timestamped_lines
    from .llm_client import load_template, chat
    from .config import BACKEND as CONFIG_BACKEND

    # Determine which backend to use (CLI flag overrides project config)
    if backend:
        os.environ['LLM_BACKEND'] = backend
        backend_used = backend
    else:
        backend_used = CONFIG_BACKEND

    timestamped = srt_to_timestamped_lines(srt_text)
    template = load_template("transcribe.tpl")
    prompt = template.replace("{{ transcript }}", timestamped)
    try:
        click.echo(f".. Sending prompt to LLM backend ({backend_used}), model={llm_model}, temp={temperature}")
        md = chat(prompt, model=llm_model, temperature=temperature)
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
            filename = slug + ".md"
        else:
            filename = output
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


if __name__ == "__main__":
    main()