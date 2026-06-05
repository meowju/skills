# Duplicate Reference Links — Detection, Prevention, and Fix

## The Problem

Duplicate `→ Full content:` link lines accumulate silently across sessions. Each line looks intentional to the human eye — both instances appear as normal content — but they are structural duplication that wastes space and corrupts the orphan audit's link-count baseline.

## Three Flavors of Duplicate Reference Links

### Flavor 0: Same-Line Double-Link (The Most Insidious)

The link text (between `[` and `]`) contains the URL twice, so the URL substring appears twice in the same line. Invisible to line-counting and confusing to regex-position-based detection.

Example (a single 69-char line, not two):
```
→ Full content: [ikigai-deep-dive.md](references/ikigai-deep-dive.md)
```

Here `ikigai-deep-dive.md` appears at offset 17 AND offset 35 in the same line. A naive `content.count('references/X.md')` returns 2 even when the link appears exactly once.

**Safe detection:**
```python
# Count by full link LINE, not URL substring — each line contributes exactly 1
all_links = re.findall(r'→ Full content: \[([^\]]+)\]\(([^()]+\.md)\)', content)
url_counts = Counter(url for _, url in all_links)
# url_counts['references/X.md'] == 1 → NOT a duplicate, skip
# url_counts['references/X.md'] == 2 → true duplicate, remove second line
```

**Fix with position-based line removal (not URL-based counting):**
```python
# Remove the second occurrence by byte position, not URL counting
line_start = content.rfind('\n', 0, second_pos) + 1
line_end = content.find('\n', second_pos)
content = content[:line_start] + content[line_end+1:]
```

### Flavor 1: Consecutive Duplicate Lines

Two identical `→ Full content: references/X.md` link lines appear in immediate succession.

```
→ Full content: [references/buffett-frameworks.md](references/buffett-frameworks.md)
→ Full content: [references/buffett-frameworks.md](references/buffett-frameworks.md)
```

Detection: count occurrences of each `→ Full content: references/` URL. Any count > 1 is suspicious.

### Flavor 2: Duplicate in Same Paragraph (Invisible)

A `→ Full content:` link is appended to a bullet that already contains the same link. Both lines are valid markdown and look intentional:

```markdown
- [x] Completed the Buffett analysis section
  → Full content: [references/buffett-frameworks.md](references/buffett-frameworks.md)
- [x] Cross-referenced with annual reports
  → Full content: [references/buffett-frameworks.md](references/buffett-frameworks.md)
```

The orphan audit (missing from disk) misses this. The duplicate-link-count audit counts the pair as one occurrence regardless of repetition. Detection: scan for `→ Full content:[^\n]+\)` lines where consecutive occurrences of the same URL appear within 200 chars of each other.

### Flavor 3: Malformed Link Text

The link text uses the bare path instead of a human-readable label. This is not invalid markdown, but it signals that the reference was inserted programmatically without label attention:

```
→ Full content: [references/research-ground-truth.md](references/research-ground-truth.md)
```

vs the correct form:

```
→ Full content: [Research Ground Truth](references/research-ground-truth.md)
```

Detection: `re.search(r'→ Full content: \[references/[^]]+\]', content)` finds all malformed link texts. Fix: replace the bare path with a proper label.

## Real Case: break-recovery Run 9

File at 99,807 chars with 193-char headroom (dangerously near limit). Six duplicate `→ Full content:` links found:

- `references/attachment-styles.md` (2×)
- `references/resilience-research.md` (2×)
- `references/research-ground-truth.md` (2×) — one was also malformed
- `references/communication-scripts.md` (2×)
- `references/forgiveness-phase.md` (2×)
- `references/forgiveness.md` (2×)

Removing the second occurrence of each freed 1,140 chars, creating 1,333 headroom — enough to add the next content cycle's deepening. The file was clean enough that no structural corruption was present; the duplicates were the only issue.

## Fix Pattern

```python
import re, pathlib
from collections import Counter
content = pathlib.Path(skill_path).read_text()

# Step 1: Count by FULL LINK LINE (not URL substring — see Flavor 0)
all_links = re.findall(r'→ Full content: \[([^\]]+)\]\(([^()]+\.md)\)', content)
url_counts = Counter(url for _, url in all_links)
dups = {k: v for k, v in url_counts.items() if v > 1}

# Step 2: For each true duplicate, remove the second occurrence by position
for ref_url, count in dups.items():
    matches = list(re.finditer(re.escape(ref_url), content))
    if len(matches) >= 2:
        second_pos = matches[1].start()
        # Remove the entire line containing second_pos
        line_start = content.rfind('\n', 0, second_pos) + 1
        line_end = content.find('\n', second_pos)
        if line_end == -1:
            line_end = len(content)
        content = content[:line_start] + content[line_end+1:]
        print(f"Removed duplicate: {ref_url}")

# Step 3: Fix malformed link texts (bare path as label)
malformed = re.findall(r'→ Full content: \[(references/[^]]+)\]\((references/[^)]+\.md)\)', content)
for bare_text, actual_url in malformed:
    old = f'→ Full content: [{bare_text}]({actual_url})'
    new_label = actual_url.replace('references/', '').replace('.md', '').replace('-', ' ').title()
    new = f'→ Full content: [{new_label}]({actual_url})'
    content = content.replace(old, new, 1)
    print(f"Fixed malformed link: {bare_text} → {new_label}")

pathlib.Path(skill_path).write_text(content)
```

**Real case (ai-money-maker Run 183):** Section 41 contained 11 consecutive `ai-leverage-path.md` links — visually identical, raising false assumption of mass duplication. Full link-line extraction revealed each had unique surrounding text (e.g., "杠杆闭环", "融资节点", "退出时机" etc.). Only 1 was a true V3 consecutive duplicate. Removed 1, kept 10.

**Verification trap:** After removal, URL-substring count still shows 11 (the bare URL appears twice per line — Flavor 0). The correct verification uses full link-line count:
```python
from collections import Counter
url_counts = Counter(url for _, url in
    re.findall(r'→ Full content: \[([^\]]+)\]\(([^()]+\.md)\)', content))
assert url_counts['references/ai-leverage-path.md'] == 10  # not raw matches
```

## Prevention: Post-Patch Duplicate Check

After ANY patch that adds a `→ Full content:` link line, run this before writing:

```python
all_links = re.findall(r'→ Full content: \[([^\]]+)\]\(([^()]+\.md)\)', content)
from collections import Counter
url_counts = Counter(url for _, url in all_links)
dups = {k: v for k, v in url_counts.items() if v > 1}
assert not dups, f"Duplicate links found: {dups}"
```

This catches the introduction of duplicates at write time, not after the file is already corrupted.

## Detection: read_file Truncation Masking True File Size

The `read_file` tool's metadata hint (`file_size: N`) can be stale in WSL environments, reporting values ~2x the actual size. A truncated display (showing only the first portion of a large file) compounds the problem — the tool shows partial content with a misleading size hint that makes the file appear much larger than it is.

**Real case:** break-recovery SKILL.md displayed as `total_lines: 1297, file_size: 100629` with `truncated: true` hint. Python confirmed actual size: 98,667 chars. The metadata was slightly stale in this case (not 2x), but the truncation flag made it unclear whether the displayed portion was the full file or just the head.

**Rule:** Always validate size with `len(pathlib.Path(skill_path).read_text())` in the same session. Never trust tool metadata hints for size in WSL.