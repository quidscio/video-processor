"""
downloader.py

Download YouTube captions as SRT using yt-dlp.
"""
import os
import sys
import tempfile
import subprocess
import shutil

def download_srt(url: str, debug: bool = False) -> str:
    """
    Download English subtitles for a YouTube URL, preferring creator-provided subs and
    falling back to auto-generated. Returns the SRT content as a string.
    """
    # Ensure yt-dlp is available
    if shutil.which("yt-dlp") is None:
        raise RuntimeError(
            "yt-dlp executable not found in PATH; please install yt-dlp "
            "(e.g. `pip install yt-dlp`) before using --youtube."
        )
    # Create temporary output directory (auto-cleaned below)
    output_dir = tempfile.mkdtemp(prefix="vpdl-")
    base_output = os.path.join(output_dir, "%(id)s.%(ext)s")
    try:
        # Try creator-provided subtitles first
        cmd = [
            "yt-dlp",
            "--write-sub",
            "--skip-download",
            "--sub-lang", "en",
            "--convert-subs", "srt",
            "-o", base_output,
            url,
        ]
        if debug:
            print(f"[debug] running creator-sub cmd: {' '.join(cmd)}", file=sys.stderr)
        stdout = None if debug else subprocess.DEVNULL
        stderr = None if debug else subprocess.DEVNULL
        try:
            subprocess.run(cmd, check=True, stdout=stdout, stderr=stderr)
        except subprocess.CalledProcessError as e:
            if debug:
                print(f"[debug] creator-sub cmd failed (exit code {e.returncode})", file=sys.stderr)

        # If no SRT produced, try auto-generated subtitles
        found = any(f.lower().endswith('.srt') for f in os.listdir(output_dir))
        if not found:
            cmd_auto = [
                "yt-dlp",
                "--write-auto-sub",
                "--skip-download",
                "--sub-lang", "en",
                "--convert-subs", "srt",
                "-o", base_output,
                url,
            ]
            if debug:
                print(f"[debug] running auto-sub cmd: {' '.join(cmd_auto)}", file=sys.stderr)
            try:
                subprocess.run(cmd_auto, check=True, stdout=stdout, stderr=stderr)
            except subprocess.CalledProcessError as e:
                if debug:
                    print(f"[debug] auto-sub cmd failed (exit code {e.returncode})", file=sys.stderr)

        # Locate downloaded SRT file
        for fname in os.listdir(output_dir):
            if fname.lower().endswith('.srt'):
                path = os.path.join(output_dir, fname)
                with open(path, encoding='utf-8') as f:
                    return f.read()
        raise RuntimeError(
            f"No SRT file found in {output_dir}: yt-dlp did not produce any .srt file.\n"
            "Please ensure captions exist, or drop -y to use Whisper transcription instead."
        )
    finally:
        # Remove temporary directory and all contents
        shutil.rmtree(output_dir, ignore_errors=True)