# Condensation + Duplicate Next-Section Risk

## Pitfall 32c: Condensing a Section Whose Body Ends at the Next Header

**The trap:** When condensing a section whose body naturally ends right before the next section's header (no explicit `---` divider between them), the boundary between the two sections is a single `\n## ` string. Extracting the old section's text for replacement risks cutting *into* the next section's header, making `old_string` span two sections. When `content.count(old_string) == 1` appears to pass, the 1 occurrence actually includes part of the next section — and the replacement corrupts both sections.

**Real case (breakup-recovery Run 8):** Six large sections were each condensed using `.replace()` with old_strings cut at `---` boundaries inside the section body. But the sections contained internal `---` markers (e.g., reference link lines ending `.md)\n---\n`). The extracted old_string's trailing `---` appeared 6+ times within itself. `content.count(old_string) == 1` passed on the wrong string. Subsequent replacements landed in wrong sections, creating embedded clusters. File restored via `git checkout`.

**Detection:** Before any condensation, check if the target section's body ends at the next section header without an intermediate `---`:
```python
import re, pathlib
content = pathlib.Path(skill_path).read_text()
# Find target section
target = "## 四十七"
tpos = content.find(target)
next_h = re.search(r'\n## ', content[tpos+5:])
npos = tpos + 5 + next_h.start()
# Check if there's a --- between target end and next header
between = content[tpos:npos]
if '---' not in between:
    print("NO DIVIDER — condensation is high-risk")
    # Count how many ---\n appear in the full section
    dividers = between.count('\n---')
    print(f"Dividers inside section: {dividers}")
```

**Fix:** Always compute `old_tactical` from a `git show HEAD` clean snapshot — not from a working copy that has been modified in the session. The `git show HEAD:path` gives the authoritative original content with correct boundaries.

```python
import subprocess, pathlib
skill_path = "skills/productivity/ai-money-maker/SKILL.md"
original = subprocess.check_output(
    ["git", "show", f"HEAD:{skill_path}"], text=True
)
# Now use original (not the in-session content) to find boundaries
```

**Prevention:** When condensing, use positional slicing anchored to the section header line + opening paragraph + a verified divider or end-marker — never cut at a generic string that appears elsewhere in the section body.
