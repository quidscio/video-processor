"""
cli.py

Command-line interface for video-processor.
"""
import click

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
def main(
    source: str,
    youtube: bool,
    whisper_model: str,
    llm_model: str,
    temperature: float,
    debug: bool,
):
    """
    Transcribe and summarize a video/audio SOURCE (file path or YouTube URL) in Markdown.
    """
    if youtube:
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

    timestamped = srt_to_timestamped_lines(srt_text)
    template = load_template("transcribe.tpl")
    prompt = template.replace("{{ transcript }}", timestamped)
    md = chat(prompt, model=llm_model, temperature=temperature)
    click.echo(md)


if __name__ == "__main__":
    main()