---
name: video-frame-analysis
description: "Analyze short-form social video (Instagram Reels, TikTok, Twitter video, Douyin) by extracting frames with ffmpeg and using vision_analyze on each frame — much faster than transcribing audio, and works for visual-only content, on-screen text, infographics, charts, and foreign-language subtitles. Use when user shares a video URL and wants to know what it shows/argues, especially when the video has heavy on-screen text (subtitles, captions, charts, slides) rather than pure narration. Different from youtube-content which transcribes audio with whisper."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [video, instagram, tiktok, frames, vision, ocr, content-extraction]
    related_skills: [youtube-content]
---

## When to use this skill

Use when the user wants to understand what a **short-form social video** shows or argues, especially:

- **On-screen text is the primary content** — subtitles, captions, slides, charts
- **Foreign-language video** (Chinese, Japanese, Korean) where reading subtitles > understanding audio
- **Visual-only content** — Instagram carousel, infographic video, no narration
- **Quick orientation needed** — "what is this video about?" without full transcript
- **Video has charts/graphs/data** — financial explainers, data presentations

**Do NOT use for**: long-form YouTube lectures (use `youtube-content` for whisper transcription), pure-audio podcasts (use `youtube-content` Path 1), videos where the audio IS the content (interviews, vlogs).

## Difference from `youtube-content`

| Aspect | youtube-content | video-frame-analysis |
|--------|----------------|---------------------|
| Approach | Transcribe audio with whisper | Extract frames + vision_analyze |
| Speed | 2-5 min (whisper) | 30-60 sec (frames only) |
| Cost | High (full audio → text) | Low (10-15 frames) |
| Best for | Lecture/interview/podcast | Reels/TikTok/shorts with text |
| Handles | Spoken content | Visual + on-screen text |
| Language-agnostic | Needs whisper per language | Vision handles any language |
| Works offline? | Needs whisper model | Just ffmpeg |

For a 140s Reel: this skill = 10 frames, ~10 vision_analyze calls, ~1 min total. Whisper would be 140s of audio + 1 model load + transcription = 3-5 min minimum.

## When to combine both

If you have a 30-min YouTube lecture with on-screen slides, run BOTH:
1. `youtube-content` → whisper transcript
2. `video-frame-analysis` → frames at major slide transitions

The frames catch things audio misses (formulas, code, charts, citations).

---

## Workflow (3-5 minutes total)

### Step 1 — Download the video

```bash
mkdir -p /tmp/vid && cd /tmp/vid
# Instagram Reel — yt-dlp handles ?igsh=... param fine
yt-dlp -f "bv*+ba/best" --merge-output-format mp4 "VIDEO_URL"

# Twitter/X video
yt-dlp -f "best" "https://twitter.com/USER/status/ID"

# TikTok
yt-dlp -f "best" "https://www.tiktok.com/@USER/video/ID"

# Douyin (Chinese TikTok) — may need cookie, often flaky
yt-dlp -f "best" "https://www.douyin.com/video/ID"
```

**Output**: `~/downloads/{source}/[title].mp4` or current dir.

**Verify with ffprobe:**
```bash
ffprobe -v error -show_entries stream=width,height,duration -of default=nw=1 "video.mp4"
# Get: width, height, duration_seconds
```

### Step 2 — Extract evenly-spaced frames

**Rule of thumb for sample count:**
- < 60s video: 6-8 frames
- 60-180s: 10-14 frames
- 3-10 min: 15-25 frames
- > 10 min: 25-40 frames

**Use uniform spacing (NOT first/last + middle):**
```bash
# For a 140s video, sample every 10s = 14 frames
for i in 00 10 20 30 40 50 60 70 80 90 100 110 120 130; do
  ffmpeg -y -ss $i -i "video.mp4" -vframes 1 -vf "scale=540:-1" "f_${i}.jpg" 2>/dev/null
done
```

**Why scale to 540 wide?**
- 540px is enough resolution for vision_analyze to read subtitles
- Reduces vision_analyze latency (vs. 1080×1920)
- Smaller files for embedding in notes

**For vertical 9:16 video (Reels/TikTok), use 540:-1 to preserve aspect.**

### Step 3 — Run vision_analyze on each frame

**⚠️ CRITICAL PITFALL — vision_analyze fails on /root/ paths with "Permission denied".** Always use /tmp/ or /opt/data/. The `cd ~/downloads/...` and pass relative path trick won't work because the absolute path is still resolved.

**Working pattern:**
```bash
mkdir -p /tmp/vidframes
cp f_*.jpg /tmp/vidframes/
```

Then call `vision_analyze` on `/tmp/vidframes/f_00.jpg`, `/tmp/vidframes/f_10.jpg`, etc.

**Question prompt — make it request VERBATIM text:**
```
Read ALL visible text in this frame VERBATIM (Chinese and English),
including subtitles, captions, charts, numbers. Describe what
charts/graphs are shown in detail — axes, labels, values, arrows.
This is from a financial explainer Reel.
```

