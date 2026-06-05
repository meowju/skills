# SKILL.md Patch Techniques (Large File Repair)

Techniques learned from repairing a corrupted 90k-char ai-money-maker SKILL.md with duplicate section headers, missing sections, and WSL filesystem caching issues.

## Core Principle: Full-Build vs Patch

| Situation | Technique |
|-----------|-----------|
| Small fix (typo, one bullet, tight context) | `patch` with `mode='replace'` |
| Structural change (reorder, insert section, fix numbering) | Full-build with Python |
| Near-limit file (>80k chars, multiple patches) | Single combined patch or full-build |

The `patch` tool is position-based — sequential patches on large files accumulate byte drift and can silently push the file over 100k without error.

---

## Full-Build Technique

```python
import pathlib, re

skill_path = pathlib.Path("/path/to/SKILL.md")
content = skill_path.read_text()

# Compute the complete new content in memory
new_content = content.replace("OLD", "NEW")  # or more complex manipulation

# Validate before writing
assert new_content.startswith("---"), "Missing leading ---"
m = re.search(r'\n---\n', new_content[3:])
assert m, "Missing closing ---"
end_pos = 3 + m.start() + m.end() - 3
fm_text = new_content[3:end_pos-3]
assert 'name:' in fm_text and 'description:' in fm_text
desc_match = re.search(r'description:\s*["\']?(.+?)["\']?\s*\n', fm_text)
assert desc_match and len(desc_match.group(1)) <= 1024
assert len(new_content) <= 100_000, f"File too large: {len(new_content):,}"
assert new_content[end_pos:].strip(), "Empty body"

skill_path.write_text(new_content)
```

---

## Duplicate Section Detection

After any patch that adds or moves a numbered section, scan for duplicates:

```python
matches = list(re.finditer(r'\n## [一二三四五六七八九十]+、', content))
section_nums = [m.group().strip() for m in matches]
from collections import Counter
dups = {k: v for k, v in Counter(section_nums).items() if v > 1}
assert not dups, f"Duplicate sections: {dups}"
```

The Chinese numbered header pattern: `## [一二三四五六七八九十]+、` (Chinese comma U+3001, not Chinese period U+002E).

---

## Orphan Reference File Audit (Always Run After Touching references/)

After any session that creates a `references/` file or adds a `→ Full content:` link, run the complete audit:

