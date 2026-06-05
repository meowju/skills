---
name: reference-link-and-orphan-patterns
description: Reference file for hermes-agent-skill-authoring — patterns for malformed reference links and orphan artifacts in large multi-session skills.
version: 1.5.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [skills, authoring, reference-links, orphans, pitfalls]
---

# Reference Link and Orphan Artifact Patterns

Real cases extracted from wealth-mindset and ai-money-maker editing sessions.

## Pattern L: Migration-Condensation Patches Create V2 Links (Primary Trigger)

**Symptom:** After migrating a large section to `references/` and inserting a condensed inline summary, two V2 malformed links appear for the same target file (e.g., `[references/ai-exit-rating-100.md]` as both text and URL). The file reads correctly but the links are malformed.

**Root cause:** When composing the condensed inline version, the agent writes the reference link using the bare filename as link text — `[references/filename.md]` — because it's the fastest way to construct the link during the migration. The `→ Full content:` prefix is present, so it *looks* correct. But `link_text == url_basename` makes it a V2 link.

**Primary trigger — not random:** Unlike other V2 instances that might appear from copy-paste or template usage, migration-condensation is a deliberate two-step operation (create reference file → insert inline summary) that naturally produces two V2 links for the same file: one in the section note paragraph and one in the body reference line.

**Detection:**
```python
v2_matches = re.findall(r'\[([^\]]+\.md)\]\(references/([^\)]+\.md)\)', content)
v2_same = [(t, u) for t, u in v2_matches if t == u]
print(f"V2 malformed links: {len(v2_same)}")
# Real case (ai-money-maker Run 209): section 100 migration → 2 V2 links, fixed in one pass
```

**Fix:** Replace both V2 instances with descriptive link text. If the same file appears twice with different surrounding context, use the same descriptive label for both (consistency) OR use different labels if the context differs meaningfully:
```python
# First occurrence (in note paragraph): descriptive
content = content.replace(
    '[references/ai-exit-rating-100.md](references/ai-exit-rating-100.md)',
    '[AI退出评级体系完整内容](references/ai-exit-rating-100.md)',
    1
)
# Second occurrence (in body, with parenthetical annotation):
# The parenthetical suffix stays; only the link text changes
content = content.replace(
    '[references/ai-exit-rating-100.md](references/ai-exit-rating-100.md)（AI退出评级体系完整内容）',
    '[AI退出评级体系完整内容](references/ai-exit-rating-100.md)（AI退出评级体系完整内容）',
    1
)
```

**Prevention:** When inserting a new `→ Full content:` reference link during a condensation/migration patch, always use descriptive link text in the same operation. Construct the link as `[descriptive label](references/filename.md)` — not `[references/filename.md]`. The extra 2 seconds of composition prevents a follow-on fix patch.

**Rule:** V2 links from migration are always a pair (same target file, two occurrences). Fix both in the same pass — replacing one leaves the other as a stale V2 that will surface in the next audit.

## Pattern A: V2-Malformed Reference Links

**Symptom:** The `→ Full content:` prefix is present and the URL path is correct, but the link text lacks the `references/` prefix: `→ Full content: [naval-framework.md](references/naval-framework.md)` — the text portion `[naval-framework.md]` should be `[references/naval-framework.md]`. This is invisible to reading and to orphan audits (the file exists and links correctly), but future skill loaders resolve the link text as display text, showing a broken path as the visible label.

**Detection:**
```python
import re
# WRONG: [^)]+ eats the ) itself since .md sits before ) in the URL
# The second capture group becomes empty/wrong → all links report as orphans
v2_wrong = re.findall(r'→ Full content:\s*\[([^\]]+)\]\(([^)]+\.md)\)', content)

# CORRECT: [^()]+ excludes ( and ) which are markdown link delimiters
# .md is before ), so the char class must stop at ( — [^()]+ does exactly that
all_links = re.findall(r'→ Full content:\s*\[([^\]]+)\]\(([^()]+\.md)\)', content)
linked = {url for _, url in all_links}
# All reference files that exist but aren't linked:
orphaned = set(f.name for f in ref_dir.glob("*.md")) - linked
# Real case: purpose-finder v4.69.0 had 33 V2 instances across all 8 frameworks, all invisible to reading; fixed in v4.70.0 with re.sub + function replacer (not a simple string replace). Headroom was only 2,965 chars after fix — no new content added; expansion deferred to next cycle.
```

