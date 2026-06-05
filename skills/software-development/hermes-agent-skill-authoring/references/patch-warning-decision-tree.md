# Patch Warning Decision Tree

## The Core Problem

The `patch` tool's internal matching algorithm normalizes whitespace and handles Unicode differently than Python's `str.count()`. A string confirmed unique by Python can be reported as "42 matches" by `patch`. Conversely, the `patch` tool's read history can confuse it into reporting 4 matches for a string that Python confirms has only 1 occurrence.

## Two Warning Types — Different Fixes

### Warning 1: "Found N matches" (N > 1)

The `patch` tool reports: `"Found N matches for old_string"`

**Cause:** `patch` normalized whitespace/Unicode differently than Python counted it.

**Decision tree:**
```
patch reports "Found N matches" for old_string
  → Run Python: content.count(old_string) == 1?
      YES: Switch to Python pathlib positional slicing immediately
           (patch tool is confused by its own normalization — do not debug patch)
      NO:  old_string genuinely appears in multiple places
           → Expand old_string with more surrounding context to achieve uniqueness
```

**Real case — purpose-finder Run 9:** Anchor string `"Purpose that spans three generations is more durable than purpose anchored in a single generation's achievement."` was confirmed unique by Python `content.count()` but `patch` reported "4 matches." Switching to Python `pathlib` positional slicing (find anchor_end, find next header, slice-replace) succeeded in one pass with no corruption.

### Warning 2: "File was modified since you last read" (after re-read)

The `patch` tool reports: `"File was modified since you last read it on disk (external edit or unrecorded writer)"`

**Cause:** Another process wrote to the file after you read it but before your `patch` call.

**Decision tree:**
```
Warning fires after re-read
  → "Partial view" (from pagination via skill_view/read_file offset): re-read via pathlib, proceed with patch
  → "Modified since you last read": DO NOT re-read
       → Use atomic write with the content already in memory
       → Re-reading a concurrently-modified file compounds the race condition
```

**Real case — ai-money-maker Run 51:** Two subagents raced. Subagent B re-read after the warning and retried `patch` — but the file had already been partially written by subagent A, so subagent B's `old_string` no longer matched the current content at that position. Result: sections embedded in the wrong section. Fix: `git checkout` + atomic write in a clean session with no concurrent sibling.

**Rule:** "Modified since you last read" → atomic write with in-memory content, never a re-read-and-retry loop.

## The Atomic Python Pattern (First Resort for Large Files)

When `patch` is unreliable or a concurrent race is possible, use this pattern:

```python
import pathlib
path = "/opt/data/skills/.../SKILL.md"
content = pathlib.Path(path).read_text()  # fresh read

# Find target section boundaries precisely
anchor_pos = content.find("UNIQUE_ANCHOR_STRING")
next_header = content.find("\n## ", anchor_pos)
next_sub = content.find("\n### ", anchor_pos)
end_pos = min(s for s in [next_header, next_sub] if s > anchor_pos)

# Verify uniqueness
target_block = content[anchor_pos:end_pos]
assert content.count(target_block) == 1, f"Not unique: {content.count(target_block)} matches"

# Build and write
new_content = content[:anchor_pos] + new_section + content[end_pos:]
pathlib.Path(path).write_text(new_content)

# Immediate verification
assert len(new_content) <= 100_000
assert "TARGET_SECTION_HEADER" in new_content
assert "NEXT_SECTION_HEADER" in new_content
```

This eliminates the read-then-write race entirely. All position computation happens on the original content snapshot before any write occurs.

## When to Prefer patch Over Python

- Small, unambiguous edits where `old_string` is clearly unique (no similar content elsewhere)
- Edits where the section boundary is unambiguous in context
- Restoring from git (version bumps, etc.)

## When to Prefer Python Pathlib

- Files >80k chars with dense `---` section dividers
- Any situation where `patch` reports unexpected match counts
- Concurrent multi-agent environments
- Edits where the target section has internal `---` markers that could confuse global search

## Quick Reference

| Signal | Likely cause | Fix |
|--------|-------------|-----|
| `patch`: "Found 4 matches" | `patch` normalization vs Python count | Python `pathlib` slicing, confirmed unique by `count() == 1` |
| `patch`: "modified since you last read" after clean re-read | Concurrent sibling wrote file | Atomic write with in-memory content; do NOT re-read |
| `patch`: "partial view" warning | Pagination via `skill_view` or `read_file(offset=...)` | Re-read via `pathlib`, then patch works |

---

Return to: [hermes-agent-skill-authoring SKILL.md](file:///home/bb/hermes-agent/skills/software-development/hermes-agent-skill-authoring/SKILL.md)