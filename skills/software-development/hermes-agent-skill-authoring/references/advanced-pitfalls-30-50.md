# Advanced Pitfalls 30–50

> Extended reference for hermes-agent-skill-authoring SKILL.md — pitfalls 30 through 50.

## 30. Sequential Patches on Large Files Shift Content Boundaries

When patch 2 alters character positions after patch 1 lands, the `old_string` for patch 2 may no longer match — or patch 1 leaves behind orphaned content (section header + body) that was supposed to be replaced.

**Real case:** patch 1 removed Dalio body (4,214 chars) and replaced with a reference link (366 chars). Subsequent patch 2 shifted positions, leaving the Classic Industrial section header AND its full body (3,920 chars) as an orphan at the end of the file.

**Prevention:** For multi-patch sequences on large files (>80k), compute all replacements in memory simultaneously and write once. If sequential is unavoidable, validate character positions after patch 1 before composing patch 2's `old_string`.

**Pattern — atomic multi-insertion:**
```python
import pathlib
path = "/opt/data/skills/.../SKILL.md"
content = pathlib.Path(path).read_text()

# Compute all anchors and deltas from the SAME original content
anchor1_pos = content.find("FIRST_ANCHOR")
anchor2_pos = content.find("SECOND_ANCHOR")

delta1 = len(new_content1) - len(old1)
# anchor2_pos is now STALE — compute from original:
# Use string search from content (not arithmetic offset)

new_content = content.replace(old1, new1, 1).replace(old2, new2, 1)
pathlib.Path(path).write_text(new_content)
```

## 31. WSL Filesystem Caching Makes `wc -c` Unreliable

In WSL environments, `wc -c` and the `read_file` tool's `file_size:` metadata hint can be wrong by up to 2x due to filesystem caching delays. Python `pathlib.read_text()` is authoritative in the same session as the write. Real case: `wc -c` reported ~100k after a write that Python confirmed was only 99,367 chars. **Rule:** always validate size with `len(pathlib.Path(path).read_text())` — never terminal tools or tool metadata hints.

## 32. Condensation Patch Targeting Wrong Section Boundary Causes Fragmentation

When condensing a large section, the `old_string` must match the exact section boundary — not a generic phrase that appears in multiple places. A generic match hits the wrong occurrence, leaving the real section in place while inserting the condensed version elsewhere, creating duplicate sections and truncating downstream content. **Fix:** always anchor `old_string` to the section header line plus opening paragraph to ensure uniqueness.

## 32b. `find()` Returning -1 Causes Silent File Truncation

When using `content.find(block)` then `content.find(block[suffix:])` for multi-step block extraction, if the second `find()` returns `-1` (not found), arithmetic with `-1` produces negative indices. `content[:neg]` silently produces an empty string — the file appears intact but writes as garbage. **Fix:** always assert `find_result != -1` before using a position variable in slicing. Real case: `pos2 = content.find(bad_block[10:])` returned `-1`; `pos - 1 = -2`; `content[-2:-1] = ''`; entire file written as 49k of empty head + first 580 lines. Use single-pass anchored replacements over multi-step find-then-find chains.

## 32c. `.replace()` Silently Replaces ALL Occurrences in Large Files

`content.replace(old_string, new_string)` replaces every occurrence of `old_string`. If `old_string` contains text that also appears elsewhere in the file, the replacement corrupts other sections. In large multi-session skills (99k+ chars, 50+ sections), any phrase of meaningful length inside the target section is likely to appear elsewhere. **Fix:** Use positional slicing for targeted replacements:
```python
sec_start = content.find("### The Negotiation Architecture: Beyond Salary")
next_sub = content.find("\n### ", sec_start + 10)
next_sec = content.find("\n## ", sec_start)
sec_end = min(s for s in [next_sub, next_sec] if s > sec_start)
assert content.count(na_exact) == 1, f"Duplicate match: {content.count(na_exact)}"
new_content = content[:na_header_pos] + na_new + content[na_end_pos:]
```

**When `.replace()` is safe:** Only when `old_string` is verified unique by `content.count(old_string) == 1` AND the replacement string contains no text that appears elsewhere in the file. Use `.replace(old, new, 1)` to limit to first occurrence.

## 32d. Duplicate-Removal via EOF-Append Creates Circular Reference

When removing a duplicate section by appending the merged version to EOF and then trying to delete the original, the `old_end` position must be computed from the **original file** — not from the modified copy already in memory. If `old_end = old_start + len(old_string)` where `old_string` is the section text AFTER the append, `old_end` overshoots, `content[old_end:]` includes the duplicate section, and the duplicate remains. **Fix:** re-read the original file from disk, compute all positions from that clean snapshot, apply exactly one atomic write.

## 32e. Computing Section End from Wrong Header Creates Negative Span

When replacing a section by computing `sec_end = content.find('\n## ' + next_header)`, if `next_header` is *before* `sec_start` in file order, `find()` returns the earlier position — producing a negative span. `assert sec_start < sec_end` before slicing. **Rule:** validate that each section's start position is less than its computed end position before slicing — any negative span is an immediate signal that the next-header search matched an earlier section.

