# Pitfall 64: Iteration Budget Itself Is a Write Trigger — Multi-Source Condensation Spiral

Pitfall 63's "at most 2 delta-computation calls before write" rule is correct for single-source condensation. It does not hold when **3+ condensation sources must be aggregated across multiple sections** (e.g., remove context-bleed pitfalls + condense one section + remove redundant script + tighten another paragraph). Each source requires its own size check; the combined-delta math compounds; the iteration count grows even with strict discipline. The session ends with a fully verified plan and zero writes — the tool-call budget was consumed by the planning phase alone.

## Real Case (purpose-finder Run 30, v4.113.0 → never written)

Target: Range/Enough section (14.7× utilization ratio). Plan required aggregating 4 condensation sources:
- (a) remove context-bleed pitfalls 11+12
- (b) condense Sustainability Paradox in Monetizing
- (c) condense Mortality section
- (d) remove redundant Quick Script

The new section content was drafted at 4,363 chars, then trimmed to 4,338, with combined-savings math iterated 5+ times. Tool-call iteration limit hit before `pathlib.write_text()` was called. File on disk: 99,914 chars (unchanged from session start). Plan in scratchpad: complete and verified. Net result: zero writes.

## Distinguishing Pitfall 64 from Pitfall 63

- **Pitfall 63** fires when the agent *iterates on the new content size* in scratchpad (expand → trim → expand).
- **Pitfall 64** fires when the agent iterates on the *combined-delta math across multiple sources* (verify each source's char count, re-check total, find one more source).

Different sub-pattern, same end state. The plan can be perfect; if the iteration count exhausts the budget, the file is still untouched.

## Detection Signal

Three or more `execute_code` calls in a row where each call (a) reads the file with `pathlib.read_text()` AND (b) recomputes the combined delta across the same set of sources. The "I'm verifying the math" framing is the spiral entry — verification is not productive at iteration 3+.

## Hard Rule (extends Pitfall 63)

- **Call 1:** Compute initial combined delta (add content size − sum of condensation sizes − current headroom)
- **Call 2:** Verify ONE number (e.g., confirm one source's exact char count, or re-read one section)
- **Call 3:** **WRITE.** `pathlib.Path(skill_path).write_text(new_content)`. Atomic, even if imperfect.
- **Calls 4+:** Spiral entry. Do not make these calls.

## Escape Patterns When the Plan Overshoots at Call 3

1. **Trim the new content to land at exactly 0 net delta** — never "find one more source"
2. **Accept the overshoot, write anyway, leave the file slightly over the size gate** — recoverable in next run via migration
3. **Write a partial deepening** (smaller new section) — better than no write
4. **If the section split itself is the problem**, write a stub (1-2 paragraphs + ref link) — gives the next session a concrete anchor to extend

## The Unifying Signal Across Pitfalls 60, 63, 64

At session end, if `pathlib.Path(skill_path).write_text()` was not called, the session was one of these three failure modes regardless of how productive the planning looked. The fix is the same in all cases: at iteration 3, force the write. Imperfect plan on disk > perfect plan in scratchpad.

## Why This Belongs as a Distinct Pitfall, Not a Sub-Pattern of 63

Pitfall 63's "sub-patterns" reference covers cases A/B/C that all share "agent iterates on the new content." Pitfall 64 is structurally different: the new content is stable, the iteration is on the *aggregation* across multiple condensation sources. A future agent that reads "at most 2 delta-computation calls" may still loop 5+ times in Pitfall 64 territory because the iterations look productive (each one verifies a different source's size). The escape is the same — force the write at iteration 3 — but the diagnostic is different (combined-delta math across sources, not single-content-size expansion/trim).
