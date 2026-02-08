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
DONE: Include sample output somewhere 

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
* Save of working files using timestamp suffix, filename_yyyymmdd-hhmmss 

# Chronology 

07.03.25 Requirements  
07.06.25 V1 YT URL works. Improvements required  
    DONE: (in progress) Eliminate environment setting dependencies; anthropic backend, any others  
    DONE: Test approach to enable WSL to windows host for ollama server config  
    BUG: This must be specified in config and can't be via CLI, ollama_host = "192.168.1.68"
07.10.25 OpenAI completed 
    DONE: Fixup README.md 
    FUTURE: Consider writeup including points to M
    FUTURE Do a program dataflow analysis & consider refactors or version on openrouter 
09.30.25 Address youtube issue 
    DONE: Address this YT video which will not download or yield SRT 
02.08.26 Updated YT, multiple refinements 

#### Details for 9/30/25 YT Issue
```properties 
    |0:user@rmhlap-wsl2)-(11:17:09.30)|
    /mnt/c/Users/rmhin/Downloads
    |8) > video-processor -o= -d -D -y https://www.youtube.com/watch?v=0DA3i69WMF4
    == Video Processor 1.5.5 20250930-111719 ==
    .. Executing /home/user/bin/video-processor -o= -d -D -y https://www.youtube.com/watch?v=0DA3i69WMF4
    .. Seeking subtitles for https://www.youtube.com/watch?v=0DA3i69WMF4
    .. Downloading full video for https://www.youtube.com/watch?v=0DA3i69WMF4
    __ Running video download with title 'Inside the high tech quest to decode the lost scrolls of Herculaneum | Casey Handmer': yt-dlp -f b -o Inside-the-high-tech-quest-to-decode-the-lost-scrolls-of-Herculaneum-Casey-Handmer_openai_o4-mini_20250930-111719.%(ext)s https://www.youtube.com/watch?v=0DA3i69WMF4
    [youtube] Extracting URL: https://www.youtube.com/watch?v=0DA3i69WMF4
    [youtube] 0DA3i69WMF4: Downloading webpage
    [youtube] 0DA3i69WMF4: Downloading tv client config
    [youtube] 0DA3i69WMF4: Downloading tv player API JSON
    [youtube] 0DA3i69WMF4: Downloading ios player API JSON
    [youtube] 0DA3i69WMF4: Downloading player da13af8d-main
    WARNING: [youtube] Falling back to generic n function search
            player = https://www.youtube.com/s/player/da13af8d/player_ias.vflset/en_US/base.js
    WARNING: [youtube] 0DA3i69WMF4: nsig extraction failed: Some formats may be missing
            n = Xw4xjSCZFPTkZs72z ; player = https://www.youtube.com/s/player/da13af8d/player_ias.vflset/en_US/base.js
            Please report this issue on  https://github.com/yt-dlp/yt-dlp/issues?q= , filling out the appropriate issue template. Confirm you are on the latest version using  yt-dlp -U
    WARNING: [youtube] 0DA3i69WMF4: nsig extraction failed: Some formats may be missing
            n = VkL-nedWV_Pu3Cgc4 ; player = https://www.youtube.com/s/player/da13af8d/player_ias.vflset/en_US/base.js
            Please report this issue on  https://github.com/yt-dlp/yt-dlp/issues?q= , filling out the appropriate issue template. Confirm you are on the latest version using  yt-dlp -U
    WARNING: [youtube] 0DA3i69WMF4: nsig extraction failed: Some formats may be missing
            n = ZU0zna3L4hHRWjHuM ; player = https://www.youtube.com/s/player/da13af8d/player_ias.vflset/en_US/base.js
            Please report this issue on  https://github.com/yt-dlp/yt-dlp/issues?q= , filling out the appropriate issue template. Confirm you are on the latest version using  yt-dlp -U
    WARNING: [youtube] 0DA3i69WMF4: Some web client https formats have been skipped as they are missing a url. YouTube is forcing SABR streaming for this client. See  https://github.com/yt-dlp/yt-dlp/issues/12482  for more details
    [youtube] 0DA3i69WMF4: Downloading m3u8 information
    ERROR: [youtube] 0DA3i69WMF4: Requested format is not available. Use --list-formats for a list of available formats
    Error: Error downloading video: Command '['yt-dlp', '-f', 'b', '-o', 'Inside-the-high-tech-quest-to-decode-the-lost-scrolls-of-Herculaneum-Casey-Handmer_openai_o4-mini_20250930-111719.%(ext)s', 'https://www.youtube.com/watch?v=0DA3i69WMF4']' returned non-zero exit status 1.
    |1:user@rmhlap-wsl2)-(11:17:29.30)|
    /mnt/c/Users/rmhin/Downloads
    |9) > video-processor -o=  -D -y https://www.youtube.com/watch?v=0DA3i69WMF4
    == Video Processor 1.5.5 20250930-112914 ==
    .. Executing /home/user/bin/video-processor -o= -D -y https://www.youtube.com/watch?v=0DA3i69WMF4
    .. Seeking subtitles for https://www.youtube.com/watch?v=0DA3i69WMF4
    __ Running creator subtitles extraction: yt-dlp -q --no-warnings --write-sub --skip-download --sub-lang en --convert-subs srt -o /tmp/vpdl-44pr9mn0/0DA3i69WMF4.srt https://www.youtube.com/watch?v=0DA3i69WMF4
    ____ There aren't any subtitles to convert
    __ Running auto subtitles extraction: yt-dlp -q --no-warnings --write-auto-sub --skip-download --sub-lang en --convert-subs srt -o /tmp/vpdl-44pr9mn0/0DA3i69WMF4.en.srt https://www.youtube.com/watch?v=0DA3i69WMF4
    __ yt-dlp exited with error code (checking for subtitle files anyway)
    Error: No SRT file found in /tmp/vpdl-44pr9mn0: yt-dlp did not produce any .srt.
    |1:user@rmhlap-wsl2)-(11:29:40.30)|
    /mnt/c/Users/rmhin/Downloads
    |10) >
```

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

