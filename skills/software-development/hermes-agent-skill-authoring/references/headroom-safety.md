# Headroom Safety Discount — Near-Limit Size-Gate Formula

## The Problem

When SKILL.md is within ~3,000 chars of the 100,000-char limit, inserting a "net-new" subsection appears to fit based on the naive estimate — but the actual final size exceeds the limit because:

1. **Anchor consumption is asymmetric:** The old_string you replace is just the insertion point (e.g., `the next relationship.\n\n→ Full content:` = ~50 chars), but your new subsection is 1,000+ chars. Net-new ≈ new_content - anchor_length, not just new_content.
2. **Version bump adds 8–10 chars** on top of the net-new delta.
3. **Blank-line normalization** can add 2–4 chars.
4. **Any inline formatting adjustments** (e.g., adding `### ` headers, `**` bold markers) adds chars beyond the plain-text estimate.

## The Rule

```
Safe max insertion = headroom × 0.40
```

When headroom < 3,000 chars, apply a **60% safety discount** to your new content estimate. Target max new content = `headroom × 0.4`.

If the content you want to add exceeds this, **migrate a section to `references/` first** — remove 3,000–15,000 chars to restore headroom, then insert freely.

## Real Cases

### Case 1: breakup-recovery v4.29.0 → v4.30.0

- File at 97,828 chars → headroom **2,172**
- New subsection estimated 1,050 chars → passed naive size check
- Replacement anchor: `the next relationship.\n\n→ Full content:` (50 chars) consumed
- Python replace showed **final size: 100,027** (+1,999 net — not +1,050)
- Root cause: estimated 1,050, but net-new = 1,050 - 50 (anchor) + 10 (version bump) = 1,010 → over by ~800
- Fix: recomputed safe max = 2,172 × 0.4 = **869 chars** → trimmed subsection to ~870 chars
- Final: 99,621 chars (379 headroom)

### Case 2: ai-money-maker v2.77

- Headroom 3,470 → safe max = 3,470 × 0.4 = **1,388 chars**
- Content needed: 2,500 chars (3 cases with numbers)
- Decision: pulled from existing `references/` instead of fresh research
- Result: 3 cases + synthesis = within safe max

### Case 3: ai-money-maker v2.70

- Three sequential patches all passed individual headroom checks (each ~500–800 new chars)
- Combined headroom was 1,076
- Three patches netted +1,900 chars → validator showed **100,296** (296 over)
- Root cause: sequential patches each reported "fits" but their net deltas accumulated past the limit
- Fix: single combined write + proactive split to `references/`

### Case 5: purpose-finder v4.110 — Exhausted Headroom State (88 chars remaining, migration-required)

- File at 99,912 chars, headroom 88 chars after Run 25 expansion
- Edit itself was valid (expanded 5-patterns with Shannon/Achterberg research), net delta within pre-edit budget
- But post-write headroom = 88 means even a version bump on next run requires migration FIRST
- Lesson: Below 200 chars headroom = migration-required state. Any content addition, even 50 chars, must be preceded by moving a section to references/. In a restricted session with no execute_code, a near-limit file (<500 headroom) should NOT be touched for boundary verification — false-positive patches consume precious headroom with no recovery path. Defer to a full-tools session.

### Case 4: purpose-finder v4.77 — Boundary Audit False Positives Triggered 11 Wasted Patches

- File at 99,973 chars (27 headroom) — already near-limit
- A boundary audit using `\s*\n##` regex flagged 11 positions as corruption (single-newline before `##`)
- String-operation verification confirmed all 11 were actually correct — each had `\n\n` before the header
- Acting on the regex output would have required 11 patches on a file with 27 chars of headroom — each patch would have added content (fixing the "corruption"), immediately exceeding the limit
- **Lesson:** A false-positive boundary audit on a near-limit file can cause catastrophic over-write attempts. Always verify boundary issues with string operations before composing any patch on a file with <500 headroom.

## The Size-Gate Script (Copy-Paste)

```python
import pathlib

skill_path = "/opt/data/skills/productivity/<name>/SKILL.md"  # adjust
content = pathlib.Path(skill_path).read_text()

current_size = len(content)
headroom = 100_000 - current_size

print(f"Size: {current_size:,} / 100,000")
print(f"Headroom: {headroom:,}")

if headroom < 3000:
    safe_max = int(headroom * 0.4)
    print(f"⚠️ Near-limit — apply 60% safety discount")
    print(f"Safe max insertion: ~{safe_max:,} chars")
else:
    safe_max = headroom - 500  # keep 500-char buffer
    print(f"Safe max insertion: ~{safe_max:,} chars")

# When estimating new content:
estimated_new = 1050  # your new content estimate
print(f"\nEstimated new: {estimated_new:,} chars")
print(f"Headroom after (naive): {headroom - estimated_new:,}")
print(f"Headroom after (safe): {headroom - safe_max:,}")

if estimated_new > safe_max:
    print(f"\n❌ TOO LARGE — migrate a section to references/ first or trim to {safe_max:,} chars")
```

## Headroom Thresholds

| Headroom | Safe Max (×0.4) | Action |
|---|---|---|
| >10,000 | 4,000+ | No restrictions |
| 5,000–10,000 | 2,000–4,000 | Minor caution |
| 3,000–5,000 | 1,200–2,000 | Moderate caution |
| 1,000–3,000 | 400–1,200 | Apply safety discount |
| 500–1,000 | 200–400 | Apply safety discount; do not patch without Python available |
| 200–500 | 80–200 | Migration strongly recommended before adding content |
| <200 | <80 | **Migration-required.** Do not attempt any content addition. Version bump alone may fail. |

## The Only Safe Multi-Patch Pattern

When headroom < 3,000 and you need multiple changes, compute ALL deltas in memory first:

```python
import pathlib

skill_path = "/opt/data/skills/productivity/<name>/SKILL.md"
content = pathlib.Path(skill_path).read_text()
original_size = len(content)
headroom = 100_000 - original_size

# Compute every change's net delta
delta1 = len(new_content_1) - len(anchor_1)      # e.g., +840
delta2 = len(new_content_2) - len(anchor_2)      # e.g., +620
version_bump = len(new_version_str) - len(old_version_str)  # e.g., +1

total_delta = delta1 + delta2 + version_bump
print(f"Total delta: {total_delta:,}, headroom: {headroom:,}")

if total_delta > headroom:
    print("FATAL: combined delta exceeds headroom")
    # Migrate a section to references/ first
else:
    # Safe to write
    new_content = content.replace(anchor_1, new_content_1, 1)
    new_content = new_content.replace(anchor_2, new_content_2, 1)
    new_content = new_content.replace(old_version, new_version, 1)
    assert len(new_content) <= 100_000
    pathlib.Path(skill_path).write_text(new_content)
```