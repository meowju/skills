# Pitfall 27e — Flavor-0 False Positive vs. True Duplicate Distinction

## The Core Distinction

**Flavor-0 (same-line double-link):** The URL substring appears TWICE inside a SINGLE line. Detection: `[^()]+` URL pattern + gap <50 between the two matches. This is NOT a true duplicate — it's one malformed line whose link text contains the URL.

**True consecutive-duplicate:** The URL appears as a separate `→ Full content:` link LINE, repeated across two distinct lines. Detection: full link-line extraction + `Counter`. Gap between the two lines is irrelevant.

## The Gap <50 Rule — What It Actually Does

The gap rule exists ONLY to distinguish "two occurrences in one line" (Flavor-0) from "two occurrences across two lines." It does NOT rule out true duplicates.

Once you confirm two separate lines exist (gap >50), the URL count determines whether removal is needed:
- `url_counts['X.md'] == 2` → true duplicate, remove second line
- `url_counts['X.md'] == 1` → Flavor-0 false positive, don't remove

## Two-Stage Detection Code

```python
import re, pathlib
from collections import Counter

content = pathlib.Path(skill_path).read_text()

# Stage 1: Flavor-0 false positive check
# Extract full link lines, not URL substrings
all_links = re.findall(r'→ Full content: \[([^\]]+)\]\(([^()]+\.md)\)', content)
url_counts = Counter(url for _, url in all_links)

# For URLs appearing exactly twice, check if they're in the same line
for url, count in list(url_counts.items()):
    if count == 2:
        matches = list(re.finditer(re.escape(url), content))
        if len(matches) == 2:
            gap = matches[1].start() - matches[0].start()
            if gap < 50:
                print(f"Flavor-0 false positive: {url} (gap={gap} — same line)")
                url_counts[url] = 1  # don't treat as duplicate

# Stage 2: remaining count > 1 = true duplicates
true_dups = {k: v for k, v in url_counts.items() if v > 1}
print(f"True duplicates: {true_dups}")

# Remove each true duplicate's second occurrence by line position
for ref_url, dup_count in true_dups.items():
    matches = list(re.finditer(re.escape(ref_url), content))
    if len(matches) >= 2:
        second_pos = matches[1].start()
        line_start = content.rfind('\n', 0, second_pos) + 1
        line_end = content.find('\n', second_pos)
        if line_end == -1:
            line_end = len(content)
        content = content[:line_start] + content[line_end+1:]
        print(f"Removed duplicate: {ref_url}")
```

## Real Case: breakup-recovery 5.10.0 → 5.11.0

File at 97,622 chars. Three duplicate `→ Full content:` links found in `## The Anger Phase` section:

| Link | Position within Anger Phase | Gap from previous | True duplicate? |
|------|----------------------------|-------------------|-----------------|
| `anger-shame-research.md` (2nd) | offset 5666 | +1821 from prev | YES — separate line |
| `self-compassion.md` (2nd) | offset 5847 | +181 from prev | YES — separate line |
| `anger-completion-somatic.md` (2nd) | offset 7832 | +1985 from prev | YES — separate line |

All three gaps were 181–1,985 chars (all >>50), confirming separate lines. Total removal: 433 chars. Freed headroom for 2,721-char Communication Scripts expansion.

If gap <50 had been mistakenly used to rule these out, all three would have stayed — and the session would have had no room for new content.

## Common Misread

> *"27e says gap <50 means no duplicate"* — this is WRONG.

The correct reading: **gap <50 means the two occurrences are in the same line** (Flavor-0 false positive). Gap >>50 means separate lines, and then the Counter logic determines whether each is a true duplicate.

## Prevention: Post-Patch Verification

Always run the two-stage check AFTER any patch that adds reference links:

```python
all_links = re.findall(r'→ Full content: \[([^\]]+)\]\(([^()]+\.md)\)', content)
url_counts = Counter(url for _, url in all_links)
true_dups = {k: v for k, v in url_counts.items() if v > 1}
# For each count==2, verify gap >50 before skipping
for url, count in url_counts.items():
    if count == 2:
        matches = list(re.finditer(re.escape(url), content))
        if len(matches) == 2 and matches[1].start() - matches[0].start() > 50:
            true_dups[url] = 2  # promote to true duplicate
assert not true_dups, f"True duplicates: {true_dups}"
```
