# V2 Detection: Regex False Positives from Parenthetical Text

## The Problem

The documented V2 detection regex:
```python
v2_matches = re.findall(r'\[([^\]]+\.md)\]\(references/([^)]+\.md)\)', content)
```

When applied to ai-money-maker v4.5.4 (99,863 chars), it returned **109 matches** — all false positives.

The cause: descriptive link text (Chinese) that contains a `.md` filename string as a substring, and that same filename also appears inside a parenthetical comment on the same line:

```
→ Full content: [ai-b2b-exit-2025.md](references/ai-b2b-exit-2025.md)（企业谈判·合同架构·退出时机完整案例）
```

The regex `[^)]+\.md` greedily captures through the `）` character (Chinese closing paren, not ASCII `)`), so the URL group captures `ai-b2b-exit-2025.md）` — but since the filename is the same in both groups, the backreference `\1` still matches.

**Result:** 109 detected "V2 links" where the actual file has 0 V2 malformed links after manual inspection.

## The Fix: String-Operation Approach

Instead of regex, use string operations on the actual `→ Full content:` link lines:

```python
import re

# Find actual → Full content: links (string scan, not regex markdown match)
corrupted = []
for m in re.finditer(r'→ Full content:[^\n]+\)', content):
    link_end = m.end()
    next_nl = content.find('\n', link_end)
    next_header = content.find('\n##  ', link_end)  # two trailing spaces = top-level
    between = content[link_end:next_header]
    if not between.startswith('\n\n'):
        corrupted.append(f"missing blank line before ## at pos {m.start()}")
    # V2 check: does link text equal URL basename?
    line = m.group(0)
    # Extract text between [ and ]
    lbra = line.find('[')
    rbra = line.find(']')
    if lbra != -1 and rbra != -1:
        link_text = line[lbra+1:rbra]
        if link_text.endswith('.md') and link_text in line:
            # Could be V2 — check if text equals URL basename
            url_start = line.find('(references/') + len('(references/')
            url_end = line.find(')', url_start)
            url_basename = line[url_start:url_end]
            if link_text == url_basename:
                print(f"V2 at pos {m.start()}: text={link_text}, url={url_basename}")
```

## Key Lesson

The regex approach `r'\[([^]]+\.md)\]\(references/\1\)'` is unreliable in skills with Chinese parenthetical text. The `[^)]+` character class does NOT stop at Chinese punctuation — Python regex treats `)` as the only delimiter, so `）` (U+FF09) passes through. Use string operations or the correct regex `[^()]+` (excludes both `(` and `)`):

```python
# Correct: excludes parentheses on both sides
v2_suspect = re.findall(r'\[([^\]]+\.md)\]\((references/[^()]+\.md)\)', content)
```

The `[^()]+` for the URL group correctly stops at any `(`, preventing the Chinese `）` from being captured.

## Real Case

- **File:** ai-money-maker v4.5.4 (SKILL.md, 99,863 chars)
- **Tool result:** 109 "V2 matches" from regex
- **Manual inspection:** 0 actual V2 malformed links (section 八十八 had the correct form already)
- **Root cause:** The regex was matching `ai-b2b-exit-2025.md` inside the parenthetical `（企业谈判·合同架构·退出时机完整案例）` as a URL, since the Chinese `）` doesn't stop the `[^)]+` character class
- **Fix applied:** N/A (file was already correct — the detection was wrong, not the file)