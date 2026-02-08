"""
downloader.py

Download YouTube captions as SRT using yt-dlp.
"""
import os
import sys
import tempfile
import subprocess
import shutil
import re
from pathlib import Path
from datetime import datetime

def download_srt(url: str, debug: bool = False, backend: str = 'default', model: str = 'default') -> str:
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
    
    # Get video info for proper filename formatting
    video_id = None
    video_title = None
    try:
        # Get video ID - don't use check=True since yt-dlp may have warnings
        id_result = subprocess.run(
            ["yt-dlp", "--get-id", "-q", url],
            capture_output=True, text=True
        )
        # Check if we got a video ID, regardless of return code (yt-dlp may return non-zero with warnings)
        if id_result.stdout.strip():
            video_id = id_result.stdout.strip()
        
        # Get video title - don't use check=True since yt-dlp may have warnings  
        title_result = subprocess.run(
            ["yt-dlp", "--get-title", "-q", url],
            capture_output=True, text=True
        )
        # Check if we got a title, regardless of return code (yt-dlp may return non-zero with warnings)
        if title_result.stdout.strip():
            video_title = title_result.stdout.strip()
    except Exception:
        pass
    
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
            # Create executable command with variable substitution
            exec_cmd = cmd.copy()
            if video_id:
                for i, arg in enumerate(exec_cmd):
                    if arg == base_output:
                        exec_cmd[i] = os.path.join(output_dir, f"{video_id}.srt")
            print(f"__ Running creator subtitles extraction: {' '.join(exec_cmd)}", file=sys.stderr)
        
        # Try creator subtitles first, but don't fail if they don't exist
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError:
            # Creator subtitles not available, will try auto-generated next
            if debug:
                print("__ Creator subtitles not available", file=sys.stderr)

        # If none, fallback to auto-generated subtitles
        found = any(f.lower().endswith('.srt') for f in os.listdir(output_dir))
        if not found:
            if debug:
                print("____ There aren't any subtitles to convert", file=sys.stderr)
            cmd_auto = [
                "yt-dlp", "-q", "--no-warnings",
                "--write-auto-sub", "--skip-download",
                "--sub-lang", "en", "--convert-subs", "srt",
                "-o", base_output,
                url,
            ]
            if debug:
                # Create executable command with variable substitution
                exec_cmd_auto = cmd_auto.copy()
                if video_id:
                    for i, arg in enumerate(exec_cmd_auto):
                        if arg == base_output:
                            exec_cmd_auto[i] = os.path.join(output_dir, f"{video_id}.en.srt")
                print(f"__ Running auto subtitles extraction: {' '.join(exec_cmd_auto)}", file=sys.stderr)
            
            try:
                subprocess.run(cmd_auto, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except subprocess.CalledProcessError:
                # yt-dlp may exit with code 1 even when subtitles are successfully downloaded
                # We'll check for actual files below rather than relying on exit code
                if debug:
                    print("__ yt-dlp exited with error code (checking for subtitle files anyway)", file=sys.stderr)
            # Note where file is written (VTT -> SRT conversion)
            if debug:
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
                
                # Read SRT content
                with open(path, encoding='utf-8') as f:
                    srt_content = f.read()
                
                # Persist SRT file with proper filename formatting
                # Use same slugification as MD files
                from .cli import slugify_filename_component
                if video_title:
                    slug = slugify_filename_component(video_title)
                elif video_id:
                    slug = slugify_filename_component(video_id)
                else:
                    slug = slugify_filename_component(Path(path).stem)
                # Add timestamp suffix to SRT files using global timestamp
                from .cli import generate_timestamp_suffix
                timestamp_suffix = generate_timestamp_suffix(backend, model)
                srt_path = Path.cwd() / f"{slug}{timestamp_suffix}.srt"
                srt_path.write_text(srt_content, encoding='utf-8')
                if debug:
                    print(f"__ Saved SRT file to {srt_path}", file=sys.stderr)
                else:
                    print(f".. Saved SRT file to {srt_path}", file=sys.stderr)
                
                return srt_content
        raise RuntimeError(
            f"No SRT file found in {output_dir}: yt-dlp did not produce any .srt."
        )
    finally:
        shutil.rmtree(output_dir, ignore_errors=True)
