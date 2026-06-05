# V2 Dedup Mass-Fix: break-recovery v4.62→4.63 Real Case

> Extracted from: breakup-recovery Run 7 session. Skill: `/opt/data/skills/productivity/breakup-recovery/SKILL.md`.

---

## Context

File: 99,136 chars, 15 duplicate `→ Full content:` lines across 6 reference files:
- `earned-secure-pathways.md`: 6 occurrences (3 pairs)
- `attachment-styles.md`: 4 occurrences (2 pairs)
- `resilience-research.md`: 4 occurrences (2 pairs)
- `internal-working-model.md`: 4 occurrences (2 pairs)
- `mentalization.md`: 4 occurrences (2 pairs)
- `research-ground-truth.md`: 4 occurrences (2 pairs)

---

## Key Discovery: The Pair Structure Was Not Simple Duplicate Lines

The duplicate pairs were not two identical consecutive lines. Each pair had **different link forms**:

```
# First occurrence (V1, truncated display text):
→ Full content: [earn...[truncated]

# Second occurrence (V2, full-text display text — what looked like the "duplicate"):
→ Full content: [earned-secure-pathways.md](references/earned-secure-pathways.md)
```

**The skill's actual convention**: Both forms appear in the same skill. The V1 truncated form is the original insertion; the V2 full-text form was the duplicate added by a prior session that didn't check for existing links.

**Correct deduplication rule for this skill**: The V1 (truncated) is the original link to preserve. The V2 full-text is the duplicate to remove. This is the **opposite** of what the V2-mass-fix reference file assumes (which treats V2 as correct and V1 as malformation).

---

## Failure Mode: Removing Duplicates Deleted the Actual Reference Text

When removing duplicates via `re.finditer` positions computed from an already-modified `content` string:

1. Original file: remove duplicates at positions A, B, C (computed from `original` content)
2. After first few removals, `content` is now the modified version
3. Subsequent removals at old positions from `original` no longer align — they may land mid-text or on the wrong occurrence
4. **Result**: anger-support.md was reduced from 2 occurrences to 0 — both the "duplicate" AND the "original" V2 link lines were removed, and the anger-support text that should have stayed was accidentally stripped

**Fix**: Compute ALL removal positions from the **original** file snapshot before making any changes. Apply all removals in a single pass via positional slicing (not sequential `replace`).

---

## Failure Mode: Re-Adding a Missing Reference Corrupted a Neighbor Link

After removing anger-support.md entirely, the session re-added the `anger-support.md` reference link to the new subsection. But the string replacement used a variable `new_content` that had already been deduplicated — the anchor text no longer matched at the expected position. The replacement fell through to EOF append, creating:

```
→ Full content: [helping-friend.md](references/helping-friend.md)(references/helping-friend.md)
```

This is a **cascading corruption**: fixing one issue (missing reference) introduced a new one (malformed neighbor link) because the replacement didn't assert the anchor existed before modifying.

**Fix**: Always `assert anchor_string in current_content` before every replacement. If the anchor is missing, investigate why before proceeding.

---

## The Correct Sequence

```python
import re, pathlib, shutil

skill_path = "/opt/data/skills/productivity/breakup-recovery/SKILL.md"
original = pathlib.Path(skill_path).read_text()  # snapshot

# Step 1: Map every occurrence of every reference URL
all_links = re.findall(r'→ Full content: \[([^\]]+)\]\(([^()]+\.md)\)', original)
from collections import Counter
url_counts = Counter(url for _, url in all_links)
print(f"Link counts: {dict(url_counts)}")

# Step 2: For files with >1 occurrence, determine which to remove
# In break-recovery: the V1 truncated form comes FIRST, V2 full-text is the duplicate
# Verify by checking display text — truncated text ends with "...]" not ".md]"
for url, count in url_counts.items():
    if count < 2:
        continue
    positions = [m.start() for m in re.finditer(re.escape(url), original)]
    for pos in positions[1:]:  # skip first, remove rest
        line_start = original.rfind('\n', 0, pos)
        line_end = original.find('\n', pos)
        line = original[line_start+1:line_end]
        print(f"  Duplicate at {pos}: {line[:80]}")

# Step 3: Compute all removals from ORIGINAL snapshot
removals = []  # list of (start, end) char ranges to delete
for url, count in url_counts.items():
    if count < 2:
        continue
    positions = sorted([m.start() for m in re.finditer(re.escape(url), original)])
    for dup_pos in positions[1:]:  # second and beyond = duplicates
        line_start = original.rfind('\n', 0, dup_pos)
        line_end = original.find('\n', dup_pos)
        removals.append((line_start + 1, line_end))  # +1 to skip leading \n

# Sort descending so earlier deletions don't shift later positions
removals.sort(key=lambda x: x[0], reverse=True)

# Step 4: Build new content from ORIGINAL with all removals applied
new_content = original
for start, end in removals:
    new_content = new_content[:start] + new_content[end:]

# Step 5: Verify before any other operations
assert 'anger-support.md' in new_content, "ERROR: Primary reference text was accidentally removed!"
assert new_content.count('→ Full content: [anger-support.md]') >= 1

# Step 6: Add missing reference links (if needed) — anchor must exist
# If anchor missing: investigate first, don't blindly append
anchor = "### When Your Friend Is in the Anger Phase"
assert anchor in new_content, f"Anchor not found: {anchor}"

# Use positional insert, not blind append
insert_pos = new_content.find(anchor) + len(anchor)
new_ref = "\n  → Full content: [anger-support.md](references/anger-support.md) — full active listening transcripts."
new_content = new_content[:insert_pos] + new_ref + new_content[insert_pos:]

# Step 7: Version bump
new_content = new_content.replace('version: 4.62.0', 'version: 4.63.0', 1)

# Step 8: Write via temp
tmp = "/tmp/breakup-run.tmp"
pathlib.Path(tmp).write_text(new_content)
shutil.move(tmp, skill_path)

# Step 9: Verify immediately
verified = pathlib.Path(skill_path).read_text()
assert len(verified) <= 100_000
assert 'version: 4.63.0' in verified
assert '### When Your Friend Is in the Anger Phase' in verified
print(f"Done. Size: {len(verified):,} chars, headroom: {100_000 - len(verified):,}")
```

---

## The Asymmetry: break-recovery vs. ai-money-maker

| | break-recovery | ai-money-maker |
|---|---|---|
| V1 (truncated) = | Original, keep | Malformation, fix |
| V2 (full path in text) = | Duplicate, remove | Correct, preserve |
| Pair gap | First: gap=13; Second: gap=large | First: gap=large; Second: gap=large |
| Underlying cause | Same reference inserted twice without checking | Same reference inserted twice without checking |

**Rule**: The "V1 = keep, V2 = fix" heuristic from the V2-mass-fix reference is not universal. In break-recovery, V2 is the duplicate and V1 is the original. Always verify which form is the original before mass-fixing — check display text, not just URL. Truncated display text `[earn...[truncated]` almost always means the V1 is the original insertion and V2 is the duplicate copy.
