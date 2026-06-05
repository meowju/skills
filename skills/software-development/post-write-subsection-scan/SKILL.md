---
name: post-write-subsection-scan
description: "Use after ANY patch that adds, moves, or renumbers a `### N、` subsection in a multi-section skill. Detects subsection placement errors invisible to reading."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [skills, authoring, verification, subsection-placement]
    related_skills: [hermes-agent-skill-authoring]
---

# Post-Write Subsection Placement Scan

## When to Use
After ANY patch that adds, moves, or renumbers a `### N、` subsection in a multi-section skill — especially a large one (>40 sections, >80k chars). This is the single most reliably missed structural error in multi-session skill maintenance.

## The Problem

When inserting a new `### N、` subsection into a parent `## N、` section via absolute position anchor, the insertion point can land in the wrong section if:
- The anchor `\n\n\n` or `---` pattern also appears in an earlier section
- The section boundary detection uses `content.find("---")` instead of the correct section-end marker
- The section ends with `\n\n---\n\n\n` but the search is for bare `---\n`

The subsection text appears readable and correctly formatted — but it is structurally embedded in the wrong parent section. The corruption is invisible to casual reading because the human reads section numbers in logical order, not file position order.

**Real case:** A session inserted "### The First Anger Cycle" at position 74279, which fell inside the Neurobiology section (72461–76220) — not the Anger Phase (76221–84624). The anchor `\n\n\n` at position 82676 (correct Anger Phase end) was identified but the patch landed at 74279 instead. The subsection read correctly but was in the wrong section. Caught manually; automated scan would have caught it in one pass.

## The Scan

```python
import re, pathlib

skill_path = "/opt/data/skills/productivity/breakup-recovery/SKILL.md"  # adjust
content = pathlib.Path(skill_path).read_text()

# Get all top-level section positions — 3-element tuples (pos, num, title)
sections = [(m.start(), m.group(1), m.group(2).strip()) for m in re.finditer(
    r'\n## ([一二三四五六七八九十百千万VI]+)、(.+)', content
)]

# Get all subsection positions — 2-element tuples (pos, label)
subsections = [(m.start(), m.group(0).strip()) for m in re.finditer(r'\n### [^\n]+', content)]

print(f"Top-level sections: {len(sections)}")
print(f"Subsections: {len(subsections)}")
print()

for sub_pos, sub_label in subsections:
    # Find which section contains this subsection
    containing = [(pos, num, title) for pos, num, title in sections if pos < sub_pos]
    if containing:
        parent_pos, parent_num, parent_title = containing[-1]
        # Find next section
        next_section = next(((pos, num) for pos, num, _ in sections if pos > sub_pos), (None, None))
        next_pos, _ = next_section if next_section else (len(content), None)
        span = sub_pos - parent_pos
        gap = next_pos - sub_pos
        print(f"'{sub_label[:40]}'")
        print(f"  Parent: ## {parent_num} at pos {parent_pos} ({parent_title[:40]})")
        print(f"  Position: {sub_pos} | Span: {span:,} | Gap to next: {gap:,}")
        print()
    else:
        print(f"ORPHAN: '{sub_label}' at pos {sub_pos} — outside all sections!")
```

## Key Check
For each subsection, verify:
1. The parent section is the INTENDED one — not the closest earlier section by file position
2. The subsection position is within the parent's byte range (parent_pos < sub_pos < next_section_pos)
3. No two subsections share the same parent section when they should be in different sections

## Also Run: Section Header Scan

After any subsection insertion, also run the header scan from pitfall 5c to catch missing `\n\n` between adjacent `##` headers — this catches merged/embedded headers that result from incorrect insertion positions:

```python
headers = [(m.start(), m.group(0)[3:].strip()) for m in re.finditer(r'\n## [^\n]+', content)]
for pos, title in headers:
    print(f"  {title[:70]}")
```

## Micro-Condensation: When Headroom Is Tight But Not Zero

When the file is >85k chars and headroom is 800–2,000 chars, and you need to add ONE subsection (200–1,000 chars), the migrate-first approach is overkill. Instead, **micro-condense** — replace the tail anchor of the target section with the new subsection content.

**Real case (ai-money-maker Run 170):** File at 98,819 chars, headroom 1,181. Needed to add 916-char subsection 五 to section 54. Migrating a section would free ~1,200–2,700 chars but require finding a migratable section and linking it. Instead: replaced the last 20 chars of section 54 (`……\n\n`) with `### 五、收入分布的非对称性\n\n[new 916-char content]\n\n` — net +896 chars, landed at 99,736 with 264 headroom.

