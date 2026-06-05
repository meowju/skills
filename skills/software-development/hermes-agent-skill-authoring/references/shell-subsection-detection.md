# Shell Subsections: Detection & Repair

## What Is a "Shell Subsection"?

A shell subsection is fix-documentation text (explaining what went wrong and how to fix it) that was accidentally placed as a `###` subsection inside the very section it describes. It occurs when:

1. A session removes a section's body but leaves the `---` boundary AND the section header
2. The next section's content slides into the now-orphaned section, creating a "shell"
3. The fix-documentation text about the problem gets placed as a `### Some Topic` subsection

**Key distinction from pitfall 24's numbered Chinese subsections:**
- Shell subsections have generic bug-description headers (e.g., `### Duplicate Section Header Shell`)
- They contain fix-documentation text, not legitimate topic content
- A duplicate top-level section with the same documentation content also exists in the file
- The duplicate top-level header falls entirely within the shell subsection's byte range, enabling single-pass removal

## Detection

Visible in a structural survey as a `### Generic-Bug-Description-Of-Problem` subsection whose content is fix-documentation text. A duplicate top-level section header with the same documentation content also appears elsewhere in the file.

**Also:** Any `###` subsection with the same content/title as a top-level `##` section elsewhere in the file — the subsection is the displaced copy, not the top-level. The subsection may be arbitrarily embedded inside an unrelated section's body.

**Detection scan:**
```python
import re, pathlib
content = pathlib.Path(skill_path).read_text()
sections = [(m.start(), m.group(1)) for m in re.finditer(r'\n## ([^\n]+)', content)]
subsections = [(m.start(), m.group(1)) for m in re.finditer(r'\n### ([^\n]+)', content)]
# Check: any subsection title matches a top-level section title?
sec_titles = {t for _, t in sections}
for sub_pos, sub_title in subsections:
    if sub_title in sec_titles:
        parent = next((f"## {num}" for sec_pos, num, _ in sections if sec_pos < sub_pos), "NONE")
        print(f"DUPLICATE SUBSECTION: ### {sub_title} inside {parent}")
```

## Fix

When the duplicate top-level header falls entirely within the embedded shell subsection's byte range, a single slice removes both:
```python
new_content = content[:shell_start] + content[shell_end:]
```

The `shell_start` must include the `---` boundary of the parent section. Then verify the parent section's new tail is properly terminated with `---` before the next section.

**After removal:** The parent section's list item marker `-` that preceded the `---` may remain orphaned at the boundary. Fix: replace `\n-\n## Next Section` with `\n---\n## Next Section`.

## Real Case: purpose-finder v4.29.0

Embedded shell subsection at pos 97655–98866 (1,207 chars) contained:
- `### Duplicate Section Header Shell` subsection
- The duplicate top-level `## Framework: Values Clarification (ACT-Inspired)` header at 98070 (inside shell range)

Removing the larger range in one pass eliminated both. File went from 99,881 to 98,670 chars.

The Professional Support section's tail had a bare `\n-\n` orphan (list item marker that was supposed to be removed with the shell). Repaired by:
```python
content = content.replace('\n-\n## Verification', '\n---\n## Verification', 1)
```

## Boundary Corruption from Shell Removal

When a shell subsection is removed via a slice that includes the parent's closing `---`, the resulting boundary may be corrupted:
```
some content\n-\n## Next Section
```
(no blank line between `-` and `##`). This is invisible to casual reading but breaks section parsing.

**Fix:** When bare `-` appears directly before `## Next Section`, replace `\\n-\\n##` with `\\n---\\n##`. Always verify parent section termination after any removal that targets a `---` boundary.