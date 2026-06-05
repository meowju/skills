---
name: hermes-agent-skill-authoring
description: "Author in-repo SKILL.md: frontmatter, validator, structure."
version: 1.0.90
author: Hermes Agent
license: MIT
---
> **Headroom rule:** If SKILL.md is above 95k chars, use full-build only. Never patch twice on a >95k file in the same session — sequential patches accumulate invisible byte drift. Rule of thumb: do `len(pathlib.read_text())` before patching. If current size + new content estimate > 98k, split first (move section to references/) then patch. Python `pathlib.read_text()` is authoritative for size; terminal `wc -c` in WSL can be stale by 2x.
→ Full content: [references/iterative-headroom-recovery.md](references/iterative-headroom-recovery.md) — iterative headroom recovery: when first plan exceeds limit, scan same sections for additional condensation, compute revised plan, apply once atomically.

→ Full content: [references/pre-flight-git-check.md](references/pre-flight-git-check.md) — 3-step git HEAD pre-flight: catch uncommitted changes, V2 corruption, and prior-session partial fixes BEFORE planning new work on large user-local skills. Real case: ai-money-maker Run 178 wasted a pass without it.

> **Patch mismatch rule:** When `patch` reports "Found N matches" for a string Python confirmed is unique (`content.count(old_string) == 1`), switch to Python `pathlib` string replacement immediately. The `patch` tool's internal matching normalizes whitespace and handles Unicode differently than Python. Real case: `patch` reported "42 matches" for a string with 1 Python occurrence. Python replacement succeeded in one pass. Rule: Python `str.count()` is authoritative; use it before debugging `patch`.

## Overview

There are two places a SKILL.md can live:

1. **User-local:** `~/.hermes/skills/<maybe-category>/<name>/SKILL.md` — personal, not shared. Created via `skill_manage(action='create')`.
2. **In-repo (this skill is about this case):** `/home/bb/hermes-agent/skills/<category>/<name>/SKILL.md` — committed, shipped with the package. Use `write_file` + `git add`. `skill_manage(action='create')` does NOT target this tree.

## When to Use

- User asks you to add a skill "in this branch / repo / commit"
- You're committing a reusable workflow that should ship with hermes-agent
- You're editing an existing skill under `/home/bb/hermes-agent/skills/` (use `patch` for small edits, `write_file` for rewrites; `skill_manage` still works for patch on in-repo skills, but not for `create`)
- You discover a reference file in `references/` that has no corresponding `→ Full content:` link in SKILL.md (audit signal — always wire it up or remove it)
- You're about to patch a skill file that is already above 90k chars (run the size gate first)
- A session creates a new `references/` file — verify it appears in SKILL.md before the session ends

## Tool Availability — What to Do When write_file Is Not Available

**The critical constraint:** Not every session has `read_file`, `write_file`, or `execute_code`. Some sessions are restricted to `memory`, `skill_manage`, `skill_view`, and `skills_list` only. The skill-authoring workflow uses `write_file` for creating support files in `references/`, `templates/`, and `scripts/` — but if those tools are absent, the workflow breaks.

**What to do when restricted tools are the only available:**
- **If the task only needs SKILL.md patching** (no new references/ files needed): use `skill_manage(action='patch')` directly — it works with restricted tools.
- **If the task needs new `references/` files and `write_file` is unavailable**: defer the reference file creation to a session that has the tools. The skill update itself (SKILL.md changes + version bump) can still be done via `skill_manage(action='patch')`. Document the pending reference file in the patch's commit message so the next full-tools session picks it up.
- **Never attempt `write_file` repeatedly** if it keeps failing with "Tool 'write_file' does not exist" — check what tools are available first with `skill_view(name='hermes-agent')` or just proceed with the SKILL.md patch and defer the reference file.

