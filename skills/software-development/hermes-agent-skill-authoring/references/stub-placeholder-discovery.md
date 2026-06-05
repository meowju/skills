# Stub-Placeholder Discovery: When Headroom Blocks the Target, Find the Thin Stub

> Real case: wealth-mindset Run 8, v1.87.0. Cyclical cron job with rotating research verticals called for "Bezos deepening." File at 96,809 chars (3,191 headroom). Bezos section inline body: 5,234 chars with an existing reference link. Estimated expansion: ~6,000 chars. Size gate: 96,809 + 6,000 = 102,809 → would exceed 100k by ~1,015. Git checkout restored original immediately.

## The Pattern

Cyclical cron jobs follow a fixed rotation (e.g., Musk → Bezos → Naval → Buffett → Power → Income → Risk → Tax → repeat). Each run has an intended target. When headroom is insufficient for the intended target, the default response is to conclude with `[SILENT]` (no content added, no version bump) — which is a wasted run.

The correct response: **search for thin placeholder stubs in the skill before concluding.**

## What Is a Thin Placeholder Stub?

A section that consists only of:
- An introductory sentence or two
- One or more `→ Full content:` reference links
- No substantive inline content

Example (the Tax Optimization Deep Dive stub, 468 chars total):
```markdown
## Tax Optimization Deep Dive: The Advanced Tactics

This section covers the tax strategies that matter most once you're earning
significant income or building meaningful assets. Each is legal, well-established,
and dramatically underused by people who don't know they exist.

→ Full content: [references/tax-optimization-deep-dive.md](references/tax-optimization-deep-dive.md)
→ Full content: [references/trust-wealth-planning.md](references/trust-wealth-planning.md)
```

Compare to a well-covered section (Bezos, 5,234 chars inline body with a reference link also on disk). The Bezos section is already substantive — expanding it further is low-value. The stub is substantive by reference only — expanding it inline is high-value.

## Decision Sequence for Cyclical Cron Jobs

1. **Size gate first:** `len(pathlib.Path(skill_path).read_text())` before anything else
2. **Estimate new content size** (don't approximate — count chars of the planned addition)
3. **If headroom insufficient for intended target:**
   a. Scan all section sizes for a thin placeholder stub (<1,000 chars, reference-link-only body)
   b. If found: expand the stub instead (switch the run's focus)
   c. If none found: condense the largest well-covered section that has a companion reference file
4. **Version bump** even if the target changed — the run produced content
5. **Verify headroom ≥500 chars** before writing; if not, migrate a section first

## Why Not Condense the Bezos Section?

Bezos had 5,234 chars inline with a companion `references/bezos-frameworks.md` on disk containing ~8,900 chars of full content. Condensing the inline body (replacing it with a 1-2 paragraph summary + the reference link) would free ~3,000 chars — but that requires a full condensation operation, which is risky on the first attempt. The stub expansion was a simpler, lower-risk operation that achieved the same headroom goal.

## The Stub Expansion Result

- Target section: Tax Optimization Deep Dive (468-char stub)
- Expansion: 3,734 chars (4 subsections with scripts)
- Final size: 99,385 chars | Headroom: 615 chars
- Version: 1.87.0 → 1.88.0
- Outcome: productive run instead of `[SILENT]`

## Anti-Pattern: Concluding with `[SILENT]`

A cyclical cron job that ends with `[SILENT]` because "all topics exist" or "headroom insufficient" is a failed run. The skill's reference library is an asset to be remined; the stub-placeholder discovery is the tool. Rule: **never conclude a cyclical run with `[SILENT]` when a placeholder stub exists.**

---

Related: `references/cron-cyclical-research-pattern.md` (existing), `references/headroom-safety.md` (existing)