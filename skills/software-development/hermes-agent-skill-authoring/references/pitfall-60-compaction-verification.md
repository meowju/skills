# Pitfall 60: Context Compaction Obscures Verification State

## The Problem

When a session's context is compacted after it claims to complete file writes (SKILL.md patched, version bumped), the next session receives only a summary — not the transcript of what actually happened. The summary may contain:

- Errors about file state (typos, wrong character counts, fabricated section positions)
- Claims about content never actually written to disk
- A mid-session compaction that leaves the receiving session unable to call `execute_code` or `patch`

## Rule

**Always verify independently via `pathlib.read_text()` + `len()`.** Never trust a compacted summary's size, headroom, section positions, or version claims. If verification tools are unavailable, treat prior session's claimed writes as unconfirmed until a full-tools session can run the orphan audit and size gate.

## WSL Caveat

`wc -c` and tool metadata hints are unreliable in WSL (can be stale by 2x). Python `pathlib.read_text()` is authoritative.

## Real Case

wealth-mindset Run 4→5: Prior session (context summary) claimed:
- Version: 1.110.0
- "Negotiating Under Leverage" section added at position 65,175
- "lynncher" typo in version history
- Headroom: 2,481 chars

Receiving session had only `memory`, `skill_manage`, `skill_view`, `skills_list` available — no `execute_code`, `read_file`, `terminal`, or `patch`. Could not verify any of the claimed state. The summary was accepted as ground truth with no verification path available.

## Prevention

For cron jobs that write to large skill files (>80k chars):
1. End the session by verifying the file state with Python `pathlib.read_text()` in the same session that wrote
2. Include the verification output (actual size, version line) in the final response so the next session's summary is accurate
3. If the session ends mid-write or with unverified state, flag this in the cron job delivery