**Rule of thumb:** Skill content additions that only touch SKILL.md (subsection additions, version bumps, description updates) are always possible with restricted tools. Additions that require new reference files need `write_file` or `execute_code`. If you have neither, patch the SKILL.md with a `→ Full content: references/...` link (even if the file doesn't exist yet) so the reference intent is captured — the file can be created in a later session.

**Detection in a restricted session:** If `read_file` fails with "Tool 'read_file' does not exist", you are in a restricted session. Do not retry — switch to `skill_manage` for SKILL.md operations and defer `references/` file creation.

## Required Frontmatter

Source of truth: `tools/skill_manager_tool.py::_validate_frontmatter`. Hard requirements:

- Starts with `---` as the first bytes (no leading blank line).
- Closes with `\n---\n` before the body.
- Parses as a YAML mapping.
- `name` field present.
- `description` field present, ≤ **1024 chars** (`MAX_DESCRIPTION_LENGTH`).
- Non-empty body after the closing `---`.

Peer-matched shape used by every skill under `skills/software-development/`:

```yaml
---
name: my-skill-name               # lowercase, hyphens, ≤64 chars (MAX_NAME_LENGTH)
description: Use when <trigger>. <one-line behavior>.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [short, descriptive, tags]
    related_skills: [other-skill, another-skill]
---
```

`version` / `author` / `license` / `metadata` are NOT enforced by the validator, but every peer has them — omit and your skill sticks out.

## Size Limits

- Description: ≤ 1024 chars (enforced).
- Full SKILL.md: ≤ 100,000 chars (enforced as `MAX_SKILL_CONTENT_CHARS`, ~36k tokens).
- Peer skills in `software-development/` sit at **8-14k chars**. Aim for that range. If you're pushing past 20k, split into `references/*.md` and reference them from SKILL.md.

## Peer-Matched Structure

Every in-repo skill follows roughly:

```
# <Title>

## Overview
One or two paragraphs: what and why.

## When to Use
- Bulleted triggers
- "Don't use for:" counter-triggers

## <Topic sections specific to the skill>
- Quick-reference tables are common
- Code blocks with exact commands
- Hermes-specific recipes (tests via scripts/run_tests.sh, ui-tui paths, etc.)

## Common Pitfalls
Numbered list of mistakes and their fixes.

## Verification Checklist
- [ ] Checkbox list of post-action verifications

## One-Shot Recipes (optional)
Named scenarios → concrete command sequences.
```

Not every section is mandatory, but `Overview` + `When to Use` + actionable body + pitfalls are the minimum for the skill to feel like a peer.

## Directory Placement

```
skills/<category>/<skill-name>/SKILL.md
```

Categories currently in repo (confirm with `ls skills/`): `autonomous-ai-agents`, `creative`, `data-science`, `devops`, `dogfood`, `email`, `gaming`, `github`, `leisure`, `mcp`, `media`, `mlops/*`, `note-taking`, `productivity`, `red-teaming`, `research`, `smart-home`, `social-media`, `software-development`.

Pick the closest existing category. Don't invent new top-level categories casually.

## Workflow

There are **two skill trees** — the authoring skill must name which one is targeted:

| Tree | Path | Creation method | Validator enforces? |
|------|------|---------------|---------------------|
| User-local | `~/.hermes/skills/<category>/<name>/SKILL.md` | `skill_manage(action='create')` | No (relaxed rules) |
| In-repo | `/home/bb/hermes-agent/skills/<category>/<name>/SKILL.md` | `write_file` + git add | Yes (strict) |

> **Note:** The live system may mount the user-local tree at a different root (e.g. `/opt/data/skills/`). Always confirm the actual path before writing. The distinction (user-local vs. in-repo) matters more than the exact path — in-repo skills must be committed; user-local skills must NOT be committed to the repo.

> **Note on cyclical cron jobs at near-limit:** When a rotating-research-verticals cron job (ai-money-maker, wealth-mindset) finds every topic already exists but headroom is <2,000 chars, the correct response is NOT "all covered, skip." The correct response: (a) check if existing reference files cover the current vertical with sufficient depth — if not, create a new reference file and corresponding inline section; (b) condense or migrate a large section to make room. Real case (ai-money-maker Run 167): all 8 verticals existed, but no reference covered insurance agents + real estate brokers. Session created `references/ai-insurance-realestate-oldmasters.md` (4,669 chars) + new Section 96 inline (1,666 chars) by migrating Section 83 to a reference link, landing at 98,674 chars with 1,326 headroom. Rule: extend the reference library when the current vertical is missing; only condense when the vertical is already richly covered.

> **Note on delta-recomputation spiral (Pitfall 63):** When planning a near-limit file edit, set the new content size budget FIRST (chosen from the reference file's content depth), then find condensations to match. Reverse order creates an unconstrained optimization that runs to the iteration limit without writing. See pitfall 63 below.

1. **Confirm target tree** — Is this a personal utility or something that should ship with hermes-agent?
2. **Pre-flight orphan check (user-local tree only):** The orphan audit regex pattern matters critically for user-local skills with `→ Full content:` links. Always normalize both sides to bare filenames before comparing:
   ```python
   import pathlib, re
   content = pathlib.Path(skill_path).read_text()
   ref_dir = pathlib.Path(skill_path).parent / "references"
   all_links = re.findall(r'\[([^\]]+)\]\(([^()]+)\)', content)
   linked = {url for text, url in all_links if url.startswith('references/')}
   linked_bare = {url.replace('references/', '') for url in linked}
   existing_files = {f.name for f in ref_dir.glob("*.md")}
   orphans = sorted(set(existing_files) - linked_bare)
   print(f"Orphans: {orphans}")  # Empty = all correctly linked
   ```
   **Orphan audit in restricted session:** If `read_file` fails with "Tool 'read_file' does not exist", you are in a restricted session. Do not retry — switch to `skill_manage` for SKILL.md operations and defer `references/` file creation.

→ Full content: [references/condense-add-atomic-pattern.md](references/condense-add-atomic-pattern.md) — condense+add as single atomic write; real case: ai-money-maker Run 152 (98,436→99,073 chars, +637 net).

→ Full content: [references/orphan-audit-patterns.md](references/orphan-audit-patterns.md) — string-anchored orphan detection; real case: purpose-finder flagged 13 false positives, actual 1.

> **Patch mismatch rule:** When `patch` reports "Found N matches" for a string confirmed unique by Python `content.count(old_string) == 1`, switch to Python `pathlib` string replacement immediately. The `patch` tool normalizes whitespace differently than Python — a string with 1 Python occurrence can be reported as "42 matches" by `patch`. Python replacement succeeds in one pass. Real case: ai-money-maker Run 57 — `patch` reported "42 matches" for a unique tail string; Python confirmed 1 occurrence; switching to Python replacement landed correctly in one pass. Rule: Python `str.count()` is authoritative for uniqueness confirmation; use it before debugging `patch`.

   > **For rewrites or structural changes:** `write_file` the whole SKILL.md. `skill_manage(action='edit')` also works but requires supplying the full new content.

   In both cases, validate before committing:
   ```python
   import re, pathlib
   content = pathlib.Path("skills/<category>/<name>/SKILL.md").read_text()
   assert content.startswith("---"), "Missing leading ---"
   # Find the FIRST \n---\n after position 3 (NOT the second --- which is a section break)
   m = re.search(r'\n---\n', content[3:])
   assert m, "Missing closing ---"
   end_pos = 3 + m.start() + m.end() - 3
   fm_text = content[3:end_pos-3]
   assert 'name:' in fm_text and 'description:' in fm_text
   # Manually check description length via regex (avoids YAML apostrophe issues):
   desc_match = re.search(r'description:\s*["\']?(.+?)["\']?\s*\n', fm_text)
   assert desc_match and len(desc_match.group(1)) <= 1024
   assert len(content) <= 100_000, f"File too large: {len(content):,}"
   assert content[end_pos:].strip(), "Empty body after frontmatter"
   ```
   **Critical:** The validator finds the FIRST `\n---\n` after position 3 — not the second `---` that closes a content section. In files with multiple `---` section breaks (e.g. `## 何时使用\n---\n## Overview`), the second `---` is a content section break, not the frontmatter close. Always search from position 3.

   **⚠️ Full-build overwrite gotcha (critical for large skills):** When using `write_file` to rewrite an entire in-repo SKILL.md, you MUST read the existing file first before composing the new content. The `write_file` tool is not an "edit" — it is a full overwrite. If you construct new content from memory rather than reading the existing file, you will lose the existing frontmatter and truncate the body. Lesson from production: a session that rewrote ai-money-maker's SKILL.md from scratch (without reading the existing 90k-char file first) resulted in losing the frontmatter and 60% of the body. **Rule: before any full-build write, always `pathlib.Path(skill_path).read_text()` the existing file first.** Then preserve the existing frontmatter when composing new content, or combine the existing frontmatter with the new body.

   **⚠️ WSL full-build validation order:** After writing a full-build patch, the file on disk may not reflect the Python write immediately due to WSL filesystem caching. Always validate with Python `pathlib.read_text()` in the same session that performed the write — never trust `wc -c` from the terminal for size validation in WSL environments.

   In both cases, validate before committing:
   ```python
   import re, pathlib
   content = pathlib.Path("skills/<category>/<name>/SKILL.md").read_text()
   assert content.startswith("---"), "Missing leading ---"
   # Find the FIRST \n---\n after position 3 (NOT the second --- which is a section break)
   m = re.search(r'\n---\n', content[3:])
   assert m, "Missing closing ---"
   end_pos = 3 + m.start() + m.end() - 3
   fm_text = content[3:end_pos-3]
   assert 'name:' in fm_text and 'description:' in fm_text
   # Manually check description length via regex (avoids YAML apostrophe issues):
   desc_match = re.search(r'description:\s*["\']?(.+?)["\']?\s*\n', fm_text)
   assert desc_match and len(desc_match.group(1)) <= 1024
   assert len(content) <= 100_000, f"File too large: {len(content):,}"
   assert content[end_pos:].strip(), "Empty body after frontmatter"
   ```
   **Critical:** The validator finds the FIRST `\n---\n` after position 3 — not the second `---` that closes a content section. In files with multiple `---` section breaks (e.g. `## 何时使用\n---\n## Overview`), the second `---` is a content section break, not the frontmatter close. Always search from position 3.

   **⚠️ Full-build overwrite gotcha (critical for large skills):** When using `write_file` to rewrite an entire in-repo SKILL.md, you MUST read the existing file first before composing the new content. The `write_file` tool is not an "edit" — it is a full overwrite. If you construct new content from memory rather than reading the existing file, you will lose the existing frontmatter and truncate the body. Lesson from production: a session that rewrote ai-money-maker's SKILL.md from scratch (without reading the existing 90k-char file first) resulted in losing the frontmatter and 60% of the body. **Rule: before any full-build write, always `pathlib.Path(skill_path).read_text()` the existing file first.** Then preserve the existing frontmatter when composing new content, or combine the existing frontmatter with the new body.

   **⚠️ WSL full-build validation order:** After writing a full-build patch, the file on disk may not reflect the Python write immediately due to WSL filesystem caching. Always validate with Python `pathlib.read_text()` in the same session that performed the write — never trust `wc -c` from the terminal for size validation in WSL environments.

5. **Git add + commit** on the active branch — only for in-repo skills.
   - **User-local skills** (`~/.hermes/skills/` or `/opt/data/skills/`): git operations silently fail because the tree is not a git repo. The file is updated on disk with no commit possible. Verify the `pathlib` — do NOT rely patch landed by reading the file with Python on `git status`. The cron scheduler may mount the user-local tree at paths that appear to be in a repo but aren't.
   - **In-repo skills** (`/home/bb/hermes-agent/skills/`): requires a terminal tool or git-capable execute_code to run `git add` and `git commit`. If neither is available in the current session, write the changes and defer committing to a session where those tools are present. An uncommitted in-repo skill change is lost on session end.
> **Note:** the CURRENT session's skill loader is cached — `skill_view` / `skills_list` will not see the new skill until a new session. This is expected, not a bug.

**When skill_view returns a truncated result:** Large skills (>100k chars) are saved to `/tmp/hermes-results/call_function_<hash>.txt`. Read that file with `execute_code: pathlib.Path(path).read_text()` in a full-tools session to access full content. In restricted sessions, `skill_manage(action='patch')` still works on the skill — patch uses the file on disk, not the truncated view.

## Section Tail Corruption — Detection & Repair

Real case: ai-money-maker v2.96→2.97. The last section's checklist items were followed by content from a different section with no `---` separator — invisible to reading but corrupts both sections.

**Symptom:** File tail shows checklist items from section N followed immediately by items from section N+1, no `---` between them:
```
- [ ] 制定了30天行动计划（找第一个这类客户）
可持续性排序
- [ ] 记住了 Claygent 的护城河本质...
```

**Fix:**
```python
checklist_item = '制定了30天行动计划（找第一个这类客户）'
pos = content.find(checklist_item)
checklist_end = pos + len(checklist_item)
new_content = content[:checklist_end] + '\n\n---\n'
# Verify: ends with ---\n and bleed-in content gone
```

**Detection signal: large inter-section gaps.** Section tail corruption often hides inside large gaps between consecutive section headers. A gap of >4,000 chars between two normally-sized sections (<2k each) is a red flag — the space between them may contain an orphaned ghost section, or duplicate checklist + off-topic content that bled into the wrong section. Always scan for gap anomalies when inspecting a file suspected of tail corruption:
```python
headers = [(m.start(), m.group(1), m.group(2).strip())
           for m in re.finditer(r'\n## ([一二三四五六七八九十]+)、([^\n]+)', content)]
for i in range(1, len(headers)):
    gap = headers[i][0] - headers[i-1][0]
    if gap > 4000:
        print(f"LARGE GAP {gap:,} chars between {headers[i-1][1]} and {headers[i][1]}")
```
→ Full content: [references/section-tail-corruption.md](references/section-tail-corruption.md) — two corruption variants now documented: Pattern A (section boundary lost) and Pattern B (intra-subsection sentence duplication, structure intact). Real case: ai-money-maker v3.05 section 四十 (Pattern A); wealth-mindset v1.144.0 Jocko Willink subsection (Pattern B).

**Detection signal: large inter-section gaps.** Section tail corruption often hides inside large gaps between consecutive section headers. A gap of >4,000 chars between two normally-sized sections (<2k each) is a red flag — the space between them may contain an orphaned ghost section with a different number than its position suggests, or duplicate checklist + off-topic content that bled into the wrong section. Always scan for gap anomalies when inspecting a file suspected of tail corruption:
```python
headers = [(m.start(), m.group(1), m.group(2).strip())
           for m in re.finditer(r'\n## ([一二三四五六七八九十]+)、([^\n]+)', content)]
for i in range(1, len(headers)):
    gap = headers[i][0] - headers[i-1][0]
    if gap > 4000:
        print(f"LARGE GAP {gap:,} chars between {headers[i-1][1]} and {headers[i][1]}")
```

**Variant: Mid-word truncation with no separator creates embedded section (breakup-recovery case).** A section-ending paragraph can be truncated mid-word (`"a def"`) with no `---` divider and immediately followed by a section header on the next line — creating an embedded duplicate section entirely inside another section's body. The truncated `"a def"` at the end of one paragraph becomes the opening of `def## The Anger Phase — Why It's Necessary and How to Work With It` on the next line, which the markdown parser interprets as a new section header. Detection: `re.finditer(r'## ')` on the full file reveals duplicate section titles that are invisible to line-based reading. Fix: restore the full paragraph text that was truncated at the section boundary, removing the embedded section block entirely. Full details in → Full content: [references/section-tail-corruption.md](references/section-tail-corruption.md)

## Section Boundary Corruption: `→ Full content:` Before `###`

When a `→ Full content:` link line is directly followed by a `###` subsection header with no blank line, markdown renders as a malformed compound link. Fix: insert `\n\n` between link `)` and `###` header.

## Two Skill Trees: Knowing Which One You're Editing

1. **Using `skill_manage(action='create')` for an in-repo skill.** `create` always writes to the user-local tree (`~/.hermes/skills/`), never to the in-repo tree (`/home/bb/hermes-agent/skills/`). For in-repo skills, use `write_file` + git add. For user-local skills, prefer `create` so the skill manager tracks it properly.

2. **Using `patch` to create a skill that doesn't exist.** `patch` requires the skill to already exist in the target tree. Verify with `skill_view(name)` before patching — `patch` on a non-existent skill fails silently or returns an unclear error. This applies to both trees.

3. **Inserting into a file with duplicate section numbers.** Before inserting a new numbered section (e.g. "## 九、"), scan all existing section numbers with `re.findall(r'\n## [一二三四五六七八九十]+、', content)` to detect duplicates or **number gaps**. If two sections share the same number, renumber BEFORE inserting so the new section lands in the correct sequence. If the target number already exists as a prior section, the new section must go after it — find the next free number first.

4. **Cascade renumbering creates new conflicts.** When you fix a duplicate by renaming section A from `十九、` to `二十四、`, you must then verify that `二十四、` was not already the target slot for the section you are about to insert. If the new section is also meant to be `二十四、`, you must re-assign it to the next free number (e.g. `二十五、`) *before* inserting — not after. The fix creates a new conflict if the new section's intended number was the one you just renamed into. Always do a fresh full scan immediately after any renumber patch, before composing the insertion.

4b. **Duplicate subsections within a section are equally dangerous.** A `### 三、` appearing twice inside `## 四十五、` is as damaging as a duplicate `## 三、`. The validator catches duplicate `## ` section numbers but not `### ` subsection numbers. After any patch that adds, moves, or renumbers subsections, always verify no duplicate `### ` numbers exist within each parent section:

```python
import re, pathlib
content = pathlib.Path(skill_path).read_text()
# Check all top-level sections and their subsections
sections = list(re.finditer(r'\n## ([一二三四五六七八九十]+)、', content))
for i, (sec_pos, sec_match) in enumerate(sections):
    sec_start = sec_pos
    sec_end = sections[i+1].start() if i+1 < len(sections) else len(content)
    sec_body = content[sec_start:sec_end]
    sub_nums = re.findall(r'\n### ([一二三四五六七八九十VI]+)、', sec_body)
    if len(sub_nums) != len(set(sub_nums)):
        from collections import Counter
        dupes = [n for n, c in Counter(sub_nums).items() if c > 1]
        print(f"DUPLICATE SUBSECTIONS in {sec_match.group(1)}: {dupes}")
```

5. **Skipping the duplicate scan after any patch that adds or moves a numbered section.** The scan must run after every such patch, even when you believe you're inserting at the end. Silent duplication persists until human review.

5b. **Skipping structural analysis before editing a large multi-session skill.** Before applying any fix (condensation, renumber, merge, or content addition) to a skill with >40 sections and >80k chars, always run a structural survey FIRST. This catches latent corruption before it compounds. Minimum survey:
```python
import re, pathlib
content = pathlib.Path(skill_path).read_text()
sections = [(m.start(), m.group(1), m.group(2)) for m in re.finditer(r'\n## ([一二三四五六七八九十百千万]+)、(.+)', content)]
nums = [n for _, n, _ in sections]
from collections import Counter
dup_titles = {k: v for k, v in Counter([t for _, _, t in sections]).items() if v > 1}
dup_nums = {k: v for k, v in Counter(nums).items() if v > 1}
print(f"Duplicates: {dup_titles}, {dup_nums}")
print(f"Total sections: {len(nums)}")
```
**Real case:** ai-money-maker v2.70 had section 五十七 at position 24096 (between 十五 and 十七), structurally behaving as section 十六 but numbered 五十七. The 4,086-char gap between 十七's start and 十八's start was caused by 五十七 being mislabeled — invisible without pre-edit structural scan. Also: duplicate section 三十四 (same title as 十七) had accumulated across sessions undetected. Detecting both BEFORE editing prevents compounding corruption. After fixing, commit immediately so subsequent sessions start from a clean state.

6. **Leading whitespace before `---`.** The validator checks `content.startswith("---")`; any leading blank line or BOM fails validation.

7. **Description too generic.** Peer descriptions start with "Use when ..." and describe the *trigger class*, not the one task. "Use when debugging X" > "Debug X".

8. **Placing `links:` at root level of frontmatter.** If you put `links:` directly under the YAML mapping root, YAML interprets `---` inside a link value as the document-end marker. Nest `links` inside `metadata.hermes.links` and use escaped quotes or rewrite to avoid the pattern.

9. **Apostrophes near the closing `---`.** YAML's `---` document separator is line-based. A string value containing `---` will confuse the parser. Use double-quoted strings with escaped apostrophes, or rewrite to avoid the pattern.

The author/license/metadata block. Not validator-enforced, but every peer has it; omitting makes the skill look half-finished.

**Pitfall 51: Authoring skill at size limit — patching requires split-first.** The skill is at 100,497 chars (497 over limit). Any patch attempt fails with the limit error even if the delta is small. Fix: migrate a well-linked section (>2k chars inline) to `references/`, replace with a `→ Full content:` link (~150 chars), then patch. The net reduction gets the file under 100k so patches can land. Version bump follows the content change.

**59. Execution Mandate for Cyclical Cron Jobs — No Reports, Only Writes.**

**Critical: Distinguish the two warning types — they have different fixes.**
- **"Partial view" warning** (from pagination): re-read the file via `pathlib` in the same session, then patch. Or use `pathlib` string replacement directly — no need to re-read the same way the tool expects.
- **"Modified since you last read" warning** (from concurrent/sibling modification): do NOT re-read and retry — the file changed between your read and write. Use atomic `pathlib.write_text()` with the content you already have in memory. Re-reading the changed file won't fix a race condition; it compounds it.
  - Real case: two subagents racing on ai-money-maker Run 51. Subagent B re-read after the warning and retried `patch` — but the file had already been partially written by subagent A, so subagent B's old_string no longer matched the current content at that position. Result: sections embedded in the wrong section. Fixed by `git checkout` + a clean atomic write in a subsequent session with no concurrent sibling.
  - Rule: "modified since you last read" → use atomic write with current in-memory content, do not re-read.

15b. **Sibling subagent concurrent modification (critical for cron-batch runs).** When multiple agent sessions run simultaneously against the same skill file (common in cron-batch scenarios), a sibling subagent can modify the file between the moment this agent reads it (via `execute_code` + `pathlib`) and the moment this agent calls `patch`. The `patch` tool does NOT re-read before writing — it uses the `old_string` as provided. If the file on disk already has a different content at that position, the patch lands incorrectly, silently corrupting downstream sections. The warning message "file was modified since you last read it on disk (external edit or unrecorded writer)" fires when this happens — but it is easily mistaken for the "partial view" warning from pitfall 15, leading the agent to re-read and retry, which only worsens the corruption as both agents race to fix the same file.

**Real case (ai-money-maker Run 51):** Two subagents both attempted to insert section 三十一 into the same file. The first patch succeeded in size but the old_string matched the wrong position in the sibling's version. The second patch used a clean `pathlib` read but still failed because the file had been partially written by the sibling agent between read and write. The result: sections disappeared from their correct positions and were embedded inside the wrong section. File was restored via `git checkout`.

**Mitigation (mandatory for cron-batch scenarios):**
1. Before any `patch` call on a large (>80k) user-local skill that may be targeted by concurrent agents, run `git status` or check file modification time. If the file was modified recently by another process, wait or coordinate.
2. After ANY `patch` call, immediately verify: (a) file size is within limit, (b) the target section appears at the correct position, (c) the following section is still intact. If any check fails, restore via `git checkout` immediately — do not attempt to fix the corruption with another patch.
3. The safest approach for concurrent multi-agent scenarios: use `execute_code` with Python `pathlib` string replacement + direct `write_text()` in a single atomic operation. This eliminates the read-then-write race entirely. Pattern:
```python
import pathlib
path = "/opt/data/skills/.../SKILL.md"
content = pathlib.Path(path).read_text()  # fresh read
# compute new_content from current content
pathlib.Path(path).write_text(new_content)  # atomic write
# verify immediately
assert len(new_content) <= 100_000
assert "TARGET_SECTION" in new_content
assert "NEXT_SECTION" in new_content
```

5. **Pre-flight git HEAD vs. on-disk check (first step before any cron session edits a large skill).** Before touching any skill file that has been modified by cron jobs or other sessions, always diff git HEAD against the on-disk file first:
```bash
git diff HEAD skills/<category>/<name>/SKILL.md
git log --oneline -3
```
If the diff shows uncommitted changes from a prior session, read them carefully. This prevents adding content that already exists, duplicating sections, missing a prior version bump, or targeting V2 corruption that was already partially fixed. **→ Full content: [references/pre-flight-git-check.md](references/pre-flight-git-check.md)**

5b. **Size gate with Python `len()` before any patch — not optional.** In WSL environments, `wc -c` and the `read_file` tool's `file_size:` metadata hint can both be stale by up to 2x due to filesystem caching. Always do this in the same session as the write:
```python
import pathlib
size = len(pathlib.Path("skills/<category>/<name>/SKILL.md").read_text())
assert size + estimated_delta < 100_000, f"File too large: {size:,}"
```
Do NOT use `wc -c` or tool metadata hints for size-gate decisions in WSL.

5d. **Cyclical cron jobs: condensation when all topics exist but headroom is tight.** When a recurring cron job following a rotating-research-verticals cycle (e.g., ai-money-maker, wealth-mindset, breakup-recovery) finds that every topic in the rotation already exists in the skill, the default response is to condense an existing large section — not conclude with "all covered" and exit thin. The trigger: headroom < 1,000 chars AND no new topic to add. Condense the largest section in a reference-linked skill (one with a `references/*.md` file) by replacing its inline body with a concise summary that preserves the reference link. Real case: breakup-recovery v5.11→5.12 (99,910 chars, 90 headroom). All 8 cyclical verticals existed but "The Science of Heartbreak" was missing. Condensed Communication Scripts (6,808→1,979, saved 4,829) and added new Science section (4,487 chars) atomically — computed both deltas simultaneously, wrote once. Net −342, landed at 99,569 with 431 headroom. Version bump + content addition as single atomic write. Rule: **never conclude a cyclical run with [SILENT] when condensation is available.**

**Real case (breakup-recovery Run 9, v5.11→5.12):** Skill at 99,910 chars (90 headroom). All 8 cyclical verticals existed but "The Science of Heartbreak" was missing (Run 1 topic). Condensed Communication Scripts (6,808→1,979 chars, −4,829) and added new Science section (4,487 chars) atomically — computed both deltas simultaneously, wrote once. Net −342, landed at 99,569 with 431 headroom. Version bump + content addition as single atomic write. Rule: when headroom < 1,000 and topic exists as a condensable section, migrate-first beats "all covered" exit.

**Pitfall 5e: "Reference-rich / inline-thin" detection — pick deepening targets by utilization ratio, not topic rotation.** In mature cyclical cron jobs (Run N>50), the topic rotation has been done multiple times and adding new top-level sections gets harder (size pressure, topic exhaustion). The default "deepen an existing section" decision needs a systematic signal, not a coin flip. The diagnostic: for every section, compute `inline_chars` vs. `total_chars_of_linked_references` and look for sections where the reference is 3–5× larger than the inline summary. Those are the highest-yield deepening targets — material is already written and linked, only the inline coverage is thin.

```python
import re, pathlib
content = pathlib.Path(skill_path).read_text()
ref_dir = pathlib.Path(skill_path).parent / "references"

positions = [(m.start(), m.group(1).strip())
             for m in re.finditer(r'\n## ([^\n]+)', content)]

print(f"{'Section':<55} {'Inline':>8} {'Refs':>8}  Ratio")
print("-" * 85)
for i, (pos, name) in enumerate(positions):
    end = positions[i+1][0] if i+1 < len(positions) else len(content)
    body = content[pos:end]
    inline = end - pos
    refs = re.findall(r'references/([^\)\s]+\.md)', body)
    refs_total = sum((ref_dir / f).stat().st_size for f in refs if (ref_dir / f).exists())
    ratio = refs_total / max(inline, 1)
    flag = "  <-- HIGH YIELD" if ratio > 4 and inline < 3000 else ""
    print(f"{name[:54]:<55} {inline:>8,} {refs_total:>8,}  {ratio:>4.1f}x{flag}")
```

**Real case (wealth-mindset v1.146.0→v1.147.0):** Skill at 97,130 chars. Section "Risk and Probability Thinking" had 1,652 inline chars linked to a 7,167-char reference file (ratio 4.3×). Inline mentioned expected value, fat tails, Antifragile, 10x/10% rule — but the reference also contained Howard Marks' second-level thinking, the math of ruin, skin in the game, and the build-vs-protect mode switch (4 frameworks, ~1,800 chars of unused material). Decision: extract those four into inline paragraphs, insert before the `→ Full content:` link, version bump 1.146.0→1.147.0. Result: section grew 1,652→3,515 chars, file landed at 98,992 (1,008 headroom), zero orphan/broken refs introduced. **Rule:** for cyclical deepening, the inline-to-reference utilization ratio is the single best signal for what to add next. Target sections where `refs_total > 3 × inline` AND `inline < 3,000`.

**Second-case validation (wealth-mindset v1.147.0→v1.148.0):** Same skill, 99 days later. File at 98,992 chars (1,008 headroom). Re-running the utilization survey picked "Mathematics of Exponential Wealth" (inline 1,375 chars vs reference 6,596 chars = 4.8× ratio) as the highest-yield target. The inline section had a redundant 416-char "Patience Premium" block whose content overlapped the deepen material that the reference would supply. **Combined atomic op:** (a) 3 V2 malformed link fixes (`[references/X.md](references/X.md)` → descriptive Chinese labels) at 0 net delta; (b) replace the redundant 416-char block with 1,267 chars of deepen material extracted from `exponential-wealth-math.md`; (c) version bump 1.147.0→1.148.0. Net delta +851 chars, landed at 99,880 (120 headroom), 0 V2, 0 orphans, 0 broken refs. **Confirmation rule:** when the chosen section has *redundant inline content that overlaps the deepen material*, replace-in-place beats add-on-top. The redundancy is itself the headroom; finding it requires reading both the inline section AND the linked reference.

**Third-case validation (purpose-finder Run 28, v4.111.0→v4.112.0):** Purpose-finder at 99,514 chars (486 headroom) with 24 sections, 45 `→ Full content:` links. Utilization survey ran across all sections. Career Capital Theory (Cal Newport) had inline 422 chars vs reference 9,207 chars = **21.8× ratio** — by far the largest gap, and inline was the smallest absolute size (well under 1k). Three Founder Mode Principles (in the Failure section) had inline 2,252 chars — large enough to absorb condensation without losing substance. **Paired operation:** (a) deepen Career Capital stub from 422 → 3,990 chars with 7 subsections (Passion Hypothesis flaws, What Capital Is/Is Not, Autonomy Paradox, 20-Hour Threshold, Deliberate Practice Hallmarks, Using in Conversation scripts, Craftsman vs Passion mindset table); (b) condense Three Founder Mode Principles 2,252 → 1,300 chars (fold "purpose application" subboxes into main paragraph; principle substance preserved); (c) condense MVP of Self Framework 751 → 427 chars; (d) drop Tactics #4 (Butterfield sentence) — fully duplicated content in the parent "Founder Mode Without a Company" subsection. **Net delta +2,040**; landed at 99,514 chars (486 headroom); 0 V2, 0 orphans, 0 broken refs, 24 sections, 45 reference links — all clean. **Generalized paired-op rule:** when the deepening target alone would exceed headroom, scan the survey output for sections >1,500 chars with structurally-redundant sub-elements (subboxes that restate the parent, single-line bullets duplicated in surrounding paragraphs, near-duplicate paragraphs). Each removable sub-element is a sub-block of headroom; aggregate them. Target the headroom budget exactly — never over-condense, never pad. **Pitfall 5e is now confirmed across three independent runs** (wealth-mindset × 2, purpose-finder × 1) on three different skills, three different verticals. The utilization ratio is the single most reliable deepening signal in mature cyclical cron jobs.

**Fourth-case validation (purpose-finder Run 29, v4.112.0→v4.113.0) — geographically-distributed condensation to fund a single target:** Purpose-finder at 99,514 chars (486 headroom). Utilization survey picked Philosophy/Religion/Wisdom Traditions as the top target with **inline 421 chars vs reference 18,253 chars = 43.4× ratio** — the highest ratio ever recorded across all pitfall 5e runs (vs the prior record of 21.8× in Run 28 and 14.7× in wealth-mindset v1.147.0). The deepening target alone was 533 chars (philosophy section: 421 → 954 inline = +533 net). With only 486 headroom available, the deepening alone would have overshot by 47 chars. Required condensation of −135 chars to balance. **Crucially, the condensation came from a DIFFERENT section than the deepening target** — SDT "Motivation Loop" paragraph (541→406 chars), in a completely different parent section (Self-Determination Theory, not Philosophy). The Run 28 sub-pattern was "all sub-elements in the same parent section" (three sub-elements all in Failure); Run 29 introduced "scan every section, not just the parent of the target." The aggregation rule scales: when the deepening target alone exceeds headroom, scan the WHOLE skill for condensable sub-elements (cascade metaphors, repeated sentences, redundant paragraphs) and accept condensation from any section — not just the section adjacent to the target. The philosophy content itself also included a refinement: when the reference's "Using This Reference in Conversation" section contains user-facing scripts, surface 2-3 of them inline directly (not just abstract insights), because user-facing scripts are the most-call-tested content. **Net delta +398**; landed at 99,914 chars (86 headroom); 0 V2, 0 orphans, 0 broken refs. The file crossed the 99,900 threshold for the first time in the skill's history — confirming the iterative-deepening strategy scales further than the Run 28 limit suggested. **Generalized rule (Run 29):** when the deepening target alone exceeds headroom, search the entire skill for ANY condensable sub-element — not just the same parent section. Geography of the source is irrelevant; what matters is total headroom budget. Pitfall 5e is now confirmed across four independent runs on three different skills.

5c. **Post-write section header scan.** After any edit that adds, moves, condenses, or replaces sections, always scan the header list:
```python
headers = [(m.start(), m.group(0)[3:].strip()) for m in re.finditer(r'\n## [^\n]+', content)]
for pos, title in headers:
    print(f"  {title[:70]}")
```
This catches missing `\n\n` between adjacent `##` headers — a silent structural corruption where two section headers render as one combined header (e.g., `## Peter Lynch: Invest in What You Know## Common Pitfalls`). Invisible to normal reading, but breaks section parsing and downstream patching.

**WSL filesystem caching (critical):** `wc -c` can report stale file sizes in WSL environments, showing values that are wrong by up to 2x. Real case: `wc -c` reported ~100k after a write that Python confirmed was only 99,367 chars. Always validate file size with Python `pathlib.read_text()` in the same session that performed the write — not from a subsequent session or with terminal tools. Python `pathlib.read_text()` is authoritative for size; terminal `wc -c` in WSL can be stale by 2x.

> **WSL + `read_file` tool metadata staleness:** The `read_file` tool outputs a hint line like `total_lines: N, file_size: M` that can also be stale in WSL environments. In one session, ai-money-maker's `read_file` returned `total_lines: 3775, file_size: 159755` — but the actual file was 79,531 chars and 3,775 lines. The `file_size` in the hint was inflated ~2x. Always validate actual content size with Python `pathlib.read_text()` in the same session, never trust tool hint metadata for size in WSL. The hint may reflect the file's pre-write cached size, not the post-write value.

**Real case:** wealth-mindset v1.29→1.30 — version bump used `patch` (first patch, no warning). Large content insertion then used `patch` again but triggered the "partial view" warning because the file had been read with `read_file(offset=...)` in an earlier call. Resolution: re-read via `execute_code` + `pathlib` before the second patch.

37. **delegate_task research failure in cyclical cron-batch jobs — mine existing references, don't defer.** When a cyclical skill-update job (e.g., ai-money-maker Run N cycling through verticals) calls `delegate_task` and all subagents fail with HTTP 404 (web search unavailable), the cron job has no human to ask. The wrong response: defer the run or ship thin content. The correct response: mine existing `references/` — treat the skill's own content library as a content asset to be remined across cycles. Real case (this session): 3 leaf agents all returned HTTP 404; existing reference files contained 3 detailed cases + ROI framework that produced a full section expansion. Rule: **don't let tool failure produce empty runs** in cyclical cron-batch contexts.

12. **File-size gate missing before patching a large in-repo skill.** When the target file is near the 100k limit (>80k chars), a patch that adds content can push the file over the limit silently. Always do a pre-patch size check: `size = len(pathlib.Path(path).read_text())` and confirm `size + estimated_delta < 100_000` before composing the new content. If near the limit, migrate a section to `references/` first, then patch.

12. **Orphaned prefix after bare link removal.** When removing a bare markdown link `[references/X.md]` from a section transition, the `→ 完整内容：` or `→ Full content:` prefix on the same line may be left dangling before a `---` divider. The result renders as a broken reference with `---` as the link text. Fix: include the full `→ X:...\n` line including the trailing newline when deleting. Full detection + fix pattern in `references/duplicate-reference-links.md` (Flavor 4).

13. **Running as a scheduled cron job without size-gate.** When the skill is invoked by a cron job that adds content (e.g., ai-money-maker Run N→N+1), the session has no human to ask for clarification. If SKILL.md is already above 90k, the cron job MUST do a pre-patch size check before composing the update. If `len(content) + new_content_estimate > 98k`, migrate a section to `references/` FIRST, then add content — not patch blind and hope.

24. **`patch` to a user-local skill targets the wrong tree.**

24b. **Numbered subsection (`### N、`) embedded inside a parent section is a silent structural corruption.** In large multi-session skills, a numbered subsection can appear anywhere within a parent section's body — not just at the intended position. This creates two failures: (a) the subsection's `###` header is invisible to the section-level duplicate-number scanner, so the corruption goes undetected by normal validation; (b) the parent section's character count is inflated by the embedded subsection, making the section appear much larger than it is. ai-money-maker had `### 五十一、信息差套利` (3,194 chars) silently embedded inside `## 三十、` — the section looked like 5,351 chars when only 2,157 were its actual body content.

**Detection:** Scan for `\n### [一二三四五六七八九十VI]+、` subsection headers anywhere in the file, then for each one, check whether its character position falls within any `## N、` section's boundaries. Subsections should only appear within their declared parent section. Use:

```python
import re, pathlib
content = pathlib.Path(skill_path).read_text()
# Find all top-level sections with their positions — 3-element tuples (pos, num, title)
sections = [(m.start(), m.group(1), m.group(2).strip()) for m in re.finditer(
    r'\n## ([一二三四五六七八九十百千万VI]+)、(.+)', content
)]
# Find all subsections — 2-element tuples (pos, num)
subsections = [(m.start(), m.group(1)) for m in re.finditer(
    r'\n### ([一二三四五六七八九十百千万VI]+)、', content
)]
for sub_pos, sub_num in subsections:
    # CRITICAL: sections tuple has 3 elements — unpack all 3 in the generator
    parent = next(
        (f"## {num}、 at pos {pos}" for pos, num, _ in sections if pos < sub_pos),
        "NONE (outside all sections — orphan!)"
    )
    print(f"### {sub_num}、 embedded inside: {parent} at pos {sub_pos}")
```

> ⚠️ **`sections` is 3-element, `subsections` is 2-element.** The generator `for pos, num, _ in sections` unpacks all three elements from each `sections` item — this is correct. The broken pattern `for sec_pos, num in sections` (only 2 targets for a 3-element tuple) raises `ValueError: not enough values to unpack` silently in `execute_code`, causing the generator to yield nothing on every iteration, so every `parent` reports `"NONE"` — masking all embedded subsections entirely. If all subsections show `"NONE"` as parent, the unpacking is broken — fix to 3-element. The same 3-element/2-element distinction applies to the `file_order` line in `references/structural-survey-code.md` (pitfall 39c): use `[(p, n, t) for p, n, t in sections]`, not `[(n, p) for p, n, _ in sections]`.

Fix: extract the subsection to become its own `## N、` section at the correct chronological position (after the section whose number is one less than the subsection's number), then delete the embedded copy from the parent. In ai-money-maker: extracted `### 五十一` from inside `三十`, placed it as `## 五十一、` after `五十、`, then renumbered the displaced `五十一` proper→`五十二` and `五十二` proper→`五十三`. After extraction, parent section shrank from 5,351→2,364 chars (−2,987).

Post-fix verification checklist (mandatory after any subsection extraction):
1. Subsection character count removed from parent section (parent size must decrease)
2. New `## N、` section appears at correct chronological position (between N−1 and N+1 sections)
3. Renumbered downstream sections still intact (N+1, N+2, etc.)
4. No duplicate `## N、` section numbers introduced by the renumbering cascade
5. The old subsection text no longer appears in the original parent section's boundaries.

24c. **Python tuple-unpacking generator bug in structural survey code.** The embedded subsection detector in pitfall 24b and the structural survey in pitfall 5b both iterate over `sections` (a list of 3-tuples `(pos, num, title)`) and use generator expressions like `next(f"## {num}" for pos, num in sections if pos < sub_pos)`. This raises `ValueError: not enough values to unpack` — `sections` has 3 elements per item but the generator unpacks each as 2. The fix: unpack all three and discard what you don't need: `next(f"## {num}" for pos, num, _ in sections if pos < sub_pos)`. This bug fires silently in `execute_code` (3 consecutive failures observed in ai-money-maker Run 101 structural survey) — the generator expression never yields, so every subsection reports `"NONE"` as parent. Detection: if all subsections show `"NONE"` as parent, the generator is broken. Fix: add the third unpack target.

> **⚠️ Same bug in `references/shell-subsection-detection.md` code block.** The detection scan in that reference file also uses the 2-element unpack pattern. Apply the same fix (`for sec_pos, num, _ in sections`) in that file's code block when editing it.

## 25. `git add` silently fails on non-repo directories.

**Orphan reference files are normal in large multi-session skills.** A session that creates a new `references/` file but never links it in SKILL.md leaves an orphan — invisible to every future agent. Detection: run the orphan audit script from pitfall 26 after any session that touches references/. Orphans accumulate silently — always check. Not a crash, but a persistent tax on discoverability.
```

27. **Reference files must be declared in the body AND linked in SKILL.md.** Two-step visibility requirement: (1) write the file to `references/` (makes it accessible to this session's skill_view), (2) add a `→ Full content: references/X.md` link in SKILL.md body (makes it discoverable to future sessions' skill loaders). Step 1 alone produces an orphan that no future agent can see.

27k. **Removing a duplicate section block can orphan its sole reference link.** When a section block is duplicated (often by an earlier `patch` mistake or two different sessions adding "the same" section), the two blocks usually have different surrounding context but the same linked reference. If a session identifies one as a duplicate and removes it, the *removal of that block also removes the only `→ Full content: references/X.md` link* that the orphan audit counts. Result: the duplicate is gone but a reference file silently becomes orphan — same end state as never adding the link in the first place.

**Pre-removal scan (mandatory for any duplicate-section deletion):**
```python
import re, pathlib
content = pathlib.Path(skill_path).read_text()
# Find all -> Full content: links and their char positions
links = [(m.start(), m.group(1)) for m in re.finditer(
    r'→ Full content:\s*\[references/([^\]]+\.md)\]', content)]
# Get the duplicate block boundaries
dup_start, dup_end = (block_start_pos, block_end_pos)
# How many -> Full content: links live inside the block we're about to remove?
in_block = [name for pos, name in links if dup_start <= pos < dup_end]
print(f"Links inside the duplicate block to be removed: {in_block}")
# For each link: is the SAME reference also linked elsewhere in the file?
for ref in in_block:
    other_count = content[:dup_start].count(ref) + content[dup_end:].count(ref)
    if other_count == 0:
        print(f"  ⚠️  {ref} is ONLY linked inside this duplicate block — will orphan it")
```

**Fix (atomic, single write):** if any `→ Full content: references/X.md` link is unique to the duplicate block, add a *new* link to that reference file from a semantically-appropriate place in the surviving copy of the section (or the surrounding section if the topic is no longer represented). The new link can be a one-liner — the goal is restoring the link, not duplicating content. Real case (purpose-finder Run 27): a duplicate "Designing Your Life — Bill Burnett & Dave Evans" subsection was identified; removing it would have orphaned `references/designing-your-life-burnett.md`. Pre-removal scan flagged the issue, and a one-line reference link was added to the new satisficing section (Burnett/Evans' Designing Your Life protocol is itself a satisficing framework — semantically natural). End state: 0 orphans, 0 V2 malformed, 0 duplicates.

**Rule:** Never delete a duplicate section block without first scanning for orphan risk on the linked references. If at risk, restore the link from a related location in the same atomic write.

27l. **Run-history / changelog files accumulate header artifacts across sessions.** Cyclical cron jobs typically maintain a `<skill>-run-history.md` (or `CHANGELOG.md`) where each run appends its entry to the top. After many sessions, the file header degrades: extra `---` separators, leftover empty `#` placeholders, blank-line clusters, partial run fragments. Real case (purpose-finder run-history.md after Run 27 cleanup): the file had a `# Purpose Finder — Run History\n\n*Started: ...*\n\n---\n\n#\n\n---\n\n\n---\n\n\n` artifact region at the top — a string-search for the exact artifact pattern fails across sessions because the whitespace/separator counts drift each time someone half-edits the file.

**Reliable cleanup pattern (split-then-rebuild, single write):**
```python
import pathlib
rh_path = pathlib.Path("<skill-dir>/references/<skill>-run-history.md")
rh = rh_path.read_text()
# Find the first "## Run" or "## " entry heading
m = re.search(r'\n## ', rh)
if m:
    header_region = rh[:m.start()]
    runs = rh[m.start():]
    # Strip any leading whitespace/separators from runs
    runs = runs.lstrip()
    # Rebuild: clean header + separator + new Run entry (prepended) + existing runs
    clean_header = "# Purpose Finder — Run History\n\n*Started: ...*"
    new_entry = "## Run N — ...\n\n**What changed:** ...\n\n**Why:** ...\n\n---\n"
    new_rh = clean_header + "\n\n---\n\n" + new_entry + "\n---\n\n" + runs
    pathlib.Path(rh_path).write_text(new_rh)
    assert new_rh.startswith("# Purpose Finder — Run History")
    assert "## Run N" in new_rh
    assert "## Run 1" in new_rh  # earliest run still present
```

**Why split-on-first-`## Run` is robust:** The artifact region (everything above the first `## Run` heading) is the variable that drifts between sessions. Splitting on the first `## ` heading gives a stable anchor that always lands on the start of the first chronological run entry. The header is then rebuilt from a known-clean template. This survives whitespace drift, doubled `---`, leftover `#` placeholders, and partial fragments — none of which survive a rebuild against a fixed template.

**Don't:** try to find-and-replace the exact artifact pattern with regex across sessions. Whitespace and separator counts drift; what works once fails next run.

**Malformed reference link taxonomy — three distinct variants, three distinct fixes.** Not all broken reference links are the same kind of breakage:

| Variant | Example | Problem | Fix |
|---------|---------|---------|-----|
| V1: Plain unprefixed | `[ai-venture-exit-deep.md](references/ai-venture-exit-deep.md)` | Missing `→ Full content:` label entirely | Prepend `→ Full content: ` |
| V2: Prefixed but malformed link text | `→ Full content: [ai-compliance-moat-2025.md](references/ai-compliance-moat-2025.md)` | Link text `[filename]` lacks `references/` prefix; URL is correct | Fix link text to `[references/ai-compliance-moat-2025.md]` |
| V3: Consecutive duplicate links | Two `→ Full content: [references/same-file.md](...)` lines in same paragraph | Visual duplication invisible to reading | Delete the bare successor; keep the one with richer surrounding context |

**V2 is the most insidious** — the `→ Full content:` prefix is present, so it looks correct, but the link text is a bare filename not a path. Future skill loaders resolve the link text as display text, showing a broken path as the visible label. Detection: scan for `→ Full content: \[[^references/][^\]]+\]\(references/` pattern (the link text starts without `references/`). Real case: three V2 instances in ai-money-maker v3.7.2 (`[ai-venture-exit-deep.md]`, `[ai-compliance-moat-2025.md]`, `[ai-compliance-moat-deep.md]`), all fixed in Run 58.

**V1 detection:** `→ Full content:` absent. Pattern: `[^→][^[]*\[([^\]]+)\]\((references/[^()]+)\)` — links without the arrow prefix. Common in sections written with raw markdown before the reference-link convention was applied.

**V3 detection:** Two consecutive `→ Full content: [same-file]` lines within 200 chars of each other. The orphan audit also misses this because both links point to an existing file — the duplication is in the link count, not in file existence. Fix: delete the one without extended context; if both have context, keep the first and note the second as redundant.

**Cross-prefix same-file references are intentional, not duplicates.** When the same target file appears once with `→ Full content:` and once with `→ 完整内容：` — these are NOT true duplicates. The two prefixes serve different narrative purposes and both are legitimate. The duplicate-detection scan should only flag same-prefix duplicates. Real case: ai-money-maker v3.7.5 flagged `ai-leverage-path.md` as a duplicate via a raw Counter sweep; manual inspection revealed one English and one Chinese prefix — intentional cross-prefix references. → Full content: [references/cross-prefix-same-file.md](references/cross-prefix-same-file.md)

→ Full content: [references/boundary-detection-method.md](references/boundary-detection-method.md) — string operations not regex; real case: purpose-finder flagged 13 false positives, actual was 1.

27j. **Chinese numeral regex `[一-千]` misses U+96F6 (零) — `一百零一` won't match.** → Full content: [references/pitfall-27j-chinese-numeral-zero.md](references/pitfall-27j-chinese-numeral-zero.md) — silent section count undercount; real case ai-money-maker Run 216 (85 reported, 86 actual).

**V2 is the most insidious**

→ Full content: [references/pitfall-61-stub-ghost-content.md](references/pitfall-61-stub-ghost-content.md) — stub section with ghost content trapped in Pitfalls; real case: purpose-finder Values Clarification stub + Natsukashii pitfall bleed-in; detection scan, atomic 4-step fix.

→ Full content: [references/v2-consecutive-duplicate-false-positive.md](references/v2-consecutive-duplicate-false-positive.md) — V2 format + consecutive duplicate removal → fullset false positive orphan audit; real case: wealth-mindset Run 3 (v1.128→v1.129): all 37 reference files reported orphans despite all being legitimately linked. Detection scan, fix pattern, consecutive-gap Python check.

→ Full content: [references/boundary-collision-pitfall-62.md](references/boundary-collision-pitfall-62.md) — 62: boundary corruption scan false positives on ##-level headers inside --- dividers; ### always fix, ## context-dependent.
→ Full content: [references/headroom-safety.md](references/headroom-safety.md) — headroom safety discount formula

**Why this is first resort, not fallback:** In skills with dense `---` section dividers (more than one `---` per section, common in multi-session skills like ai-money-maker with 50+ sections), any phrase in the condensed text can appear elsewhere. `patch` scans for the old_string pattern globally — unique section boundaries still fail if the boundary *text* overlaps with other content. Python boundary extraction bypasses this entirely. **Real case (ai-money-maker Run 56):** Section 三十一 (~2807 chars) was condensed by replacing the entire section body (header→verification checklist) with a 500-char summary. `patch` reported "Found 2 matches" because phrases like "Gross Margin" and "AI Agent" appeared in adjacent sections. Python boundary extraction succeeded in one pass.

33. **Restoring content from git HEAD after failed patches.** When a condensation patch goes wrong and creates duplicate sections or truncates content, the correct content can be recovered from `git show HEAD:skills/<category>/<name>/SKILL.md`. The original section content (item numbering, full text) exists in git and can be inspected with `git show HEAD:... | sed -n 'Ln1,Ln2p'`. This avoids guessing what the "correct" content should be — just restore verbatim from HEAD.

34. **Pre-insertion number-gap scan (critical for multi-session skills with sequential section numbering).** Before inserting a new numbered section (e.g. "## 四十七"), ALWAYS scan all existing section numbers first to detect which number is missing before composing the insertion:
```python
import re, pathlib
content = pathlib.Path("SKILL.md").read_text()
headers = re.findall(r'\n## ([一二三四五六七八九十]+)、', content)
print(f"Current sections ({len(headers)}): {headers}")
# Find the gap: which sequential number is absent
```
Insert at the correct chronological position — not at EOF. After inserting, run the scan again to confirm no duplicate was introduced. Real case: a session tried to add "四十七" without checking if it already existed — the number was simply absent from the sequence entirely, making the insertion itself correct but the section list still showed a gap. Always scan BEFORE inserting.

**34b.** The universal orphan pattern catches V2 links as orphan candidates — link text `[references/X.md]` is counted as an orphan because the filename `X.md` doesn't appear in the link URL. When the audit reports an orphan count equal to the total reference file count (e.g., "73 orphans out of 73 files"), it's a false positive — all files ARE linked, but via V2 format. Run a V2 pre-scan first:

```python
v2_matches = re.findall(r'\[references/([^]]+\.md)\]\(references/([^)]+\.md)\)', content)
print(f"V2 malformed links: {len(v2_matches)}")
```

If V2 count > 0, fix those first (replace `[references/X.md]` with `[descriptive label]` for each), then run the orphan audit. See pitfall 27b for the complete V2/V3 taxonomy and fix patterns.

**Decision rule for large orphan counts:** If the audit reports more than ~20 orphans on a multi-session skill with 50+ reference files, the pattern is likely mismatched — not a real orphan crisis. Switch to the universal pattern immediately and re-run before drawing conclusions. Full pattern and code in pitfall 27i.

```python
41b. **WSL filesystem caching makes `wc -c` unreliable for size-gate decisions.** In WSL environments, `wc -c` can report file sizes wrong by up to 2x due to filesystem caching delays. Always use Python `pathlib.read_text()` in the same session as the write to validate size. The `read_file` tool's `file_size:` metadata hint is equally unreliable in WSL.

37. **Concurrent multi-agent race condition on large skill files (critical for cron-batch).** When multiple agent sessions run simultaneously against the same skill file (>80k chars), a sibling subagent can modify the file between the moment this agent reads it (via `execute_code` + `pathlib`) and the moment this agent calls `patch`. The `patch` tool does NOT re-read before writing — it uses the `old_string` as provided. If the file on disk has changed at that position, the patch lands incorrectly, silently corrupting downstream sections.

**Post-patch verification checklist (always run after ANY write):**
1. File size ≤ 100,000 chars (Python `pathlib` read, not terminal `wc -c`)
2. Target section appears at correct character position
3. Following section still intact and at expected position
4. No duplicate section headers introduced
5. Version bumped (if applicable)

**Real case (wealth-mindset v1.144.0):** The Jocko Willink subsection in the Unstoppable Execution section had a sentence duplicated at its tail (`beats the brilliant person who starts and stops。` appeared twice consecutively, 49 chars). Invisible to reading but caught by a character-level tail scan. Fixed via `rfind()` + positional slice.

**Real case (ai-money-maker Run 51):** Two subagents both attempted to insert section 三十一 into the same file. The first patch's `old_string` matched the sibling's version at the wrong position. The second patch, despite a clean `pathlib` read, used `patch` (not atomic write) and landed incorrectly — sections disappeared from their correct positions. File was restored via `git checkout`. The fix: used `patch` with a correctly-anchored `old_string` in a subsequent session with no concurrent sibling. Rule: when concurrent modification is possible, prefer atomic Python `pathlib.write_text()` over `patch`.

**Real case (breakup-recovery v4.49.0):** File at 99,193 chars (807 headroom). Needed two operations: remove a duplicate `→ Full content:` link (−185 chars) and add a new `###` subsection (+848 chars). Naively the +848 section "doesn't fit" — but the combined delta = +848 − 185 = +663 chars fits within 807. Both operations computed in memory simultaneously → atomic write: 99,856 chars. If treated as sequential (fix duplicate first, then add section), the second patch would have failed the size gate alone. **Rule:** when combining structural fixes with content additions, always compute the *combined* net delta — the structural fix may free enough headroom to make a net-new insertion viable without migration.

38. **Run N → Run N+1 version bumping

38. **Run N → Run N+1 version bumping in cron-batch multi-session skills.** When a skill is updated via recurring cron jobs with a rotating research-verticals instruction (e.g., ai-money-maker: "Run 1 covers X, Run 2 covers Y, then repeat deeper"), each session bumps the version by one patch level (2.67.0 → 2.68.0). If two subagents run concurrently and both patch the version line independently, the file on disk will reflect only whichever write lands last — but that version may not match the content that also landed. The rule: treat the version bump and the content addition as a single atomic write (Python `pathlib.write_text()`), not two sequential `patch` calls. When using `patch` on version lines in concurrent environments, verify post-write that version and content are in sync — not just that the patch succeeded. Real case: concurrent subagents both patched version (2.68.0 → 2.69.0 and 2.68.0 → 2.68.0) with one also writing new section 五十五; final file showed version 2.68.0 with the new section present (sibling's content landed but version from the other agent's failed write persisted). The file was internally consistent but the version number was stale — this is invisible unless you check both.

39. **Section disorder (out-of-file-position) is invisible to casual reading.** In skills with Chinese numeral section headers, sections can appear in the file at the wrong position — e.g., 五十五 (副业收入) before 五十四 (B2B成交力学) in ai-money-maker — while the human reader doesn't notice because both headers are readable and the eye reads them in logical number order. This creates a mismatch between "where the section is in the file" and "where it should be in sequence," which breaks any patching that relies on sequential assumption. Detection: use Python `re.findall` to get ALL section positions, then sort by character position and compare against the expected sequential order. The `re.finditer` pattern produces a list in file-read order; compare against the sorted-integer Chinese-numeral order to find swaps. Real case: ai-money-maker v2.72 had 五十四 (副业收入) at file position 92,289 and 五十五 (B2B成交力学) at position 90,792 — a 1,497-char swap invisible to reading but fatal to any sequential patching logic. Fix: extract both-section-content blocks, reassemble in correct order, write once atomically.

**39b. Large inter-section gaps are the primary detection signal for section disorder.** The gap between consecutive section headers reveals disorder before any number-comparison scan. When a gap between section N and section N+1 is abnormally large (e.g., >3× average section size where adjacent sections average <1,000), it often means a displaced section from later in the file is sandwiched between them — a section swap. The gap size itself flags the problem; the swap is confirmed by comparing actual positions.

**Real case (ai-money-maker Run 86, v2.86→2.87):** The gap between 五十九 (pos 60,661) and 三十五 (pos 63,874) was 3,213 chars — far above the per-section average. The sections at those positions were 五十九 and 三十五, but the Chinese numerals jumped backward (五十九 → 三十五 should be impossible in sequential order). This immediately flagged that 六十二 and 六十一 had been swapped: 六十二 (should be at pos ~92,000) was found at pos 89,094 (between 五十八 and 六十一), while 六十一 was at pos 92,479 (where 六十二 should be). The fix: extract both blocks, swap their positions, write once. Zero-byte-delta operation — only the order changes, not the size.

**39c. Ghost-section embedding: a later section's body contains earlier numbered sections as invisible ghost content.** When sections are displaced by a swap, the wrong-position section's body may contain the ghost copies of the sections that should have appeared there. In ai-money-maker v3.55, section 八十八 had a 9,706-char body starting at pos 76,289 — but inside that body were embedded copies of sections 83-87 (ghost content), while section 83 proper started at pos 78,264. The gap between 82 and 88 (>9,000 chars) flagged the problem immediately. The fix: extract all `## N、` headers within the displaced section's body boundaries, identify which belong outside it, move them to correct positions, write once atomically. **The six-step structural survey (pitfall 5b) would have caught this before the disorder compounded.** Full detection + fix code in references/section-disorder-embedded-clusters.md.

**Detection:** After any patch that touches large sections, run a boundary-consistency check:
```python
import re, pathlib
content = pathlib.Path(skill_path).read_text()
sections = [(m.start(), m.group(1), m.group(2).strip())
            for m in re.finditer(r'\n## ([一二三四五六七八九十百千万VI]+)、(.+)', content)]
for i in range(1, len(sections)):
    prev_end = sections[i-1][0]
    next_start = sections[i][0]
    gap = next_start - prev_end
    prev_num, curr_num = sections[i-1][1], sections[i][1]
    in_gap = re.findall(r'\n## ([一二三四五六七八九十百千万VI]+)、', content[prev_end:next_start])
    if in_gap:
        print(f"MISPLACED headers in gap ({gap} chars) between ## {prev_num} and ## {curr_num}: {in_gap}")
    elif gap > 3000:
        print(f"LARGE GAP ({gap} chars) between ## {prev_num} and ## {curr_num} — investigate ghost embedding")
```

→ Full content: [references/section-disorder-embedded-clusters.md](references/section-disorder-embedded-clusters.md) — gap scan + number-order detection, embedded cluster pattern, pre-removal inner-header check, extract+reorder fix strategy. Real case: ai-money-maker v3.1.4 had 七十二、` at pos 60,717 between 三十六 and 四十.

**Gap threshold update:** The large-gap threshold for structural surveys should be **>3000 chars**, not >4000. The >4000 threshold produces false negatives on dense multi-section skills. Real case: ai-money-maker v3.05 had a 5,097-char gap between 十七 and 十八 — correctly flagged at >3000, revealed orphaned content. At >4000, this gap would have been missed.

**13b. Cyclical cron-job migrate-first pattern.** When a recurring cron job targets a file >95k with headroom <5k, migrate sections to `references/` FIRST, then add content — not patch blind and hope. Compute all replacements in memory simultaneously, write once, verify headroom ≥20k before writing new content. Web research failure → mine existing `references/` files instead of shipping thin content. Version bump and content addition must be atomic. Full pattern in → Full content: [references/cheap-offset-via-duplicate-removal.md](references/cheap-offset-via-duplicate-removal.md) — near-limit insertion via duplicate reference-link removal; real case: breakup-recovery v4.94 at 99,992 chars.

→ Full content: [references/cron-cyclical-research-pattern.md](references/cron-cyclical-research-pattern.md) — migrate-first at near-limit; headroom gate; RBF+Acqui-hire real case (ai-money-maker v3.26, Run 57): 99,858 chars + web search HTTP 404 → mined existing references → new section added.

**50. Migrate-first for near-limit cyclical jobs — "all covered" ≠ terminal.** When a cyclical cron job reports "all topics already exist," check headroom before concluding. If headroom < 1,500 and topic exists, migrate a section to `references/` first, then deepen. Real case: wealth-mindset at 99,399 chars (601 headroom), section existed but couldn't be expanded. Migrated 4,486-char section → `references/power-execution-unstoppable.md`, replaced with 924-char summary + link. Version bumped, 4,160 headroom gained, zero orphans. Rule: defer is wrong when headroom is the blocker.

## Handoff File: Mature Cyclical Skill State Machine (Run N > 20)

Once a cyclical cron skill passes ~20 runs, the original prompt template ("Run 1: X, Run 2: Y, repeat deeper") no longer reflects reality. The verticals in the original prompt are already covered, headroom has shrunk, and the agent has to re-derive the entire state every run. The fix: maintain a `references/cron-next-run-handoff.md` file as the de facto state machine.

**Required fields per run:**
- File size + headroom (CRITICAL — next run's size-gate)
- Section count + version
- Last run's section + reference path
- 2-3 recommended next verticals (with rationale)
- Headroom trend (rising/falling/stable across last 3 runs)
- Known structural issues (V2 links, version drift)

**Update protocol:** Separate commit after SKILL.md commit. Preserves granular git history (content vs. state-machine advances) without breaking atomicity of either.

**Real case (ai-money-maker Run 217):** Skill prompt said "Run 1: AI Old Masters, Run 2: B2B Sales..." — by Run 217, all 8 original verticals were covered multiple times. The handoff file's "Recommended Verticals" was the actual source of truth, not the prompt. Without it, every run re-derived 5-8 tool calls of state discovery.

→ Full content: [references/cron-handoff-file-pattern.md](references/cron-handoff-file-pattern.md) — full template, bump protocol, headroom trend tracking, anti-patterns (handoff as TODO, handoff as session log, stale handoff files).

→ Full content: [references/stub-placeholder-discovery.md](references/stub-placeholder-discovery.md) — wealth-mindset Run 8 real case: size gate blocked Bezos expansion (96,809 + 6,000 > 100k); switched to 468-char Tax Deep Dive stub → landed 99,385 chars, version 1.88.0. Thin-placeholder-stub discovery prevents `[SILENT]` conclusions in cyclical cron jobs.

41. **`pathlib.write_text()` silently fails to persist in WSL sandbox environments.** Writes report success and Python re-reads confirm new content in-memory, but `git diff` shows no changes — the file on disk reverts to HEAD. **Detection:** `git diff` returns empty after a confirmed Python write. **Exception — user-local tree (`/opt/data/skills/`):** not a git repo; Python `pathlib.read_text()` re-read is the ONLY authoritative verification.

**Workaround:** Write to a temp path first, then `shutil.move()`:
```python
import pathlib, shutil
pathlib.Path("/tmp/skill-temp.md").write_text(new_content)
shutil.move("/tmp/skill-temp.md", skill_path)
```
31. **WSL filesystem caching makes terminal `wc -c` unreliable.** `wc -c` can report stale file sizes in WSL environments, showing values that are wrong by up to 2x. Always validate file size with Python `pathlib.read_text()` in the same session that performed the write — not from a subsequent session or with terminal tools.

→ Full content: [references/wsl-write-persistence-workaround.md](references/wsl-write-persistence-workaround.md)
→ Full content: [references/regex-return-shape-bug.md](references/regex-return-shape-bug.md)
→ Full content: [references/pitfall-60-compaction-verification.md](references/pitfall-60-compaction-verification.md)

41b. **WSL filesystem caching makes `wc -c` unreliable for size-gate decisions.** In WSL environments, `wc -c` can report file sizes wrong by up to 2x due to filesystem caching delays. Always use Python `pathlib.read_text()` in the same session as the write to validate size. The `read_file` tool's `file_size:` metadata hint is equally unreliable in WSL.

→ Full content: [references/boundary-detection-method.md](references/boundary-detection-method.md) — the regex `\s*\n##` cannot distinguish correct from corrupt boundaries; string operations are correct; real case: purpose-finder flagged 13 false positives, actual corruption count was 1.

37. **Concurrent multi-agent race condition on large skill files (critical for cron-batch).** The six-step survey (pitfall 39c) must run before any patch, condensation, reordering, or insertion — regardless of whether the session is user-initiated or a scheduled cron job. Cron sessions are particularly dangerous because: (a) they have no human to ask if something looks wrong, (b) they inherit whatever state the file was left in by the previous session, (c) previous-session corruption (embedded subsections, swapped sections, duplicate headers) compounds if patched blindly. The survey catches disorder, embedded subsections, orphan blocks, and large gaps that indicate section swaps. Only after confirming a clean state should the session proceed to add new content. If the survey finds issues, fix them first — do not add new content to a corrupted file.

→ Full content: [references/patch-mismatch-pitfalls.md](references/patch-mismatch-pitfalls.md) — three-newline anchor uniqueness failure (breakup-recovery Run 8 real case); patch vs Python mismatch decision tree; patch debugging wastes tool calls, Python replacement first resort.
→ Full content: [references/duplicate-reference-links.md](references/duplicate-reference-links.md) — three flavors of duplicate → Full content: links; real case: break-recovery Run 9 (99,807 chars, 193 headroom, 6 duplicates removed, 1,140 chars freed); post-patch duplicate check pattern.

→ Full content: [references/section-tail-corruption.md](references/section-tail-corruption.md) — section-boundary uniqueness trap, dense-divider cascade failure, multi-step find-chain truncation, positional slicing as first-resort.
→ Full content: [references/reference-link-fixes.md](references/reference-link-fixes.md) — malformed/broken/orphaned reference link fixes, WSL sandbox write persistence for user-local skills.
→ Full content: [references/stale-size-from-compaction.md](references/stale-size-from-compaction.md)
→ Full content: [references/pitfall-60-orphan-tail.md](references/pitfall-60-orphan-tail.md) — orphan tail: section ends with broken reference link text (no → Full content: prefix); real case: wealth-mindset Risk section had " -- extended risk frameworks..." orphan fragment; detection scan, fix pattern.

→ Full content: [references/pitfall-63-delta-spiral.md](references/pitfall-63-delta-spiral.md) — delta-recomputation spiral: compute deltas correctly but never write; 5+ scratchpad iterations vs 0 disk writes; budget-first rule (set new content size from reference depth BEFORE finding condensations); real case: purpose-finder Run 30 (this session).

**Pitfall 60: Orphan Tail — Section Closes with Broken Reference Link Text**

**Rule:** Execute the write in the same session that does the planning. An imperfect patch is recoverable; a silent no-op is not. If you have headroom and a verified plan, apply the patch before the session ends. (Real cases 5x: see `references/pitfall-60-63-tool-call-budget.md`; fifth case (purpose-finder Run 31): plan verified, 30+ tool calls consumed, `pathlib.write_text()` never called — unifying signal across all 5.)

→ Full content: [references/pitfall-60-63-tool-call-budget.md](references/pitfall-60-63-tool-call-budget.md) — forward-looking 6-8 tool-call budget for near-limit planning; the three mechanical checkpoints; "trim the new content, don't expand condensation search" rule.

---

## Pitfall 63: Delta-Recomputation Spiral — Compute Once, Commit, Write; Don't Re-Run the Math 6×

A different failure mode from Pitfall 60: instead of *failing to write*, the session *writes* — but only to its own scratchpad. It computes `add_chars - remove_chars - headroom = net_delta` over and over in `execute_code`, each time tweaking the new content (1654 → 1677 → 1719 → 2200 → 2617 chars), recomputing the headroom match, finding it overshoots, trimming, recomputing, finding it undershoots, expanding, recomputing. Six iterations of delta math, zero writes to disk. The session ends with a precise plan documented in the chat history but nothing on disk.

**Detection signals (any one fires):**
1. Three or more `execute_code` calls in a row that ONLY print/calculate deltas without writing to the file
2. The new content string appears in 3+ variations within the session (slight rewrites, not bugs)
3. The "Net file delta" / "Headroom after" line is printed repeatedly with different values
4. The session reaches the tool-call limit mid-recomputation, not mid-execution

**Real case (purpose-finder Run 30, v4.113.0 → ?):** Target identified cleanly (Range/Generalists/Enough, 14.7× utilization ratio). Four valid condensation sources identified. Headroom: 86. New content drafted (Hedonic Treadmill + Sociometer insight). Plan should have been: write a ~1,400-char subsection + ~500 chars of Quick-Script condensations = net ~+0. Instead, the session **iterated on the new section size in scratchpad 8+ times** (1,200 → 1,400 → 1,610 → 1,683 → 1,646 → 1,431 → 1,758 → 2,058 chars), each time responding to a perceived headroom deficit by *expanding* the new content, then trimming, then expanding again. **Second-order spiral signal not in the original reference file: the agent's mental estimate of the new section's char count was wrong by ~30% in every iteration** — predicting 1,200 chars and getting 1,683, then predicting 1,400 and getting 2,058. Each miscount triggered a "let me recompute the total" call, which revealed a new overshoot, which triggered another recomputation. The file on disk remained at 99,914 chars (unmodified). Lesson: when the section size estimate keeps being wrong, STOP estimating and WRITE a draft to a string, then `len()` it — do not assume your inline char-count arithmetic is right. **Pre-write size check (mandatory before any patch in a spiral):** `actual = len(new_section.encode('utf-8'))` — Python string length is authoritative, not in-head counting.

**Confirmed across two independent sessions (purpose-finder Run 28 + Run 30):** Run 28 hit the spiral at a different point (computed 6 different new-content sizes, never wrote). Run 30 hit it at a different point (estimated 8 different sizes wrong by 30%, never wrote). Different trigger, same failure mode. The unifying signal across both: at the end of either session, `pathlib.Path(skill_path).write_text()` was never called. If that function was not called, the session was pitfall 63 regardless of how productive the planning looked.

**Root cause:** The optimization target is unclear. "Add a meaningful Range section" has many valid sizes (1,100 / 1,650 / 2,200 / 2,600 chars) and "stay under 100k" is a hard constraint with no soft feedback loop. Each delta-print shows a "still over" or "barely fits" result, triggering another iteration. Without a committed size target, the loop continues.

**The fix — pick a number, commit, write:**

```python
# 1. SET the size budget ONCE at the top
ADD_BUDGET = 1500  # chars of new content (chosen, not derived)
# 2. Find condensation sources until sum >= ADD_BUDGET + 86
required_condensation = ADD_BUDGET - 86  # = 1414
condensations = [
    ("VIA dup", content[start:end]),     # 555
    ("Burnett intro", content[s:e]),     # 316
    ("OODA group", content[s:e]),        # 277
    # that's 1148, need 266 more
]
# 3. Compose the new content TO EXACTLY ADD_BUDGET (not "as much as fits")
new_content = compose(range_section, target_chars=ADD_BUDGET)  # exact, no optimization
# 4. Compute and verify the EXACT net delta
net = len(new_content) - (len(original_section)) - sum(len(c[1]) for c in condensations) - 86
assert net <= 0, f"Still over: {net}"
# 5. Write ONCE, atomically
pathlib.Path(skill_path).write_text(new_full_content)
```

**The decision rules that break the spiral:**

1. **Set the new content size budget FIRST, before finding condensations.** "I want to add 1,500 chars of new content" is the input. Finding 1,500+ chars of condensation is a derived task. Reversing the order (find condensations first, then make new content fit) creates an unconstrained optimization.

2. **The new content size should be chosen from the deepening target's REFERENCE FILE, not derived from headroom math.** "How much material is in `enoughness-philosophy.md` that isn't already inline?" → read the reference, find the unique sections, target those. The reference file's content determines the deepening depth, not the available headroom.

3. **Once a plan is computed and the net delta is ≤ 0 (lands at or below 100k), WRITE. Don't recompute to "make sure."** Re-running the math 6 times is not validation — it's procrastination disguised as precision.

4. **If the plan overshoots, the fix is to TRIM THE NEW CONTENT, not to find more condensation.** The "find more condensation" reflex is what creates the spiral. New content can always be smaller; condensation has diminishing returns past the obvious redundancies (V2 links, duplicated intro paragraphs, closing quotes that restate the body). **Cascade hunt escalation (Run 31):** if >5 cross-section surveys happen without a writeable plan, the deepening does not fit at this size — switch to migrate-first or partial deepening.

**Hard trigger (purpose-finder Run 30 case):** the moment you compute a residual like "overshoots by 360 chars — need more condensation," STOP the search and trim the new content. Cutting 400 chars from a 2,879-char new section to land at 99,957 (43 headroom) is a clean write; finding one more 360-char condensation in a *different* section is a spiral step. New content is local and bounded; cross-section condensation hunts are unbounded and burn tool calls without writing. **Rule: any "need N more chars" sentence is the last delta-computation call before the write.**

5. **Write a partial deepening if necessary.** A 1,100-char subsection that lands cleanly is better than a 2,600-char deepening that doesn't get written at all. The next run can extend it.

→ Full content: [references/pitfall-63-sub-patterns.md](references/pitfall-63-sub-patterns.md) — three sub-patterns beyond the classic "Plan A vs Plan B" trap: (A) 30% size-estimate spiral, (B) "Plan A vs B vs C" trap, (C) "need N more chars" recursion. All three share the unifying rule: at most 2 delta-computation `execute_code` calls before `pathlib.write_text()`.
- Pitfall 60: zero writes, plan documented only in the final response
- Pitfall 63: writes happen (in scratchpad), but the disk file is never touched; the plan is correct and present in the session, just not applied

**Distinguishing Pitfall 63 from Pitfall 58 (atomic-deltas):** Pitfall 58 is about computing deltas correctly (don't sequential-patch; combine into one atomic write). Pitfall 63 is about the *prior step* — knowing when to stop computing and start writing. Pitfall 58 says "write once with all deltas combined." Pitfall 63 says "you'll never reach Pitfall 58's write if you keep recomputing."

---

## Pitfall 61: Sandbox Variable-Name Persistence — String Assigned, Then Reused as Path

**Symptom:** `AttributeError: 'str' object has no attribute 'read_text'` (or `write_text`) when calling a method on a variable that was correctly defined as a `pathlib.Path` in the code block. The variable's current value in the *running sandbox* is a plain string, not a `Path`, because a prior `execute_code` call in the same session assigned a string to the same name and the new call did not rebind it.

**Why this is different from the standard `'str' object` typo:** The standard cause is forgetting `pathlib.Path()` wrap on a fresh variable. The sandbox-persistence cause is *shadowing* — the variable *was* a Path in the *intended* code, but the actual executing code inherited an earlier assignment. The error message looks identical, but the fix is different.

**Real case (purpose-finder Run 28):**
```python
# Call N (in a prior tool call):
import pathlib
rh_path = "/opt/data/skills/productivity/purpose-finder/references/purpose-finder-run-history.md"
# Used `rh_path` (a string) to do something terminal — e.g. print() it.

# Call N+1 (this tool call) — assumed `rh_path` was still a Path:
import pathlib, re
rh = rh_path.read_text()  # AttributeError: 'str' object has no attribute 'read_text'
```
The error looks like a missing `pathlib.Path()` wrap. The actual cause: the prior call bound `rh_path` to a string, and the new call did not rebind it. Adding `pathlib.Path()` wrap silently fails to fix it because the variable was *not* a typo — it was a *carry-over*.

**Detection:**
1. The error fires on a variable name that *looks* correct in the code.
2. The code includes `import pathlib` but the failing variable is never wrapped in `pathlib.Path()` in the current call.
3. The variable name was used in a prior `execute_code` call in the same session (check the conversation history).

**Fix (always — in every new `execute_code` call):**
```python
# Use a distinct variable name OR wrap unconditionally:
rh_path = pathlib.Path("/opt/data/.../run-history.md")
# Then use:
rh = rh_path.read_text()
```

**Better discipline: never re-use the same variable name across `execute_code` calls.** Sandboxes vary in how aggressively they reset state; some keep module-level names, some don't. The safe pattern: use a fresh name each call (`rh_path_v2`, `rh_path2`) or always re-`pathlib.Path()` the variable unconditionally at the top of the call. This is a load-bearing habit, not an optional one.

**The other side: writing a string to a Path variable.** A subtler variant: a session that *intends* to assign `pathlib.Path(some_string)` but accidentally assigns the bare `some_string` to a `Path`-named variable (`skill_path = "..."` instead of `skill_path = pathlib.Path("...")`). Subsequent `skill_path.read_text()` then errors the same way. **Rule:** every Path-named variable must be a `pathlib.Path` object. If the value comes from a function that returns a string, wrap it. If the value comes from a string literal, wrap it. The only exception is when the value is being passed to a function that accepts `str | Path` (rare in this domain).

---

## Pitfall 58: Computing All Deltas Atomically Before Touching a Near-Limit File

When a file is at ~99,900 chars and you need to change reference links (+84 net) AND expand a section (~+276 net), you cannot patch sequentially and hope. The combined budget must be computed in memory before writing. Real case: planned two patches (reference link swap + self-anger expansion) but after computing both deltas together found the combined size was 100,162 — needed one more trim to land at ≤100,000. Rule: **never sequential-patch a near-limit file**; compute all deltas, write once.

---

## Pitfall 59: delegate_task Research Failure in Cyclical Cron-Batch Jobs — Mine Existing References, Don't Defer

When a cyclical skill-update job calls `delegate_task` and all subagents fail with HTTP 404 (web search unavailable), the cron job has no human to ask. The wrong response: defer the run or ship thin content. The correct response: mine existing `references/` — treat the skill's own content library as a content asset to be remined across cycles. Real case (this session): 3 leaf agents all returned HTTP 404; existing reference files contained detailed anger-to-forgiveness and self-anger content that produced the needed expansion. Rule: **don't let tool failure produce empty runs** in cyclical cron-batch contexts.

---

## Verification Checklist
- [ ] File is at `skills/<category>/<name>/SKILL.md` (not in `~/.hermes/skills/`)
→ Full content: [references/embedded-duplicate-real-case.md](references/embedded-duplicate-real-case.md) — full case transcript: ai-money-maker v2.79 duplicate 五十九 block contained legitimate top-level sections (二十六–三十五); pre-removal inner-header check prevents catastrophic deletion.

**Summary (inline):** In ai-money-maker v2.79, Copy A was a `### 五十九、` subsection embedded inside `## 三十三、` (not a top-level section), and Copy B was the real `## 五十九、` top-level header. A prior session attempted to "remove the duplicate" by deleting the block between `## 三十三、` and `## 三十五、` — losing 10 legitimate top-level sections (二十六–三十五). Recovery: `git checkout HEAD -- path`. Prevention: always check for `## N、` headers inside a suspected duplicate block before removing it.

**Pitfall N: Context bleed — meta-pitfalls from one workflow infecting a different skill.** A user-facing skill (one that talks to humans about their problems) sometimes contains pitfall entries that reference tool-internal concepts (`pathlib`, `skill_view`, `patch`, `headroom`, `100_000`, `user-local tree`, `in-repo skill`). Real case (purpose-finder Run 30): Common Pitfalls entries 11 and 12 told a person seeking life direction to run a Python size gate. Source of the bleed: co-located editing with a dev skill, or pitfall-number collision driving copy-paste from the most-recently-edited skill. Detection scan + fix pattern in → Full content: [references/context-bleed-meta-pitfalls-into-user-skill.md](references/context-bleed-meta-pitfalls-into-user-skill.md) — apply as standard pre-edit survey on user-facing skills, like orphan audit is for dev-facing skills.

→ Full content: [references/patch-mismatch-pitfalls.md](references/patch-mismatch-pitfalls.md) — three-newline anchor uniqueness failure (breakup-recovery Run 8 real case); patch vs Python mismatch decision tree; patch debugging wastes tool calls, Python replacement first resort.
→ Full content: [references/duplicate-reference-links.md](references/duplicate-reference-links.md) — three flavors of duplicate → Full content: links; real case: break-recovery Run 9 (99,807 chars, 193 headroom, 6 duplicates removed → 1,333 headroom); post-patch duplicate check pattern.
→ Full content: [references/pitfall-27e-flavour0-false-positive.md](references/pitfall-27e-flavour0-false-positive.md) — Flavor-0 false positive vs. true duplicate distinction; gap <50 rule applies only to same-line double-links; breakup-recovery 5.10.0 real case: three intra-section duplicates with 1,800–2,000-char gaps (all >>50, all true), 433 chars freed → 2,721-char expansion.

→ Full content: [references/v2-regex-false-positive-parens.md](references/v2-regex-false-positive-parens.md) — regex `[^)]+` false positives on Chinese `）` punctuation; correct `[^()]+` for URL group; string-operation boundary scan as fallback.

→ Full content: [references/reference-link-fixes.md](references/reference-link-fixes.md)
```python
# Post-extraction verification scan
import re, pathlib
content = pathlib.Path(skill_path).read_text()
sections = [(m.start(), m.group(1)) for m in re.finditer(r'\n## ([一二三四五六七八九十VI]+)、', content)]
subsections = [(m.start(), m.group(1)) for m in re.finditer(r'\n### ([一二三四五六七八九十VI]+)、', content)]
for sub_pos, sub_num in subsections:
        parent = next((f"## {num}" for sec_pos, num, _ in sections if sec_pos < sub_pos), "NONE")
    print(f"  ### {sub_num}、 inside: {parent} at pos {sub_pos}")
# Any output means an orphaned subsection remains — extract + delete it
```

- [ ] File is at `skills/<category>/<name>/SKILL.md` (not in `~/.hermes/skills/`)
- [ ] Frontmatter starts at byte 0 with `---`, closes with `\n---\n`
- [ ] `name`, `description`, `version`, `author`, `license`, `metadata.hermes.{tags, related_skills}` all present
- [ ] Name ≤ 64 chars, lowercase + hyphens
- [ ] Description ≤ 1024 chars and starts with "Use when ..."
- [ ] Total file ≤ 100,000 chars (aim for 8-15k)
- [ ] Structure: `# Title` → body starts immediately after frontmatter (sections can be in any order; `## Overview` + `## When to Use` + actionable body + `## Common Pitfalls` + `## Verification Checklist` is the peer-standard pattern — not enforced but expected)
- [ ] `related_skills` references resolve in-repo (or are explicitly OK to be user-local)
- [ ] `git add skills/<category>/<name>/ && git commit` completed on the intended branch
- [ ] After patching any numbered section, ran `re.findall(r'\n## [一二三四五六七八九十]+、', content)` to confirm no duplicate numbering was introduced
- [ ] After adding support files, called `skill_view` to verify they rendered correctly
- [ ] After adding any `→ Full content:` link to SKILL.md, the corresponding file exists in `references/` before session ends (defer file creation if `write_file` is unavailable; document pending file in patch commit message)
- [ ] Cross-prefix same-target references (→ Full content: + → 完整内容： to same file) confirmed intentional before flagging as duplicate
- [ ] All `→ Full content: references/` links point to files that actually exist on disk
- [ ] No V2-malformed links remain: scan `r'\[([^\]]+\.md)\]\(references/([^\)]+\.md)\)'` and confirm `t == u` count is 0. Fix: replace `[filename.md]` link text with a descriptive label.
- [ ] Size gate: checked `len(pathlib.Path(path).read_text())` BEFORE patching any skill already >85k chars
- [ ] After any session that creates a `references/` file: verify the `→ Full content:` link appears in SKILL.md (run orphan audit script from pitfall 26)
- [ ] All `→ Full content: references/` links point to files that actually exist on disk
- [ ] No V2-malformed links remain: scan `r'\[([^\]]+\.md)\]\(references/([^\)]+\.md)\)'` and confirm `t == u` count is 0. Fix: replace `[filename.md]` link text with a descriptive label.
- [ ] If writing both SKILL.md and references/*.md in same session: verify version: in user-local tree matches intent; if not, the wrong tree may be targeted
- [ ] Run `scripts/skill-authoring-audit.py` after any multi-patch session or structural edit (duplicate sections, subsection embedding, orphan refs, boundary corruption)

The audit script replaces the manual orphan checks from pitfall 26 and extends it with: duplicate section/subsection detection, embedded subsection detection (pitfall 24b), boundary corruption detection (pitfall 27c), and backtick-format link discovery. Run it against ai-money-maker or any large multi-section skill after major edits.