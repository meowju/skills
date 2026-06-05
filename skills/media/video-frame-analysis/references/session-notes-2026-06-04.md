# Session Notes — 2026-06-04

## What happened

User shared an Instagram Reel: `https://www.instagram.com/reel/DZH_LlTF_JG/`
User verb: "看视频学习怎么做这个" → "watch this video and learn how to do it"

This is a **tutoring/learning framing**, not a "summarize" or "research" framing. The user wants to:
1. Understand what the video shows
2. Extract the actionable workflow
3. (Possibly) save as a reusable note for later

## Video content (hedge.sphere.ai Reel, 149.6s)

Chinese-language **AI 古风短剧 (Chinese-period-drama) production tutorial**. The 5-step workflow taught:

1. **Build character assets first** (multi-view reference sheet, 4 or 3 views)
2. **Lock clothing structure** via ControlNet / IP-Adapter with the reference
3. **Don't pile decorative terms** into prompts —凤冠+项链+妆容 is enough
4. **Lighting is a separate dimension** — write it as its own prompt phrase
5. **Use subject separation** (CapCut / 剪映 AI) to composite later
6. **Write storyboard first** — 4-column table: 镜号 / 分镜 / 提示词 / 运动标注, with character board + style reference attached
7. **Don't fetishize prompts** — the closing thesis

Tool stack shown: ComfyUI (node IDs visible in frames: `node_157`, `node_158`, `node_152`).

## Frame analysis results (13 frames sampled at 12s intervals)

| Frame | Subtitle (verbatim) | Visual |
|---|---|---|
| f_00 | (none) | Cover portrait: AI-generated Hanfu woman |
| f_12 | 但生成的视频还是一眼假 | Same portrait, with disclaimer banner |
| f_24 | 如果把一部AI短剧拆开来看 | Male xianxia character, white + gold robes |
| f_36 | 而是先搭建人物资产 | ComfyUI dark canvas (no nodes visible yet) |
| f_48 | 用一张图的信息量是不够的 | Hanfu woman, "information not enough" subtitle |
| f_60 | 去固定人物的服装结构 | ComfyUI: node_157 + node_152 reference sheets (4-views + 3-views) |
| f_72 | 很多人喜欢给人物堆特别多 | node_158 (portrait) + node_152 (3-view) |
| f_84 | 金色古风头饰和浅色系长裙 | Portrait with white dashed circle around headdress |
| f_96 | 光效其实是这种 | Lower-body shot: Hanfu skirt + embroidered shoes on wood floor + falling petals |
| f_108 | 它能把人物和背景分开 | Portrait with neon-green selection mask outline |
| f_120 | 这样是很难出爆款质感的 | Two figures under cherry blossom tree (anti-example) |
| f_132 | (overlay) 保存一个故事版在5秒之内 | Full storyboard document: 《金管局》9-shot storyboard with color legend + character board + style refs |
| f_144 | 不要迷信提示词 | Male xianxia character, closing thesis |

## Workflow mishaps encountered (now patched in SKILL.md)

1. **Terminal cwd drift**: I `cd /tmp/instareel` in one call, ffmpeg wrote frames to default workdir `/opt/data/` not `/tmp/instareel/`. Next call's `ls` looked in default workdir, found files (lucky coincidence), but my reasoning was confused. **Fix: always use absolute paths in ffmpeg and verify with `ls -la <abs_path>` before vision_analyze.**

2. **vision_analyze "Invalid image source" on 7 frames in parallel batch**: I retried the same calls instead of checking the path first. Cost ~30s of wasted tool calls. The actual cause was that I assumed files were at `/tmp/instareel/f_00.jpg` from my mental model of `cd` having worked — they were at `/opt/data/f_00.jpg`. **Fix: SKILL.md pitfall #11 added.**

3. **Domain-bias from uploader name**: I assumed `hedge.sphere.ai` = finance, prompted vision_analyze with "financial explainer Reel" framing. First frame (a Hanfu portrait with no text) should have told me I was wrong, but I only widened the prompt after seeing the result. The right move: **run one neutral-prompt frame first to confirm the content type before batching 10+ frames with a domain-specific prompt.** SKILL.md pitfall #13 added.

## Note saved

`/opt/data/notes/ai-chinese-drama-tutorial-2026-06-04.md` (4.9 KB)
- Verdict line
- 13-row timeline table with verbatim subtitles
- 5-step workflow breakdown (extracted from video)
- Tool stack (ComfyUI + Kling/Vidu + CapCut)
- "可执行项" section: 5 concrete next steps for the user

## Synthesis lesson

When the user says "看视频学习怎么做这个", the chat reply should:
1. **Open with a 1-sentence verdict on what the video IS** (not "the video shows..." but "this is a X tutorial")
2. **Hand back a clean extraction of the workflow/methodology** (numbered steps, not frame-by-frame)
3. **Name the tools used** (so user can actually replicate)
4. **End with a follow-up question** (do you want me to dig into the next video? want me to set up a ComfyUI workflow for you?)

NOT:
- Pasting raw vision_analyze outputs
- Bullet list of frame content
- Hedging language ("it appears to be...")
- The user pattern is **directness + dense useful info + file pointer**
