# Run 100 New Pattern: Condense-Previously-Reference-Linked → Zero Content Loss

> Captured from: ai-money-maker v3.97.0 (Run 100). Session: 2026-05-31. Skill: hermes-agent-skill-authoring.

## The Discovery

Section 97 in ai-money-maker (`## 九十七、AI + 县城蓝领经济 Season 2`) was 2,729 chars inline, but the full content already existed on disk as `references/ai-county-blue-collar-season2.md` — a complete, well-structured reference file written during a prior session. The inline version had rich content (4 subsections + verification checklist), but the key realization: since the reference file exists and is complete, condensing the inline version loses **nothing**.

This unlocked a pattern: **near-limit headroom + a reference-linked section = safe condensation with no content loss**.

## The Operation

| Step | Action | Delta |
|------|--------|-------|
| 1 | Condense section 97 (already reference-linked): 2,729 → 656 chars | −2,073 |
| 2 | Expand section 22 (Run 100 target): add 7 freelance prompt templates | +968 |
| 3 | Version bump: 3.85.0 → 3.97.0 | +18 |
| **Net** | | **−1,087** |

**Before:** 99,307 chars (headroom 693)
**After:** 98,204 chars (headroom 1,796)

## Why This Is Different from the Condense-then-Expand in Run 175

Run 175's condense-then-expand worked because the target section's content was already fully covered by the reference file — but the session didn't know that ahead of time. It inferred coverage by reading the reference file and confirming it contained the same material.

**Run 100's pattern is cleaner:** the section being condensed was **already reference-linked** in the original file. The reference file existed at the time of the operation — the skill had been using the `→ Full content: [ai-county-blue-collar-season2.md]` link for some time. Condensing was zero-risk because the reference file was already known-complete.

**Distinction:** Run 175's condense-then-expand was discovery-driven (did the reference cover the section?). Run 100's pattern is certainty-driven (the reference file already exists and is known complete).

## The Pre-Condensation Checklist

Before condensing any section to free headroom:

1. **Reference file exists on disk** — `pathlib.Path(skill_dir / "references" / filename).exists()` returns True
2. **Reference file is complete** — not a stub, has substantive content matching the inline section
3. **`old_string` = exact section block** — from `## N、` header to the next `## N、` header, extracted via positional find, not regex
4. **`content.count(old_string[:50]) == 1`** — confirms no other section has this header text
5. **Both replacements computed from same original `content` snapshot** — never modify `content` and then compute positions from it
6. **Atomic write** — `shutil.move("/tmp/temp.md", skill_path)`, not sequential patches

## Why Prefer Reference-Linked Condensation

The generic condense-then-expand pattern (Run 175) requires reading the reference file to confirm coverage before committing. The reference-linked condensation (Run 100) **skips the confirmation step** — because the skill already uses the `→ Full content:` link, the reference file's completeness is already trusted.

The only additional step: verify the reference file on disk is not a stub (e.g., `<500 chars, or just a header with no body). If the reference file looks complete, proceed.

## Headroom Outcome

| Metric | Before | After |
|--------|--------|-------|
| File size | 99,307 | 98,204 |
| Headroom | 693 | 1,796 |
| Section 97 size | 2,729 | 656 |
| Section 22 size | 1,391 | 2,359 |
| Version | 3.85.0 | 3.97.0 |

## Related Patterns

- `references/cron-cyclical-research-pattern.md` — the broader migrate-first pattern for near-limit cyclical jobs
- `references/condense-add-atomic-pattern.md` — atomic condense+add as single write
- `references/iterative-headroom-recovery.md` — iterative headroom recovery when first plan exceeds limit