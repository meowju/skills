---
name: youtube-content
description: "Extract transcripts, captions, and content from YouTube and other video platforms — including platforms with no native transcript API (Instagram, TikTok, etc.). Transform transcripts into summaries, threads, blogs."
platforms: [linux, macos, windows]
---

# Video Content Extraction

## When to use

Use when the user shares any video URL (YouTube, Instagram Reels, TikTok, etc.) and asks to summarize, transcribe, or extract content from it. Transforms content into structured formats (chapters, summaries, threads, blogs).

**Two paths:**
1. **Native transcript API** (YouTube, Vimeo, etc.) — use `youtube-transcript-api` via the helper script
2. **No transcript API** (Instagram Reels, TikTok, most social video) — use `yt-dlp` + `faster-whisper` to download + transcribe

This skill covers both.

**Companion skill:** For short-form social video (Reels/TikTok/X) where the primary content is on-screen text/subtitles/charts rather than narration, use the `video-frame-analysis` skill instead — it uses vision_analyze on extracted frames, which is 3-5× faster than whisper for visual-heavy content.

## Setup

```bash
# Path 1 dependencies
pip install youtube-transcript-api

# Path 2: use openai-whisper (NOT faster-whisper — faster-whisper is not on PyPI)
# Install via uv run --with (avoids Python 3.13 venv restrictions on Debian/Ubuntu)
uv run --with openai-whisper python3 -c "import whisper; print('ok')"
```

## Path 1 — Native Transcript API (YouTube, Vimeo, etc.)

`SKILL_DIR` is the directory containing this SKILL.md file.

```bash
# JSON output with metadata
python3 SKILL_DIR/scripts/fetch_transcript.py "https://youtube.com/watch?v=VIDEO_ID"

# Plain text
python3 SKILL_DIR/scripts/fetch_transcript.py "URL" --text-only

# With timestamps
python3 SKILL_DIR/scripts/fetch_transcript.py "URL" --timestamps

# Specific language with fallback chain
python3 SKILL_DIR/scripts/fetch_transcript.py "URL" --language tr,en
```

## Path 2 — No Transcript API (Instagram Reels, TikTok, most social video)

Use `yt-dlp` to download the video, then `openai-whisper` to transcribe. **Do NOT use `faster-whisper`** — it is not on PyPI. Use `uv run --with openai-whisper` instead.

```bash
# 1. Download the video+audio merged
# Instagram Reels have ?igsh=... tracking param — yt-dlp handles it fine either way
uv run --with yt-dlp yt-dlp -o "/tmp/video.mp4" "VIDEO_URL"

# 2. Extract audio (16kHz mono wav)
ffmpeg -i /tmp/video.mp4 -vn -acodec pcm_s16le -ar 16000 -ac 1 /tmp/audio.wav

# 3. Transcribe with openai-whisper
uv run --with openai-whisper python3 - <<'EOF'
import whisper
model = whisper.load_model('small')   # 'tiny' for speed, 'small' for accuracy, 'medium' for best
result = model.transcribe('/tmp/audio.wav', language='en')
for seg in result['segments']:
    print(f'[{seg["start"]:.1f}-{seg["end"]:.1f}] {seg["text"]}')
EOF
```

**Model size guide:**
- `tiny` — fastest, lower accuracy on proper nouns, brand names
- `small` — **recommended default** for clean narration; good accuracy/speed tradeoff
- `medium` — best accuracy, especially for brand names, technical terms; slower

**Language:** always specify `language=` explicitly (e.g., `language='en'`, `language='zh'`) to avoid misdetection.

**Note:** `openai-whisper` runs on CPU. First load downloads the model (~72MB for `tiny`, ~461MB for `small`, ~1.4GB for `medium`). Models are cached at `~/.cache/whisper/`.

**Note:** Instagram Reel URLs include a tracking parameter (`?igsh=...`). Strip it before passing to `yt-dlp` (it works fine with or without, but cleaner without it).