```python
import pathlib, re; from collections import Counter
skill_path = "/opt/data/skills/productivity/ai-money-maker/SKILL.md"  # adjust
ref_dir = pathlib.Path(skill_path).parent / "references"
content = pathlib.Path(skill_path).read_text()

existing_files = set(f.name for f in ref_dir.glob("*.md"))

# Three link types to scan — NOTE: pattern is [^()] NOT [^)] — pitfall 27e
full_links = re.findall(r'→ Full content:\s*\[([^\]]+)\]\(([^()]+\.md)\)', content)
related_links = re.findall(r'→ Related:\s*\[([^\]]+)\]\(([^()]+\.md)\)', content)
backtick_links = re.findall(r'`(references/[^`]+)`', content)

all_linked = {p for _, p in full_links + related_links} | set(backtick_links)
orphans = sorted(set(f.name for f in ref_dir.glob("*.md")) - all_linked)
print(f"Orphans: {orphans}")   # must be empty

# Duplicate link-count detection
pair_dups = [(k, v) for k, v in
    Counter(re.findall(r'→ (?:Full content|Related): ([^\n]+)', content)).items()
    if v > 1]
print(f"Duplicate link lines: {pair_dups}")
```

**Note:** Both `→ Full content:` and `→ Related:` link types must be checked.
**Critical regex detail:** The URL capture group must use `[^()]+` (excludes both parentheses), NOT `[^)]+`. The broken pattern `[^)]+` greedily consumes the `)` delimiter itself, producing 100% false positive orphans every time — see pitfall 27e.

**Real case (ai-money-maker v2.78):** Audit reported 36 orphans, but every flagged file was present 2–8× inline in body via `[refs/X.md](refs/X.md)` format, not `→ Full content:` arrow-prefixed links. The correct fix: scan body for bare filename occurrences, not just arrow-prefixed patterns.

**Real case (this session, ai-money-maker Run 81):** Audit reported 43 "orphans" across 41 reference files. Every flagged file appeared 2–8× inline in body via `[refs/X.md](refs/X.md)` format, but the audit only matched `→ Full content:` arrow-prefixed links. After checking, every single reference file existed inline in body content — zero actual orphans.

---

### Pre-Existing Orphans in Cron Sessions: What to Do

When a cyclical cron job runs an orphan audit and finds orphans that existed *before this session started* (not created by this session), the default should be: **fix them, not leave them**.

**Decision tree:**
1. **Orphan file has substantive content** (>500 chars) → add the missing `→ Full content:` link to the appropriate section in SKILL.md. The file exists on disk for a reason — a prior session created it to be discovered.
2. **Orphan file is a stub or unclear purpose** → inspect the file briefly. If it appears to be a research artifact or draft that was never wired up, either link it appropriately or remove it.
3. **Orphan created by the current session** → always link it before the session ends — that is a session-level failure to follow the two-step visibility rule (write file + add link in SKILL.md).
4. **Pre-existing orphan in a file with <1,500 chars headroom** → link it anyway (links are ~60 chars each, low cost). If headroom would be exceeded, note it as a pending fix for a future condensation pass.

**Why fix pre-existing orphans:** They accumulate silently across sessions and represent a persistent discoverability tax. A file that exists on disk but is never linked is invisible to every future agent. Cron sessions that only add content without auditing and fixing structural debt will leave the skill progressively more opaque over time.

**Real case:** breakup-recovery v4.36.0 → v4.37.0 (this session pattern). The session found `anger-phase.md` (13,721 chars) and `run8-diagnostic-findings.md` as pre-existing orphans. `anger-phase.md` had substantive content — it should have been linked in the Anger Phase section when it was created in a prior run. The fix: add `→ Full content: [references/anger-phase.md](references/anger-phase.md)` to the appropriate section rather than deleting 13k of useful content.

**Consecutive Duplicate Reference Link Detection (Critical — Not Caught by Standard Audits)**

The orphan audit and duplicate-link-count audit both MISS a distinct failure mode: **two identical `→ Full content:` lines appearing consecutively in the same location** (same bullet, same paragraph). This happens when a session inserts a reference link by appending it to an existing bullet that already ends with the same link — producing a double entry:

```
- Some bullet content → Full content: [references/power-execution.md](references/power-execution.md)
  → Full content: [references/power-execution.md](references/power-execution.md) -- extended...
```

Both lines are syntactically valid markdown and survive repeated reads — invisible to reading but consuming redundant space and confusing downstream editors.

**Detection (run this in addition to the standard orphan+count audits):**
```python
import re, pathlib
content = pathlib.Path(skill_path).read_text()

# Find every reference link line
link_lines = [(m.start(), m.group(0).rstrip())
              for m in re.finditer(r'→ Full content:[^\n]+\)', content)]

# Check for consecutive pairs (same file, adjacent positions)
consecutive_dups = []
for i in range(len(link_lines) - 1):
    pos1, line1 = link_lines[i]
    pos2, line2 = link_lines[i + 1]
    if pos2 - pos1 < 200 and line1 == line2:
        consecutive_dups.append((pos1, line1))
        print(f"CONSECUTIVE DUPLICATE at {pos1}: {line1[:80]}")

assert not consecutive_dups, f"Found {len(consecutive_dups)} consecutive duplicate link(s)"
```

**Why the standard audits miss this:**
- **Orphan audit** compares linked files against files on disk — it never sees duplicates because both copies point to existing files
- **Duplicate-link-count audit** counts unique `(label, URL)` pairs — it sees the pair once regardless of how many times it appears

**Fix:** Delete the duplicate line, keeping the one with `-- extended...` suffix if present (signals richer content).

**Real case (wealth-mindset v1.71.0):** A bullet in the Bezos section contained two identical `→ Full content: [references/power-execution.md](references/power-execution.md)` lines — bare duplicate removed (saving 79 chars), suffixed line kept. File: 99,966 → 99,887 chars, no content loss.

**Real case (breakup-recovery v4.36.0 → v4.37.0):** Session found `anger-phase.md` (13,721 chars) and `run8-diagnostic-findings.md` as pre-existing orphans.

## Duplicate Header Pitfall (Critical)

The `patch` tool with default mode replaces the **first** occurrence of the string. If the old_string appears multiple times, the patch lands at the wrong location.

**Fix:** Always include enough surrounding context to make the old_string unique. For section header deduplication, include the **last line of preceding section content** in the old_string.

```python
# WRONG — too generic
old_string = "## 十、AI副业收入报告\n\n## 十、AI副业收入报告"

