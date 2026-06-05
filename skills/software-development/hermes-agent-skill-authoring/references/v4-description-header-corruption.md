# Reference Link Description Header Corruption (V4)

## The Pattern

A `→ Full content:` link description ends with text that is structurally a markdown section header:

```
→ Full content: [mentalization.md](references/mentalization.md) — Fonagy & Bateman's research, psychic equivalence / teleological / pretend modes, and how mentalization capacity predicts grief processing ## Breaking the Attachment Pattern — Earned Security as the Goal
```

The `## Breaking the Attachment Pattern — Earned Security as the Goal` portion is *description text*, not a section header — but it renders as one because it starts with `## `. The entire following section body becomes embedded prose inside the parent section with no visible separation.

## Why This Is Invisible to Reading

The human reader sees a section header on the next line. The eye skips over the `## ` embedded in the description line because it reads as part of the description. The structural corruption is only detectable via:

```python
import re, pathlib
content = pathlib.Path(skill_path).read_text()

# Scan for "## " inside reference link description lines (V4 pattern)
# A legitimate section header on its own line starts with \n##
# If "## " appears mid-sentence on a line that also has "→ Full content:",
# the ## is part of the description text, not a real header
v4_candidates = []
for m in re.finditer(r'→ Full content: [^\n]+## [^\n]+', content):
    line_start = content.rfind('\n', 0, m.start()) + 1
    line = content[line_start:content.find('\n', line_start)]
    if '→ Full content:' in line:
        v4_candidates.append((m.start(), line[:80]))

print(f"V4 candidates: {v4_candidates}")
```

## Detection Checklist

1. A section that should be a subsection (e.g., `### Breaking…`) appears as a top-level `## ` in the header scan
2. The section count via `re.findall(r'\n## [一二三四五六七八九十]+、')` is lower than expected (phantom header not counted)
3. A gap >3,000 chars between two normally-sized sections (<2k each) — the phantom header consumed an entire section body as inline text

## Fix

Replace the description text before `## ` with properly punctuated ending, then insert the section header as a standalone line:

```
# Before (corrupt):
…predicts grief processing ## Breaking the Attachment Pattern — Earned Security as the Goal
> *Y...

# After (fixed):
…predicts grief processing.

## Breaking the Attachment Pattern — Earned Security as the Goal

> *Y...
```

**Real case:** breakup-recovery v4.94 — mentalization.md link at pos ~15,141 had a 3,599-char "Breaking" section consumed as prose inside the Internal Working Model section. Fix saved 64 chars and restored the section to visibility. File: 99,992 → 99,928 chars.

## Prevention

When writing reference link descriptions, never use `## ` or `### ` syntax inside the description text. If you need to reference another section's title, use plain text: `see also "Breaking the Attachment Pattern"` — not `## Breaking...`.