**Decision tree:**

| Headroom | Available operation |
|----------|---------------------|
| >3,000 | Direct addition |
| 1,500–3,000 | Condense a medium section (1,500–3,000 chars), migrate if needed |
| 800–1,500 | Micro-condense: find a trailing anchor (5–30 chars) in the target section, replace with new subsection |
| <800 | Migrate-first mandatory (find largest reference-linked section, migrate to references/) |

**Micro-condense anchor requirements:**
- Anchor must be a unique string at the END of the target section (last 10–30 chars before trailing `\n\n`)
- Replacement must be `### N、Section Title\n\n` + new content + `\n\n`
- Verify new subsection is within intended parent section boundaries after patch

**Verification after micro-condensation:**
1. New subsection byte position falls within target section byte range
2. Target section size grew by approximately new_content_size − anchor_size
3. Following section still intact (no content bleed)
4. No new duplicate section or subsection numbers introduced

## Recovery Protocol — When the Scan Finds Misplaced Subsections

When a subsection is found in the wrong parent section (pos falls outside intended parent boundaries):

1. **Extract** the full subsection text from its current wrong position
2. **Delete** it from the wrong location (find subsection header → find next `\n### ` or `\n## ` → slice out)
3. **Insert** at the correct position in the intended parent (use section header + first line as unique anchor, not absolute byte position)
4. **Verify** with a second scan run immediately after — confirm subsection now falls within correct parent

**Critical:** Do NOT attempt to fix by patching from the wrong position outward. The file state is already corrupted — always read fresh from disk before computing the fix. See `hermes-agent-skill-authoring` pitfall 32 for the positional slicing pattern.

**Common Root Causes**

| Cause | Fix |
|-------|-----|
| Anchor `\n\n\n` also appears in earlier section | Use unique text anchor (section header + first line) instead of position |
| Section end marker `find("---")` matches decorative `---` inside section | Use `\n\n---\n\n\n` with surrounding newlines |
| Sequential patches shift absolute positions | Atomic write: compute all positions in memory, write once |
| Section close computed from wrong section number | Use absolute position from original file read, not computed offset |

### Detecting Duplicate Top-Level `##` Section Headers

The scan above detects subsection (`###`) placement errors. But top-level `##` section headers can also be duplicated — two consecutive identical `## Framework: X` headers with no content between them — producing a section that appears to declare itself twice. This is invisible to reading because the human reads section numbers in logical order, not file position order.

**Real case:** purpose-finder v4.90.1 had two consecutive `## Framework: Family-of-Origin Patterns and Purpose Formation` headers at positions 38637–38698. The duplicate was found by listing all `##` headers in file-position order and noticing they appeared as consecutive entries with no intervening content. The gap between the correct Family section and the next section (Experimentation) was only ~150 chars — consistent with a duplicate that added 0 meaningful content but consumed a section declaration slot.

**Detection:** After any patch that adds, moves, or renumbers a `## N、` section header, run this scan:

```python
import re, pathlib
content = pathlib.Path(skill_path).read_text()
headers = [(m.start(), m.group(0)[3:].strip()) for m in re.finditer(r'\n## [^\n]+', content)]
# Print headers in file order — consecutive duplicates will appear adjacent
for i in range(1, len(headers)):
    if headers[i][1] == headers[i-1][1]:
        print(f"DUPLICATE HEADER at pos {headers[i][0]}: {headers[i][1][:60]}")
# Also flag: two ## headers with <200 chars between them (possible embedded duplicate)
for i in range(1, len(headers)):
    gap = headers[i][0] - (headers[i-1][0] + len(headers[i-1][1]) + 4)
    if gap < 200:
        print(f"TIGHT GAP ({gap} chars) between '{headers[i-1][1][:40]}' and '{headers[i][1][:40]}'")
```

**Fix:** Collapse two consecutive identical headers into one. Preserve the reference link if one followed the second header.

**Also run after any condensation or migration** — these operations can accidentally leave behind a duplicate header from the original section's closing pattern.

## Verification Checklist

- [ ] Every subsection's position falls within its declared parent section's byte range
- [ ] No subsection reports "ORPHAN: outside all sections"
- [ ] No two different-numbered subsections with the same parent (unless intentionally shared)
- [ ] No duplicate top-level `##` section headers (two consecutive identical headers)
- [ ] No tight-gap pairs (<200 chars between consecutive `##` headers)
- [ ] Section header scan shows no merged/embedded headers
- [ ] File size ≤ 100,000 chars