# RIGHT — include unique preceding context
old_string = """验证清单\n\n---\n\n## 十、AI副业收入报告\n\n## 十、AI副业收入报告（2024-2025实操数据）"""
```

---

## WSL Filesystem Caching

In WSL environments, `terminal` tool commands (`wc -c`, `stat`, `cat | wc`) can read **stale file sizes** from OS filesystem cache. Python pathlib reads the **correct current content**.

**Rule:** Always use Python (`pathlib.Path.read_text()`) for byte-accurate reads and size validation. Never trust `wc -c` from terminal for size checks in WSL.

**Real case (ai-money-maker v2.51):** After a successful full-build write, `stat` reported `st_size=208,783` while Python `len(content)=99,807` — a 2.09× ratio. Python was authoritative.

---

## Sequential Patch Strategy for Near-Limit Files

When SKILL.md is within ~5k of 100k limit and you need multiple changes:
- Combine all changes into ONE patch
- Before patching: do `len(pathlib.Path(...).read_text())` to check available space
- If current size + new content estimate > 95k: split first (move section to references/) THEN patch

---

## Stub Section Removal

**Stub sections** are sections with headers but <250 chars of substantive content — empty placeholders. Detection:
```python
import re, pathlib
content = pathlib.Path(skill_path).read_text()
section_headers = list(re.finditer(r'\n## ([一二三四五六七八九十VI]+)、', content))
stub_sections = []
for i, m in enumerate(section_headers):
    start = m.start()
    end = section_headers[i+1].start() if i+1 < len(section_headers) else len(content)
    if end - start < 250:
        stub_sections.append((m.group(1), start, end))
# Remove in reverse offset order to preserve positions
```

**Key distinction:** A stub is NOT an obsolete section with real content. Move substantively-rich sections to `references/` instead of deleting them.

---

## Pre-Insertion Number-Gap Scan

Never trust session summaries for section numbers. Before inserting:
```python
import re, pathlib
content = pathlib.Path(skill_path).read_text()
headers = re.findall(r'\n## ([一二三四五六七八九十]+)、', content)
from collections import Counter
dup_headers = [h for h, c in Counter(headers).items() if c > 1]
print(f"Duplicates: {dup_headers}")
```

**Real case: ai-money-maker v2.55→v2.56.** Session summary said "use 四十六" but 四十六 already existed at offset 784 from a prior session. Gap scan caught it; used 四十七 instead.

---

## WSL pathlib Write Persistence (New Failure Mode)

In some WSL configurations, `pathlib.Path(path).write_text(new_content)` reports success and subsequent Python reads within the same session confirm the new content, but the file on disk reverts to its original state after the session ends. This is different from the known caching staleness issue (where `wc -c` reports wrong sizes but writes land correctly). Here, the write appears to succeed in-memory but never persists to disk.

**Detection:**
1. Write new content → Python read confirms it in-memory
2. `git diff skills/<category>/<name>/SKILL.md` shows no changes — file on disk matches HEAD

**Real case:** Multiple Python writes against `/opt/data/skills/productivity/breakup-recovery/SKILL.md` each confirmed new content in-memory but disk remained at HEAD state after each write. Python re-reads within the same session showed modified content, but `git diff` was always empty.

**Workarounds (in order of reliability):**
1. Use `skill_manage(patch)` for small targeted edits — bypasses the Python layer entirely, writes directly via the skill manager tool
2. Write to a temp file first, then `shutil.move()`:
   ```python
   import tempfile, shutil, pathlib
   tmp = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md', encoding='utf-8')
   tmp.write(new_content); tmp.close()
   shutil.move(tmp.name, skill_path)
   ```
3. Use `open(path, 'w').write()` instead of `pathlib.write_text()`
4. Add `subprocess.run(['sync'])` after write to force OS flush

**Verification rule:** In WSL sandbox contexts, always verify writes with `git diff` — not Python re-read. Python's in-memory state can show modified content that was never flushed to disk.

**Prevention:** When working in a WSL environment where write persistence is uncertain, prefer `skill_manage(patch)` for any edits it can handle (unique anchor strings, single replacements). Reserve Python `pathlib.write_text()` for atomic multi-change scenarios where no other approach works.

---

## Boundary Corruption Audit: False Positive Pattern

The `scripts/skill-authoring-audit.py` boundary corruption check flags `→ Full content:` links followed by `\n##` with no preceding `\n\n`. The regex `\s*\n##` has a subtle flaw: `\s*` matches zero characters, then `\n` consumes the **first** `\n` of a `\n\n##` sequence — making the check pass on correctly formatted content and producing false positives.

