# Condense + Add: Atomic Headroom Recovery Pattern

## The Core Problem

When a near-limit skill file (e.g., 98k chars, 1.5k headroom) needs:
1. A large section condensed → migrated to `references/`
2. A new section added → net new content

These two operations have a combined delta that fits within headroom, but sequential patching fails because the second patch alone doesn't fit.

**Example:** Section 82 at 3,117 chars condensed to 1,240 chars (−1,877), new Section 88 added at 2,514 chars → net +637 → 98,436→99,073 ✓

If done as two sequential patches:
- Patch 1 (condense section): succeeds, file now ~96.5k
- Patch 2 (add new section): size gate says 2,514 doesn't fit in ~3,500 remaining → FAILS

But combined delta = −1,877 + 2,514 = +637, which fits within 1,500 headroom.

## The Atomic Pattern

```python
import pathlib, re

skill_path = "/opt/data/skills/productivity/ai-money-maker/SKILL.md"
content = pathlib.Path(skill_path).read_text()

# 1. Find section boundaries
m_old = re.search(r'\n## 旧章节标题', content)
m_next = re.search(r'\n## 下一个章节标题', content)
old_start = m_old.start()
next_start = m_next.start()

# 2. Create condensed version
condensed = """..."""

# 3. Create new section
new_section = """..."""

# 4. Build new content IN MEMORY — both changes at once
new_content = content[:old_start] + condensed + new_section + content[next_start:]

# 5. Bump version atomically
new_content = re.sub(r'version:\s*X.Y.Z', 'version: X.Y.Z', new_content, count=1)

# 6. Validate size BEFORE writing
assert len(new_content) <= 100_000, f"TOO LARGE: {len(new_content):,}"

# 7. Single atomic write
pathlib.Path(skill_path).write_text(new_content)
```

## Key Rules

1. **Always migrate a section that already has a reference link.** The reference file already exists → no orphan risk, no file creation to coordinate.
2. **Compute combined delta before touching the file.** If net savings or net addition fits within 100k, proceed atomically.
3. **Never do two sequential patches on a near-limit file.** The cumulative offset problem (pitfall 30b) applies to sequential patches, but more importantly: patch 2 may fail the size gate even when combined delta fits.
4. **Write the reference file before editing SKILL.md.** The orphan audit checks that every `references/` file is linked — create the file and link it in the same session.

## Related Pitfalls

- Pitfall 30b: Dense `---` dividers cause cascade offset failures on sequential patches
- Pitfall 32b: `.find()` returning -1 causes silent truncation
- Pitfall 38: Version bump must be atomic with content change