# Pitfall 63: Delta-Recomputation Spiral — Detailed Walkthrough

## The Pattern in Detail

Pitfall 63 is the failure mode where a session *plans correctly* and *computes correctly* — but never *commits to a single plan and writes it to disk*. The session shows every signal of productive work (planning, computing deltas, scanning for condensation sources) but produces zero on-disk changes.

**Diagnostic check (any one of these means you're in the spiral):**
1. Three or more `execute_code` calls in a row whose output is a "Net file delta:" or "Headroom after:" line
2. The new content string appears in 3+ variations within the same session (slight rewrites each iteration)
3. The phrase "need X more chars of condensation" appears in 2+ consecutive tool-call responses
4. You find yourself drafting a "Plan A vs Plan B vs Plan C" comparison in scratch — the *act of comparison* is the spiral, not the result

## The Anatomy of One Iteration (Anatomy of a Spiral Step)

```
Call N:   print("delta: +2441 chars, overshoots by 671")
Call N+1: (mentally: "I need 671 more chars of condensation, OR shrink the new content")
Call N+2: (search for more condensation sources)
Call N+3: (find one, but only 277 chars)
Call N+4: print("delta: +2164, overshoots by 394")
Call N+5: (mentally: "still not enough, expand the new content to cover the gap")
Call N+6: print("delta: +1654 (with bigger new content), overshoots by -116" - wait, UNDERshoots)
Call N+7: (decide to add even more new content to use the headroom)
Call N+8: print("delta: -342, lands at 99,572")
...repeating until tool-call limit
```

Each iteration's output looks productive. Each is correct math. None writes to disk. The "still over → find more / still under → expand" oscillation is the spiral's signature.

## Real Case (Purpose-Finder Run 30)

**File state:** 99,914 chars, 86 headroom
**Target identified:** Range/Generalists/Enough, 14.7× utilization ratio
**New content drafted:** Hedonic Treadmill + 3-Step Enough Point Practice
**Condensations identified (4):** −1,598 chars

**What the session did (reconstructed from conversation):**
1. Computed initial plan: +1,654 new, −1,598 condense, −86 headroom, net −30 — "lands cleanly"
2. (Iteration 1) Decided to add Forager/Farmer model subsection, recomputed: net +757, "overshoots by 671"
3. (Iteration 2) Searched for additional condensation in Burnett section (Mindmapper Exercise, Prototype Walk) — found not-actually-redundant
4. (Iteration 3) Decided to TRIM new content instead, recomputed: net −342, "safe margin 421"
5. (Iteration 4) Noted the "safe margin 421" looked like dead headroom, recomputed with a richer version
6. (Iteration 5) Got a final plan with 36 chars headroom, decided "too tight, need one more condensation"
7. Hit tool-call limit

**Final disk state:** 99,914 chars (unmodified). Plan was correct at iteration 3 but never written.

## The Five Decision Rules (Inline, For Memory)

1. **Set new content size FIRST, derived from reference file depth, not from headroom math.** "How much unused material is in `references/enoughness-philosophy.md`?" → read it, count unused sections, set new content size = sum of those.

2. **Find condensations to MATCH the budget, not the other way around.** "I need to add 1,500 chars; what condensation sources exist?" is bounded. "I have these condensation sources; how much can I add?" is unbounded and creates the spiral.

3. **Once the plan lands at ≤ 100,000, WRITE. Don't verify "just to be sure."** Re-running the math is not validation. An over-tight landing (e.g., 99,964 with 36 headroom) is still safer than not writing.

4. **If the plan overshoots, the fix is to TRIM the new content, not find more condensation.** New content has natural bounds (what's actually in the reference). Condensation is unbounded (you can always find something).

5. **A 1,100-char subsection that lands cleanly beats a 2,600-char deepening that doesn't get written.** Next run can extend. This run cannot recover a missing write.

## Counter-Examples (When Recomputation IS the Right Call)

The spiral rule has a few legitimate exceptions — *brief* recomputation, not multi-iteration spirals:

- **First-call validation:** Run the delta math once to confirm a plan lands. This is correct.
- **Cross-checking two design options:** "Option A: smaller new content + 2 condensations. Option B: larger new content + 4 condensations." Pick one in one extra call, write in the next. That's 2 delta computations, not 6.
- **Atomic-delta confirmation (Pitfall 58):** When the plan has 3+ operations and you need to verify the combined delta — that's one call, not a loop.

**The legitimate rule is: at most 2 delta-computation calls before the write.** Beyond that, the computation is not serving the write — the write is being deferred to serve the computation.

## Distinguishing Pitfall 63 from Neighboring Pitfalls

| Pitfall | Trigger | Fix |
|---------|---------|-----|
| 58 (atomic-deltas) | Two ops combined overshoot, need to recompute combined delta | Compute combined delta, trim, write once |
| 60 (orphan-tail) | Session exhausts tool calls on reads/analysis, no write | Recognize the limit approaching, write partial |
| 61 (sandbox-persistence) | `str` object error from stale variable name | Use distinct variable name per call |
| **63 (delta-spiral)** | **Session computes deltas correctly, never stops computing, no write** | **Set new content budget from reference depth FIRST, find condensations to match, write after 2nd delta call** |

## Detection Heuristic for the Next Session

At the end of any near-limit editing session, ask:
1. Did I call `pathlib.Path(skill_path).write_text(new_content)` at least once?
2. Did I call `assert len(new_content) <= 100_000`?
3. Did I confirm the new content is on disk via a fresh `pathlib.read_text()`?

If the answer to (1) is no, the session was Pitfall 63. If (1) is yes but (2) or (3) is no, it was Pitfall 60 or 41. If all three are yes, the session succeeded regardless of how many delta-computation calls came before.
