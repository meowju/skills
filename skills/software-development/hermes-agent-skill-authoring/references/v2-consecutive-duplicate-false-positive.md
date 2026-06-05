# V2 + Consecutive Duplicate: Fullset False Positive Orphan Audit

> Extracted from hermes-agent-skill-authoring pitfall 27j (v1.0.74). Real case: wealth-mindset Run 3 (v1.128→v1.129).

---

## The Failure Mode

A cyclical cron skill uses V2 link format throughout. A session removes consecutive duplicate reference links, then runs an orphan audit. The audit reports ALL reference files as orphans — even though every single file is legitimately linked.

**Wealth-mindset v1.129 real case:**
- 37 reference files on disk, all properly linked via V2 format
- 2 consecutive duplicate links removed (income-acceleration-tactics.md, psychology-wealth-building.md)
- Universal orphan audit reported: **37 orphans out of 37 files**
- Manual verification confirmed: all 37 files were linked in different sections

## Root Cause

The combination of V2 format + consecutive duplicate removal produces a specific failure in the orphan audit's link-counting logic:

1. V2 link: `[references/X.md](references/X.md)` — link text and URL are identical
2. Consecutive duplicate removed: two identical V2 links, one deleted
3. Audit extracts `all_links` via universal pattern → finds URL `references/X.md`
4. `linked_bare = {url.replace('references/', '') for url in linked}` → `{X.md}`
5. When consecutive duplicates exist in the ORIGINAL content before removal, the orphan calculation's denominator was based on a link count that included the duplicates — after removal, the orphan computation incorrectly produces a fullset result

The actual bug: the audit script computes `orphans = existing_on_disk - linked_bare`. When V2 links appear consecutively in original content (before duplicate removal), the `linked` set construction has one entry per link occurrence. After duplicate removal, the on-disk file has fewer link occurrences, but the orphan computation treats the difference as "all files missing" because the V2 URL strip produces identical bare names for consecutive identical links.

## Detection Scan

```python
import re, pathlib

skill_path = "/opt/data/skills/productivity/wealth-mindset/SKILL.md"
content = pathlib.Path(skill_path).read_text()

# Step 1: V2 pre-scan
v2_count = len(re.findall(r'\[references/([^]]+\.md)\]\(references/[^)]+\.md\)', content))
print(f"V2 links: {v2_count}")

# Step 2: Consecutive duplicate scan
full_links = re.findall(r'→ Full content: \[([^\]]+)\]\(([^()]+\.md)\)', content)
from collections import Counter
url_counts = Counter(url for _, url in full_links)
consecutive_dups = {url for url, c in url_counts.items() if c > 1}
print(f"Duplicate URLs: {consecutive_dups}")

# Step 3: Orphan audit with explanation
ref_dir = pathlib.Path(skill_path).parent / "references"
existing = {f.name for f in ref_dir.glob("*.md")}
all_links = re.findall(r'\[([^\]]+)\]\(([^()]+)\)', content)
linked = {url for text, url in all_links if url.startswith('references/')}
linked_bare = {url.replace('references/', '') for url in linked}
orphans = sorted(existing - linked_bare)
print(f"Orphans: {len(orphans)} ({orphans[:3]}...)")

# If V2 > 0 AND consecutive_dups non-empty AND orphans == len(existing):
# → False positive from V2+duplicate combination
if v2_count > 0 and consecutive_dups and len(orphans) == len(existing):
    print("FALSE POSITIVE: V2 format + consecutive duplicates inflate orphan count")
```

## Fix

After removing consecutive duplicates, the orphan audit normalizes. The wealth-mindset v1.129 case showed:
- Before duplicate removal: audit reported 37 orphans
- After duplicate removal: audit reported 0 orphans

The removal itself was correct — the audit false positive was a transient state during the same session.

## Prevention

When running orphan audit on a V2-format skill that recently had duplicate link removals:
1. Always run V2 pre-scan first (pitfall 27i pattern)
2. If V2 count > 0, note that orphan count may be unreliable until after audit re-run
3. The true orphan state is visible only after all V2 links are converted to proper format

## Related

- → Full content: [references/v2-zero-orphan-illusion.md](references/v2-zero-orphan-illusion.md) — V2 gives zero orphans by coincidence; wealth-mindset v1.114 case
- → Full content: [references/v2-link-mass-fix.md](references/v2-link-mass-fix.md) — mass-fix pattern for V2 links; ai-money-maker Run 137 case
- → Full content: [references/universal-orphan-audit.md](references/universal-orphan-audit.md) — universal pattern always; never standard pattern for initial pass