**Fix:** Use `re.sub` with a function-based replacer to inject `references/` into link text only when absent:
```python
def fix_v2(m):
    full = m.group(0)
    b_start = full.index('['); b_end = full.index(']')
    text = full[b_start+1:b_end]
    if text.startswith('references/'): return full
    return full.replace(f'[{text}]', f'[references/{text}]')

v2_pattern = r'→ Full content: \[[^\]]+\.md\]\(references/[^\)]+\.md\)'
fixed = re.sub(v2_pattern, fix_v2, content)
```

**Prevention:** Always use the full path in both text and URL portions of markdown reference links. When inserting a new reference link, copy the exact URL path into the text portion. The `[^()]+` pattern is always correct for markdown URLs; the `[^)]+` variant silently fails on `.md` links because `.` is not a path terminator.

`[^()]+` pattern is always correct for markdown URLs; the `[^)]+` variant silently fails on `.md` links because `.` is not a path terminator.

**Simple bulk-fix when all V2 links need descriptive text:** Use `str.replace` in a loop with a `url_to_label` dict — no `re.sub` needed, more auditable. Real case (breakup-recovery Run 9): 52 V2 links fixed with a dict mapping each URL to its descriptive label, one `replace()` call per URL. Each replacement was unique (different old text per URL), so `str.replace` worked without accidental cross-substitution. Function-based `re.sub` is correct but unnecessary when all V2 links use bare filenames that differ per URL.

**Why descriptive link text prevents double-counting bugs:** V2 format `[filename.md](references/filename.md)` causes `content.count("filename.md")` to return **2** (once in link text, once in URL) — inflating reference counts and causing false duplicate detection when composing `old_string` for section insertions. Descriptive text like `[Internal Working Model Research](references/internal-working-model.md)` makes the same count return **1** (URL only). Always prefer descriptive link text; it also improves readability.

## Pattern J: Verifying Uniqueness of old_string Containing a Complete Markdown Link

When `old_string` is a complete markdown reference link line like:
```
→ Full content: [Founder Mode Direction](references/founder-mode-purpose.md)

---
```
calling `content.count("founder-mode-purpose.md")` returns **2** — once in the link text portion `[...]`, once in the URL portion `(...)`. This is not a bug in your logic; it's how complete markdown links work. The filename appears in both the visible text and the URL.

**Wrong verification:**
```python
# DANGER: Returns 2 for a file that appears exactly once as a complete link
assert content.count("founder-mode-purpose.md") == 1  # FAILS — returns 2
```

**Correct verification — use the full old_string:**
```python
# CORRECT: counts the complete link line as it appears in the file
assert content.count(old_string) == 1  # Full string, not just filename
```

**Alternative: URL-only count via regex:**
```python
from collections import Counter
complete_links = re.findall(r'→ Full content: \[([^\]]+)\]\(([^()]+\.md)\)', content)
url_counts = Counter(url for _, url in complete_links)
assert url_counts.get('references/founder-mode-purpose.md', 0) == 1  # URL-only, no text inflation
```

**Rule:** To verify an `old_string` that is a complete link line is unique in the file, use `content.count(old_string)` with the full string. Do NOT substitute a bare filename substring — you'll get a false failure even when there's only one instance of the link.

**Real case (this session):** purpose-finder Run 1 — `old_string = '## Framework: Founder Mode — How Builders Find Direction\n\nBrian Chesky (Airbnb): "Most people think they should start by figuring out their passion..."\n\n→ Full content: [Founder Mode Direction](references/founder-mode-purpose.md)\n\n---\n'` (396 chars). `content.count(old_string) == 1` confirmed unique. `content.count("founder-mode-purpose.md")` would have returned 2 (one in link text, one in URL), leading to a false assumption that the string appears twice.