### Model Price Comparison and Effectiveness Prediction 

[ChatGPT Link (private)](https://chatgpt.com/g/g-p-686a9bb5e49c8191a7e2969739b3e334-ai/c/686f1420-a0bc-800c-a74b-0ac44ec12a92) 

🔁 Normalized Cost and Ranking Prediction Table

| Model             | Input Norm | Output Norm | Summary Rank |
| ----------------- | ---------- | ----------- | ------------ |
| Claude Opus 4     | 5.00       | 5.00        | **1**        |
| Claude Sonnet 4   | 1.00       | 1.00        | **2**        |
| GPT‑4.1           | 0.67       | 0.53        | **3**        |
| GPT‑4o            | 1.67       | 1.33        | **4**        |
| o4‑mini           | 0.37       | 0.29        | **5** (tie)  |
| GPT‑4o‑mini       | 0.20       | 0.16        | **5** (tie)  |
| Codex‑mini‑latest | 0.50       | 0.40        | **6** (tie)  |
| GPT‑4.1‑mini      | 0.13       | 0.11        | **6** (tie)  |
| o3                | 0.67       | 0.53        | **6** (tie)  |

📊 Raw Cost Table

| Model             | Input (\$/M tok) | Output (\$/M tok) |
| ----------------- | ---------------- | ----------------- |
| GPT‑4.1           | 2.00             | 8.00              |
| GPT‑4.1‑mini      | 0.40             | 1.60              |
| GPT‑4o            | 5.00             | 20.00             |
| GPT‑4o‑mini       | 0.60             | 2.40              |
| o3                | 2.00             | 8.00              |
| o4‑mini           | 1.10             | 4.40              |
| Codex‑mini‑latest | 1.50             | 6.00              |
| Opus 4            | 15.00            | 75.00             |
| Sonnet 4          | 3.00             | 15.00             |

Interesting to note, between the Anthropic models, Sonnet is actually superior. 

Models to try after Sonnet 4: 

gpt-4.1-2025-04-14
gpt-4.1-mini-2025-04-14
gpt-4o-mini-2024-07-18
o3-2025-04-16
o4-mini-2025-04-16

#### Overall Effectiveness and Cost Ranking 

| Model               | Input norm | Output norm | Rank (Group 1)        |
|---------------------|------------|-------------|------------------------|
| o3                  | 1.82       | 1.82        | 1                      |
| Opus 4              | 13.64      | 17.05       | 2                      |
| o4‑mini             | 1.00       | 1.00        | 3                      |
| GPT‑4.1             | 1.82       | 1.82        | 4                      |
| GPT‑4.1‑mini        | 0.36       | 0.36        | 5                      |
| Sonnet 4            | 2.73       | 3.41        | 6                      |
| GPT‑4o              | 4.55       | 4.55        | (Not in Group 1)       |
| GPT‑4o‑mini         | 0.55       | 0.55        | (Not in Group 1)       |
| Codex‑mini‑latest   | 1.36       | 1.36        | (Not in Group 1)       |

From this table and experience, perform a close analysis of: 
* Sonnet 4: the previous winner 
* o4-mini: performs well in page-summary tool 
* gpt-4.1-mini: scored close to o4-mini and is 1/3 the cost
