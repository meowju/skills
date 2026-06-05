# Universal Orphan Audit Pattern

> Extracted from hermes-agent-skill-authoring SKILL.md pitfall 27i (Run 6 lessons). Real case: wealth-mindset v1.81.0.

## The Problem

The standard orphan audit pattern only matches `→ Full content:` labeled links:

```python
# WRONG — only matches → Full content: links
full_links = re.findall(r'→ Full content:\s*\[([^\]]+)\]\(([^()]+\.md)\)', content)
related_links = re.findall(r'→ Related:\s*\[([^\]]+)\]\(([^()]+\.md)\)', content)
```

Skills using plain markdown links `[filename.md](references/filename.md)` are **invisible** to this pattern. The result: every reference file appears as an orphan even when all are correctly linked.

## Real Case: wealth-mindset v1.81.0

The skill uses `[references/buffett-frameworks.md](references/buffett-frameworks.md)` format throughout — no `→ Full content:` labels. Running the standard audit:
- Standard pattern: found **0** linked references
- 24 existing files appeared as orphans — a complete false positive

The skill was actually clean. The audit was wrong.

## The Universal Pattern

```python
import pathlib, re

skill_path = "/opt/data/skills/productivity/wealth-mindset/SKILL.md"
content = pathlib.Path(skill_path).read_text()
ref_dir = pathlib.Path(skill_path).parent / "references"

existing = {f.name for f in ref_dir.glob("*.md")}

# Universal — catches ANY bracketed markdown link regardless of label text
all_links = re.findall(r'\[([^\]]+)\]\(([^()]+)\)', content)
linked = {url for text, url in all_links if url.startswith('references/')}
linked_bare = {url.replace('references/', '') for url in linked}
orphans = sorted(existing - linked_bare)

print(f"Orphans: {orphans}")  # Empty = all correctly linked
```

The universal pattern matches `[any text](references/file.md)` links regardless of whether the label says `→ Full content:`, `→ Related:`, `→ Full analysis:`, `→ 完整内容:`, `→ 相关资料:`, or has no label at all.

## When to Use Which Pattern

| Skill type | Link format | Audit pattern |
|---|---|---|
| Peer-standard (ai-money-maker) | `→ Full content:` / `→ 完整内容:` | Standard `→ Full content:` + `→ Related:` scan |
| Plain markdown (wealth-mindset) | `[filename.md](references/)` | Universal `\[...\]\((...)\)` scan |
| Unknown / first audit | Any | Universal — always start here |

## The Correct Sequence

1. **Always start with the universal pattern** when auditing a skill for the first time — it handles all link label conventions.
2. Only switch to the `→ Full content:` variant when you've confirmed the skill consistently uses that exact label format everywhere.
3. If the universal pattern reports zero orphans and the skill clearly uses `→ Full content:` labels, the skill is clean.
4. If the universal pattern reports orphans but you suspect the skill uses `→ Full content:` format, run the standard audit to compare.

## Why the Standard Pattern Fails on Plain Markdown Skills

The `→ Full content:` pattern requires the literal text `→ Full content:` before the link. A plain markdown link like:
```
[references/buffett-frameworks.md](references/buffett-frameworks.md)
```
contains no `→ Full content:` text, so the pattern matches nothing.

The second capture group in the standard pattern also has a subtle bug: `[^)]+` consumes the `)` character itself (since `)` is not excluded from the character class), so the URL captured is truncated. The correct pattern uses `[^()]+` (excludes `(` and `)`):
```python
# Correct: excludes ( and ) from the URL capture
full_links = re.findall(r'→ Full content:\s*\[([^\]]+)\]\(([^()]+\.md)\)', content)
```

## Pre-commit: Run Even When You Didn't Touch references/

The most common reason an audit catches 20+ orphans is NOT that links are missing — it's that prior sessions created files and linked them, then the next session added more files and linked those, but the first batch was never properly connected. The orphan debt accumulates silently.

**Rule:** Always run the universal orphan audit before ending ANY session that edited a skill with a `references/` directory — regardless of whether THIS session touched references/. One session's clean edit doesn't clear prior sessions' orphan debt.

Real case: ai-money-maker Run 8 edited SKILL.md only (no references/ files created). The pre-write audit found 27 orphaned files — all from prior sessions, none from this one. The file was clean in-session but carried historical orphan debt into the next session.

## Also Check for Duplicate Link Lines

After orphan audit, run duplicate link count:
```python
from collections import Counter
dups = [(k, v) for k, v in Counter(
    re.findall(r'→ (?:Full content|Related): ([^\n]+)', content)
).items() if v > 1]
print(f"Duplicate link lines: {dups}")
```

Consecutive duplicate reference links (same URL within 200 chars twice) are missed by both orphan and duplicate-link-count audits — detectable only by scanning for consecutive occurrences of the same URL.

## WSL Verification Note

For user-local skills at `/opt/data/skills/` (not git repos), git diff is unavailable. Use Python `pathlib.read_text()` as the only authoritative verification after any patch.