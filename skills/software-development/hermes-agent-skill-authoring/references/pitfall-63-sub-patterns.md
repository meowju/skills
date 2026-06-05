# Pitfall 63: Sub-Patterns Beyond the Classic "Plan A vs Plan B" Trap

## Sub-Pattern A: The 30% Size-Estimate Spiral

The classic pitfall-63 case (Run 28) was about indecision between design options. A second sub-pattern emerged in Run 30 that looks different but produces the same no-write outcome: **the agent's mental char-count of a new section is wrong by ~30% in every iteration.**

### Real Case (Purpose-Finder Run 30, Confirmed)

Target section size planned for 1,200 chars. Actual length: 1,683 chars (40% over). Re-planned for 1,400. Actual: 2,058 chars (47% over). Re-planned for 1,610. Actual: 1,646. Re-planned for 1,431. Actual: 1,431 (matched by chance, not by accuracy). Each miscount triggered a "recompute the total plan" call, which revealed a new overshoot, which triggered another recomputation. The miscount was the *cause* of the iteration, not a side effect.

**File state at session end:** 99,914 chars (unmodified). Plan was correct at iteration 2 but never written. The agent was right that the section would need 700-800 net delta; wrong about how many chars the proposed text would take. Each wrong estimate triggered a re-plan, which produced a new (also wrong) estimate, which triggered another re-plan.

### Why This Is Different from "Indecision About Design"

The session had a clear design (add Hedonic Treadmill + Sociometer to Range/Enough section). It was the *measurement* of that design, not the design itself, that kept changing the plan. The agent knew WHAT to write; it kept getting the SIZE wrong.

### Detection

When you type "this section will be ~1,200 chars" and then compute a delta that doesn't match the new total, ask: did I actually `len()` the string, or did I count in my head?

**Heuristic:** in-head char-counting has a 30-50% error margin for multi-paragraph content. The error compounds across multi-section rewrites: 3 sections with 40% errors = plan could be 2x off from reality.

### Fix (Mandatory Before Any Non-Trivial Section Write)

```python
new_section = """[content here]"""
print(f"Actual size: {len(new_section.encode('utf-8'))} chars")
# If actual > expected, TRIM, not REPLAN
if len(new_section) > expected_budget:
    # Cut from the end of the longest paragraph until size matches
    # Do NOT recompute the total plan budget from the corrected section size
    pass
```

**Rule:** the assertion is one extra call. The spiral is 5+ calls. The arithmetic is one extra line. The miscount is unbounded. Always do the arithmetic before the planning math.

### Real-Case Distillation (For Memory)

The most concise lesson from Run 30: **"in-head char-counting" is the spiral trigger as often as "in-decision design" is.** The fix is identical (one extra `len()` call), but the detection signal is different — the agent isn't comparing plans, the agent is comparing the same plan against different (wrong) char estimates.

## Sub-Pattern B: The "Plan A vs Plan B vs Plan C" Trap

Drafting a multi-option comparison in scratch IS the spiral, not the prelude to a decision. The act of comparison produces more options (Plan D, E, F) and the decision never gets made.

### Detection

- If you find yourself typing "Plan A:" and "Plan B:" in the same `execute_code` call, you are already in the trap.
- Two `execute_code` calls with separate plans = the trap.
- One `execute_code` call choosing between two options = OK.

### Fix

Stop. Pick the simplest plan that lands at ≤100,000. Write it. Iterate later. The next run can revise. This run cannot recover a missing write.

### Why This Sub-Pattern Matters

Even when the agent knows the design (sub-pattern A is absent), the comparison reflex creates a new failure mode: the agent has 3 valid plans, computes 3 deltas, sees one is 5% tighter than another, decides to find a 4th plan that combines the best of all 3, never writes. The fix is to recognize that "good enough to write" beats "perfect to think about."

## Sub-Pattern C: The "I Need N More Chars" Recursion

When the agent's mental response to "overshoots by 360 chars" is "let me find 360 more chars of condensation," it triggers a search of the entire skill for any sub-element that can be removed. This search is unbounded — there is always *something* that could be condensed — and it burns tool calls without writing.

### Real Case (Run 30)

After computing "net +377, overshoots by 291," the agent searched for Quick Script trims, Self-Compassion subsection trims, then considered removing pitfalls 7+10 entirely. Each search yielded smaller gains than expected (-23 chars, -24 chars, -79 chars). The agent never reached the "actually just trim the new content" decision.

### Fix

When the plan overshoots by ≤500 chars, **the default response is to TRIM THE NEW CONTENT, not find more condensation.** New content has natural bounds (what's actually in the reference file). Condensation is unbounded (you can always find something). The search itself is the spiral, not the answer.

**Hard trigger (Run 30 case):** the moment you compute a residual like "overshoots by 360 chars — need more condensation," STOP the search and trim the new content. Cutting 400 chars from a 2,879-char new section to land at 99,957 (43 headroom) is a clean write; finding one more 360-char condensation in a *different* section is a spiral step. **Rule: any "need N more chars" sentence is the last delta-computation call before the write.**

## Decision Rule That Unifies All Three Sub-Patterns

Each sub-pattern has a different trigger:
- A: wrong size estimate → re-plan
- B: indecision between designs → re-compare
- C: "need N more chars" → search for more condensation

Each has the same fix: **one extra `len()` or "pick the simplest, write it" call BEFORE the second planning call.** The unifying rule:

> **At most 2 delta-computation `execute_code` calls before the `pathlib.write_text()` call.** Beyond that, the computation is not serving the write — the write is being deferred to serve the computation.

This is the single most important rule for pitfall 63. The 5-decision-rule list in the main SKILL.md expands on *what* to do; this rule expands on *when* to stop thinking and start writing.
