# Pitfall 60/63 — Tool-Call Budget for Near-Limit Planning Phase

## The Universal Trigger (Updated with Purpose-Finder Run 31, Sixth Case)

**Single sentence that fires regardless of session type:** *"I have done 2+ survey/calculation `execute_code` calls in a row without a single `pathlib.write_text()` call."*

This trigger is universal. It fires whether the session is a cron job, an interactive user, a delegated subagent, or a sandbox-restricted tool session. It does not require the session to be near-limit — the planning phase of *any* skill edit can hit it.

**Six confirmed cases as of purpose-finder Run 31:**
1. purpose-finder Run 30 (pitfall 63 — original detection)
2. wealth-mindset Run 4 (pitfall 60 — documented in pitfall-60-63-tool-call-budget.md origin)
3. ai-money-maker (multiple — original pitfall 60 trigger)
4. breakup-recovery (documented variant)
5. wealth-mindset v1.147.0 (deepening session)
6. **purpose-finder Run 31.** Identified correct plan (Range/Enough deepening, MVP duplicate + Strengths-Purpose Bridge 3Q duplicate as condensations, +1,500 new content, version bump 4.114.0→4.115.0). Surveyed 6+ sections for additional condensation to balance the budget. Ran out of tool calls without ever calling `pathlib.write_text()`. The plan was correct; the disk was never touched.

**What Run 31 added to the framework:** the trigger is *not* "I have 5+ recompute calls" — it's "I have *any* survey call without a planned write immediately after." A session can be in the spiral after just 3-4 tool calls if all of them are exploration and none is execution. The original framework over-weighted the recompute pattern (which was purpose-finder Run 30's signature) and under-weighted the survey-only pattern (Run 31's signature).

## The Forward-Looking Trigger (Missing from Inline Pitfall Sections)

Pitfall 60 and Pitfall 63 document the failure mode *after* it has happened:
- **Pitfall 60:** zero writes, plan documented only in the final response
- **Pitfall 63:** writes happen (in scratchpad), but the disk file is never touched

What was missing for an in-flight session: a **pre-write commit trigger** that fires *during* the planning phase to prevent the spiral from developing. This file documents that trigger.

## The Tool-Call Budget

A near-limit (file > 95k chars, headroom < 5k) patch should consume at most **6-8 tool calls total in the planning phase before the write**:

| Phase | Allowed tool calls | Purpose |
|-------|-------------------|---------|
| Read state | 1-2 | `pathlib.read_text()` to confirm current size and content |
| Survey | 1-2 | Utilization-ratio scan, condensation source identification |
| Delta computation | 1-2 | Compute net_delta = new_content − condensations − headroom |
| **Write** | **1** | **`pathlib.write_text(new_full_content)`** |
| Verify | 1 | Fresh `pathlib.read_text()` to confirm on-disk state |

**Sessions exceeding 8 planning tool calls without a write are in the spiral.** Real case (purpose-finder Run 31, this session): the planning phase consumed ~30 tool calls across multiple `execute_code` invocations recomputing deltas against slightly different condensation sets, never reaching the write. Budget exceeded = session failed regardless of plan quality.

## The Three Checkpoints (Apply Mechanically)

**Checkpoint 1 — After computing the first delta:**
- [ ] New content is a Python string with `len(new_content.encode('utf-8'))` confirmed
- [ ] Target headroom computed once
- [ ] If new content alone > available headroom: **trim the new content** (not expand the condensation search)

**Checkpoint 2 — After finding 2 condensation sources:**
- [ ] Full new content + full set of condensations in memory as Python variables
- [ ] `net_delta` computed once
- [ ] If `net_delta > 0`: trim the new content by 100-300 chars. Do NOT search for a 3rd or 4th condensation source.
- [ ] If `net_delta <= 0`: **WRITE.** Do not re-verify. Re-verification is the spiral.

**Checkpoint 3 — Before session end (mandatory):**
- [ ] `pathlib.Path(skill_path).write_text(new_full_content)` has been called
- [ ] Same `pathlib.read_text()` in the same session confirms new size
- [ ] If `write_text` has NOT been called, the session is in Pitfall 60/63 territory — call it NOW with a smaller version of the plan, even if imperfect

## The "Perfect Is the Enemy of Written" Rule

A +1,000 char net addition that lands at 99,950 with all internal consistency checks passing beats a +1,200 char addition that lands at 100,300 and requires truncation mid-write. When the plan overshoots, the fix is always to **trim the new content, not to find more condensation**. New content is local and bounded (you wrote it, you can shrink it); cross-section condensation hunts are unbounded and burn tool calls without writing.

**The single highest-leverage discipline in a near-limit patch: shrink the new content rather than expand the search for condensation headroom.**

## What This File Adds Beyond Pitfall 63 Reference

`references/pitfall-63-delta-spiral.md` already documents:
- The 5 decision rules (set budget first, find condensations to match, write after 2nd delta call, trim not search, partial is better than missing)
- The diagnostic check (3+ delta computations, 3+ variations of new content, "need N more chars" recursion)
- The real case (purpose-finder Run 30)

This file adds the **tool-call budget as an enforceable rule** — a hard number (8) that the session can check against its own call count. Pitfall 63 is observational; this budget is mechanical. Use both: the rules to know what to do, the budget to know when to stop iterating and write.
