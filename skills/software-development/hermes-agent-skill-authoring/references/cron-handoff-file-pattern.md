# Handoff File: State Machine for Mature Cyclical Cron Skills

> When a cyclical cron skill passes ~20 runs, the original prompt template ("Run 1: X, Run 2: Y, repeat deeper") no longer reflects reality. This reference codifies the handoff file as the de facto state machine for skill evolution past the original rotation.

## The Problem

Cyclical cron skills (ai-money-maker, wealth-mindset, breakup-recovery, purpose-finder) follow a rotating-verticals instruction. By Run 20-30:

- All original verticals are already covered (often multiple times)
- Headroom has shrunk to 1,000-5,000 chars
- Each run's "what to add" decision has to be re-derived from scratch
- The next agent has no clean source of truth for "what should I work on?"

The wrong responses observed across runs:
- "All covered, skip" → silent no-op, headroom permanently unused
- Re-derive the entire state by re-reading every section header → wastes 5-10 tool calls per run
- Re-attempt verticals that were completed 30 runs ago → duplicate work

## The Handoff File Mechanism

Every cyclical cron skill should maintain a `references/cron-next-run-handoff.md` file that captures the state machine. Each successful run updates it.

**Required fields (update every run):**

| Field | Why It Matters |
|-------|----------------|
| File size + headroom | Next run's size-gate. Without this, the next run re-derives it |
| Section count + version | Drift detection — confirms the run actually landed |
| Last run's section + reference path | Avoid re-doing recent work |
| 2-3 recommended next verticals | The actual source of truth for "what next" |
| Known structural issues (V2 links, version drift) | Prevents the next run from re-discovering pre-existing problems |
| Headroom trend (rising/falling/stable) | Tells the next run whether to add, condense, or migrate |

**Reference template:**

```markdown
# Cron Next Run Handoff

> Session state captured at Run N (vX.Y.Z). Next cron invocation reads this before touching SKILL.md.

## Current State
- File: skills/<category>/<name>/SKILL.md
- Version: X.Y.Z
- Size: 96,575 chars
- Headroom: 3,425 chars — TIGHT (next migration may be required)
- Sections: 87 (一 through 一百零二)
- Reference files: 120 total (+1 new: <last-run-ref>.md)
- Headroom trend: falling (94,528 → 96,575 over last 3 runs)

## Run N Changes (vX.Y.Z)

**New section added:** <number>、<title>

**Content summary:**
- <2-3 bullets describing what was added>

**Reference file:** `references/<ref>.md` (<N> chars) — <one-line summary>

**Net delta:** +2,047 chars (94,528 → 96,575)
**Headroom:** 5,472 → 3,425 chars

## Recommended Verticals (Next Run)
- Run N+1: <vertical 1> — <rationale: why this fills a gap>
- Run N+2: <vertical 2> — <rationale>
- Run N+3: <vertical 3> — <rationale>

## Known Issues
- V2 malformed links: 109 (pre-existing, deferred to maintenance pass)
- Inline version (v4.5.17) vs git tag (v4.2.5) mismatch — pick one next pass
- Section 一百零二: inline <2,500 chars, ref 3,761 chars — ratio 1.5×, low deepening yield

## Next Section Number
一百零三
```

## Why This Is Class-Level (Not Session-Specific)

Every mature cyclical skill (ai-money-maker Run 217+, wealth-mindset Run 100+, breakup-recovery, purpose-finder) eventually reaches the state where the original template is exhausted. The handoff file is the *only* mechanism that lets the next session pick up cleanly without re-discovering the structural state.

Without a handoff file:
- Run 218 re-derives that headroom is 3,425 (2-3 tool calls)
- Run 218 re-discovers which verticals are covered (3-5 tool calls)
- Run 218 picks a vertical that was completed Run 215 (wasted work, or worse, duplicate section)

With a handoff file:
- Run 218 reads the handoff, gets state + 3 recommendations in one call
- Run 218 picks the top recommendation, validates it still fits, writes
- Total state-discovery overhead: 1 tool call instead of 6-8

**Real case (ai-money-maker Run 217):** The skill prompt said "Run 1: AI Old Masters, Run 2: B2B Sales, Run 3: Vertical AI..." — by Run 217, all 8 original verticals had been covered multiple times. The handoff file's "Recommended Verticals" section was the actual source of truth for what to add, not the prompt. The session picked "AI 知识产品化 2.0 (newsletter/课程/ebook)" because the handoff noted that "high-net-worth personal knowledge products" was a gap, even though the prompt template's Run N no longer corresponded to any topical coverage.

## Bump Protocol — Two Commits, One Atomic Skill Update

Update the handoff file in a **separate commit** after the SKILL.md commit:

1. Commit 1: SKILL.md changes + new reference files (the actual skill update, atomic)
2. Commit 2: handoff file update (state machine advance)

This preserves granular git history (you can `git log --oneline` to see exactly when state advanced) without breaking atomicity of either operation. Each commit is self-consistent — if you `git checkout` commit 1 alone, you get the old handoff + new skill; if you checkout commit 2 alone, you get the new handoff + old skill.

**Anti-pattern:** Combining both into one commit loses the ability to bisect state-machine advances vs. content updates.

## Update Triggers (When to Write the Handoff File)

Write the handoff file:
- ✓ After every successful SKILL.md content addition (version bump + section added)
- ✗ NOT after a no-op run (skip if you did nothing)
- ✗ NOT during a run (only at the end, after the commit)
- ✗ NOT with a separate pre-write update (the pre-write state is speculative; only post-commit state is authoritative)

## Headroom Trend Tracking

Track headroom across the last 3-5 runs. The trend signals what kind of run to do next:

| Trend | Next Run Should |
|-------|-----------------|
| Falling (each run adds 1-3k chars) | Add content, but pick small verticals; prepare for migration soon |
| Stable (±200 chars, mostly condensation) | One more condensation pass, then switch to deepening |
| Rising (condensation freed headroom) | Add new content while headroom is available |
| Below 2,000 chars | Mandatory migration before any new addition |
| Below 1,000 chars | Migration + condensation; do not add new content this run |

The trend is computed at handoff-update time, not run-time. Without historical tracking, the next session can't tell whether the file is approaching the limit or has stabilized.

## Anti-Patterns to Avoid

1. **Handoff as TODO list.** The handoff is state, not a task list. Don't list "TODO: fix V2 links" — list "V2 malformed links: 109, deferred to maintenance pass." The latter is observable state; the former is wishful thinking.

2. **Handoff as session log.** Don't record every tool call. Record the outcome: section added, files created, net delta, headroom.

3. **Stale handoff files.** A handoff file that says "Run 217" but the actual file is at Run 220 = corruption. Always update in the same session that does the work, and verify the version matches the latest commit.

4. **Handoff without version pin.** If the handoff says "Recommended: 1,000-True-Fans framework" but doesn't pin the file at the version where it was recommended, the next session may try to add it and find the topic is already covered.
