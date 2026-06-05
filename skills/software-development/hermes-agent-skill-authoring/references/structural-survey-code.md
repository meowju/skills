# Six-Step Structural Survey (>80k Skills)

Full survey code from pitfall 39c of the hermes-agent-skill-authoring SKILL.md.

Run this before ANY edit to a >80k SKILL.md — user-initiated or cron session. It catches disorder, embedded subsections, orphan blocks, and large gaps that indicate section swaps. Only after confirming a clean state should the session proceed to add new content.

```python
import re, pathlib
from collections import Counter

skill_path = "/opt/data/skills/productivity/ai-money-maker/SKILL.md"  # adjust
content = pathlib.Path(skill_path).read_text()
sections = [(m.start(), m.group(1), m.group(2)) for m in re.finditer(
    r'\n## ([一二三四五六七八九十百]+)、([^\n]+)', content
)]

# Step 1: size + headroom
print(f"Size: {len(content):,}, headroom: {100_000 - len(content):,}")

# Step 2: section count
print(f"Sections: {len(sections)}")

# Step 3: disorder scan (file position vs. expected sequential order)
nums = [n for _, n, _ in sections]
file_order = [(p, n, t) for p, n, t in sections]
disorder = [(sections[i][1], sections[i+1][1]) for i in range(len(sections)-1)
            if sections[i][0] > sections[i+1][0]]
print(f"Disorder pairs: {disorder}")

# Step 4: large-gap scan (>3000 chars between adjacent sections)
for i in range(len(sections)-1):
    gap = sections[i+1][0] - sections[i][0]
    if gap > 3000:
        print(f"  LARGE GAP: {sections[i][1]}→{sections[i+1][1]}: {gap} chars @ pos {sections[i][0]}")

# Step 5: duplicate numbers
dup_nums = {k: v for k, v in Counter(nums).items() if v > 1}
print(f"Duplicate numbers: {dup_nums}")

# Step 6: duplicate titles
titles = [t for _, _, t in sections]
dup_titles = {k: v for k, v in Counter(titles).items() if v > 1}
print(f"Duplicate titles: {dup_titles}")
```

## Disorder Detection Logic

Compare file order vs. sequential order:
- `file_order = [(p, n, t) for p, n, t in sections]` — in file position order (3-element unpack: position, number, title)
- `seq_order = sorted(sections, key=lambda x: cn_to_int(x[1]))` — sorted by Chinese numeral value
- Any position where `num != expected_num` = section out of place

> ⚠️ **Critical:** `sections` contains 3-element tuples `(pos, num, title)`. The `file_order` line MUST unpack 3 elements — `(p, n, t)` not `(n, p)`. The broken pattern `(n, p) for p, n, _ in sections` silently drops the third element, causing the generator to fail and every `parent` report `"NONE"` in the embedded subsection scan (pitfall 24c). This is the same bug that appears in the inline embedded subsection detector code in SKILL.md pitfall 24b. Always verify both files are in sync.

```python
# WRONG (2-element unpack — breaks the generator):
file_order = [(n, p) for p, n, _ in sections]  # ValueError: not enough values to unpack

# CORRECT (3-element unpack):
file_order = [(p, n, t) for p, n, t in sections]
```

Full `cn_to_int` converter:
```python
def cn_to_int(cn):
    mapping = {'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,'十':10,'百':100}
    result = 0
    temp = 0
    for char in cn:
        if char == '百':
            result = (temp or 1) * 100
            temp = 0
        elif char == '十':
            temp = temp * 10 + 10 if temp else 10
        else:
            temp += mapping.get(char, 0)
    return result + temp
```

## Gap Threshold
**Gap Threshold**
The survey threshold for "large gap" should be **>3000 chars** (not >4000). The >4000 threshold was used in early sessions but produces false negatives on dense multi-section skills where even 3,500-char gaps are normal (not indicative of embedded blocks). Real case: ai-money-maker v3.05 had a 5,097-char gap between 十七 and 十八 — correctly flagged at >3000, revealed orphaned content. At >4000, this gap would have been missed. Always use >3000.

**Critical: Gap scan regex must match two-digit Chinese numerals.**
The pattern `\n## ([一二三四五六七八九十]+)、` only matches section numbers up to 10 (一 to 十). For sections numbered 二十 (20), 二十一 (21), etc., the regex silently fails to match, causing the gap scan to compute gaps between the *previous* matched section and the *next* matched section — a completely wrong pair. Real case: gap scan reported "3,492 chars between 72 and 73" but actual section 73 was only 1,677 chars; the regex matched 二十 (section 十 at pos X) instead of 七十三, creating a phantom gap that didn't correspond to any real section boundary.

