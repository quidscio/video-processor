# The Problem 
I claim that in every 30-60 minute podcast and/or youtube video, there's at most 10 minutes of essential content [to me]. Consequently, if I spend more then 5-10 minutes watching that content, my marginal return is negative. I can do better things with my time. But...how to ingest up to 60 minutes of content in 5, a 12x productivity multiplier? 

## LLMs are the Answer

Maybe. I tried UIs for Claude, ChatGPT, and OpenWebUI as a starter. 
* Claude failed to fetch or create a transcript and invited me to provide the transcript
* ChatGPT also failed to fetch or create a transcript and invited me to provide the transcript
* OpenWebUI allowed me to try local and remote models including Llama 3 Augment, Deepseek R1 0528, Opus 4, and Llama 4 Scout. With these approaches, I could mostly get a transcript but without timestamps. Timestamps are required to quickly navigate to content of interest. Overall, have to consider OpenWebUI a miss. 

## Manual Approach 

After some experimentation I found the following approach worked. 
* Use yt-dlp downloader to extract the transcript 
* Feed the transcript to Claude Opus 4 with the _Transcription Prompt_ 
* Review and act accordingly 
* Time saved to reach this point 

TODO: Include transcription prompt somewhere  
TODO: Include sample output somewhere 

### Fine Points 
While a simple process, there are fine points to consider
1. There are different transcripts one might extract from youtube 
1. Not all sources are youtube videos. Other sources include local videos and audio-only podcasts 

#### Types of youtube Transcripts 
Users may upload their own transcript. Presumably, these are of higher quality and should be preferred. The video downloader command is
```bash
yt-dlp --write-sub --skip-download --sub-lang en --convert-subs srt "https://www.youtube.com/watch?v=VIDEO-KEY"
``` 
If youtube is to generate the transcript, use the `--write-auto-sub` flag: 
```bash
yt-dlp --write-auto-sub --skip-download --sub-lang en --convert-subs srt "https://www.youtube.com/watch?v=VIDEO-KEY"
```

