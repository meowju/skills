# Session Learning: Near-Limit Patch Strategy and Orphan Audit Patterns

> Extracted from wealth-mindset SKILL.md expansion session (v1.88.0 → v1.89.0).

## Context

File: `/opt/data/skills/productivity/wealth-mindset/SKILL.md`
State at session start: 98,463 chars (headroom: 1,537)
State at session end: 99,658 chars (headroom: 342)

The session expanded the Unstoppable Execution section by replacing a 420-char execution stack with a 1,615-char expanded version — net +1,195 chars.

## Key Learning: Python String Replacement Over patch on Near-Limit Files

When the file is >98k chars and headroom is <2,000, `patch` tool failures are likely (file over limit before write completes). Python string replacement via `pathlib` is more reliable because:

1. You compute all deltas in memory before writing
2. You can verify `len(new_content) <= 100_000` before the write
3. The `shutil.move()` workaround handles WSL persistence issues

Pattern used:
```python
import pathlib, shutil

path = "/opt/data/skills/productivity/wealth-mindset/SKILL.md"
content = pathlib.Path(path).read_text()

# Confirm uniqueness
assert content.count(old_block) == 1, f"Not unique: {content.count(old_block)} matches"

# Replace
new_content = content.replace(old_block, new_block, 1)

# Verify before write
assert len(new_content) <= 100_000, f"TOO LARGE: {len(new_content):,}"

# Version bump
new_content = new_content.replace(old_version, new_version, 1)

# Atomic write via temp path (WSL persistence workaround)
tmp_path = "/tmp/skill-temp.md"
pathlib.Path(tmp_path).write_text(new_content)
shutil.move(tmp_path, path)

# Verify post-write
verified = pathlib.Path(path).read_text()
assert len(verified) <= 100_000
assert "TARGET_CONTENT" in verified
```

## Key Learning: Universal Orphan Audit vs. Standard Orphan Audit

Two distinct patterns exist. Always start with the universal.

**Standard pattern** (only catches `→ Full content:` labeled links):
```python
full_links = re.findall(r'→ Full content:\s*\[([^\]]+)\]\(([^()]+\.md)\)', content)
# Bug in second capture group: [^)]+ consumes the ) char
```

**Universal pattern** (catches ANY bracketed link):
```python
all_links = re.findall(r'\[([^\]]+)\]\(([^()]+)\)', content)
linked = {url for text, url in all_links if url.startswith('references/')}
orphans = sorted(set(f.name for f in ref_dir.glob("*.md")) - {url.replace('references/', '') for url in linked})
```

**When standard fails:** wealth-mindset uses plain `[references/X.md](references/X.md)` format. Running standard audit found 0 linked files → 27 orphans reported. Universal found all 27 correctly linked. Rule: if audit reports >20 orphans on a 50+ section skill, the pattern is wrong, not the skill.

## V2 Malformed Links: 29 Instances Found and Fixed

The session audit found all 29 reference links in wealth-mindset were V2-malformed (`[references/X.md](references/X.md)` format). This was confirmed by the universal orphan audit returning 0 true orphans — V2 links have the bare filename in the URL so the orphan set-difference works correctly. However, the 319 chars of V2 overhead was consuming the limited headroom at 99,449 chars (551 headroom).

V2 fix: `re.sub(r'\[references/([^]]+)\.md\]\(references/([^)]+)\.md\)', lambda m: f'[{m.group(1)}.md](references/{m.group(1)}.md)', content)` freed 319 chars, bringing headroom to 870. This was the prerequisite that enabled the Bezos expansion patch to land.

## Structural Note: Duplicate Link Lines in wealth-mindset

The orphan audit also found duplicate link pairs (same URL appearing 2-4× across different sections). These are cross-section references, not intra-section duplicates — each represents a reference link that legitimately appears in multiple sections. The audit flagged:

- `references/musk-frameworks.md` (2× — different sections)
- `references/naval-framework.md` (2× — different sections)
- `references/dalio-frameworks.md` (2× — different sections)
- `references/financial-frameworks.md` (4× — appears in multiple section transition points)

These are NOT the same as consecutive duplicate lines within a paragraph. They represent legitimate cross-section referencing and are intentionally preserved.

## Headroom at Session End: 65 chars

The skill has 65 chars of headroom after v1.115 update (V2 fix + Bezos expansion). This is critically low — below the minimum safe buffer (500). The next expansion cycle MUST either:
1. Migrate a large section (5,000+ chars) to `references/` to restore 5,000+ headroom
2. Condense multiple large inline sections before any new content can be added

With only 65 chars of headroom, any patch larger than ~60 chars will fail. The skill is structurally sound (0 V2 malformed links, 0 true orphans, 33 sections), but the headroom crisis means the next run must prioritize space recovery over content addition.

**Pre-run checklist for next session:**
- Run V2 pre-scan (already clean after v1.115)
- Run orphan audit
- Check size: if >99,500, migrate before expanding