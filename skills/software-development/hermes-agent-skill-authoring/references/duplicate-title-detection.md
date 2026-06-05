# Duplicate Title Detection in Multi-Session Skills

> Real case: ai-money-maker v3.60 Run 161. Section 八十四 and section 九十二 had **identical titles** ("AI + 教育培训：被98%的AI创业者忽视的万亿刚需市场") but different section numbers and different content. The duplicate was invisible to the section-number duplicate scanner. Detection required title-level comparison.

## Why Section Numbers Catch This but Titles Don't

The standard structural survey catches duplicate **section numbers** (two `## 五十九、` headers). But skills that grew across 150+ runs can develop duplicate **titles** — sections with different numbers but identical display names. This happens when:
- A session adds a section on topic X with title T
- A later session adds a different (usually shorter or older) section on the same topic, same title T, different number N
- Both pass the number-duplicate scan because N ≠ M
- The skill_view tool shows both titles in navigation, creating confusion

## Detection Pattern

```python
import re, pathlib
from collections import Counter

skill_path = "/opt/data/skills/productivity/ai-money-maker/SKILL.md"
content = pathlib.Path(skill_path).read_text()

sections = [(m.start(), m.group(1), m.group(2).strip()) for m in re.finditer(
    r'\n## ([一二三四五六七八九十百千万VI]+)、(.+)', content
)]

titles = [t for _, _, t in sections]
title_counts = Counter(titles)
dup_titles = {k: v for k, v in title_counts.items() if v > 1}

for title, count in dup_titles.items():
    positions = [(num, pos) for pos, num, t in sections if t == title]
    print(f"\nDuplicate title '{title}' appears {count}x:")
    for num, pos in positions:
        next_pos = next((p for p, _, _ in sections if p > pos), len(content))
        size = next_pos - pos
        has_ref = "→ Full content:" in content[pos:next_pos] or "→ 完整内容:" in content[pos:next_pos]
        print(f"  ## {num}、 pos={pos} size={size:,} has_ref={has_ref}")
```

## Decision Rule: Which to Remove?

When duplicate titles are found:

1. **Keep the more detailed version** — the one with `→ Full content:` reference links and richer content
2. **Remove the less detailed/larger inline version** — the one without reference links and more raw content inline
3. **If neither is reference-linked:** keep the larger one (more content) and migrate to references/ if needed
4. **If both have reference links:** keep the one that appears earlier in file order (chronologically older session = already had a chance to be refined)

**Real case (ai-money-maker Run 161):**
- 八十四 (pos 84,008): 1,624 chars, no reference link, older session (Run 152)
- 九十二 (pos 94,228): 3,555 chars, no reference link initially, newer session (Run 159)
- Action: Migrated 九十二 body to references/, kept 九十二 as the container, deleted 八十四 entirely

## Key Insight

The duplicate TITLE scanner is separate from the duplicate NUMBER scanner. Run both:
```python
# Duplicate numbers
nums = [n for _, n, _ in sections]
dup_nums = {k: v for k, v in Counter(nums).items() if v > 1}

# Duplicate titles  
titles = [t for _, _, t in sections]
dup_titles = {k: v for k, v in Counter(titles).items() if v > 1}

print(f"Duplicate numbers: {dup_nums}")
print(f"Duplicate titles: {dup_titles}")
```

**Never assume one scan covers the other.** A skill can have zero duplicate numbers but N duplicate titles.