#### Video or Audio Files as a Source 
You might have the video file from some other tool such as `Google Admin Toolbox Screen Recorder` or `OBS`. In these cases, I prefer local transcription such as by a slightly modified version of [VIdeo-Transcription](https://github.com/marc-shade/VIdeo-Transcription). This approach uses Ollama server and local models. Using Whisper is a perfectly reasonable alternative. 

FUTURE: Convert *.webm files to VIdeo-Transcription friendly format  
FUTURE: Test and Enable *.mp3 audio to be converted

#### CLI Initial Prompt 
Examine the readme_rmh.md file with focus on the requirements. 
We are creating a python application to accomplish the goals set out using the tools specified.

I want you to suggest a way to structure and accomplish the requirements goals.
If you see better approaches than suggested, check with me before proceeding.

Program progress should look something like:  
```text
== Video Processor 2025-07-04 ==
.. Downloading youtube SRT [URL] and command line options used 
__ DBG [command being used or other debug statement]
.. Received [filename]
** Error: Errors start with "**" 
```

Prefix definitions are as follows 
```text 
== denotes program start 
.. Normal status 
__ Debug statements citing external command strings and key decisions 
** Errors start with "**" 
```

The program must have a -d --debug flag to enable debug output. 
Debug output should include:
* External commands used exactly as used without unevaluated parms
* Important decisions made and why
* Save of working files using timestamp prefix, yyyymmdd_hhmmss_filename 

# Chronology 

07.03.25 Requirements  
07.06.25 V1 YT URL works. Improvements required  
    TODO: (in progress) Eliminate environment setting dependencies; anthropic backend, any others  
    TODO: Test approach to enable WSL to windows host for ollama server config  
    BUG: This must be specified in config and can't be via CLI, ollama_host = "192.168.1.68"

#### Setup items 
We want to make this configurable (video-processor.cfg) or via .env or via command line option 
* WSL 
    * export LLM_BACKEND=anthropic
    * export ANTHROPIC_API_KEY=sk...
    * set OLLAMA_URL=http://192.168.1.68:11434
    * export OLLAMA_URL=192.168.1.68
* Powershell 
    * Set-NetFirewallRule -DisplayName "Allow Ollama on port 11434" -EdgeTraversalPolicy Allow

We need to cleanup configuration. Some set of the following were needed to get a WSL instance running on a Windows host where Ollama runs under Windows. Explain each item and whether it is needed for this command: 
* video-processor  -d   --llm-model claude-opus-4-20250514    -y https://www.youtube.com/watch?v=3bpNxeKmWug

Config items: 
* WSL 
    * export LLM_BACKEND=anthropic
    * export ANTHROPIC_API_KEY=sk...
    * set OLLAMA_URL=http://192.168.1.68:11434
    * export OLLAMA_URL=192.168.1.68
* Powershell 
    * Set-NetFirewallRule -DisplayName "Allow Ollama on port 11434" -EdgeTraversalPolicy Allow

#### Fixing debug output. 

> python3 -m video_processor.cli -d   --backend ollama -l deepseek-r1:7b    -y https://www.youtube.com/watch?v=3bpNxeKmWug
[debug] running creator-sub cmd: yt-dlp --write-sub --skip-download --sub-lang en --convert-subs srt -o /tmp/vpdl-iq63t47c/%(id)s.%(ext)s https://www.youtube.com/watch?v=3bpNxeKmWug
[youtube] Extracting URL: https://www.youtube.com/watch?v=3bpNxeKmWug
[youtube] 3bpNxeKmWug: Downloading webpage
[youtube] 3bpNxeKmWug: Downloading tv client config
[youtube] 3bpNxeKmWug: Downloading tv player API JSON
[youtube] 3bpNxeKmWug: Downloading ios player API JSON
[youtube] 3bpNxeKmWug: Downloading m3u8 information
[info] 3bpNxeKmWug: Downloading 1 format(s): 137+251
[info] There are no subtitles for the requested languages
[SubtitlesConvertor] There aren't any subtitles to convert
[debug] running auto-sub cmd: yt-dlp --write-auto-sub --skip-download --sub-lang en --convert-subs srt -o /tmp/vpdl-iq63t47c/%(id)s.%(ext)s https://www.youtube.com/watch?v=3bpNxeKmWug
[youtube] Extracting URL: https://www.youtube.com/watch?v=3bpNxeKmWug
[youtube] 3bpNxeKmWug: Downloading webpage
[youtube] 3bpNxeKmWug: Downloading tv client config
[youtube] 3bpNxeKmWug: Downloading tv player API JSON
[youtube] 3bpNxeKmWug: Downloading ios player API JSON
[youtube] 3bpNxeKmWug: Downloading m3u8 information
[info] 3bpNxeKmWug: Downloading subtitles: en
[info] 3bpNxeKmWug: Downloading 1 format(s): 137+251
[info] Writing video subtitles to: /tmp/vpdl-iq63t47c/3bpNxeKmWug.en.vtt
[download] Destination: /tmp/vpdl-iq63t47c/3bpNxeKmWug.en.vtt
[download] 100% of  450.29KiB in 00:00:00 at 2.49MiB/s
[SubtitlesConvertor] Converting subtitles
Deleting original file /tmp/vpdl-iq63t47c/3bpNxeKmWug.en.vtt (pass -k to keep)
[debug] Sending prompt to LLM backend (ollama), model=deepseek-r1:7b, temp=0.0
[debug] Received result from LLM (length=4382 chars)

General approach: 

== denotes program start 
.. Normal status 
__ Debug statements citing external command strings and key decisions 

Sample: 
== Video Processor [Version] == 
.. Seeking subtitles for https://www.youtube.com/watch?v=3bpNxeKmWug
__ Running creator titles extraction: [put command here]
____ There aren't any subtitles to convert 
__ Running auto-titles extraction: [put command here] 
____ Writing subtitles to file []
.. Received subtitles, 100% of  450.29KiB in 00:00:00 at 2.49MiB/s
.. Sending prompt to LLM backend (ollama), model=deepseek-r1:7b, temp=0.0
.. Received result from LLM (length=4382 chars)

### Favorite command lines

```bash
video-processor -o= -w medium -b ollama -l deepseek-r1:7b  -y https://www.youtube.com/watch?v=VIDEO
video-processor -o= -w medium -b anthropic -l claude-opus-4-20250514     -y https://www.youtube.com/watch?v=VIDEO
```
