# Cyclical Cron Research: Migrate-First Pattern at Near-Limit

> Real case: ai-money-maker Run 151 (v3.46.0→3.47.0). Section 43 stub expansion triggered by headroom check. Pattern codified for future sessions.

## The Core Problem

Cyclical cron jobs (ai-money-maker, wealth-mindset) follow a rotating-research-verticals cycle. Each run picks one vertical, deepens it, adds content. After many runs, the file approaches 100k chars. Headroom shrinks to a few thousand chars. A new run needs to add content, but headroom is too tight for any meaningful addition.

**Naive fix:** Skip the addition. Ship thin content. Report "all topics covered."

**Wrong response:** This leaves headroom permanently unused. A section that was 162 chars at near-limit was expanded to 1,483 chars by finding content already present in a reference file and inlining it — no web research needed.

## The Migrate-First Pattern

When headroom < 2,000 chars and the file is >85k chars, follow this sequence:

1. **Check reference files first** — mine existing references for content that can be inlined. This session expanded a 162-char reference-link section to 1,483 chars using content already in `ai-2025-tools-deep.md`. No web research, no delegate_task calls.

2. **Condense a medium section** — a 1,500-3,000 char section that is reference-linked can be reduced to ~300 chars (summary + reference link), freeing 1,200-2,700 chars of headroom in one operation.

3. **Migrate a large section** (>2,500 chars) to `references/` if headroom < 1,500 and condensation alone is insufficient.

## Headroom Thresholds

| Headroom | Action |
|----------|--------|
| >3,000 | Safe to add new content directly |
| 1,500-3,000 | Condense or migrate first, then add |
| <1,500 | Migrate-first mandatory, add only after headroom recovered |
| <500 | Migrate largest section, do not attempt addition |

## Section 43 Real Case

**Before:** 162 chars (reference link stub only)
```
## 四十三、AI工具最新动态与变现地图（2025补充篇）

> Run 深度研究新增。本节覆盖 AI 编程工具与浏览器扩展变现赛道。完整内容见：

→ Full content: [references/ai-2025-tools-deep.md](references/ai-2025-tools-deep.md)
```

**After:** 1,483 chars (inlined reference content + new framework)
- Cursor Agent Mode 2025 capabilities + 3 monetization paths
- Windsurf differentiation
- Browser Extension monetization framework
- Still references `ai-2025-tools-deep.md` for full content

**Net addition:** +1,321 chars. Headroom went from 2,417 to 1,096. Tight but still functional.

## The "All Covered" Trap

When all rotation verticals already exist in the skill, the naive response is to conclude "nothing new to add." This is wrong when headroom allows deepening. A 162-char stub is not "covered" — it's a missed opportunity. Mine the reference files, inline the content, expand it.

**Rule: never conclude a cyclical run with [SILENT] when expansion is possible via existing references.**

## Version Bump in Cyclical Jobs

When the file is near the limit (>90k chars), the version bump (+0.0.1 patch level) and the content addition must be computed as a single delta and written atomically. Two sequential patches on a near-limit file risk hitting the limit between patches, leaving the file in a corrupted state.

Compute: `content + version_bump + new_section` as one combined string, write once.

## Structural Pre-Flight

Before ANY cyclical job touches a large skill (>80k chars), run the structural survey first:
1. File size + headroom check
2. All section positions
3. Duplicate check
4. Average section size + gap scan
5. Number-order scan (reversal detection)
6. Subsection embedding scan

The survey catches section disorder (which this session found and fixed) before it compounds into patching corruption.

## Web Search Failure → Mine Existing References (Not Defer)

When a cyclical skill-update job calls `delegate_task` for web research and all subagents return HTTP 404 (web search unavailable), the cron job has no human to ask. **The correct response: mine existing `references/`.** Treat the skill's own content library as a content asset to be remined across cycles.

**Real case (ai-money-maker Run 175):** 3 leaf subagents all returned HTTP 404. Session mined existing `ai-compound-asset-deep.md` (5,598 chars), identified that section 83's inline content (2,746 chars) was already fully covered by the reference file. Condensed section 83 → 683 chars (summary + reference link, −2,063 chars), then expanded section 7 with new Old Masters content (+994 chars), all in one atomic write. File went from 99,420 → 98,351 chars. **Produced a full Run 175 output with no web research.**

**Rule: don't let tool failure produce empty runs in cyclical cron-batch contexts.** When web search fails:
1. Scan `references/` files for content already covered by existing inline sections
2. Identify sections that are already reference-linked — condensing them loses no content
3. Apply the **condense-then-expand pattern**: condense a reference-linked section (>2,000 chars → ~500-700 chars = frees 1,300-1,500 chars) then expand another section with new content. Both computed in memory simultaneously, one atomic write.

**Condense-then-expand atomic write pattern:**
```python
import pathlib, shutil
skill_path = "/opt/data/skills/productivity/ai-money-maker/SKILL.md"
content = pathlib.Path(skill_path).read_text()

# Condense: section already reference-linked (no content loss)
old83 = content[content.find("## 八十三、"):content.find("## 八十四、")]
new83 = """## 八十三、Building AI Assets That Compound：退出时机 + 资产复合化
...condensed summary + → Full content: link..."""
assert content.count(old83) == 1, "Not unique"

# Expand: section without reference links
old7_anchor = "ai-old-masters-new-cases.md](references/ai-old-masters-new-cases.md) — ..."
new7_addition = "\n\n---\n\n### New subsection content here..."
assert content.count(old7_anchor) == 1, "Anchor not unique"

# Compute both in memory from same original
new_content = content.replace(old7_anchor, old7_anchor + new7_addition, 1)
new_content = new_content.replace(old83, new83, 1)

tmp = pathlib.Path("/tmp/skill-temp.md")
tmp.write_text(new_content)
shutil.move(str(tmp), skill_path)

# Verify
verify = pathlib.Path(skill_path).read_text()
assert len(verify) <= 100_000
assert "TARGET_CONTENT" in verify
assert new83[:50] in verify
```

**Headroom outcome from Run 175:** section 83 condense (−2,063) + section 7 expand (+994) = net −1,069. File: 99,420 → 98,351. Headroom: 580 → 3,193 chars.