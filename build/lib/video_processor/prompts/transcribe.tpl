You are an AI assistant. You will receive a transcript of a video or audio file with timestamps.
Please produce output in Markdown with the following structure:

1. Separate the transcript into sections by major idea. Use markdown level-2 headings (## Section Title).
2. Under each section, break the transcript into paragraphs based on speaker or idea changes.
   - Each paragraph should begin with the timestamp when that paragraph starts (e.g., [00:01:23]).
3. After the transcript sections, include a "## Topics Summary" section with a short paragraph summarizing the key topics covered.
4. Then include a "## Action Items" section listing any action items mentioned as bullet points. If there are none, write "None.".

Here is the transcript:
{{ transcript }}

End of transcript.