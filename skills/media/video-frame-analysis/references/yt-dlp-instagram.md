# yt-dlp for Instagram Reels — Verified June 2026

## Quick start (Reels, TikTok, X, Douyin)

```bash
# Instagram Reel — ?igsh= param is fine, yt-dlp handles it
yt-dlp -f "bv*+ba/best" --merge-output-format mp4 \
  "https://www.instagram.com/reel/DXZXTM-AVul/?igsh=ZTlibG0xbWJlOGlx"

# Twitter/X video
yt-dlp -f "best" "https://twitter.com/user/status/1234567890"

# TikTok (regular short URL)
yt-dlp -f "best" "https://www.tiktok.com/@user/video/1234567890"

# TikTok (vm.tiktok.com short link — expand first if yt-dlp fails)
yt-dlp -f "best" "https://vm.tiktok.com/ZS1234567890/"

# Douyin (Chinese TikTok) — needs cookie most of the time
yt-dlp --cookies cookies.txt -f "best" \
  "https://www.douyin.com/video/1234567890"
```

## Output paths and naming

By default yt-dlp saves to:
```
~/downloads/{uploader}/[title with spaces].mp4
```

Use `-o` to control:
```bash
# Save to specific dir with custom template
yt-dlp -f "bv*+ba/best" --merge-output-format mp4 \
  -o "/tmp/vid/%(uploader)s_%(id)s.%(ext)s" \
  "URL"
```

For Instagram Reels, common patterns:
- `~/downloads/{uploader}/{title} [shortcode].mp4` (default)
- `~/downloads/{uploader}/Video by {uploader} [{shortcode}].mp4` (literal "Video by")

If filename has spaces (common for IG), quote in subsequent commands:
```bash
mv "~/downloads/zytx666/Video by zytx666 [DXZXTM-AVul].mp4" /tmp/vid/reel.mp4
```

## Format selectors explained

| Selector | Behavior |
|----------|----------|
| `best` | Single best muxed file (no merge) |
| `b` / `ba` | Best audio-only stream |
| `bv*+ba/best` | Best video + best audio, fallback to muxed (default for IG) |
| `bv*+ba/b` | Best video + best audio, fallback to best muxed |
| `bv*[height<=720]+ba/best[height<=720]` | Cap at 720p |
| `worst` | Smallest file (sometimes audio-only) |

**Recommended for frame analysis:** `bv*+ba/best --merge-output-format mp4` — gets highest quality video+audio merged, then you can extract audio separately if needed.

## Verified Instagram quirks (June 2026)

1. **DASH adaptive stream**: IG returns video and audio as separate DASH files. yt-dlp auto-merges with `--merge-output-format mp4` (uses ffmpeg).
2. **?igsh= tracking param**: harmless — yt-dlp strips it. Don't manually remove.
3. **Username in URL is optional**: `instagram.com/reel/ID` works as well as `instagram.com/user/reel/ID`.
4. **Private accounts**: 403 from yt-dlp. Can't bypass.
5. **Region-locked**: Some Reels are EU-only or US-only. yt-dlp will say "Video unavailable" with no error code.
6. **Default save to `~/downloads/`**: ytdl's default. Check there first if file "disappears".

## Verify download with ffprobe

```bash
ffprobe -v error -show_entries stream=width,height,duration -show_entries format=size \
  -of default=nw=1 "/path/to/video.mp4"
# Expected output:
# stream=width=1080
# stream=height=1920
# stream=duration=140.300000
# format=size=30000000
```

If `duration` is 0 or missing, the merge didn't complete — re-run with explicit `--merge-output-format mp4`.

## Size expectations

| Source | Duration | Expected size |
|--------|---------:|--------------:|
| IG Reel (1080×1920) | 30s | 5-10 MB |
| IG Reel (1080×1920) | 90s | 15-30 MB |
| IG Reel (1080×1920) | 140s | 25-40 MB |
| TikTok (1080×1920) | 30s | 4-8 MB |
| Twitter/X (1920×1080) | 60s | 8-15 MB |

If sizes are way off, the merge likely failed. Re-run.

## Common errors

| Error | Cause | Fix |
|-------|-------|-----|
| `ERROR: [Instagram] This content is not available` | Private, deleted, or region-locked | Skip; ask user for screenshot or description |
| `ERROR: Sign in to confirm you're not a bot` | YouTube aggressive rate-limit | Use `--cookies-from-browser chrome` or wait |
| `WARNING: Unable to download media: HTTP Error 403` | IG throttling | Wait 5 min, retry once |
| File is `f.mp4` (no audio) | DASH merge failed, only video saved | Re-run with `--merge-output-format mp4 -k` (keep originals) |
| `Conversion failed!` | ffmpeg not in PATH | `sudo apt install ffmpeg` or use `apt-get install -y ffmpeg` in WSL |

## WSL-specific notes

WSL often has ffmpeg pre-installed. Check:
```bash
which ffmpeg  # /usr/bin/ffmpeg
```

If missing:
```bash
sudo apt update && sudo apt install -y ffmpeg
```

Or use the user-space one (no sudo):
```bash
# Check ~/bin
ls ~/bin/ | grep ffmpeg
```

The yt-dlp binary should be at `~/bin/yt-dlp` (in this user's setup). Memory note: curl GitHub release + chmod a+rx.

## Extract audio (for whisper fallback if needed)

```bash
# 16kHz mono WAV — whisper's preferred format
ffmpeg -i video.mp4 -vn -acodec pcm_s16le -ar 16000 -ac 1 audio.wav
```

## Quick download + frame-extract + cleanup pipeline

```bash
URL="$1"
WORKDIR="/tmp/vid_$(date +%s)"
mkdir -p "$WORKDIR" && cd "$WORKDIR"

# Download
yt-dlp -f "bv*+ba/best" --merge-output-format mp4 -o "raw.mp4" "$URL"

# Probe duration
DUR=$(ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "raw.mp4" | cut -d. -f1)
echo "Duration: ${DUR}s"

# Extract frames every 10s
for i in $(seq 0 10 $DUR); do
  ffmpeg -y -ss $i -i "raw.mp4" -vframes 1 -vf "scale=540:-1" "f_${i}.jpg" 2>/dev/null
done

ls -lh f_*.jpg
# Now ready for vision_analyze on each f_*.jpg
```

## When yt-dlp fails entirely

For Instagram specifically, fallback options:
1. **Try with browser cookies**: `yt-dlp --cookies-from-browser chrome "URL"`
2. **Try with -U flag** (force update): `yt-dlp -U` then retry
3. **Try a different video from the same creator**: If only one is broken, may be a regional issue
4. **Ask user to download manually** and provide a path on disk

DO NOT try to install Chrome or Puppeteer for this — they fail in WSL and the entire `browser_navigate` pipeline is fragile. The yt-dlp + ffmpeg + vision_analyze pattern is the production solution.
