# Condensation + Replacement Patterns

## Section-Boundary Uniqueness Trap

When condensing a section by replacing the full body with a shorter summary, the `old_string` must be unique within the file. A generic phrase like "Common Pitfalls" appears in multiple places — it will hit the wrong occurrence, leaving the real section in place while inserting the condensed version elsewhere.

**Dense-divider cascade failure:** Skills with multiple `---` section dividers throughout the body (not just frontmatter) are structurally different from skills with one `---` per section. When inserting reference links at absolute positions computed from the original file, each insertion shifts all subsequent positions — subsequent patches land in the wrong section.

**Real case (ai-money-maker v2.59→2.72):** 3 consecutive patches using position + cumulative_offset all inserted references into adjacent wrong sections. The skill had 57 numbered sections and multiple `---` section dividers throughout the body.

**Multi-step find-chain truncation:** When using `content.find(block)` then `content.find(block[suffix:])` for multi-step block extraction, if the second `find()` returns `-1` (not found), arithmetic like `pos - 1` with a `-1` result produces a negative index. `content[:neg]` or `content[neg:pos]` with a negative index silently produces an empty or near-empty string — the file appears intact in memory but writes as truncated garbage.

**Real case:** `pos2 = content.find(bad_block[10:])` returned `-1`; `pos - 1 = -2`; `content[pos:pos2]` → `content[-2:-1]` = `''`; entire file written as 49k of empty head + first 580 lines.

**Fix: Positional slicing as first resort.** For targeted replacements in large files:
```python
import pathlib
path = "/opt/data/skills/productivity/<name>/SKILL.md"
content = pathlib.Path(path).read_text()

# Find target section boundaries precisely
na_header_pos = content.find("### The Negotiation Architecture: Beyond Salary")
next_sub_pos = content.find("\n### ", na_header_pos + 10)
next_sec_pos = content.find("\n## ", na_header_pos)
na_end_pos = min(s for s in [next_sub_pos, next_sec_pos] if s > na_header_pos)
na_exact = content[na_header_pos:na_end_pos]

# Confirm uniqueness before replacing
assert content.count(na_exact) == 1, f"Duplicate match: {content.count(na_exact)} occurrences"

# Build new content via slicing
new_content = content[:na_header_pos] + na_new + content[na_end_pos:]
pathlib.Path(path).write_text(new_content)
```

**When `.replace()` is safe:** Only when `old_string` is verified unique by `content.count(old_string) == 1` AND the replacement string contains no text that appears elsewhere in the file. Prefer slicing when in doubt.
