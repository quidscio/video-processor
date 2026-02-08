# Program Flow Summaries

## YouTube Input (`--youtube`)
Common:

1. Start CLI, set a global timestamp used for artifact suffixes, and echo the banner and command line.
2. Resolve LLM backend from CLI or config.

Unique:  

3. If `--download-video` is set, use `yt-dlp` to fetch the title, download the best single-file video, and update the file mtime. Video filename uses `slug + _backend_model_timestamp`.
4. Download captions via `yt-dlp`:
   - Try creator-provided subtitles, then auto-generated if needed.
   - Read the `.srt` file from a temp directory.
   - Save a copy of the SRT to the working directory with the same timestamp suffix as other outputs.
5. Parse SRT into timestamped lines.

Common:

6. Load the prompt template and submit to the configured LLM backend.
7. Write the Markdown summary to a file if `-o` is provided (or auto-generate with `-o=`), using the same timestamp suffix. Otherwise, print to stdout.
8. Exit non-zero if truncation or other tracked errors occurred.

## Local Video/Audio Input

Common: 

1. Start CLI, set a global timestamp used for artifact suffixes, and echo the banner and command line.
2. Resolve LLM backend from CLI or config.

Unique:

3. Convert the media to mono 16kHz WAV via `ffmpeg` (temp file).
4. Run Whisper transcription on the WAV.
5. Build SRT content from Whisper segments and always save the SRT to the working directory using `slug + _backend_model_timestamp`.
6. If `--debug` is set, also save the intermediate WAV and emit detailed debug logging.
7. Parse SRT into timestamped lines.

Common:

8. Load the prompt template and submit to the configured LLM backend.
9.  Write the Markdown summary to a file if `-o` is provided (or auto-generate with `-o=`), using the same timestamp suffix. Otherwise, print to stdout.
10. Exit non-zero if truncation or other tracked errors occurred.
