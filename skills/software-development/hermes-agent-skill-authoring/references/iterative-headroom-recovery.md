# Iterative Headroom Recovery

## The Pattern

When a patch plan fails the size gate (estimated delta > available headroom), the wrong response is to conclude or defer. The correct response: **scan the same sections for additional condensation sources within the same session**, compute a revised plan, and apply once atomically.

**Real case: breakup-recovery v4.78→v4.79:**
- File: 99,957 chars, 43 headroom
- Initial plan: 3 patches, estimated +91 chars over limit → blocked
- Iteration: re-read the same sections, found 2 additional condensation targets (Bond/Sullivan paragraph + anniversary paragraph) not in the original plan
- Revised plan: 4 patches (2 condensations + 2 reference link additions) → landed at 99,691 chars (309 headroom)

## Technique B: Iterative Content Trimming

When initial content addition overshoots the headroom, a second technique — distinct from seeking additional condensation elsewhere — is to **iteratively trim the new content itself** until it fits within the available headroom.

**Real case (wealth-mindset Run, v1.135→v1.136):**
- File: 99,098 chars, 902 headroom
- Psychology section: 173 chars (bare reference link, no inline content)
- Initial plan: 2,256-char expansion → delta +2,083 → file 101,181 (over by 1,181)
- Attempt 2: 1,272 chars → +1,099 → 100,197 (over by 197)
- Attempt 3: 1,376 chars → +1,203 → 100,301 (over by 301)
- Attempt 4: 1,212 chars → +1,039 → 100,137 (over by 137)
- Attempt 5: 1,104 chars → +931 → 100,029 (over by 29)
- Attempt 6: 1,076 chars → +903 → 100,001 (over by 1)
- Attempt 7: 1,072 chars → +899 → 99,997 (3 chars headroom ✓)

The lesson: start with the full desired content, then trim from the bottom up — remove the least-critical items first, preserve the highest-value core. Each trim was ~100-200 chars. The final 1,072-char section kept: identity-based change framework, four costly distortions, and internal locus of control.

**Why This Isn't Obvious**

Sessions often treat the initial plan as the ceiling. The first plan represents the content you know you want to add — but it's not the only condensable content in the file. Sections with verbose academic paragraphs or dense bullet lists often have more than one condensation target. The "first plan failed" signal should trigger "look harder at the same file" not "stop."

**When to use Technique B vs. Technique A:** Technique A (seek additional condensation elsewhere) requires finding more content to remove from the file. Technique B (trim the new content) works when the new content itself can be shortened without losing its core value. If the source reference file has dense, separable content, B is faster — you control the trimming, not the file's existing structure. If the file has no more condensable fat, A is unavailable and B is the only path.

## Implementation Checklist

```python
# After first plan fails size gate, TWO options are available:
# Option A: Seek additional condensation sources in the file itself
# Option B: Iteratively trim the new content until it fits

# OPTION A — Additional condensation (original pattern):
# 1. Re-read the sections already targeted for condensation
# 2. Scan for ADDITIONAL condensation opportunities in those sections:
#    - Dense academic paragraphs (>300 chars) that reference external files
#    - Bullet lists with 5+ items in sections >80k total
#    - Anniversary/ritual paragraphs with extended protocols
# 3. Compute combined delta: (additional condensation freed) + (original plan headroom)
# 4. If combined >= original plan needed, proceed with revised plan

# OPTION B — Iterative content trimming (new pattern):
# 1. Start with the full desired new content
# 2. Trim from the bottom up: remove least-critical items first
# 3. Each iteration: compute delta, check against remaining headroom
# 4. Stop when delta <= available headroom (even if1-3 chars)
# 5. Preserve the highest-value core; discard extended examples
```

**Key Rule**

> A negative headroom plan is NOT terminal. Try Technique B first if the new content itself is trimmable — it's faster and more controlled than hunting condensation elsewhere. Switch to Technique A when the new content is already at its minimum viable size.

This applies to any skill >95k chars with <1k headroom where the initial content addition plan overshoots.