**Variant: `content.count(url)` can return 2 for a SINGLE link line when URL appears twice.** When the URL substring (e.g., `decision-frameworks.md`) appears as a plain substring inside BOTH the link text portion AND the URL portion of the same markdown link, `content.count(url_substring)` counts both occurrences even though only one link instance exists. Real case (purpose-finder Run 25): `decision-frameworks.md` appeared at offsets 9080 and 9112 within the same 149-char line — `count() == 2` → agent incorrectly concluded there were duplicate links and planned to delete the sole occurrence. The fix: always use `full_links` regex extraction and `Counter` on URL-only group, not a bare substring count. Rule: gap <50 chars between two substring matches = same single link. True duplicates (different lines) have gap ≥80 chars.

## Pattern G: Bare Duplicate vs. Intentional Cross-Reference

**Symptom:** A reference link appears multiple times in a file and must be reduced to one, but some occurrences are intentional cross-references (different sections, each with contextual annotation) while others are bare duplicate lines (same section boundary, no annotation). The difference is invisible to a naive `content.count(url)` count.

**Real case (ai-money-maker Run 181):** `ai-compound-asset-deep.md` appeared 5 times:
- Lines 565 (section 14, annotated context)
- Line 1263 (section 57, annotated context)
- Line 2916 (section 84/85 boundary, bare duplicate — no annotation, just the raw link line)
- Line 3109 (section 89, multi-reference block)
- Line 75272 (another section, annotated)

Naive duplicate scan would report 5 occurrences and risk removing intentional ones. The correct filter: a **bare duplicate** = a `→ Full content:` link line whose **text portion equals the URL portion** AND which is the **only link to that file in its immediate context** (no adjacent annotation). An **intentional cross-reference** = the link line has a preceding sentence that describes WHY this reference is relevant in this specific section.

**Detection:** For each file appearing N times, check each occurrence's context:
```python
for match in re.finditer(r'→ Full content: \[([^\]]+)\]\(([^()]+\.md)\)', content):
    url = match.group(2)
    pos = match.start()
    line_start = content.rfind('\n', 0, pos) + 1
    line_end = content.find('\n', pos)
    line = content[line_start:line_end].strip()
    # Bare if: link text == filename AND no preceding sentence ending in punctuation within 200 chars
    is_bare = (line == f'→ Full content: [{url}]({url})')
    print(f"{'BARE' if is_bare else 'CONTEXT'}: {url} at pos {pos}")
```

**Rule:** Remove bare duplicates at section/subsection boundaries. Preserve annotated cross-references even if they point to the same file. When in doubt, check whether the surrounding text adds unique value in that section's context — if yes, keep it.

**Pattern I: Same-Section Consecutive Duplicate**

A duplicate link can appear within the **same section** as two consecutive lines (gap < 50 chars). Both have the `→ Full content:` prefix; the second is a truncated version of the first (shorter descriptive text, same URL). This is invisible to reading because both look like normal content.

**Real case (ai-money-maker Run 205, section 二十二):** The link appeared twice within the same subsection:
- Line 1 (pos 20,980): `含视频带货脚本·邮件序列·CRO checklist·$500→$20k升级路径` — the richer occurrence
- Line 2 (pos 21,302): `含CRO checklist·$500→$20k升级路径` — truncated duplicate, removed

Detection: scan for `→ Full content:` link lines where the same URL appears twice within 200 chars of each other (Pattern J count=2 but gap < 50 means same single link). Fix: keep the occurrence with longer descriptive text; delete the bare truncated duplicate.

**Verification after removing a bare duplicate:** Confirm the remaining count equals the number of sections that genuinely benefit from the reference. If removing a bare duplicate at position X leaves the file with N-1 occurrences but the file should logically link to the reference in N sections, re-add at the correct section with annotation.

## Pattern H: Net-Delta Computation for Near-Limit Files

When headroom is <1,000 chars and multiple operations are planned (e.g., remove duplicate link −81 chars AND add new content +269 chars), the operations must be computed as a **combined net delta** in memory before writing, not as sequential patches. Sequential patching fails the size gate individually even though the combined delta fits.

**Real case (ai-money-maker Run 181):** File at 99,102 chars (898 headroom). Planned: remove bare duplicate (−81 chars) + expand B2B section (+269 chars). Sequential: patch 1 removes duplicate → file at 99,021 chars. Patch 2 adds B2B content → would push to 99,290 chars. Both patches succeed individually AND combined is within limit. However, if the operations were reversed (expand first, then remove duplicate), patch 2 would fail the size gate alone even though the net delta is +188 chars. The fix: compute `size + sum(all_deltas)` and write once.

