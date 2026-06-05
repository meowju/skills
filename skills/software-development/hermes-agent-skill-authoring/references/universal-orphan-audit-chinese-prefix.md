# Universal Orphan Audit: Chinese-Prefix False Positive

> Extracted from hermes-agent-skill-authoring context. Real case: ai-money-maker v4.2.9→v4.3.0 (Run 189).

## The Problem

The standard orphan audit pattern in pitfall 27i uses:
```python
full_links = re.findall(r'→ Full content:\s*\[([^\]]+)\]\(([^()]+\.md)\)', content)
```

This only matches `→ Full content:` (English) prefixed links. Skills using `→ 完整内容:` (Chinese) throughout will show **zero matches** under the standard scan — making every correctly-linked reference file appear as an orphan.

## Real Case: ai-money-maker

- Reference files on disk: 120
- Correctly linked via `→ 完整内容:` (Chinese): 76
- Standard `→ Full content:` pattern matched: **0**
- Result: all 76 files appeared as orphans despite all being correctly linked

## The Fix

Always run dual-prefix detection:

```python
full_links = re.findall(r'→ Full content:\s*\[([^\]]+)\]\(([^()]+\.md)\)', content)
china_links = re.findall(r'→ 完整内容:\s*\[([^\]]+)\]\(([^()]+\.md)\)', content)
all_link_urls = {url for _, url in full_links + china_links}
# Now compare against existing ref files
```

Or use the universal pattern (catches all markdown link formats regardless of prefix):
```python
all_links = re.findall(r'\[([^\]]+)\]\(([^()]+)\)', content)
linked = {url for text, url in all_links if url.startswith('references/')}
```

## Trigger Condition

Any skill that uses `→ 完整内容:` or other non-English reference link prefixes. The pattern name `→ Full content:` in the audit code is the signal — if a skill's body uses a different prefix everywhere, the standard pattern is the wrong tool.

## Audit Sequence

1. Always start with the **universal** pattern when auditing a skill for the first time
2. If it reports orphans, check whether the skill uses `→ 完整内容:` or other Chinese prefixes
3. Run dual-prefix scan to get true counts
4. If dual-prefix count ≈ existing ref file count → skill is clean, orphan report was a false positive

## See Also

- references/universal-orphan-audit.md — the universal pattern and why to always start with it
- references/cron-orphan-false-positive.md — another class of false positive (inline mentions vs proper links)