## Workflow

1. **Detect** whether the platform has a native transcript API (YouTube → Path 1, otherwise → Path 2).
2. **Fetch** using the appropriate path. Validate output is non-empty.
3. **Chunk if needed**: if the transcript exceeds ~50K characters, split into overlapping chunks (~40K with 2K overlap) and summarize each chunk before merging.
4. **Transform** into the requested output format. Default: summary.
5. **Verify**: re-read the output for coherence and completeness.

## Output Formats

After fetching the transcript, format it based on what the user asks for:

- **Chapters**: Group by topic shifts, output timestamped chapter list
- **Summary**: Concise 5-10 sentence overview of the entire video
- **Chapter summaries**: Chapters with a short paragraph summary for each
- **Thread**: Twitter/X thread format — numbered posts, each under 280 chars
- **Blog post**: Full article with title, sections, and key takeaways
- **Quotes**: Notable quotes with timestamps

### Example — Chapters Output

```
00:00 Introduction — host opens with the problem statement
03:45 Background — prior work and why existing solutions fall short
12:20 Core method — walkthrough of the proposed approach
24:10 Results — benchmark comparisons and key takeaways
31:55 Q&A — audience questions on scalability and next steps
```

## Pitfalls

- **`faster-whisper` is not on PyPI** — do not use it. Use `openai-whisper` via `uv run --with openai-whisper python3`. The skill previously recommended `faster-whisper`; that was wrong.
- **`pip`/`pip3` not in PATH**: use `uv pip install <package>` or `uv run --with <package>` as fallback.
- **`python3 -m pip` fails with "ensurepip not available"** on Debian/Ubuntu with Python 3.13: system Python venv is broken. Use `uv run --with openai-whisper` instead — `uv` manages its own environment and doesn't need system pip.
- **`uv pip install --system` fails** with the same PEP 668 error: same root cause. Always use `uv run --with` for packages that conflict with system Python.
- **Whisper misrecognizes language**: always specify `language=` explicitly for non-English video to avoid misdetection.
- **Whisper garbles brand names/proper nouns**: try a larger model (`small` or `medium` instead of `tiny`). For English narration with technical terms, `small` is the recommended default — significantly better than `tiny` at only moderate speed cost.
- **YouTube bot detection**: YouTube frequently blocks `youtube-transcript-api` and `yt-dlp` with "Sign in to confirm you're not a bot" — this can happen even with a valid video URL and correct setup. This is not a setup error; YouTube actively flags non-browser clients. When this occurs:
  1. Try the **oembed fallback** — `curl -s "https://www.youtube.com/oembed?url=https://youtu.be/VIDEO_ID&format=json"` — returns title, channel, thumbnail even when transcripts are blocked. Useful for getting video context when full transcript is unavailable.
  2. Fall back to **Path 2** (download + whisper) — if `yt-dlp` is also blocked, try different Invidious instances: `yewtu.be`, `invidious.privacyredirect.com`, `iv.nboeck.de`, `invidious.kavin.rocks`. Note: most Invidious instances are unreliable or down.
  3. If all fallbacks fail, inform the user with the video title and channel (from oembed) so they can watch it directly.
- **Instagram Reels**: URL contains `?igsh=...` tracking param — strip it or pass as-is (both work). Video downloads as DASH adaptive stream (video+audio separate files) — `yt-dlp` auto-merges them. Target ~9-10MB per minute of video.

## Error Handling

- **Transcript disabled or unavailable**: switch to the download+transcribe path (Path 2).
- **Private/unavailable video**: relay the error and ask the user to verify the URL.
- **No matching language**: retry without `--language` to fetch any available transcript.
- **Download fails (Instagram)**: try stripping `?igsh=...` param, or try alternative URL variants.
- **Whisper transcription garbled**: try a larger model (`medium` or `large`) or specify the correct language explicitly.