**Rule:** When combining structural fixes (duplicate removal) with content additions, always compute the combined net delta. A section that "doesn't fit" in isolation may fit when a concurrent duplicate removal frees headroom. When headroom < 2,000 chars and multiple changes are planned, write once with all deltas computed together.

## Pattern B: Dangling Orphan Paragraph

**Symptom:** A paragraph ending with an em-dash followed by descriptive text (`— Naval's complete 14-part tweet storm...`) but with **no actual `→ Full content:` reference link attached** on the same line. This is a leftover artifact from a prior failed edit — content was placed but the reference was never wired. It consumes space and breaks the reference chain.

**Detection:** Scan for `— [A-Z]` pattern in paragraphs that don't contain `→ Full content:` or `→ 完整内容:` on the same line.

**Real case (wealth-mindset v1.99.0 → v1.100.0):** At byte position 41606, the text `"The book has been translated into 40+ languages. — Naval's complete 14-part tweet storm on wealth and life."` was a 239-char orphan with no link attached. The fix: remove the orphan paragraph entirely and replace with a proper `→ Full content: [naval-framework.md](references/naval-framework.md)` link pointing to the existing reference file.

**Fix:** Remove the orphan paragraph and replace with a proper reference link. If the reference file doesn't exist yet, create it or defer the orphan cleanup to a session that can write files.

## Pattern C: Sequential Patches on Near-Limit Files

When a file is at ~99,900 chars and needs multiple changes (e.g., link fixes + section expansion), sequential patching fails because the combined delta must be computed in memory before writing. Real case: planned two patches (reference link swap + section expansion) but after computing both deltas together found the combined size was 100,162 — needed one more trim to land at ≤100,000. Rule: **never sequential-patch a near-limit file**; compute all deltas, write once.

## Pattern D: Full-Build Overwrite Gotcha

When using `write_file` to rewrite an entire in-repo SKILL.md, you MUST read the existing file first before composing the new content. The `write_file` tool is not an "edit" — it is a full overwrite. If you construct new content from memory rather than reading the existing file, you will lose the existing frontmatter and truncate the body. **Rule: before any full-build write, always `pathlib.Path(skill_path).read_text()` the existing file first.** Lesson from production: a session that rewrote ai-money-maker's SKILL.md from scratch (without reading the existing 90k-char file first) resulted in losing the frontmatter and 60% of the body.

## Pattern E: WSL Write Persistence

`pathlib.write_text()` silently fails to persist in WSL sandbox environments. Writes report success and Python re-reads confirm new content in-memory, but `git diff` shows no changes — the file on disk reverts to HEAD. Detection: `git diff` returns empty after a confirmed Python write. Exception: user-local tree (`/opt/data/skills/`) is not a git repo; Python `pathlib.read_text()` re-read is the ONLY authoritative verification. Workaround: write to `/tmp/` first, then `shutil.move()`.

## Pattern F: Orphan Audit 100% False Positive — Specific vs. Universal Link Patterns

**Symptom:** The orphan audit reports every reference file as an orphan (e.g., "29 orphans out of 29 files") when in reality **zero files are orphaned**. All reference files are correctly linked in SKILL.md, but the audit pattern only matches one link-label convention while the skill uses a different one throughout.

**Root cause:** The audit uses a specific pattern like `→ Full content:\s*\[([^\]]+)\]\(([^()]+\.md)\)` which only matches links with the `→ Full content:` prefix. If the skill consistently uses a different label (e.g., `→ 完整内容:`, `→ Related:`, or plain markdown `[filename.md](references/filename.md)` without any prefix), the pattern finds zero links. The orphan audit then computes `all_linked = set()` — empty — so `orphaned = existing - empty = existing`, reporting 100% false positives.