The "VERBATIM" and "ALL visible text" prompts dramatically improve text extraction accuracy. Without them, vision_analyze summarizes instead of transcribing.

### Step 4 — Synthesize

Two options depending on user's ask:

**Option A — Quick summary (default):**
- Read all vision_analyze outputs
- Group by topic/timeline
- Write 5-8 bullet summary in chat

**Option B — "小笔记" (saved note) — user pattern:**
- Write full markdown note to `/opt/data/notes/{topic}-{YYYY-MM-DD}.md`
- Include: cover frame, timeline of subtitle changes, key visual elements
- Chat reply: 1-line verdict + 5-bullet breakdown + file path

User pattern: "看视频" → summary in chat; "你觉得这个有道理吗" → my opinion with both sides; "有道理的话写小笔记" → save to disk.

### Step 5 — Deliver (if Discord / file)

If sending to Discord DM (cron context):
```bash
# Build a preview grid
cd /tmp/vidframes
ffmpeg -y -i thumb_01.jpg -i thumb_02.jpg -i thumb_03.jpg -i thumb_04.jpg \
  -i thumb_05.jpg -i thumb_06.jpg -i thumb_07.jpg \
  -filter_complex "tile=4x2:padding=8:color=black" -frames:v 1 preview_grid.jpg
```

Then attach `preview_grid.jpg` and the original `video.mp4` to the Discord message.

**⚠️ Pitfall — Discord 403 in cron context.** The `send_message` tool returns `403 Missing Access` from cron subprocess. Save the file path in chat and let the user fetch it from `/tmp/...` or `~/downloads/...`.

---

## Prompting vision_analyze for different content types

### Subtitles-heavy content (Reels/TikTok with hardcoded subs)
```
Read ALL visible text in this frame VERBATIM (Chinese and English),
including subtitles, captions. Note the timestamp progression if any.
This is from a [finance/health/tech] Reel.
```

### Charts / data slides
```
Read ALL text and numbers VERBATIM. Describe the chart in detail:
type, axes, labels, values, color coding, arrows, annotations.
This is from a financial data presentation.
```

### Code / terminal output
```
Read ALL visible text VERBATIM including code, terminal output,
filenames, error messages. Note syntax highlighting colors if
relevant. This is from a coding tutorial.
```

### People / talking head
```
Describe the person, their expression, what they're doing with
their hands, what's behind them. Read any visible text overlay.
This is from a [language lesson / interview / commentary].
```

### Mixed / unknown content
Default to the subtitle-extraction prompt — works for almost everything.

### Chinese video tutorial with tool UI (ComfyUI, video editor, storyboard)
When the Reel is a tutorial showing software/workflow screens — ComfyUI node canvas, video editor, character reference sheet, storyboard table — the subtitle-only prompt misses most of the teaching content (which lives in the UI, not the subs). Use:

```
Read ALL visible text VERBATIM (Chinese + English). Describe the
software UI in detail: node names, connection wires, file paths,
panel labels, button text. If the frame shows a storyboard/script
table, transcribe the cell content (shot number, prompt text,
motion labels, color legend). If the frame shows character reference
sheets, describe each view (front/side/back) and what's in it.
This is from a Chinese AI video production tutorial Reel.
```

**Tells that this is the right prompt:**
- Frame has grid/dot background with rectangular image cards + colored connection lines (ComfyUI / similar node editor)
- Frame shows a table or spreadsheet with Chinese column headers
- Frame shows multiple views of the same character (front/side/back reference sheet)
- Subtitle uses workflow vocabulary: 节点 (node), 提示词 (prompt), 资产 (assets), 分镜 (storyboard), 运动标注 (motion annotation), 光效 (lighting effect), 人物分离 (subject separation)

