# Flavor 1 False Positive: Consecutive Different-URL Reference Links Are NOT Duplicates

## The Misdiagnosis

During breakup-recovery Run, a duplicate-link audit flagged `anger-support.md` (at position 73884) as a duplicate of the same URL at position 82848 — because both were `→ Full content:` lines for `references/anger-support.md`.

But between them, at position ~72959, was:
```
→ Full content: [social-anger.md](references/social-anger.md) — the full social anger map...
```

This was correctly a **different URL** — `social-anger.md` — and should NOT have been removed.

## What Happened

The audit code scanned for pairs of consecutive `→ Full content:` lines without checking whether the URLs were actually the same. Two correctly distinct reference links (`social-anger.md` followed by `anger-support.md`) looked like a "duplicate pair" because:
1. Both had the same prefix label format
2. Both were on adjacent lines  
3. The auditor was looking for *any* two consecutive `→ Full content:` lines, not two consecutive occurrences of the *same* URL

## The Fix Applied

Only remove a `→ Full content:` link line when:
- The **same URL** appears more than once in the file
- AND the one being removed is the second (or later) occurrence

**Never remove a correctly distinct reference** even if it happens to be on a line adjacent to another `→ Full content:` line.

## Correct Detection Pattern

```python
from collections import Counter
import re

all_links = re.findall(r'→ Full content: \[([^\]]+)\]\(([^()]+\.md)\)', content)
url_counts = Counter(url for _, url in all_links)

# Only these are true duplicates
true_dups = {url: count for url, count in url_counts.items() if count > 1}
# {'references/anger-support.md': 2} → only anger-support.md needs removal

# Two different URLs on adjacent lines → NOT a duplicate
# e.g., [social-anger.md] then [anger-support.md] → each appears once, zero action needed
```

## Key Lesson

The question is never "are there two consecutive `→ Full content:` lines?" — it is always "does the same URL appear more than once?" Two adjacent `→ Full content:` lines pointing to **different** files are a correctly functioning skill, not a structural error.
