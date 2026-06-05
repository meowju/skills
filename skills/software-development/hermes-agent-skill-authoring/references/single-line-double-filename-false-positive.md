# Reference Link False Positive: Single-Line Double-Filename Pattern

## The Problem

When auditing duplicate `→ Full content:` (or `→ 完整内容:`) reference links in large multi-session skills, a naive count of filename occurrences can produce false positives. This causes agents to waste tool calls investigating non-existent duplicates or, worse, to attempt "deduplication" patches that find zero matches and abandon the audit.

## Root Cause

Many reference links use the format:
```
→ Full content: [references/ai-leverage-path.md](references/ai-leverage-path.md)
```

This single line contains the filename **twice**:
1. In the **link text** portion: `[references/ai-leverage-path.md](...)`
2. In the **URL** portion: `[...(references/ai-leverage-path.md)]`

A raw `content.count("ai-leverage-path.md")` counts **2 occurrences** — one per location — making the file appear twice as many times as it actually is.

## False Positive Pattern in This Session

- `ai-leverage-path.md` was reported as "6 occurrences" → actually 3 single-line links, each appearing twice per line = 6 filename mentions
- `ai-b2b-sales-psychology-deep.md` was reported as "4 mentions" → actually 2 single-line links
- `ai-compliance-moat-v2.md` was reported as "5 mentions" → actually 3 single-line links (disk) or 2 (git HEAD)

## Correct Detection

Use line-level parsing, not raw string counts:

```python
import re
from collections import Counter

content = open('SKILL.md', 'r', encoding='utf-8').read()

# Find all reference link lines (ANY markdown link to references/)
ref_lines = re.findall(r'\[([^\]]+)\]\((references/[^()]+\.md)\)', content)

# Count by URL (each unique line = one link, regardless of filename appearing twice in it)
url_counts = Counter(url for _, url in ref_lines)
dup_urls = {url: cnt for url, cnt in url_counts.items() if cnt > 1}

print(f'Files with >1 unique link line:')
for url, cnt in sorted(dup_urls.items(), key=lambda x: -x[1]):
    print(f'  {url}: {cnt} times')
```

## Counter-Example: True Duplicate Lines

A true duplicate is the **same `→ Full content: [references/X.md](references/X.md)` line appearing on two separate lines** — two identical line strings. Detected by:

```python
# True duplicates: same line string appears more than once
from collections import Counter
lines = content.split('\n')
full_content_lines = [l for l in lines if l.strip().startswith('→ Full content:') or l.strip().startswith('→ 完整内容:')]
duplicate_line_strings = {l: c for l, c in Counter(full_content_lines).items() if c > 1}
```

If `duplicate_line_strings` is empty but `dup_urls` is non-empty → all "duplicates" are single-line double-filename patterns.

## Rule

**Always verify with line-level parsing before attempting any deduplication patch.** Raw `str.count()` on filenames is unreliable for this format. A filename appearing >2 times may indicate a real duplicate link line (same line on multiple lines) OR multiple single-line links — only line-level parsing disambiguates.