## 34. Pre-Insertion Number-Gap Scan

Before inserting a new numbered section (e.g., "## 四十七"), scan all existing section numbers first to detect missing numbers:
```python
headers = re.findall(r'\n## ([一二三四五六七八九十]+)、', content)
# Insert at correct chronological position — not at EOF
```
**Real case:** a session tried to add "四十七" without checking — the number was absent from the sequence, making the insertion land at the wrong file position. Always scan BEFORE inserting.

## 35. Orphan Audit Is Mandatory When `references/` Is Touched — Wrong Audit Is Worse Than None

The old audit scanning `→ Full content:` only silently misses `→ Related:`, `→ 完整内容:`, `→ 相关资料:`, and raw markdown `[text](references/X.md)` formats. **Real case:** ai-money-maker v3.6.2 had 55 reference files. A `→ Full content:` only audit found 9 linked → 46 orphans reported. Universal pattern found 26 linked → only 29 true orphans. **Rule:** start with universal pattern on any skill you've never audited:
```python
all_links = re.findall(r'\[([^\]]+)\]\(([^()]+)\)', content)
linked = {url for text, url in all_links if url.startswith('references/')}
linked_bare = {url.replace('references/', '') for url in linked}
orphans = sorted(set(f.name for f in ref_dir.glob("*.md")) - linked_bare)
```
If count > ~20 on a 50+ ref-file skill → pattern mismatch, not real orphans.

## 37. Concurrent Multi-Agent Race Condition on Large Skill Files

When multiple agent sessions run simultaneously against the same file (>80k chars), a sibling subagent can modify the file between read and write. The `patch` tool uses the `old_string` as provided — if the file changed, the patch lands incorrectly, silently corrupting sections. **Post-patch verification checklist:**
1. File size ≤ 100,000 chars (Python `pathlib` read)
2. Target section appears at correct position
3. Following section still intact
4. No duplicate section headers introduced

**Rule:** When concurrent modification is possible, prefer atomic `pathlib.write_text()` over `patch`.

## 38. Version Bump and Content Addition Must Be Atomic

When using `patch` on version lines in concurrent environments, verify post-write that version and content are in sync — not just that the patch succeeded. **Real case:** concurrent subagents both patched version; final file showed stale version with new content present. Check both.

## 39. Section Disorder (Out-of-File-Position) Is Invisible to Casual Reading

In skills with Chinese numeral section headers, sections can appear in the file at the wrong position — invisible to reading but fatal to any patching that relies on sequential assumption. **Detection:** compare section positions (by Chinese numeral value) against file positions. **Real case:** ai-money-maker v2.72 had 五十四 (副业收入) at pos 92,289 and 五十五 (B2B成交力学) at pos 90,792 — a 1,497-char swap. **Fix:** extract both blocks, reassemble in correct order, write once atomically.

## 39b. Large Inter-Section Gaps Are the Primary Detection Signal

A gap between section N and section N+1 that exceeds 3,000 chars often means a displaced section from later in the file is sandwiched between them. **Real case:** gap of 3,213 chars between 五十九 (pos 60,661) and 三十五 (pos 63,874) flagged section 六十二/六十一 swap. **Threshold:** use >3,000 chars, not >4,000 — the higher threshold produces false negatives on dense multi-section skills.

## 39c. Six-Step Structural Survey (Pre-Edit, Mandatory for >80k Skills)

```python
import re, pathlib; from collections import Counter
skill_path = "/opt/data/skills/.../SKILL.md"  # adjust
content = pathlib.Path(skill_path).read_text()
sections = [(m.start(), m.group(1), m.group(2)) for m in re.finditer(
    r'\n## ([一二三四五六七八九十百千万]+)、([^\n]+)', content)]

def cn_to_int(cn):
    mapping = {'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,'十':10}
    result = 0
    for char in cn:
        if char == '百': result = (result or 1) * 100
        elif char == '千': result = (result or 1) * 1000
        elif char == '万': result = (result or 1) * 10000
        elif char == '十': result = (result * 10) + 10 if result else 10
        else: result += mapping.get(char, 0)
    return result

nums = [n for _, n, _ in sections]
print(f"Size: {len(content):,}, headroom: {100_000 - len(content):,}")
print(f"Sections: {len(sections)}")
disorder = [(nums[i], nums[i+1]) for i in range(len(nums)-1)
            if cn_to_int(nums[i]) > cn_to_int(nums[i+1])]
print(f"Disorder: {disorder}")
for i in range(len(sections)-1):
    gap = sections[i+1][0] - sections[i][0]
    if gap > 3000: print(f"  LARGE GAP: {sections[i][1]}→{sections[i+1][1]}: {gap} chars")
dup_nums = {k: v for k, v in Counter(nums).items() if v > 1}
print(f"Duplicate numbers: {dup_nums}")
```

