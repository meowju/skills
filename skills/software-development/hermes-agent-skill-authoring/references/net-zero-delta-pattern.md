# Net-Zero Delta Pattern for Near-Limit Skill Files

> When a skill is above 85k chars and headroom is below 2k, adding content by research is blocked — but adding content by redistribution is not. The net-zero delta pattern: condense one section to fund another, without changing total file size.

## The Pattern

1. **Size gate** — if `len(content) > 85,000` and `headroom < 2,000`, net-zero delta applies.
2. **Audit existing sections** for condense candidates — sections with dense scripts, repeated reference links, or verbose tables that can be summarized with a `→ Full content:` pointer.
3. **Condense one section** — replace section body (not header) with 1-2 paragraph summary + reference link.
4. **Add new section** using freed space.
5. **Result:** new content added, total size unchanged or reduced, headroom increased.

## Breakup-Recovery v4.30.0→v4.31.0 Real Case

- File at 99,621 chars, headroom 379.
- **Condense target:** Communication Scripts section (9,911 chars → 2,174 chars, freed 7,737).
- **Condense method:** Move full scripts to `references/communication-scripts.md` (already existed and was already linked — just condensed the body). Replace with 12-paragraph summary covering all key scripts.
- **Addition:** new Dating After Breakup subsection (2,976 chars).
- **Net delta:** −4,761 chars. File went from 99,621 to 94,860. Headroom: 379 → 5,140.
- **Version:** 4.30.0 → 4.31.0.

Key insight: the reference file already existed and was already linked — the work was condensing the body, not creating new reference content. The skill's own `references/` directory was the content asset being rebalanced, not new research.

## When NOT to Use This Pattern

- Fresh research is available and the section genuinely needs new data, not just redistribution.
- Headroom > 5,000 → space for original content; net-zero is unnecessarily complex.
- The section to condense has no existing reference file → condensing requires creating the reference file first, which adds session complexity.
- The condense target is the same section being expanded (self-condense) — this is a signal the section needs restructuring, not redistribution.

## Reference Mining vs. Fresh Research (Cron-Batch Cyclical Jobs)

In cyclical cron jobs where each run picks a research vertical (e.g., ai-money-maker rotating through verticals):
- When web search fails (HTTP 404) and headroom is low → mine existing references for the vertical.
- The skill's `references/` directory is itself a content asset to be remined across cycles, not just a link repository.
- Real case (breakup-recovery Run 4): no new research needed — existing `references/dating-after-breakup.md` (160 lines, 11,954 chars) already had the content. Added a 3-paragraph inline summary + reference link in the body.

## Trigger Conditions

| Condition | Action |
|---|---|
| `100_000 - len(content) < 1_500` AND vertical has existing reference files | Mine existing references |
| `100_000 - len(content) < 2_000` AND a section can be condensed | Net-zero delta: condense + add |
| `100_000 - len(content) < 500` | Emergency condensation: largest section first |
| `100_000 - len(content) > 5_000` | Fresh research OK, no condensation needed |

## Decision Script

```python
import pathlib
path = "/opt/data/skills/<category>/<name>/SKILL.md"
content = pathlib.Path(path).read_text()
headroom = 100_000 - len(content)
print(f"Size: {len(content):,}, Headroom: {headroom:,}")
if headroom < 1500:
    print("→ Net-zero delta pattern applies. Audit sections for condensation.")
elif headroom < 500:
    print("→ Emergency condensation. Find largest section.")
else:
    print("→ Normal addition mode.")
```