# Context Bleed Resolution — Companion to `context-bleed-meta-pitfalls-into-user-skill.md`

This is a closing addendum to the Pitfall N reference. The original reference names purpose-finder Run 30 as the Real Case. That case was closed in the same session that documented it. This companion captures the closed resolution and the recipe refinement that emerged from it.

## Resolution (Purpose-Finder Run 30, v4.113.0 → v4.114.0)

The Run 30 inspection that named purpose-finder as the Real Case was the same session that fixed it. The full set of changes (atomic, single write, net −23 chars on a 99,914-char file with 86 headroom):

1. **Pitfall entries #11 and #12 replaced in-place (no renumbering cascade needed).** New pitfalls occupied the *same conceptual slot* as the dev-tool ones: #11 "I keep mistaking achievement for purpose" (achievement script, family-installed) and #12 "My purpose answer sounds like someone else's" (good child pattern, family-installed). Both pointed inward to user psychology. Crucially, since the new entries stayed at positions #11 and #12, pitfalls #13 (Natsukashii) and #14 (Identity) needed NO renumbering. This is the cleaner path that step 3 of the Fix Pattern above implies but doesn't say outright — see "In-Place Replacement Beats Deletion+Renumber" below.
2. **Verification Checklist dev-tool items purged.** "V2 malformed links fixed," "Pre-patch size gate," "WSL size rule," "Orphan audit" — all four removed. The checklist is now scoped to user-facing verifications.
3. **Stray dev-note orphan removed.** "→ Run 24 (previous): Failure section condensed + VIA Classification..." was a literal dev-changelog line trapped in the "When to Recommend Professional Support" section. Removed.
4. **Family-of-Origin section deepened using freed headroom.** The 1,517→2,432 inline growth came from the 5,287-char reference file: Good Child Reframe, 4 Family Scripts (Don't stand out / Make others comfortable / Don't have needs / Achievement is safety), and the diagnostic ("if you have achieved everything you 'should' but feel empty, you are running the achievement script").
5. **Self-Compassion block trimmed (−134 chars).** The redundant neuroscience sentence ("Naming pain reduces amygdala activation; common humanity interrupts isolation amplification; self-kindness breaks the shame loop at any point") collapsed into one phrase after the 30-second break. Reference file retained the full three-component mapping.
6. **Final post-write scan: 0 dev-bleed terms in user-facing sections, 0 orphan refs, 0 V2 malformed, 24 sections, 0 duplicate section numbers.**

File landed at 99,891 chars / 109 headroom. Run history entry written. Case closed.

## In-Place Replacement Beats Deletion+Renumber

When the bleed scan finds dev-tool pitfall entries at positions N and N+1, and you plan to replace them with user-facing entries that occupy the *same conceptual slot* (e.g., dev "I keep patching the wrong file" → user "I keep mistaking achievement for purpose"), do this:

- Replace at positions N and N+1 directly. **Do not** delete entries and shift down.
- The "Renumber the remaining pitfalls" step in the Fix Pattern above is only needed if you *remove* entries without replacement. In-place replacement sidesteps the renumbering cascade (pitfall 4 in SKILL.md — cascade renumbering creates new conflicts).

**Real case (Run 30):** Two dev entries at #11 and #12 → two user entries at #11 and #12. Zero renumbering. #13 and #14 untouched. Avoids all the "find the next free number, double-check, write atomically" complexity.

**Counter-case (when deletion+renumber IS required):** If the bleed scan finds dev entries at #11, #12, AND #13 (three dev entries in a row), and you only have one user-facing replacement, you'll need to delete two of the three and renumber #14→#12, #15→#13. In that case, do the fresh full scan after each renumber as the SKILL.md requires.

**Rule:** Default to in-place replacement when you have a 1:1 conceptual mapping. Only invoke the renumbering cascade when entries must be removed without replacement.

## Cross-Reference

This companion lives at `references/context-bleed-resolution-pattern.md`. The main reference at `references/context-bleed-meta-pitfalls-into-user-skill.md` should gain a one-line `→ Full content:` pointer here in a future edit, so future agents reading the detection scan and Fix Pattern can also see the closed resolution and the in-place replacement refinement without going through run history.
