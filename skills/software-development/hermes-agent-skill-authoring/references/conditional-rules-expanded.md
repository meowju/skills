# Conditional Rules Expanded (SKILL.md Condensation Target)

> Extracted from `hermes-agent-skill-authoring` SKILL.md to bring it under the 100k char validator limit. These sections are fully represented here; SKILL.md now holds only the summary + `→ Full content:` pointer.

## 1. patch Partial-View vs. Modified-Since Warning (Pitfall 1)

**Two warning types, two fixes:**

- **"Partial view"** (from pagination): re-read via `pathlib` in same session, then patch. Or use `pathlib` string replacement directly — no need to re-read the same way the tool expects.
- **"Modified since you last read"** (concurrent edit): do NOT re-read — use atomic `pathlib.write_text()` with content you already have in memory. Re-reading the changed file compounds the race.

Real case: two subagents racing on ai-money-maker Run 51. Subagent B re-read after warning and retried `patch` — but the file had already been partially written by subagent A, so subagent B's old_string no longer matched. Result: sections embedded in the wrong section. Fixed by `git checkout` + clean atomic write.

**Cascade fix for concurrent multi-agent scenarios:**
```python
import pathlib
path = "/opt/data/skills/.../SKILL.md"
content = pathlib.Path(path).read_text()  # fresh read
# compute new_content
pathlib.Path(path).write_text(new_content)  # atomic write
assert len(new_content) <= 100_000
```

## 2. Pre-flight Git HEAD vs. On-Disk Check (Pitfall 2)

Before touching any skill modified by cron/other sessions:
```bash
git diff skills/<category>/<name>/SKILL.md
git log --oneline -3
```
Prevents: adding content that already exists, duplicating sections, missing prior version bumps. Real case: wealth-mindset Run 8 started intending to add Peter Lynch content — git diff revealed it was already present at 99,401 chars. Session switched to condensation.

## 2b. Size Gate — Python len() Not Optional (Pitfall 2b)

`wc -c` and `read_file` metadata hints can be stale by up to 2x in WSL. Python `pathlib.read_text()` is authoritative. Always size-check in the same session as the write — not from a subsequent session or terminal tool.

Real case: `wc -c` reported ~100k after a write that Python confirmed was only 99,367 chars.

## 2d. Cyclical Cron — Condense When All Topics Exist (Pitfall 2d)

Trigger: headroom < 2,000 chars AND no new topic to add. Condense the largest section that has a `references/*.md` file — replace inline body with concise summary + preserve the reference link.

Real case: wealth-mindset at 99,487 chars (513 headroom), all 8 research verticals present. Condensed Charlie Munger (5,206 → 3,934 chars) via existing reference link, freed 1,272 chars. Rule: **never conclude a cyclical run [SILENT] when condensation is available.**

## 2c. Post-Write Section Header Scan (Pitfall 2c)

After any edit that adds/moves/condenses/replaces sections:
```python
headers = [(m.start(), m.group(0)[3:].strip()) for m in re.finditer(r'\n## [^\n]+', content)]
for pos, title in headers:
    print(f"  {title[:70]}")
```
Catches missing `\n\n` between adjacent `##` headers — silent structural corruption where two headers render as one combined header.

## 3. delegate_task Research Failure — Mine Existing References (Pitfall 3)

When a cyclical cron job's subagents all return HTTP 404: don't defer or ship thin content. Mine existing `references/` files. Real case: 3 leaf agents returned HTTP 404; existing reference files contained 3 detailed cases + ROI framework that produced a full section expansion. Rule: **don't let tool failure produce empty runs** in cyclical cron-batch contexts.

## 4. File-Size Gate Before Patching Large In-Repo Skill (Pitfall 4)

When target file is near 100k (>80k), a patch can push over the limit silently. Pre-patch size check:
```python
size = len(pathlib.Path(path).read_text())
assert size + estimated_delta < 100_000
```
If near limit: migrate a section to `references/` first, then patch.

## 5. Orphaned Prefix After Bare Link Removal (Pitfall 5)

When removing a bare markdown link `[references/X.md]` from a section transition, the `→ Full content:` or `→ 完整内容:` prefix on the same line may be left dangling before a `---` divider. Fix: include the full `→ X:...\n` line including trailing newline when deleting. See also: `references/duplicate-reference-links.md` (Flavor 4).

## 6. Cron Job Without Size-Gate (Pitfall 6)

When the skill is invoked by a cron job that adds content and SKILL.md is already above 90k: pre-patch size check is mandatory. If `len(content) + new_content_estimate > 98k`, migrate a section to `references/` FIRST, then add content — not patch blind and hope.