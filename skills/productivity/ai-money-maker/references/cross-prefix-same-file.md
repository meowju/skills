# Cross-Prefix Same-File References Are Intentional, Not Duplicates

## The Case

When the same reference file appears twice in SKILL.md — once with `→ Full content:` and once with `→ 完整内容：` (or `→ Related:`) — these are NOT true duplicates. The two prefixes serve different narrative purposes:

- `→ Full content:` signals English-language or western-market context
- `→ 完整内容：` signals Chinese-language or Asia-market context
- `→ Related:` signals tangential or supplementary connection

A duplicate-detection scan that only counts occurrences of the same file (without checking prefix type) will flag these as duplicates and incorrectly remove one.

## The Real Case: ai-money-maker v3.7.5

`ai-leverage-path.md` appeared once with `→ Full content:` (position ~94,822) and once with `→ 完整内容：` (position ~96,262). Gap: 1,440 chars — same file, two different prefix types, both legitimate.

A raw Counter sweep flagged it as a duplicate pair. Manual inspection revealed:
- First instance: within a western-market B2B context (Leverage Path section)
- Second instance: within a Chinese-market 信息差套利 context

Both references were correct for their respective sections.

## Correct Detection Logic

```python
from collections import Counter

# WRONG — treats cross-prefix as duplicates
all_full = re.findall(r'→ Full content: [^\n]+', content)
for k, v in Counter(all_full).items():
    if v > 1:
        print(f"DUPLICATE: {k}")  # False positive for cross-prefix references

# CORRECT — only flag SAME-PREFIX duplicates within 200 chars
# Scan for consecutive duplicate lines (within 200 chars = same paragraph)
duplicate_pairs = []
links = list(re.finditer(r'→ (?:Full content|Related|完整内容): [^\n]+', content))
for i in range(len(links)-1):
    gap = links[i+1].start() - links[i].end()
    if gap < 200 and links[i].group() == links[i+1].group():
        duplicate_pairs.append((links[i].group(), gap))
```

## Rule

- **Same file, different prefix** → always intentional cross-reference
- **Same file, same prefix, consecutive within 200 chars** → V3 duplicate, delete one
- **Same file, same prefix, >200 chars apart** → legitimate cross-section reference

## Metadata Tag

This case is a pitfall-class lesson for reference-link duplicate detection. It applies to:
- Any skill using bilingual reference links (English + Chinese prefixes)
- Any skill where the same file serves different vertical contexts
- Any cron-cyclical skill where different runs may insert the same reference independently

The fix: add this detection rule to the skill-authoring workflow as a permanent pitfall (pitfall 44 in ai-money-maker).