**More critically:** The pattern also fails on any section numbered with 零 (zero) — 一百零一, 一百零二, etc. The 零 character is not in the character class, so the regex stops at 零 and captures only the prefix — e.g., 一百 instead of 一百零一. This makes all 零-using sections (101, 102, 103, etc.) completely invisible to the structural survey. Real case (ai-money-maker Run 180): sections 101-105 were present in the file but the survey reported only 85 sections (all numbered 一 through 一百); the zero-prefixed sections were undetected. Adding 零 to the class fixes the blind spot.

**Correct regex for section matching (use in gap scan AND structural survey):**
```python
# WRONG — only matches 一 through 十 (1-digit numerals) AND misses 零:
r'\n## ([一二三四五六七八九十]+)、'

# WRONG — still misses 零:
r'\n## ([一二三四五六七八九十百千万]+)、'

# CORRECT — matches any Chinese numeral including 零一, 零二, 二十一, etc.:
r'\n## ([一二三四五六七八九十百千万零]+)、'
```
The character class `[一二三四五六七八九十]` only matches one of those characters. A section header like `七十二` is five characters — the regex stops at the first character it can't match (七), so it captures only `七` instead of `七十二`. This makes the gap scan report gaps for completely wrong section pairs. Always use the extended character class for section number matching.

## Disorder Detection — Correct Logic

```python
def cn_to_int(cn):
    mapping = {'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,'十':10}
    result = 0
    for char in cn:
        if char == '百':
            result = (result or 1) * 100
        elif char == '千':
            result = (result or 1) * 1000
        elif char == '万':
            result = (result or 1) * 10000
        elif char == '十':
            result = (result * 10) + 10 if result else 10
        else:
            result += mapping.get(char, 0)
    return result
```

## Complete Corrected Survey Code

```python
import re, pathlib
from collections import Counter

skill_path = "/opt/data/skills/productivity/ai-money-maker/SKILL.md"  # adjust
content = pathlib.Path(skill_path).read_text()
sections = [(m.start(), m.group(1), m.group(2)) for m in re.finditer(
    r'\n## ([一二三四五六七八九十百千万]+)、([^\n]+)', content
)]

def cn_to_int(cn):
    mapping = {'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,'十':10}
    result = 0
    for char in cn:
        if char == '百':
            result = (result or 1) * 100
        elif char == '千':
            result = (result or 1) * 1000
        elif char == '万':
            result = (result or 1) * 10000
        elif char == '十':
            result = (result * 10) + 10 if result else 10
        else:
            result += mapping.get(char, 0)
    return result

nums = [n for _, n, _ in sections]

# Step 1: size + headroom
print(f"Size: {len(content):,}, headroom: {100_000 - len(content):,}")

# Step 2: section count
print(f"Sections: {len(sections)}")

# Step 3: disorder scan (Chinese numeral values must increase with file position)
disorder = [(nums[i], nums[i+1]) for i in range(len(nums)-1)
            if cn_to_int(nums[i]) > cn_to_int(nums[i+1])]
print(f"Disorder pairs: {disorder}")

# Step 4: large-gap scan (>3000 chars between adjacent sections)
for i in range(len(sections)-1):
    gap = sections[i+1][0] - sections[i][0]
    if gap > 3000:
        print(f"  LARGE GAP: {sections[i][1]}→{sections[i+1][1]}: {gap} chars @ pos {sections[i][0]}")

# Step 5: duplicate numbers
dup_nums = {k: v for k, v in Counter(nums).items() if v > 1}
print(f"Duplicate numbers: {dup_nums}")

# Step 6: duplicate titles
titles = [t for _, _, t in sections]
dup_titles = {k: v for k, v in Counter(titles).items() if v > 1}
print(f"Duplicate titles: {dup_titles}")
```

## When Survey Finds Issues

If any step returns non-empty suspicious result, fix that problem FIRST before adding new content. A disordered file patched blindly compounds corruption. Real case: ai-money-maker v2.86 had both disorder and large gaps; running the survey before patching caught the disorder. Without the survey, the next insertion would have landed in the wrong section due to wrong positional assumptions.