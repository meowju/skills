# Cron-Batch Orphan Audit False Positive: Inline Mentions

## The Pattern

In cyclical cron-batch skills (e.g. wealth-mindset, ai-money-maker), a `references/` file may have its path appear inline in body text without being a properly formatted reference link.

Example: `references/research-cycle.md` existed on disk and its path appeared verbatim in the Verification Checklist section as plain text:
```
See references/research-cycle.md for the cycle tracking.
```

A naive `content.find("research-cycle.md")` returned a positive position — making the file appear linked. But the orphan audit (using the universal markdown link pattern `r'\[([^\]]+)\]\(([^()]+)\)'`) correctly found zero properly formatted markdown links pointing to it, revealing it as an orphan.

## The Fix

Always use the universal markdown link audit pattern, never `content.find()`:
```python
# WRONG — false positive when path appears inline
if content.find("references/X.md") >= 0:
    print("linked")  # Misleading!

# CORRECT — only counts actual markdown links
all_links = re.findall(r'\[([^\]]+)\]\(([^()]+)\)', content)
linked = {url for text, url in all_links if url.startswith('references/')}
orphans = sorted(set(f.name for f in ref_dir.glob("*.md")) - {url.replace('references/', '') for url in linked})
```

## Trigger Condition

Applies to skills that: (a) have a `references/research-cycle.md` or similar tracking file, (b) have inline mentions of reference file paths in body text without formal `→ Full content:` links. Any skill with cyclical cron-run documentation is at risk.

## Related Pitfalls

- 27f: `content.find()` on link path confirms presence but not placement
- 27: Universal orphan audit pattern must catch `→ Full content:`, `→ Related:`, and backtick links
- 37: delegate_task research failure → mine existing references (same session, same principle: don't defer, use what's already there)
