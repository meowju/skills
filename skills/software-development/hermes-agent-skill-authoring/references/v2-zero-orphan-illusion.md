# V2 Link Contamination: The Zero-Orphan Illusion

## The Problem

When ALL links in a skill are V2-malformed (`[references/X.md](references/X.md)` format), the universal orphan audit correctly returns **0 orphans** — because the URL portion is `references/X.md`, and when stripped of the `references/` prefix, it yields the bare filename that matches the existing files.

This creates a false sense of security. The skill looks "clean" — 0 orphans — but the V2 overhead is still consuming chars.

**Real case: wealth-mindset v1.114**
- 29 reference links, all V2-malformed
- Universal orphan audit: 0 orphans (correct by coincidence)
- V2 overhead: 319 chars
- File size: 99,449 chars, headroom: 551 chars
- Result: Near-limit expansion blocked until V2 was fixed

## Always V2-Pre-Scan Before Near-Limit Expansion

```python
v2_matches = re.findall(r'\[references/([^]]+\.md)\]\(references/([^)]+\.md)\)', content)
print(f"V2 malformed links: {len(v2_matches)}")
```

If V2 count > 0, fix them first — even when orphan audit shows 0 orphans. The V2 fix frees real headroom that may be the difference between being blocked and being able to expand.

## Rule

Near-limit expansion (file >95k chars, <5k headroom) should always V2-pre-scan before starting. Fix V2 as a prerequisite — it's free headroom and doesn't require condensing or migrating any content.
