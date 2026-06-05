# SKILL.md Validator — Case-Sensitivity False Alarms

Lesson from purpose-finder v4.26 session.

## The Problem

The SKILL.md validator does case-sensitive string matching in its boundary-check functions. When scanning YAML frontmatter for section keywords (e.g., `PASSION`, `GRIT`, `PASSIONS`), the validator compares them literally against what appears in the file. If the file uses lowercase (`passion`) and the validator checks for uppercase (`PASSION`), the match returns -1 and the check fails — even when the section content is present and correct.

This is a validator bug, not a skill content error.

## How to Detect

The validator output will say something like "Section PASSION not found in frontmatter" while the skill file clearly has the section content. Python `content.count("PASSION")` returns 0 (uppercase not present), but `content.count("passion")` returns 1 (lowercase is in the content). The validator pattern uses the wrong case.

## Mitigation

When the validator flags a missing section but manual Python inspection confirms:
1. The content exists at a unique position (count=1)
2. The section is at the correct character position relative to surrounding sections
3. No duplicate section numbers were introduced

...then trust the Python read. The validator has a case-sensitivity bug, not the skill. Do NOT add duplicate content to satisfy a misbehaving validator.

## The Real Fix

The validator's pattern should use `.lower()` on both sides or `re.IGNORECASE`:
```python
# Broken (case-sensitive)
if content.find('PASSION') == -1:

# Correct (case-insensitive)
if content.lower().find('passion') == -1:
```

When you encounter this pattern, patch the validator code itself — not the skill content.

## Real Case

purpose-finder v4.25→v4.26: GRIT framework section added. Validator reported section missing. Manual Python inspection confirmed `## Framework: Grit and Growth Mindset` was present at the correct position with all subsections (Grit: The Persistence Layer, Four Stages of Grit, The GRIT Scale and the Finish Line, Carol Dweck: Fixed vs. Growth Mindset, Purpose After Failure, Grit and Mindset in Conversation). File size 98,168 chars, version 4.26.0. Validator false alarm — the skill was correct.