# Near-Limit Headroom Recovery: Condense-Already-Linked Pattern

> Extracted from ai-money-maker Run 101 (v3.3.0 → v3.4.0). File at 99,936 chars, 64-char headroom.

## The Problem

SKILL.md at 99,936 chars — only 64 chars of headroom. Need to add a new 1,800-char section but there is literally zero room. Standard response: migrate content to references/ first. But migration requires finding content to move, writing a reference file, linking it, and verifying the link. That's 4+ operations for ~1,800 chars of gain.

## The Insight

When a section already has valid reference links to existing reference files AND the inline content is a summary of the same reference files, the inline content is **redundant**. Condensing it to a 1-paragraph summary + reference link is not "losing content" — it's removing duplication. The content lives in the reference file.

**Safe to condense without new migration work:**
- Section has 2+ `→ Full content: references/X.md` links
- Inline content summarizes or restates what's in those reference files
- The reference files already exist and are linked elsewhere in the skill

**NOT safe to condense (requires new migration):**
- Section has no reference files
- Content is unique to this section (not duplicated in references/)
- The reference file doesn't exist yet

## The 4-3-1 Rule

When headroom < 2,000 chars:
1. **Scan for 4 things** that indicate safe condensation: (a) section has existing reference links, (b) reference files already on disk, (c) inline content is a summary, (d) the same reference links appear elsewhere in the skill
2. **Pick 3 sections** that meet the safe-condense criteria — targeting the longest ones
3. **Free 1 target amount** — compute how many chars you need, target 3-4x that in freed space to allow buffer

## Run 101 Case Study

**Starting state:** 99,936 chars, 64 headroom
**Goal:** Add section 27 (1,867 chars)
**Needed:** ~2,000 chars

| Section | Before | After | Saved | Safe? |
|---------|--------|-------|-------|-------|
| 七、行业老法师AI增值 | 3,747 | 542 | -3,205 | ✓ Already 3 refs |
| 二十一、AI自由职业者白皮书 | 5,092 | 375 | -4,717 | ✓ Already has ref |
| 三十七（body only）| 639 | 604 | -35 | ✓ Preserve 38 |
| 三十九、AI竞争情报 | 481 | 262 | -219 | ✓ Already has ref |
| **Total** | | | **~8,176** | |

**Result:** 93,665 chars, 6,335 headroom. New section inserted with room to spare.

## Pre-Check Script

```python
import pathlib, re
path = "/opt/data/skills/productivity/ai-money-maker/SKILL.md"
content = pathlib.Path(path).read_text()
size = len(content)
headroom = 100_000 - size
print(f"Size: {size:,} | Headroom: {headroom:,}")
if headroom < 2000:
    # Find sections with existing reference links — safe to condense
    for m in re.finditer(r'\n## ([^\n]+)\n([^→]+?(?:→ Full content: references/|→ 完整内容: references/)[^\n]+\n)', content):
        section_name = m.group(1)
        ref_count = len(re.findall(r'→ (?:Full content|完整内容|Related):', m.group(2)))
        print(f"  SAFE CONDENSE: {section_name[:40]} ({ref_count} ref links)")
```

## Key Constraint

Condensed sections MUST still make sense as standalone summaries. The paragraph you leave behind must still answer: "What does this section teach?" The reference link is an escape hatch for readers who want depth — not an excuse to leave a placeholder.

## Contrast with Standard Migration

| | Standard migration | Condense-already-linked |
|---|---|---|
| New reference file needed? | Yes | No |
| Link verification required? | Yes (new link) | No (already verified) |
| Content risk? | Low (new file) | Zero (content exists in refs) |
| Operations per section | 3-4 | 1 |
| Headroom gained per section | Variable | 500-4,000 |

The condense-already-linked pattern is the fastest way to recover headroom when you have sections that are already "half migrated" (have reference links but still have full inline content).