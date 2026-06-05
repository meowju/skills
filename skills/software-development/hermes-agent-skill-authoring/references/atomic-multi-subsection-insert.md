# Atomic Multi-Subsection Insert: Pattern & Decision Tree

> Run 153 new reference. Documents the atomic write pattern for inserting multiple new subsections into a large skill file in a single pass — eliminating the cascade-offset-failure problem that plagued ai-money-maker v2.59→v2.72.

---

## The Core Problem

When a large skill file (>80k chars, 50+ sections, dense `---` dividers) requires inserting multiple new subsections (or section additions), sequential `patch` calls accumulate byte-offset drift. Each patch shifts all subsequent positions — subsequent patches land in the wrong section.

**Real case (ai-money-maker v2.59→v2.72):** Three consecutive patches using absolute position + cumulative offset all inserted into adjacent wrong sections. The file appeared to succeed at each patch but silently embedded references into the wrong sections.

---

## The Fix: Atomic Multi-Insertion

Load the full file content into memory once. Compute every insertion's anchor and replacement simultaneously. Produce the complete new content. Write once.

```python
import pathlib, re

skill_path = "/opt/data/skills/productivity/ai-money-maker/SKILL.md"
content = pathlib.Path(skill_path).read_text()

# Step 1: Read the original file ONCE
# Step 2: Compute all anchors from the SAME original content
# Step 3: Build all replacements in memory
# Step 4: Apply all replacements to the same original content object
# Step 5: Write ONCE

# Example: Two new subsections to insert
# Anchors computed from the SAME original content
anchor1_pos = content.find("INSERT_POINT_1_ANCHOR_TEXT")
anchor2_pos = content.find("INSERT_POINT_2_ANCHOR_TEXT")

# Deltas computed from original
old1 = "anchor1_text_to_replace"
old2 = "anchor2_text_to_replace"
new1 = "new_content_1"
new2 = "new_content_2"

# ALL replacements on the same content object
new_content = content.replace(old1, new1, 1).replace(old2, new2, 1)

# Single write
pathlib.Path(skill_path).write_text(new_content)
```

**Key rule:** All `old_string` values must be computed from the **same original** `content` — never from a modified copy in memory.

---

## Decision Tree: Which Approach to Use

| Scenario | Approach |
|----------|----------|
| 1 new section at EOF | `content += new_section` — simple append |
| 1 targeted replacement (unique old_string) | `content.replace(old, new, 1)` verified unique |
| Multiple insertions at different positions | **Atomic multi-insert** — all at once from same original |
| File >90k chars, headroom <2k | Migrate-first → then atomic insert |
| Condensation + new section in same session | Compute combined delta → atomic write |
| Concurrent sibling agents possible | Atomic write + post-verify checklist |

---

## Post-Write Verification Checklist

After any write to a large skill file:

1. **Size gate:** `len(pathlib.Path(path).read_text())` ≤ 100,000 — use Python, not `wc -c`
2. **Target section:** confirm section appears at expected character position
3. **Following section:** confirm next section still intact at expected position
4. **No duplicates:** run `re.findall(r'\n## [一二三四五六七八九十]+、')` and verify count
5. **Version sync:** confirm version line matches the content that landed

---

## Structural Survey: Pre-Edit Mandatory Scan

Before ANY edit to a >80k skill, run the six-step survey:

```python
import re, pathlib; from collections import Counter
skill_path = "/opt/data/skills/productivity/ai-money-maker/SKILL.md"  # adjust
content = pathlib.Path(skill_path).read_text()
sections = [(m.start(), m.group(1), m.group(2)) for m in re.finditer(
    r'\n## ([一二三四五六七八九十百千万]+)、([^\n]+)', content
)]

def cn_to_int(cn):
    mapping = {'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,'十':10}
    result = 0
    for char in cn:
        if char == '百': result = (result or 1) * 100
        elif char == '千': result = (result or 1) * 1000
        elif char == '万': result = (result or 1) * 10000
        elif char == '十': result = (result * 10) + 10 if result else 10
        else: result += mapping.get(char, 0)
    return result

nums = [n for _, n, _ in sections]
print(f"Size: {len(content):,}, headroom: {100_000 - len(content):,}")
print(f"Sections: {len(sections)}")

# Step 3: disorder scan
disorder = [(nums[i], nums[i+1]) for i in range(len(nums)-1)
            if cn_to_int(nums[i]) > cn_to_int(nums[i+1])]
print(f"Disorder: {disorder}")

# Step 4: large-gap scan (>3000 chars)
for i in range(len(sections)-1):
    gap = sections[i+1][0] - sections[i][0]
    if gap > 3000: print(f"  GAP: {sections[i][1]}→{sections[i+1][1]}: {gap} chars")

# Step 5: duplicate numbers
dup_nums = {k: v for k, v in Counter(nums).items() if v > 1}
print(f"Duplicate numbers: {dup_nums}")
```

**⚠️ Critical bug in inline embedded subsection detector (pitfall 24c):**
The inline code in SKILL.md uses `next(f"## {num}" for pos, num in sections if pos < sub_pos)` — this is a **2-element unpack** on a **3-element tuple**, which raises `ValueError: not enough values to unpack` silently. Every subsection reports `"NONE"` as parent, masking all embedded subsections. The fix: `for pos, num, _ in sections`.

**⚠️ Same bug in references/structural-survey-code.md — `file_order` line:**
```python
# WRONG (2-element — crashes the generator):
file_order = [(n, p) for p, n, _ in sections]

# CORRECT (3-element):
file_order = [(p, n, t) for p, n, t in sections]
```

**⚠️ Regex character class bug:** The pattern `r'\n## ([一二三四五六七八九十]+)、'` only matches one character — section numbers like 二十 (20), 七十二 (72), etc. are silently truncated. Use `r'\n## ([一二三四五六七八九十百千万]+)、'` (extended character class).

---

## Cyclical Cron-Job Execution Mandate (Pitfall 57)

A session that reads and analyzes extensively, plans the exact patch needed, but reaches the tool-call limit before applying the write — has failed. The cron job delivered a report, not the work.

**Rule:** Execute the write in the same session that does the planning. An imperfect patch to a large skill is recoverable; a silent no-op is not.

When headroom is tight AND all topics exist, **condense** — don't conclude with "[SILENT]". Defer is wrong when headroom is the blocker.

---

## Headroom Safety Formula

When planning content addition on a near-limit file:
```
estimated_headroom_needed = new_section_size + overhead
if current_size + estimated_headroom_needed > 98_000:
    migrate-first (condense largest ref-linked section → references/)
    then add
```

**Real case (wealth-mindset Run 8):** Size gate blocked Bezos expansion (96,809 + 6,000 > 100k); switched to 468-char stub placeholder → landed 99,385 chars. Stub discovery prevents no-op conclusions.