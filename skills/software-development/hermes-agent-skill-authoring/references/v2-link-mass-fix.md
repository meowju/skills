# V2 Link Mass-Fix: Pattern and Real Case

> Extracted from hermes-agent-skill-authoring pitfall 51 (v1.0.52). Full case: ai-money-maker Run 137.

---

## What Are V2 Malformed Links

V2 links are markdown reference links where the display text and URL both contain `references/`:

```
V2 (broken):    [references/ai-monetization-frameworks.md](references/ai-monetization-frameworks.md)
Correct form:   [ai-monetization-frameworks.md](references/ai-monetization-frameworks.md)
```

The `→ Full content:` label is present but the link text has the full path instead of the bare filename.

**Real cases:**
- ai-money-maker v3.33: 59 V2 instances, 649 chars freed. At 98,585 with 1,415 headroom → new section (1,124 chars) landed at 99,059 with 941 headroom.
- wealth-mindset v1.115: 29 V2 instances, 319 chars freed. At 99,130 with 870 headroom → Bezos PR/FAQ + Blue Origin subsections landed at 99,935 with 65 headroom. V2 fix was the prerequisite that unlocked the expansion.

---

## The Mass-Fix Pattern

Run BEFORE getting section positions — V2 fix does not change positions (same-length replacements), but positions must be computed from the fixed content.

```python
import re, pathlib, shutil

skill_path = "/opt/data/skills/productivity/ai-money-maker/SKILL.md"
original = pathlib.Path(skill_path).read_text()

# Step 1: Fix all V2 links
v2 = re.compile(r'\[references/([^]]+)\.md\]\(references/([^)]+)\.md\)')
content_fixed = v2.sub(lambda m: f'[{m.group(1)}.md](references/{m.group(1)}.md)', original)
print(f"V2 fixed: {len(original):,} -> {len(content_fixed):,} chars")

# Step 2: Get section positions FROM FIXED content
all_sections = [(m.start(), m.group(1), m.group(2).strip()) for m in re.finditer(
    r'\n## ([一二三四五六七八九十百千万VI]+)、(.+)', content_fixed)]

# Step 3: Build final content from content_fixed (not original)
# Example: insert new section at position of section 五十七
pos57 = next((p for p, n, _ in all_sections if n == '五十七'), None)
final_content = content_fixed[:pos57] + new_section + content_fixed[pos57:]

# Step 4: Version bump inline
final_content = final_content.replace('version: X.Y.Z  # Run N:', 'version: X.Y.Z+1  # Run N+1:', 1)

# Step 5: Write via temp (WSL persistence workaround)
tmp_path = "/tmp/skill-runXXX.tmp"
pathlib.Path(tmp_path).write_text(final_content, encoding='utf-8')
shutil.move(tmp_path, skill_path)

# Step 6: Verify immediately
verified = pathlib.Path(skill_path).read_text(encoding='utf-8')
assert '## NewSectionName' in verified
assert len(verified) <= 100_000
```

**Critical order:** V2 fix → positions → build → write. Never get positions from `original` and build from `content_fixed` — the delta causes sections to land in wrong positions.

---

## Detection Only (No Fix)

```python
v2_pattern = r'\[references/([^]]+)\.md\]\(references/([^)]+)\.md\)'
matches = list(re.finditer(v2_pattern, content))
print(f"V2 instances: {len(matches)}")
```

## Variant: `.md.md` URL Corruption Precedes V2 Fix

If a prior session ran a regex that doubled `.md` in URLs (e.g., `content.replace('.md)', '.md.md)')`), all reference URLs become `references/F.md.md)`. When the V2 fix regex then runs against this corrupted content, it extracts `F.md` from the display text `references/F.md` and produces `[F.md.md](references/F.md.md)` — doubling `.md` again on every link.

**Fix order for this variant:**
1. `content_clean = content.replace('.md.md)', '.md)')` — restore URLs first
2. Then run the V2 fix on the clean `content_clean`

```python
# Step 0: Undo prior .md.md corruption
content_clean = content.replace('.md.md)', '.md)')

# Step 1: Fix all V2 links on clean content
v2 = re.compile(r'\[references/([^]]+)\.md\]\(references/([^)]+)\.md\)')
content_fixed = v2.sub(lambda m: f'[{m.group(1)}.md](references/{m.group(1)}.md)', content_clean)
```

**Real case:** ai-money-maker Run 167 had 76 `.md.md` URLs from a prior malformed regex. Applied `.md.md) → .md)` first (−228 chars), then V2 fix on clean content. Result: 75 V2 instances fixed, all URLs restored to `references/F.md` format.

---

## Size Impact

| V2 instances | Chars freed |
|---|---|
| 10 | ~110 |
| 30 | ~330 |
| 59 (ai-money-maker case) | ~649 |
| 100 | ~1,100 |

At near-limit conditions (95k+, <5k headroom), mass-fixing V2 links is the difference between being able to add a new section or being blocked.