> **⚠️ Critical:** `sections` is 3-element tuples `(pos, num, title)`. The generator `next(f"## {num}" for pos, num in sections if pos < sub_pos)` (2-element unpack) raises `ValueError: not enough values to unpack` silently — every `parent` reports `"NONE"`. Always use `for pos, num, _ in sections`.

## 41. `pathlib.write_text()` Silently Fails to Persist in WSL Sandbox

Writes report success and Python re-reads confirm new content in-memory, but `git diff` shows no changes. **Workaround:** write to a temp path first, then `shutil.move()`:
```python
import pathlib, shutil
pathlib.Path("/tmp/skill-temp.md").write_text(new_content)
shutil.move("/tmp/skill-temp.md", skill_path)
```
For user-local skills, `pathlib.read_text()` is the only authoritative verification (not `git diff`).

## 44. Reference Link Before `###` Without Blank Line — Fix Spacing, Not the Link

When a `→ Full content:` link ends with `)` and the next line is a `###` header with no blank line between them, the corruption is missing separation — not a broken link. **Fix:** insert `\n\n` between the link line and the `###` header. Never remove the link to fix a boundary problem.

## 45. Subsection Scan Mandatory After Section-Extraction

When extracting a displaced `### N、` subsection into its own `## N、` top-level section, the operation leaves the old copy behind in the parent. **Post-extraction scan:**
```python
subsections = [(m.start(), m.group(1)) for m in re.finditer(r'\n### ([一二三四五六七八九十百千万VI]+)、', content)]
for sub_pos, sub_num in subsections:
    parent = next((f"## {num}" for sec_pos, num, _ in sections if sec_pos < sub_pos), "ORPHAN")
    print(f"  ### {sub_num}、 inside: {parent}")
```
Any output means the embedded copy still remains — extract + delete it.

## 46. Section Boundary Corruption Detection — String Ops, Not Regex

The regex `\s*\n##` cannot reliably distinguish correct `\n\n` from corrupt `\n` boundaries — `\s` matches `[ \t\f\r\v]` but not `\n`, so the pattern passes on both correct and corrupt. Use string operations:
```python
for m in re.finditer(r'→ Full content:[^\n]+\)', content):
    link_end = m.end()
    next_nl = content.find('\n', link_end)
    next_header = content.find('\n##  ', link_end)  # two trailing spaces
    between = content[next_nl:next_header]
    if not between.startswith('\n\n'):
        corrupted.append(f"link at pos {m.start()} missing blank line before ##")
```
**Key check:** `not between.startswith('\n\n')`. **Real case:** purpose-finder flagged 13 false positives; actual was 1.

**False-positive case — `---` decorative dividers between link and header.** Many skills use `---` as a visual section break placed between a reference link and the next `## ` header. The boundary scan correctly finds the `##  ` header (two trailing spaces avoids matching `##` inside `---` blocks), but the `between` text is `---` with no leading blank line — triggering a false positive. The spacing is correct: the link is followed by `---`, then `\n\n`, then `## `. The corruption check only fires when `between` is a bare newline with no separator at all. To distinguish: if `between` contains a `---` divider, check whether there is a blank line *after* that divider (before the `## ` header). If yes, the structure is `link)\n---\n\n## ` — which is correct, not corrupted. If no `---` and no `\n\n`, it is genuine corruption.

**Revised detection logic:**
```python
for m in re.finditer(r'→ Full content:[^\n]+\)', content):
    link_end = m.end()
    next_nl = content.find('\n', link_end)
    next_header = content.find('\n##  ', link_end)
    between = content[next_nl:next_header]
    # Skip if --- divider exists between link and header (possible false positive)
    if '---\n' in between:
        # Verify: is there a blank line AFTER the --- and BEFORE ## ?
        after_divider = between.split('---\n', 1)[1] if '---\n' in between else ''
        if after_divider.startswith('\n'):
            continue  # legitimate: link)\n---\n\n##  — correct spacing
    if not between.startswith('\n\n'):
        corrupted.append(f"link at pos {m.start()} missing blank line before ##")
```

## 47. V2 Link-Text Double-Counting Trap

Many skills use `[filename.md](references/filename.md)` — link text identical to URL path. When composing a new section with the same format, `filename.md` appears twice (link text + URL), inflating `count()` assertions. **Fix:** use descriptive link text: `[descriptive label](references/filename.md)`. Count actual link lines, not raw string occurrences.

## 48. Ellipsis Placeholder (`...`) in `execute_code` Silently Fails on String Write

When `new_content` is assigned via `final = ...` (Ellipsis object) and passed to `pathlib.write_text(final)`, it fails with `TypeError: data must be str, not ellipsis`. The error surfaces inside `execute_code`, not at the assignment. **Rule:** use explicit string variables; never leave `...` as a stand-in in a variable passed to `write_text()`.

## 50. Sequential Patches on Dense-`---` Files Cascade Into Wrong Sections

Skills with `---` section dividers throughout (not just frontmatter) shift positions unpredictably across insertions. Three consecutive patches in ai-money-maker v2.59→2.72 all inserted into adjacent wrong sections. **Fix:** atomic Python `pathlib.write_text()` pattern — compute all insertions from the same original content, write once.