**Real cases:**
- purpose-finder v4.16: 12 flagged positions, all verified as correctly formatted
- wealth-mindset v1.54: 13 flagged positions, 10 were false positives

**Correct verification (do this instead of trusting the script):**
```python
# For each flagged position, check the text between link end and header start
for m in re.finditer(r'→ Full content:[^\n]+\)', content):
    link_end = m.end()
    next_header = content.find('\n## ', link_end)
    between = content[link_end:next_header]
    if between.startswith('\n\n'):
        # CORRECT — has blank line before header
        pass
    elif between.strip() == '':
        # CORRUPT — no blank line, header immediately follows
        fix_needed.append(m.start())
    else:
        # Has text between link and header — likely legitimate description
        pass
```

**Rule:** Never "fix" a boundary corruption flagged by the audit script without first verifying with the string inspection above. Attempting to "fix" a false positive by adding extra `\n\n` to already-correct content introduces real corruption. The script's `\s*` bug means it flags correct content more often than it catches real issues.

---

## Shell Section Pattern (Empty Header Left Behind)

A **shell section** is a specific sub-type of duplicate header: a section header line followed by a `---` separator, with no body content between them. It forms when a session replaces a section's body but the `old_string` only matched up to the `---` — leaving the old `---` in place as a section boundary for a section that no longer exists.

**How it forms:** Session replaces `## Header\n\n<section body>` with `## Header\n\n<new body>` but the `old_string` anchored at `## Header\n\n<section body>` without including the trailing `---` that closes the section. The old `---` separator survives, creating a header-only section followed immediately by the real section with the same header.

**Detection:**
```python
import re, pathlib
content = pathlib.Path(skill_path).read_text()
# Find all top-level section headers
headers = [(m.start(), m.group(0)) for m in re.finditer(r'\n## ([^\n]+)', content)]
# Check each for: header immediately followed by --- (shell = no body)
for i, (pos, hdr) in enumerate(headers):
    next_pos = headers[i+1][0] if i+1 < len(headers) else len(content)
    between = content[pos:next_pos]
    if between.strip().endswith('---') and len(between) < 200:
        print(f"SHELL at {pos}: {hdr!r} — {len(between)} chars, likely empty")
```

**Real case (purpose-finder v4.27.1):** A section replacement left behind `## Framework: Values Clarification (ACT-Inspired)\n\n---\n` as a 56-char shell — the second VC header with no body, immediately before the real VC section. File appeared to have 2 VC headers; only one was real.

**Fix (atomic):**
```python
import pathlib
content = pathlib.Path(skill_path).read_text()
# Shell: header at pos S, ends with \n---\n
# Real section starts where shell ends: find the next ## Header
shell_start = pos
next_header = content.find('\n## ', shell_start + 10)
# Remove shell: content[shell_start:next_header]
new_content = content[:shell_start] + content[next_header:]
pathlib.Path(skill_path).write_text(new_content)
```

**Prevention:** When replacing an entire section, anchor `old_string` to the section header line AND the `---` separator that closes it. The old_string must include the final `\n---\n` of the section being replaced.

**Key distinction from ordinary duplicate:** An ordinary duplicate has two copies of the header with body content in both. A shell has one header with body and one header that is only `\n## Header\n\n---\n` (≤56 chars). The shell is invisible to reading — it appears as a section break, not a section. Always scan for `<200 char` section spans when auditing large files.

---

## Two Skill Trees: Knowing Which One You're Editing

The `skill_manage` tool operates on the **user-local tree** (`~/.hermes/skills/` or `/opt/data/skills/`), NOT the in-repo tree. When `skill_manage(patch)` fails to find your old_string, it may be pointing at the wrong tree.

**Path signature:** `/opt/hermes/skills/` = in-repo; `/opt/data/skills/` = user-local.

**Detection:** Check `version:` in both trees. If they differ, you may be patching the wrong file. Use `skill_view(name)` to read and confirm which tree has the content you're targeting.
