# Near-Limit Patch Overshoot — Prevention and Recovery

Real case: purpose-finder v4.52→4.53. File at 94,873 chars with 5,127 headroom. Added 3 decision frameworks (OODA Loop, Eisenhower Matrix, 10-10-10 Rule). Estimated 3,300 chars of new content. Patch landed at 100,285 — 285 over the hard limit. Recovery required a second condensation patch.

## The Mechanism

The `patch` tool reports success even when the file exceeds 100k post-write. There is no post-patch size validation — it only checks that the `old_string` was found. The file silently crosses the limit.

First-patch overshoot is especially dangerous in multi-session skills because:
- The patch tool's byte-count estimate from `len(new_content)` is approximate (Unicode normalization, whitespace handling)
- Adding a section also shifts all section boundaries, making the actual delta larger than the new content alone
- A second patch attempt on the now-over-limit file fails with "content exceeds 100k" — leaving the skill in a broken state

## Prevention Gate

```python
import pathlib
path = "/opt/data/skills/productivity/purpose-finder/SKILL.md"
size = len(pathlib.Path(path).read_text())
estimated_delta = len(new_content)  # measured from the new content string itself
assert size + estimated_delta < 98_000, f"Need migration first: {size+estimated_delta:,} > 98k"
```

Use 98k as the gate, not 100k — gives a 2k safety margin for boundary-shift errors and Unicode normalization differences between Python string length and patch tool's internal computation.

## Recovery Pattern

Do NOT attempt incremental micro-condensations. Take the largest block and cut it 40-60% in one pass.

Real case recovery:
- OODA Loop: 1,349 chars → 586 chars (57% reduction)
- Eisenhower Matrix: 566 chars → 310 chars (45% reduction)
- Total freed: 1,019 chars
- Final size: 99,268 (732 headroom)

The 57%/45% cuts were aggressive but landed cleanly in a single follow-up patch. Three 15% micro-trims would have required three separate patch calls with three opportunities for new errors.

## Rule

When headroom is under 5k and the addition is more than 2k chars, always run the size gate before patching. If gate fails, migrate a section to `references/` first, then patch.