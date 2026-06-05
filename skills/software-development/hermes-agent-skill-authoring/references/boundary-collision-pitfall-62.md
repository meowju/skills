# Pitfall 62: Boundary Corruption Scan — `## ` vs `### ` After `→ Full content:` Links

## The Distinction

**`###` case (subsection header, always corruption):**
When a `→ Full content:` link line is directly followed by a `###` subsection header with no blank line between them, markdown renders as a malformed compound link. This is **always** a structural defect and requires a `\n\n` fix.

**`##` case (top-level header, context-dependent):**
When a `→ Full content:` link is directly followed by a `## ` top-level section header, the boundary is **often intentional** — the link closes a section and the `## ` opens the next. Only flag as corruption when the content between link and `## ` contains visible text that should be rendered separately, not when it's a `---` divider block containing section labels.

## The False Positive: `## N、` Inside `---` Divider Blocks

The string-operation boundary scan uses `content.find('\n## ', link_end)` to locate the next section header. This matches any `## ` — including `## N、` labels **inside** `---` divider blocks that act as decorative section separators.

**Real case:** breakup-recovery flagged 19 positions as boundary corruption. All 19 were `## N、` labels embedded inside `---...---` divider blocks — not actual violations. The bare `\n## ` look-ahead could not distinguish between:
- A decorative `## N、` label inside a `---` divider block
- The real `## N、` section header that follows the divider block

The spacing **before the real header** was correct in every case.

## Detection Fix

After flagging a position, verify the matched `## ` is outside any `---...---` block before marking as corruption:

```python
import re, pathlib
content = pathlib.Path(skill_path).read_text()

def inside_divider(pos, content):
    """Returns True if position is inside a ---...--- block."""
    # Find the most recent opening ---
    opens = [m.end() for m in re.finditer(r'\n---\n', content[:pos])]
    if not opens:
        return False
    last_open = opens[-1]
    # Find the next closing --- after last_open
    closes = [m.start() for m in re.finditer(r'\n---\n', content[last_open:])]
    if not closes:
        return False
    first_close = last_open + closes[0]
    return last_open < pos < first_close

corrupted = []
for m in re.finditer(r'→ Full content:[^\n]+\)', content):
    link_end = m.end()
    next_nl = content.find('\n', link_end)
    next_header = content.find('\n## ', link_end)
    between = content[next_nl:next_header]
    # Check: no \n\n AND not inside a divider block
    if not between.startswith('\n\n') and '---' not in between:
        corrupted.append(f"pos {m.start()}: {between[:50]!r}")
    elif not between.startswith('\n\n') and inside_divider(next_header, content):
        # Inside a divider — skip, this is a false positive
        pass

print(f"Real boundary corruption: {len(corrupted)}")
for c in corrupted:
    print(c)
```

## Rule Summary

| Pattern | Action |
|---------|--------|
| `→ Full content: link` → `\n### N、` (no blank line) | Always fix: insert `\n\n` |
| `→ Full content: link` → `\n## N、` (no blank line) + visible text | Fix: insert `\n\n` |
| `→ Full content: link` → `\n## N、` inside a `---` divider block | Skip: false positive |
| `→ Full content: link` → `\n## N、` followed by `\n---` | Intentional: skip |

**Bottom line:** The bare `content.find('\n## ', ...)` look-ahead is insufficient — always check whether the matched header falls inside a `---...---` block before flagging.
