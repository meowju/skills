# Vision Analyze Prompt Library — Verified June 2026

## Default prompt (works 80% of the time)

For most short-form social video, use this:

```
Read ALL visible text in this frame VERBATIM (Chinese and English).
Include subtitles, captions, overlay text, watermarks. Describe any
charts/graphs shown — axes, labels, values, arrows. This is from
a [FINANCE / TECH / HEALTH] Reel.
```

Key phrases that improve results:
- `READ ALL VISIBLE TEXT VERBATIM` — without this, vision_analyze summarizes instead of transcribing
- `CHINESE AND ENGLISH` — explicit bilingual instruction
- `DESCRIBE ANY CHARTS` — catches the visual data not in subtitles
- `This is from a [DOMAIN] Reel` — domain context helps with jargon

## Content-type specific prompts

### 1. Subtitle-heavy content (default for Reels/TikTok)

```
Read ALL visible text VERBATIM including subtitles, captions, and
overlay text (both Chinese and English). Note the timestamp
progression of the subtitles if you can see it. This is from a
[finance/health/tech/education] Reel.
```

**When to use:** Most talking-head Reels with hardcoded subs. Also: lecture clips, commentary, news.

### 2. Charts / data slides

```
Read ALL text and numbers VERBATIM. Describe the chart in detail:
type (bar/line/pie), axes (label + range), data series labels,
values, color coding, arrows, annotations, and any trend line.
This is from a financial data presentation.
```

**When to use:** Stock analysis Reels, macro explainers, data journalism.

**Output example:**
```
Bar chart: "2000-2025 S&P 500 drawdowns"
- X-axis: years 2000, 2008, 2020, 2025
- Y-axis: % drawdown from peak
- Bars: -49% (2000-2002), -57% (2008), -34% (2020), -19% (2025)
- Annotation: "S&P 6000 → 7000"
- Red arrow pointing to 2025
```

### 3. Code / terminal output

```
Read ALL visible text VERBATIM including code, terminal output,
filenames, error messages. Note syntax highlighting colors if
relevant. This is from a coding tutorial.
```

**When to use:** Programming tutorials, dev tools demos.

### 4. People / talking head (visual only)

```
Describe the person: their appearance, expression, body language,
what they're doing with their hands. Describe the background and
props. Read any visible text overlay, captions, or graphics.
This is from a [language lesson / interview / vlog].
```

**When to use:** ASMR, vlogs, no-subtitle Reels, language lessons.

### 5. Cooking / product showcase

```
List all ingredients/items shown, with quantities. Note the steps
being performed in order. Read any on-screen text, recipe cards,
or captions. This is from a [cooking/product unboxing] Reel.
```

**When to use:** Recipe Reels, unboxing, product demos.

### 6. Mixed / unknown content

Default to the subtitle-extraction prompt. Vision model is multimodal — it handles text + visuals naturally.

## Multi-frame analysis (advanced)

When extracting 10-15 frames, run a **pass 1** to identify keyframes, then a **pass 2** for detail:

**Pass 1 (10 frames, basic prompt):**
```
Briefly describe what this frame shows (1-2 sentences). Note
if it contains a chart, code, or key text.
```

**Pass 2 (3-5 keyframes only, detailed prompt):**
```
Read all visible text VERBATIM. Describe the chart/code/scene
in maximum detail. This is a key frame.
```

This two-pass approach catches detail without 15× vision_analyze latency.

## Bilingual pattern (Chinese-first creator)

Many Chinese creators use:
- Chinese 简体 / 繁体 subtitle
- English term in parentheses
- Mixed-language content

The prompt:
```
Read all Chinese (both 简体 and 繁体) and English text VERBATIM.
Note the parallel structure: Chinese term → English translation
in parentheses. This is from a Chinese-language finance Reel.
```

The "Chinese 简体 繁体" hint matters — 简体 (simplified) and 繁体 (traditional) are visually different characters, and vision models sometimes confuse them.

## Common vision_analyze errors

| Error | Cause | Fix |
|-------|-------|-----|
| `Permission denied` (no body) | File is in `/root/...` or unreadable dir | `cp` to `/tmp/` first |
| Empty response | File not an image or corrupted | Verify `file thumb.jpg` → "JPEG image data" |
| "I'm not sure what you're asking" | Bad prompt | Use a more specific prompt from above |
| Long response (1000+ words) | Vision treated it as analysis, not transcription | Add "be concise" to prompt |
| Wrong text (e.g., "ABC" instead of "ABG") | Low resolution | Re-extract at `scale=720:-1` or original size |

## Frame count vs prompt verbosity tradeoff

| Goal | Frames | Prompt detail |
|------|-------:|---------------|
| Quick orientation (5 sec) | 5 | "Briefly describe" |
| Default Reel analysis (15-30 sec) | 10-12 | "Read all text VERBATIM" |
| Detailed analysis (1-2 min) | 12-15 | "Read all text + describe visuals" |
| Two-pass (2-3 min) | 10 + 3-5 follow-up | First pass light, second pass deep |

For most user requests, the **default (10-12 frames, full prompt)** is the sweet spot.

## Pitfalls

1. **Vision ignores "I see" framing** — prompts that say "In the image I see..." get normalized. Be direct: "Read all text".

2. **Don't ask for "translation" in the same call** — vision_analyze returns whatever it sees. If you want English translation of Chinese subtitles, do it in a second step (LLM call) or use the bilingual prompt.

3. **Charts with low-contrast labels** — vision can miss gray-on-white axis labels. The fix: re-extract that specific frame at higher resolution (`scale=720:-1` or original 1080) and re-analyze.

4. **"OCR-only" prompts underperform** — saying "act as OCR" gives worse text extraction than "read all text VERBATIM". The model performs better when asked to describe naturally.

5. **Vision hallucinations on tiny text** — if the text is genuinely unreadable (sub-12px font), vision will sometimes invent plausible text. Verify any key fact against a second frame or external source.

6. **Watermarks and brand names** — sometimes garbled. Don't rely on vision to extract creator's handle/username from a watermark; get that from the URL or caption instead.

7. **Foreign-language video without subs** — vision can describe what it sees but can't translate speech. For foreign narration without subs, fall back to whisper.
