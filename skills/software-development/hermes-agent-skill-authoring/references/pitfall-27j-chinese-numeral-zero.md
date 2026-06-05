# Pitfall 27j — Chinese Numeral Regex Range Misses U+96F6 (零)

## The Bug

A common pattern in Chinese section-numbering is `## 一百零一、AI 内容平台...` where `零` (U+96F6, "zero") is the bridging character. The character class `[一-千]` covers U+4E00 (`一`) to U+5343 (`千`), but U+96F6 (`零`) is outside that range.

So `re.findall(r'\n## ([一二三四五六七八九十百千万]+)、', content)`:
- ✅ Matches `## 一百、` (U+4E00, U+767E)
- ❌ Does NOT match `## 一百零一、` — the `零` (U+96F6) is silently dropped

Result: section count from regex is wrong, the cron job's "section count" metric is wrong, and any downstream `sections[idx+1]` boundary calculation lands on the wrong section.

## The Fix

```python
# WRONG — misses 零
re.findall(r'\n## ([一二三四五六七八九十百千万]+)、', content)

# CORRECT — explicit enumeration with 零
re.findall(r'\n## ([\u4e00\u4e8c\u4e09\u56db\u4e94\u516d\u4e03\u516b\u4e5d\u5341\u767e\u5343\u4e07\u96f6]+)、', content)

# ALSO CORRECT — short form
re.findall(r'\n## ([\u4e00-\u5343\u96f6]+)、', content)
```

## Detection Signal

If the regex-based section count doesn't match the count of `\n## 数字、` headers found with a manual `grep | wc -l`, the character class is missing a character. Always cross-check with raw counting when introducing or modifying a Chinese-numeral section scanner.

```python
import re, pathlib, subprocess
content = pathlib.Path(skill_path).read_text()
regex_count = len(re.findall(r'\n## ([一二三四五六七八九十百千万]+)、', content))
# Cross-check with grep
raw_count = int(subprocess.check_output(
    ['grep', '-c', r'^## .*、', skill_path]
).decode().strip())
assert regex_count == raw_count, f"Regex missed: {raw_count - regex_count} sections"
```

## Real Case: ai-money-maker Run 216

Initial regex report: 85 sections. Actual count after `grep | wc -l`: 86. The 86th (`## 一百零一、AI 内容平台变现 2025`) had been miscounted because all prior sections ended at 一百 (no 零 in any of them), and no one noticed the regex was incomplete. The bug had been latent since the skill first crossed 100 sections — the regex just silently misreported 85 every time.

After the fix, the regex correctly reports 86 and all boundary calculations work.

## Rule

For any Chinese-numeral section scanner in a skill that may grow past 一百, always include `\u96f6` (零) in the character class. Skills that stay below 一百 may omit it, but once you cross that boundary the omission is a silent counting bug — not a crash, just wrong numbers.

## Prevention Pattern

Store the canonical regex in a constant near the top of any structural survey script:

```python
# Canonical Chinese-numeral section-header regex — must include 零 (U+96F6)
SECTION_HEADER_RE = re.compile(
    r'\n## ([\u4e00\u4e8c\u4e09\u56db\u4e94\u516d\u4e03\u516b\u4e5d\u5341\u767e\u5343\u4e07\u96f6]+)、(.+)'
)
```

Then use `SECTION_HEADER_RE.finditer(content)` everywhere instead of inlining the character class. A single place to fix if the skill ever needs to support 零-亿-兆-京 numerals.
