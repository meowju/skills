# Ghost Section Headers: Detection, Fix, and Prevention

> Real case: ai-money-maker v3.9.1. Ghost header `→ ## 二十六、AI心理健康与情感经济` at position 48,751 inside section 二十五's body. The `→ ` prefix made it a corrupted reference link text artifact, not a real section header. Invisible to section-number scanners because it lacked a proper preceding `\n\n## ` pattern.

## What Is a Ghost Section Header

A markdown link whose **display text** contains `## N、` (a section header pattern). When the link renders, the display text shows a section-like header but the actual structural position is inline text inside a parent section.

The tell: a line starting with `→ ## N、` — the `→ ` prefix is a malformed link text artifact. Real section headers are preceded by `\n\n` and are top-level structural elements.

## Why It Forms

During multi-session skill editing, a session inserts a markdown link `[text](references/file.md)` where `text` contains `## N、` (e.g., from a section title being used as link text). The `→ ` prefix in `→ ## 二十六、` comes from the link label format: `→ Full content: [references/...]`. When the link text itself is a section header pattern, it renders ambiguously.

## Detection

```python
import re, pathlib
skill_path = "/opt/data/skills/productivity/ai-money-maker/SKILL.md"
content = pathlib.Path(skill_path).read_text()

# Pattern 1: Lines starting with → and containing ## N、
ghost_lines = [(m.start(), m.group(0).strip())
               for m in re.finditer(r'^→ ## [一二三四五六七八九十]+、[^\n]+', content, re.MULTILINE)]
print(f"Ghost header lines (→ prefix): {ghost_lines}")

# Pattern 2: Any ## N、 lacking proper \n\n prefix
for m in re.finditer(r'## [一二三四五六七八九十]+、', content):
    pos = m.start()
    prefix = content[max(0, pos-5):pos]
    if not prefix.endswith('\n\n'):
        print(f"Suspicious header at pos {pos}: {repr(content[pos:pos+50])}")
        print(f"  Prefix: {repr(prefix)}")
```

In ai-money-maker v3.9.1:
- Ghost line: `→ ## 二十六、AI心理健康与情感经济` at pos 48,751
- Prefix was `\n→ ` (single newline + arrow), not `\n\n` (double newline)
- Confirmed: ghost header was embedded inside section 二十五's body, not a top-level section

## Fix

1. Identify the containing section (the `## N、` that appears before the ghost header in file order)
2. Decide: promote to real section OR demote to `###` subsection
3. Remove the `→ ` prefix
4. Ensure proper `\n\n` before the header
5. Verify section boundaries are intact after the change

In ai-money-maker v3.9.1: the ghost was inside section 二十五. Removed `→ ` prefix and ensured `\n\n` before `## 二十六、`. Result: 48,751 changed from `\n→ ## 二十六、` to `\n\n## 二十六、` (proper section break).

## Prevention

When inserting reference link lines, never let the link text accidentally contain `## ` section markers. The `→ ` prefix on a section-like line is the corruption indicator.

After any session that adds content to a large multi-section skill, run the detection scan to catch ghost headers before they compound.