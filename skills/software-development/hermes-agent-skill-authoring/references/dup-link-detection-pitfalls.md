# Reference: Duplicate Link Detection — False Positive Patterns

> Extracted from breakup-recovery Run 5 lessons (v4.40.0 → v4.41.0).

## 1. The Regex Captures the Wrong Part of the Link

The pattern `→ (?:Full content|Related): ([^\n]+)` captures the **display text** inside `[]`, not the URL. For a link like:

```
→ Full content: [references/forgiveness.md](references/forgiveness.md)
```

The captured group is `references/forgiveness.md` — which **includes the closing `)`**. The regex is looking for the display text but the `.md)` of the URL looks like a second occurrence of `references/forgiveness.md` (without the leading bracket). Counting `re.findall` hits on this pattern reports **2 occurrences for 1 actual link**.

## 2. What the Regex Actually Matches

For `[references/forgiveness.md](references/forgiveness.md)`:
- Match 1: `references/forgiveness.md` (display text, starts at the `[`)
- Match 2: `references/forgiveness.md` (URL text, found inside `()`)

Both are the same string. The closing `)` is included in the second match because `([^\n]+)` is greedy and the `)` is not excluded.

**Real case (breakup-recovery Run 5):** The audit script found `forgiveness.md: 2 times` via this regex, but scanning for the actual full link text found only ONE occurrence (pos 85011). The regex matched the `)` at the end of the link as a separate "match."

## 3. Correct Detection Code

```python
# CORRECT: Find all → Full content: lines with their exact text
all_lines = [(m.start(), m.group(0)) for m in re.finditer(r'→ Full content: [^\n]+', content)]

# Find consecutive same-URL pairs (within 80 chars = true duplicate)
consecutive_dups = []
for i in range(len(all_lines)-1):
    p1, line1 = all_lines[i]
    p2, line2 = all_lines[i+1]
    if p2 - p1 < 80:
        url1 = re.search(r'\((references/[^)]+\.md)\)', line1)
        url2 = re.search(r'\((references/[^)]+\.md)\)', line2)
        if url1 and url2 and url1.group(1) == url2.group(1):
            consecutive_dups.append((url1.group(1), p1, p2))

# Cross-section same-URL links (gap >80 chars) are INTENTIONAL — do NOT flag as duplicates
```

**Rule:** Only consecutive same-URL pairs (gap <80 chars) are true duplicates. A file linked in two different sections (e.g., `references/communication-scripts.md` in both `Communication Scripts` and `Reconciliation` sections) is correct multi-section referencing — not a bug.

## 4. Quick Diagnostic

```python
import pathlib, re
skill_path = "/opt/data/skills/.../SKILL.md"
content = pathlib.Path(skill_path).read_text()

# Find actual consecutive duplicate pairs
all_lines = [(m.start(), m.group(0)) for m in re.finditer(r'→ Full content: [^\n]+', content)]
dups = [(re.search(r'\(([^)]+\.md)\)', l).group(1), p)
          for i, (p, l) in enumerate(all_lines)
          if i < len(all_lines)-1
          and re.search(r'\(([^)]+\.md)\)', l)
          and re.search(r'\(([^)]+\.md)\)', all_lines[i+1][1])
          and re.search(r'\(([^)]+\.md)\)', l).group(1) == re.search(r'\(([^)]+\.md)\)', all_lines[i+1][1]).group(1)
          and all_lines[i+1][0] - p < 80]
print(f"Consecutive duplicate pairs: {dups}")
```

## 5. The Universal Orphan Audit (For Reference)

The orphan audit also needs the correct pattern to avoid 100% false positives on non-standard link formats:

```python
# Universal: catches any bracketed link regardless of label text
all_links = re.findall(r'\[([^\]]+)\]\(([^()]+)\)', content)
linked = {url for text, url in all_links if url.startswith('references/')}
linked_bare = {url.replace('references/', '') for url in linked}
orphans = sorted(set(f.name for f in ref_dir.glob("*.md")) - linked_bare)
```