**Real case (wealth-mindset v1.107.0 run):** The skill has 29 reference files, all correctly linked in SKILL.md with the standard `→ Full content: [file.md](references/file.md)` format. The session's audit code used `→ Full content:\s*\[([^\]]+)\]\(([^()]+\.md)\)` which correctly matches 31 lines. However, the `→ Full content:` lines in the audit's **own pattern documentation** (the second capture group uses `[^()]+` which is correct) were being counted separately. The real failure mode: the audit matched 31 `→ Full content:` links but the skill's 29 files plus the `income-acceleration-tactics.md` link appeared in TWO sections (Income Acceleration AND Advanced Income Acceleration), so the Counter-based duplicate-line scan reported the line text as a "duplicate" even though it was correctly linking two separate sections to the same file. The orphan audit itself was clean (0 orphans). The false signal came from the **duplicate-link-count** check, not the orphan check.

**Detection decision tree:**
1. Run universal orphan audit first (catches ALL markdown links regardless of label):
   ```python
   all_links = re.findall(r'\[([^\]]+)\]\(([^()]+)\)', content)
   linked_bare = {url.replace('references/', '') for text, url in all_links if url.startswith('references/')}
   orphans = sorted(set(f.name for f in ref_dir.glob("*.md")) - linked_bare)
   print(f"Universal orphan count: {len(orphans)}")
   ```
2. If orphan count = 0: no real orphans. Any additional "duplicates" reported are cross-section links to the same file — intentional and correct.
3. If orphan count > 0: confirm whether the skill uses non-standard link labels. Run label scan:
   ```python
   prefixes = re.findall(r'→ ([^:\n]+):', content)
   print(f"Link prefixes used: {set(prefixes)}")
   ```
4. If `→ Full content:` audit says N orphans but universal audit says 0: the specific pattern missed the actual label format — not a real orphan problem. Trust the universal audit result.

**Rule:** Always start with the universal orphan pattern. The specific `→ Full content:` pattern is only correct when you've already confirmed the skill consistently uses that exact prefix for all reference links. The universal pattern works on all skill link conventions.

**Also:** A "duplicate link" for the same reference file appearing in two different sections is NOT a duplication problem — it's correct cross-referencing. The duplicate detection should flag same-prefix, same-line, same-file appearing twice in the same paragraph (within 200 chars), not cross-section reuse of the same reference file.

## Pattern K: V2 Detection Regex False Positives from Chinese Parentheticals

**Symptom:** A V2 detection regex returns dozens of "matches" on a file that manual inspection shows is actually clean (zero V2 malformed links). The file appears to pass the check but the detection tool reports anomalous results.

**Root cause:** The URL capture group `[^)]+` (or `[^()]+` if `)` appears in the text) can incorrectly capture the `.md` filename from a Chinese parenthetical `(...)` on the same line, when the parenthetical immediately follows a valid V2 link. Example:
```
→ Full content: [ai-b2b-exit-2025.md](references/ai-b2b-exit-2025.md)（企业谈判·合同架构·退出时机完整案例）
```
The regex `[^)]+` greedily matches past the Chinese `）` (U+FF09, not ASCII `)`), capturing `ai-b2b-exit-2025.md）` as the URL. Since the captured text ends in `.md`, it may trigger the V2 pattern detection.

**Real case:** ai-money-maker v4.5.4 — a regex scan reported 109 "V2 matches" on a file with 0 actual V2 malformed links. The detection regex was matching the filename inside Chinese parenthetical descriptions, not actual link text=URL pairs. The file required no fixes.

**Fix: String-operation detection (authoritative).**
```python
# Find → Full content: link lines, check if link_text == url_basename
for m in re.finditer(r'→ Full content:[^\n]+\)', content):
    line = m.group(0)
    b_start = line.index('['); b_end = line.index(']')
    link_text = line[b_start+1:b_end]
    u_start = line.index('(references/') + len('(references/')
    u_end = line.find(')', u_start)
    url_basename = line[u_start:u_end]
    if link_text == url_basename and link_text.endswith('.md'):
        print(f"V2 at pos {m.start()}: text={link_text}")
```

**Fix: Correct regex with `[^()]+` for URL group.**
```python
# [^()]+ excludes both ( and ), correctly stopping at ASCII ) regardless of Chinese punctuation
v2_candidates = re.findall(r'→ Full content:\s*\[([^\]]+\.md)\]\(([^()]+)\)', content)
```

**Rule:** When V2 detection returns an unexpectedly high count (>>10 on a file known to be clean), the regex is producing false positives from Chinese `）` in parenthetical descriptions. Verify with string operations, not regex count alone.