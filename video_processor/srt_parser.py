"""
srt_parser.py

Convert raw SRT text into timestamped plain-text lines.
"""
import srt

def srt_to_timestamped_lines(srt_text: str) -> str:
    """
    Parse SRT content and return lines of the form:
        [HH:MM:SS] subtitle text
    one per subtitle segment.
    """
    subs = list(srt.parse(srt_text))
    lines = []
    for sub in subs:
        start = sub.start
        hours, remainder = divmod(int(start.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        ts = f"{hours:02}:{minutes:02}:{seconds:02}"
        text = " ".join(sub.content.splitlines())
        lines.append(f"[{ts}] {text}")
    return "\n".join(lines)