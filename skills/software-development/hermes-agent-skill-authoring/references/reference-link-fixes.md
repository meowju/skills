# Reference Link Fixes

## Malformed/Broken/Orphaned Reference Link Fixes

### V2 Malformed Links
**Pattern:** `[references/X.md](references/X.md)` — link text has `references/` prefix, making it redundant and malformed.

**Detection:** `r'\[references/([^]]+\.md)\]\(references/([^)]+\.md)\)'`

**Fix:** Replace with `[X.md](references/X.md)` (remove `references/` from link text).

**Real case:** wealth-mindset v1.111.0 had `[references/time-leverage-wealth.md](references/time-levelage-wealth.md)` in the Time as a Lever section. Fixed by replacing with `[time-leverage-wealth.md](references/time-leverage-wealth.md)`.

---

### Orphan Tail (Broken Reference Link Text)
**Pattern:** A section body ends with a raw text fragment (`-- extended risk frameworks...`) that was meant to be a reference link but lost its `→ Full content: [` prefix. No markdown link, just orphan suffix.

**Detection:** Scan section tails for text after `---` that looks like reference link fragments without the prefix.

**Fix:** Create the reference file and replace orphan tail with proper `→ Full content: [filename.md](references/filename.md)` link.

---

### Orphan Reference Files
**Pattern:** A `references/` file exists on disk but is not linked from SKILL.md.

**Detection:**
```python
import re, pathlib
content = pathlib.Path(skill_path).read_text()
ref_dir = pathlib.Path(skill_path).parent / "references"
# Universal pattern — catches ANY bracketed link regardless of label text
all_links = re.findall(r'\[([^\]]+)\]\(([^()]+)\)', content)
linked = {url for text, url in all_links if url.startswith('references/')}
linked_bare = {url.replace('references/', '') for url in linked}
existing_files = {f.name for f in ref_dir.glob("*.md")}
orphans = sorted(set(existing_files) - linked_bare)
```

Note: Use universal pattern, not `→ Full content:` only — skills that use raw markdown link format are invisible to the latter.

---

### Consecutive Duplicate Reference Links
**Pattern:** Same `→ Full content: references/X.md` appears twice within 200 chars.

**Detection:**
```python
from collections import Counter
lines = re.findall(r'→ Full content: \[([^\]]+)\]\(([^()]+\.md)\)', content)
url_counts = Counter(url for _, url in lines)
dups = [(k, v) for k, v in url_counts.items() if v > 1]
```
Note: Count by full link LINE, not URL substring — a single link like `[X.md](references/X.md)` contains the URL twice within the same line, and naive `content.count(url)` would report 2 matches for 1 actual link.

---

### Boundary Corruption: Reference Link Before `###` Without Blank Line
**Pattern:** `→ Full content: [file.md](references/file.md)\n### Sub` — missing `\n\n` between the link and subsection header.

**Fix:** Insert `\n\n` between the link line and the `###` header. Do NOT remove the link.

---

### WSL Sandbox Write Persistence Workaround
**Pattern:** `pathlib.write_text()` reports success but `git diff` shows no changes.

**Detection:** `git diff` returns empty after confirmed Python write.

**Fix:** Write to `/tmp/` first, then `shutil.move()`:
```python
import pathlib, shutil
pathlib.Path("/tmp/skill-temp.md").write_text(new_content)
shutil.move("/tmp/skill-temp.md", skill_path)
```
