# Embedded Duplicate: The Case Where "Removing a Duplicate" Deleted 10 Real Sections

> Extracted from hermes-agent-skill-authoring SKILL.md pitfall (original pitfall 50 content before refactor). Real case: ai-money-maker v2.79.

## What Happened

A structural survey found `## 五十九、` appearing twice in ai-money-maker v2.79.0:
- Copy A: at position ~60,661 (between `## 三十三、` and `## 三十五、`), 3,213 chars
- Copy B: not present as a top-level header

The survey's "五十九 appearing twice" referred to the `### 五十九、` **subsection** (a lower-level header), not a top-level section. The true structure was:

- `### 五十九、` inside `## 三十三、` (embedded, not top-level)
- A real `## 五十九、` was expected but did NOT exist as a top-level header

## The Block That Almost Got Deleted

The block between `## 三十三、` (pos 60,273) and `## 三十五、` (pos 63,888) contained:
- `### 五十九、` subsection (3,214 chars) — the "embedded copy"
- Below it: `## 二十六、` through `## 三十五、` (10 full top-level sections, ~18k chars)

## What Went Wrong

A session attempted to "remove the duplicate 五十九" by targeting the embedded `### 五十九、` block (3,214 chars). But the removal boundary was too wide — it caught the entire block down to `## 三十五、`, deleting not just the embedded subsection but also the 10 legitimate top-level sections (二十六 through 三十五) that had been placed inside it.

**File shrank from ~99k to ~71k in one edit.**

Recovery: `git checkout HEAD -- path` restored the file.

## Why the Survey Was Misleading

In ai-money-maker's multi-session history, section 五十九 had been moved and re-inserted as a subsection inside section 三十三. The 10 sections that followed (二十六–三十五) were also placed inside this block by a prior session. The embedded `### 五十九、` was never a "duplicate" — it was the only copy of the section that should have been `## 五十九、` (top-level), and the block containing it also held 10 other top-level sections that had no other location in the file.

## Pre-Removal Checklist (Mandatory)

When you find a "duplicate" section number, run this before removing anything:

```python
import re, pathlib

skill_path = "/opt/data/skills/productivity/ai-money-maker/SKILL.md"
content = pathlib.Path(skill_path).read_text()

# Find the suspected duplicate block
pos_dup = content.find('\n## 五十九、')  # adjust number as needed
dup_len = 3500  # approximate length of the duplicate block

# Get text of the block
block_text = content[pos_dup:pos_dup + dup_len]

# Check what's inside
inner_toplevel = re.findall(r'\n## ([一二三四五六七八九十]+)、', block_text)
inner_subsections = re.findall(r'\n### ([一二三四五六七八九十]+)、', block_text)

print(f"Inner ## top-level headers: {inner_toplevel}")  # non-empty = cluster, NOT duplicate
print(f"Inner ### subsection headers: {inner_subsections}")

if inner_toplevel:
    print("⚠️ BLOCK IS AN EMBEDDED CLUSTER — NOT a duplicate. Do NOT remove.")
    print("These are legitimate sections that exist nowhere else in the file.")
    print(f"These sections would be LOST: {inner_toplevel}")
```

## Fix Strategy for Embedded Clusters

If the block contains legitimate `## N、` headers:

1. **Do NOT remove the block** — those sections exist nowhere else
2. Extract the inner `## N、` headers as top-level sections at their correct chronological positions
3. Extract the embedded `### N、` subsections as their own `## N、` top-level sections
4. Only then remove the now-empty shell block

## The Rule

Any time a structural survey flags a "duplicate" section number, the FIRST action is to check whether the suspected duplicate block contains other `## N、` top-level headers. If it does, the block is an embedded cluster — not a duplicate — and removing it is a catastrophic deletion.

The question to ask: "Does this block contain sections that would disappear from the file if I delete this block?" If yes, it is not a duplicate; it is a displaced cluster that needs to be untangled, not removed.