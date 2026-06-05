# Video Platform Transcription Reference

## IMPORTANT — Tool Correction (2025-05-31)

**Use `openai-whisper`, NOT `faster-whisper`.** `faster-whisper` is not on PyPI and cannot be `uv pip install`ed. Correct invocation:

```bash
uv run --with openai-whisper python3 -c "
import whisper
model = whisper.load_model('small')
result = model.transcribe('/tmp/audio.wav', language='en')
for seg in result['segments']:
    print(f'[{seg[\"start\"]:.1f}-{seg[\"end\"]:.1f}] {seg[\"text\"]}')
"
```

## Instagram Reels

Instagram Reels have **no public transcript API**. The only viable path is download + ASR transcription.

### Steps that worked

```bash
# Step 1: Get direct video URL
uv run --with yt-dlp yt-dlp --get-url "https://www.instagram.com/reel/DX6Rt-6OE6b/"

# Returns two URLs (video + audio track for DASH adaptive stream)
# Ex: .../.../AQNSPQV2pba6yKSaUuPuz8oiZgQ....mp4
#     .../.../AQPp0uhV2YYCC3cb4tX98WxvfzD6ERn....mp4 (audio)
```

Instagram Reels download as DASH adaptive streams (separate video and audio files). `yt-dlp` auto-merges them into a single MP4 when using `-o /tmp/video.mp4`.

```bash
# Step 2: Download (merged MP4)
uv run --with yt-dlp yt-dlp -o "/tmp/insta_reel.mp4" "https://www.instagram.com/reel/DX6Rt-6OE6b/"

# Note: Instagram Reel URLs contain a tracking param: ?igsh=MW0weXI0ZjlteWthZg==
# yt-dlp handles this fine — no need to strip it, but also safe to strip.
# Typical file size: ~9-10MB per minute of video.
```

```bash
# Step 3: Extract audio (16kHz mono WAV)
ffmpeg -i /tmp/insta_reel.mp4 -vn -acodec pcm_s16le -ar 16000 -ac 1 /tmp/insta_audio.wav
```

```bash
# Step 4: Transcribe
uv run --with openai-whisper python3 -c "
import whisper
model = whisper.load_model('small')
result = model.transcribe('/tmp/insta_audio.wav', language='en')
for seg in result['segments']:
    print(f'[{seg[\"start\"]:.1f}-{seg[\"end\"]:.1f}] {seg[\"text\"]}')
"
```

**Model selection (tested on clean English narration):**
- `tiny` (~72MB): fast but garbles brand names (e.g., "Micron" → random syllables)
- `small` (~461MB): **recommended default** — good accuracy on proper nouns at moderate speed
- `medium` (~1.4GB): best accuracy on technical terms; used when `small` still garbles brand names

**Settings:**
- `language='en'` — always specify explicitly
- CPU inference (FP16 not supported on CPU → uses FP32, warning is harmless)
- First run downloads model to `~/.cache/whisper/`

**Result quality:** `small` model on clean English AI/finance narration — all key terms came through clearly (SK Hynix, Micron, HBM, NVIDIA). Minor issues with compound phrases but full meaning intact.

## TikTok

Same approach as Instagram Reels — no transcript API, use `yt-dlp` + `openai-whisper`.

## YouTube

Use Path 1 (native transcript API via `youtube-transcript-api`) first. Only fall back to download+whisper if:
- The video has transcripts disabled
- The transcript is available but corrupted/missing sections
- The user wants auto-generated captions which may differ from official subtitles
