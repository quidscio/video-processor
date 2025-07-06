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
        # Creator-provided subtitles
        cmd = [
            "yt-dlp", "-q", "--no-warnings",
            "--write-sub", "--skip-download",
            "--sub-lang", "en", "--convert-subs", "srt",
            "-o", base_output,
            url,
        ]
        if debug:
            print(f"__ Running creator subtitles extraction: {' '.join(cmd)}", file=sys.stderr)
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # If none, fallback to auto-generated subtitles
        found = any(f.lower().endswith('.srt') for f in os.listdir(output_dir))
        if not found:
            print("____ There aren't any subtitles to convert", file=sys.stderr)
            cmd_auto = [
                "yt-dlp", "-q", "--no-warnings",
                "--write-auto-sub", "--skip-download",
                "--sub-lang", "en", "--convert-subs", "srt",
                "-o", base_output,
                url,
            ]
            print(f"__ Running auto subtitles extraction: {' '.join(cmd_auto)}", file=sys.stderr)
            subprocess.run(cmd_auto, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            # Note where file is written (VTT -> SRT conversion)
            for fname in os.listdir(output_dir):
                if fname.lower().endswith('.srt'):
                    path = os.path.join(output_dir, fname)
                    print(f"____ Writing subtitles to file {path}", file=sys.stderr)
                    break

        # Read SRT content and report size
        for fname in os.listdir(output_dir):
            if fname.lower().endswith('.srt'):
                path = os.path.join(output_dir, fname)
                size = os.path.getsize(path)
                # human-readable size
                n = float(size)
                for unit in ('B','KiB','MiB','GiB'):
                    if n < 1024.0:
                        hr = f"{n:.2f}{unit}"
                        break
                    n /= 1024.0
                else:
                    hr = f"{n:.2f}TiB"
                print(f".. Received subtitles ({hr})", file=sys.stderr)
                with open(path, encoding='utf-8') as f:
                    return f.read()
        raise RuntimeError(
            f"No SRT file found in {output_dir}: yt-dlp did not produce any .srt."
        )
    finally:
        shutil.rmtree(output_dir, ignore_errors=True)