**What to extract that subtitle-only prompts miss:**
- Node IDs (`node_157`, `node_158`) — these are real workflow identifiers, not noise
- Image content within UI cards (the tutorial's actual visual deliverable)
- Color legends (red=相机运动 / blue=人物运动 / green=环境运动)
- Storyboard shot numbers and motion arrows

---

## Frame-count tradeoffs

| Frames | Pros | Cons |
|--------|------|------|
| 5 | Fast, cheap | Misses most content |
| 10-15 | Good for 60-180s Reel | Sweet spot |
| 20-30 | Catches fast content | Slow, redundant |
| 50+ | Catches every slide change | Way too redundant for shorts |

For a typical Instagram Reel (30-90s), 8-12 frames is enough. For dense content (3 fps slides, dense charts), 20-30.

**Adaptive sampling:** If vision_analyze on frame N reveals a chart, extract 3-5 sub-frames around N to get full chart content. The 2-pass approach (uniform → focused) catches detail without bloating the initial extraction.

---

## Pitfalls (verified — these WILL bite you)

1. **`vision_analyze` fails on `/root/...` with "Permission denied"** (verified Jun 2026 session). The vision service runs in a sandbox that can't read /root/. Always `cp` to `/tmp/` or `/opt/data/` before calling. **This is the #1 time-sink.**

2. **Instagram URLs include `?igsh=...` tracking param** — yt-dlp handles it fine, but if you want a clean URL for logs, strip it: `sed 's/?igsh=.*//'` before passing to yt-dlp.

3. **yt-dlp on Instagram returns DASH adaptive stream** — video and audio come as separate files, then get merged. Don't pass `--no-merge` unless you know what you're doing. The `bv*+ba/best` format selector handles this automatically.

4. **Vertical 9:16 video (Reels/TikTok) is 1080×1920** — use `scale=540:-1` to maintain aspect, not `scale=540:540` (that'd crop).

5. **Some videos are >5 min, splitting is needed** — for very long content, chunk by 60s segments and extract 5 frames from each. The vision context window can be saturated by 30+ frames at once.

6. **Vision on text-heavy frames can miss small subtitles** — scale=540 is usually enough but if subtitle is tiny (e.g., TikTok 6-line reply comments), go to 720 or use original 1080 for that specific frame.

7. **`browser_navigate` may not have Chrome installed** — first failure: `Chrome not found. Checked: agent-browser cache, system Chrome, Puppeteer, Playwright`. Don't try to install Chrome; use yt-dlp + ffmpeg + vision_analyze (this skill) instead.

8. **Some IG accounts are private / region-locked** — yt-dlp will return 403 or empty. In that case, fall back to: ask user to describe content, or skip the analysis.

9. **Whisper is for AUDIO content, vision is for VISUAL content** — don't reach for `youtube-content` (which uses whisper) when the user says "what does this Reel say?" — this skill is 3-5× faster for visual-heavy Reels.

10. **Concatenating frame descriptions is the hard part** — vision_analyze returns 10-15 separate descriptions. Don't paste them raw into the chat reply. Synthesize into a timeline:
    - Group consecutive frames with same visual
    - Identify the 3-5 key "moments" in the video
    - For each moment, list the subtitles/visuals in order
    - End with 1-line takeaway

11. **`vision_analyze` "Invalid image source" error = file not found, not tool broken** (verified Jun 2026). When 7+ calls fail with this exact error in a batch, the path is wrong — do `ls -la <path>` and `realpath <path>` immediately. Don't retry the calls. Common cause: a `cd` in a prior terminal call did NOT persist (each terminal call resets cwd to workdir), so output files went to a different dir than you thought.

12. **Terminal cwd resets every call** (verified Jun 2026) — `cd /tmp/foo && ffmpeg ... out.jpg` in one terminal call does NOT mean `f_*.jpg` is in `/tmp/foo/` next call. Output goes to wherever ffmpeg's absolute path says, but the NEXT `ls` in a new call will use the default workdir. Always use absolute paths for both input and output AND verify with `ls -la <abs_path>` before calling vision_analyze. If you see `f_*.jpg` in `ls f_*.jpg` (relative) but the next call can't find them, you have cwd drift.

13. **Don't pre-bias vision_analyze with assumed content type from the uploader name** (verified Jun 2026). I assumed `hedge.sphere.ai` → finance Reel, but the video was an AI Chinese-period-drama production tutorial. If the first frame shows art/portraits/no text, the uploader name is misleading you. Either:
    - Use a domain-neutral first pass: `"Describe what's in this frame and read any visible text VERBATIM"`
    - Or pre-check the account with one neutral vision call before batching 10+ frames with a finance prompt
    
    The wrong prompt wastes a full batch — domain signals steer the model to "find" content that isn't there.

---

## Combinations

### With SEC EDGAR / stock data
If the video is a financial explainer (e.g., creator discusses a specific stock), after running this skill, pipe the subtitle content into a `stock-fundamental-due-diligence` research note. The video gives you **what the creator thinks**, the research gives you **what the data shows**.

### With cron / Discord delivery
If running in a cron context and you need to deliver the summary to Discord, the chat reply here IS the deliverable — no need to call `send_message` (which fails in cron). The cron scheduler will deliver the chat output to Discord DM automatically.

---

## References

- `references/yt-dlp-instagram.md` — full yt-dlp patterns for Instagram Reels (URL formats, format selectors, output filenames, post-merge cleanup)
- `references/vision-prompts.md` — copy-paste vision_analyze prompt library for common video content types (subtitles, charts, code, talking head, mixed)
- `references/frame-extraction.md` — adaptive sampling strategies: uniform, focused (after first pass detects interesting content), chunked for long video
- `references/session-notes-2026-06-04.md` — concrete example of a Chinese-AI-video-tutorial Reel, frame-by-frame transcript, workflow extraction pattern
