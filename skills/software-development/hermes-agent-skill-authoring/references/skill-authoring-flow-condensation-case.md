# Flow Autotelic Training — Condensation Reference Case

**Source:** purpose-finder v4.54.0 → v4.55.0  
**Trigger:** File at 99,981 chars (19-char headroom), Flow States section largest at 11,444 chars  
**Pattern:** Subsection extraction + inline summary + → Full content reference link  
**Result:** −2,444 chars inline; 2,462 headroom freed; 0 orphans

---

## Pre-State

| Metric | Value |
|--------|-------|
| SKILL.md size | 99,981 chars |
| Headroom | 19 chars |
| Target section | `## Framework: Flow States and Purpose` (11,444 chars) |
| Target subsection | `### Self-Directed Flow Training — The Autotelic Path` (3,941 chars) |

---

## Extraction Decision

**Why this subsection:** Self-contained (no cross-references within the file), well-bounded, had depth that would be useful standalone. Other subsections in the same section had internal references, making them riskier extraction targets.

**Why not extract the whole section:** Flow States section had 11,444 chars and likely contained references to other sections. Extracting the whole section would require updating all internal links and potentially create orphaned references. The subsection was the right minimum viable extraction.

---

## Inline Summary Written (1,497 chars replacing 3,941)

```
### Self-Directed Flow Training — The Autotelic Path

The deepest layer of flow cultivation is becoming an *autotelic* personality —
someone who can generate flow from whatever situation they're in. Csikszentmihalyi's
20-year longitudinal study tracked people who spontaneously developed this capacity.
It is trainable.

**Layer 1 — Attention Training (Weeks 1–4)**
The prerequisite for flow is present-moment awareness. Without the ability to notice
what you're attending to, you cannot calibrate challenge to skill.

**Layer 2 — Challenge-Skill Rebalancing (Weeks 5–12)**
Once attention is manageable, the core mechanism of flow is simply: raise challenge
until anxiety appears, lower it until boredom disappears, find the channel between.

**Layer 3 — Purpose Integration (Months 3–12)**
The autotelic personality is not just someone who enters flow easily — it is someone
who has woven purpose into their daily structure. Daily review ritual, meaningful
difficulty audit, and the 90-minute focus block are the three operational practices.

→ Full content: [references/flow-autotelic-training.md](references/flow-autotelic-training.md)
```

Key practices preserved in condensed form: 90-Minute Focus Block, Calibration Protocol, Meaningful Difficulty Audit, Autotelic Self-Test.

---

## Boundary Fix Required After Insertion

After inserting the reference link, the boundary was:
```
md)\n\n## Framework: Identity-Based Habits
```
(i.e., one blank line between the `)` and the `##`).

This is **boundary corruption** — markdown renders correctly but it is one `\n` short of the two `\n\n` required for clean section separation.

**Fix applied:**
```
md)\n\n## Framework: Identity-Based Habits  →  md)\n\n\n## Framework: Identity-Based Habits
```
Anchor used: `"for what it will get me?*\n\n→ Full content: [references/flow-autotelic-training.md](references/flow-autotelic-training.md)\n\n## Framework: Identity-Based Habits"` — unique, confirmed via `content.count()`.

---

## Post-State

| Metric | Value |
|--------|-------|
| SKILL.md size | 97,538 chars |
| Headroom | 2,462 chars |
| Reference file | `references/flow-autotelic-training.md` (4,648 bytes) |
| Orphans | 0 (verified via universal orphan audit) |
| Boundary | Correct (`\n\n` before next `##`) |
| Version | 4.54.0 → 4.55.0 |

---

## Lessons

1. **Self-contained subsections are the safest extraction targets** — no internal cross-references means no orphaned links after migration.
2. **One blank line before `##` is a common boundary error** — always write `\n\n` (two newlines) between a reference link line and the next section header, even if it looks fine in raw text.
3. **Use the preceding paragraph as patch anchor** — `for what it will get me?` (a full sentence ending with `*`) is unique enough to anchor the boundary fix without affecting any other section.
4. **Headroom of 19 chars is not an emergency — it is a signal** — the session did a full pre-edit structural survey, identified the Flow section, and chose the right subsection before touching the file.
5. **Reference link + summary pattern preserved all key practices** — the inline summary kept the four named practices (90-Minute Focus Block, Calibration Protocol, Meaningful Difficulty Audit, Autotelic Self-Test) so future agents don't need to open the reference file to know what's in it.