# V2 Mass-Fix + New Content: Combined Delta Pattern

> Extracted from: purpose-finder Run (cron job) — v4.67.0 → 4.69.0

## What Happened

**Initial state:** purpose-finder SKILL.md at 95,637 chars / 4,363 headroom.

**Audit results:**
- 33 V2 malformed links: `[references/X.md](references/X.md)` — link text has `references/` prefix, visually correct but not standard form
- 1 boundary corruption: `→ Full content: [motivation-and-drive.md](references/motivation-and-drive.md)\n## Framework: The Psychology` — missing blank line before `##`
- A new subsection planned: "Cross-Cultural Purpose" (~1,397 chars)

**Headroom analysis:**
- V2 fix alone: −362 chars → 4,725 headroom
- New subsection alone: +1,397 chars → would need 4,725 headroom, only had 4,363

If treated sequentially (V2 fix first, then subsection), the size gate blocks the subsection because individual deltas are checked. The correct approach: compute both together.

**Combined delta:** −362 + 1,397 = +1,035 chars. With initial 4,363 headroom: 4,363 − 1,035 = 3,328 remaining. Both operations fit within the original headroom.

**Result:** File at 96,672 chars → 3,328 headroom. Version 4.67.0 → 4.69.0.

---

## The Pattern

When near-limit (>95k chars, <5k headroom) AND planning new content AND audit reveals V2 links:

1. **Fix V2 links first** — they are always present in multi-session skills and always invisible to casual reading. A `[references/` count finds them quickly.
2. **Compute combined delta** — V2 chars freed + new content chars needed. If combined fits in current headroom, proceed atomically.
3. **Build all changes in memory** — V2 fix + content insertion + version bump, all computed from original content simultaneously.
4. **Write once** — atomic `pathlib.write_text()` + `shutil.move()`.

**Why sequential patching fails here:** After V2 fix (−362), headroom becomes 4,725. Then patching the new subsection (+1,397) — the size gate check sees 96,637 + 1,397 = 98,034, which passes. But if the order is reversed (subsection first, then V2 fix), the subsection alone (+1,397) against 4,363 headroom fails the size gate. The combined delta always fits; the sequential order can make it fail.

---

## V2 Link Detection (Correct Pattern)

The critical regex uses `[^()]+` for the URL group — excludes both `(` and `)`. The `[^)]+` variant (common in older versions of this file) captures the markdown `)` as part of the URL, breaking the pattern on any filename with `.md)` suffix. Real case: purpose-finder v4.82.2 session confirmed 36 V2 links using `[^()]+`; the old pattern would have matched 0.

```python
import re
# Correct pattern: [^()] excludes both ( and ), stopping at the markdown )
v2_pattern = r'\[([^\]]+\.md)\]\((references/[^()]+\.md)\)'
matches = list(re.finditer(v2_pattern, content))
print(f"V2 instances: {len(matches)}")
# V2 link: [filename.md](references/filename.md) — bare filename in link text, correct URL
```

**Size freed per instance:** ~11 chars (the `references/` prefix in link text, 9 chars per link × ~1.2 average occurrences)

| Instances | Chars freed |
|---|---|
| 10 | ~110 |
| 33 (purpose-finder) | ~362 |
| 59 (ai-money-maker v3.33) | ~649 |

---

## Boundary Corruption Detection

The boundary corruption (reference link directly followed by `##` header with no blank line) is distinct from V2 links. Detection:

```python
# Find → Full content: links followed directly by ## header
for m in re.finditer(r'→ Full content:[^\n]+\)', content):
    link_end = m.end()
    after = content[link_end:link_end+10]
    if after.startswith('\n##'):
        print(f"Boundary corruption at {m.start()}: {content[m.start():m.end()+40]}")
```

**Fix:** Insert `\n\n` between link `)` and `##` header.

---

## Key Lessons

1. **V2 links are invisible but pervasive.** 33 instances in a skill that had been actively maintained — not a one-time creation error but an accumulation pattern across many sessions.
2. **Combined delta > sequential delta.** When headroom is tight, compute all operations together before deciding whether they fit.
3. **Boundary corruption + V2 fix can both be done in one atomic write** — they don't interfere with each other.

---

## Reference

- File: `/opt/data/skills/productivity/purpose-finder/SKILL.md`
- Commits: `33bd47c` (V2 fix + boundary fix, v4.68.0), prior commit (content addition, v4.69.0)
- Audit: 33 V2 → 0, 1 boundary corruption → fixed, 0 orphans