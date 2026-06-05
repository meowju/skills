# Consolidation Target Pattern: One File Resolves Three Orphan Slots

> Extracted from purpose-finder Run 6 (v4.77.0) — cyclical condensation session.

## The Pattern

In cyclical cron-batch skills where each run condenses multiple large subsections simultaneously, a single reference file may be a **consolidation target** — it already contains the full content for all subsections being condensed in one session. When you link it from each condensed subsection, one file resolves multiple orphan slots at once.

## Real Case: purpose-finder Run 6

The session condensed three subsections inside `## Framework: The Ikigai Lens`:

| Subsection | Before | After | Δ |
|---|---|---|---|
| `### The Eudaimonic Well-Being Frame` | 558 chars | 399 chars | −159 |
| `### Natsukashii — Longing as a Purpose Signal` | 601 chars | 371 chars | −230 |
| `### Cross-Cultural Purpose` | 726 chars | 428 chars | −298 |

A pre-existing `references/ikigai-framework-complete.md` (6,069 chars) contained the full analysis for ALL THREE subsections. When the orphan audit was corrected to strip `references/` prefix from link URLs before comparing against disk basenames, it revealed `ikigai-framework-complete.md` as a stranded consolidation target — not actually orphaned in content, but invisible to the audit because the comparison logic didn't account for the `references/` path prefix.

Three condensed subsections each gained:
```
→ Full content: [references/ikigai-framework-complete.md](references/ikigai-framework-complete.md)
```
One file resolved three orphan slots simultaneously. The audit went from **41 orphans out of 41 files** (false positive — pattern mismatch, not real orphan debt) to **2 true orphans** in one pass.

## Trigger Conditions

- **Signature pattern:** Orphan audit reports N orphans where N ≈ total reference file count (e.g., "41 orphans out of 41 files"). This is the signature of a pattern mismatch, not real orphan debt. Switch to universal pattern immediately.
- **Multiple subsections being condensed simultaneously** in the same session — high probability one existing reference file already covers them all
- **Large orphan count with no prior session having created new reference files** this session — the debt is historical, not fresh

## Fix Sequence

1. Run universal orphan audit pattern (strips `references/` from URLs before comparing against disk basenames)
2. If orphan count drops to near-zero, the problem was the pattern — not real orphans
3. Identify any remaining true orphans: each is either a consolidation target (one file serving multiple subsections) or a genuinely unlinked file
4. For consolidation targets: point all condensed subsections at the same file — no new file creation needed

## Why the First Orphan Audit Failed

The initial audit used the standard `→ Full content:` pattern without stripping the `references/` prefix:
```python
# First pass — WRONG: compared full paths against basenames
full_links = re.findall(r'→ Full content:\s*\[([^\]]+)\]\(([^()]+\.md)\)', content)
all_linked = {url for _, url in full_links}  # e.g., "references/ikigai-framework-complete.md"
orphans = set(existing_files) - all_linked  # existing_files are basenames — no match
```

Correct comparison:
```python
# Correct: strip references/ before comparing
all_linked_basenames = {url.replace('references/', '') for _, url in full_links}
orphans = sorted(set(existing_files) - all_linked_basenames)
```

## Key Insight

The universal orphan audit pattern and the consolidation target pattern are often discovered together: the audit reports a suspiciously high orphan count (pattern mismatch), and investigation reveals the files ARE linked — just to a consolidation target that one session's multiple subsections all share. Fix the pattern first, then count real orphans.