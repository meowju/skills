# Near-Limit Insertion via Duplicate Reference-Link Removal

**Pattern name:** cheap-offset via duplicate reference-link removal

**Trigger:** File is near 100k limit (< 1,500 chars headroom) and new content needs to be inserted. Sequential patching is impossible because any patch risks breaching the limit.

**Core insight:** Duplicate `→ Full content:` links to the same reference file are structurally free offsets. The content already exists in the skill. Removing one instance of a 3× or 2× link loses nothing if the concept was already introduced by the first link.

**When NOT to remove:**
- A 2× link where the second instance adds genuinely distinct, non-overlapping context
- A link whose removal would leave a paragraph that references a now-absent citation

**When to remove:**
- A 3× link where the concept is covered by the first link and later instances are pure redundancy
- A duplicate inside a specific target section where the concept was already introduced earlier in the skill

## Detection Pattern

```python
from collections import Counter
import re

full_links = re.findall(r'→ Full content:\s*\[([^\]]+)\]\(([^()]+\.md)\)', content)
url_counts = Counter(url for _, url in full_links)
dups = {f: c for f, c in url_counts.items() if c > 1}
# dups = {'references/earned-secure-pathways.md': 3, ...}
```

For each duplicate, inspect whether any instance is redundant (same conceptual introduction already done earlier in the skill).

## Real Case: breakup-recovery v4.93→4.94

- File size before: 99,164 chars
- Headroom: 836 chars
- New subsection needed: ~1,091 chars (sleep disruption bridging section)
- Problem: 99,164 + 1,091 = 100,255 → 255 over limit
- Scanning duplicate links found: `earned-secure-pathways.md` referenced 3×
  - First link: introduces the earned security concept at the start of the IWM section
  - Second link (inside "For disorganized attachment" prose): same framework re-cited, 263 chars
  - Third link: later section, different context
- Decision: remove the second instance (redundant within the same section's prose)
- Chars freed: ~263
- Net insertion: +1,091 − 263 = +828
- Final size: 99,992 chars (8-char headroom)

## Why Not Trim Prose?

The new subsection was already stripped to its minimum viable length during iterative trimming. The prose quality was at the floor — further trimming would have made the section thin and less useful. The duplicate-link removal was lossless: it removed a citation, not original content.

## Rule

**Scan duplicates before trimming prose.** On near-limit files, a duplicate reference link is always the first resort for offset. It is free structurally and carries no content loss when the concept is already introduced elsewhere.