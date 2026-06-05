# WSL `pathlib.write_text()` Persistence Workaround + Multi-Patch Staleness

> Extracted from hermes-agent-skill-authoring SKILL.md pitfall 41d (Run 10). Real case documented from ai-money-maker Run 10. Updated with pitfall 41e (Run 63).

## Pitfall 41e: Multi-Patch Staleness in Same Session (Run 63)

**The problem:** Even after applying the temp-file workaround correctly, `old_string` from Patch N becomes stale by Patch N+1. Each `shutil.move()` lands a new version on disk — but your Python variable `content` still holds the previous version's state. If Patch N+1 uses text from the stale `content` variable as `old_string`, it matches the wrong position.

**Real case (ai-money-maker Run 10).
**⚠️ `shutil.move()` can also silently revert.** Even after the temp-file workaround, the destination file can revert to its previous state within seconds — no exception raised. Read back with `pathlib.Path(path).read_text()` in the **same tool call** that performed the move. Do NOT trust terminal tools, separate tool calls, or subsequent sessions.
**Real case (ai-money-maker Run 63):** Three sequential patches on a 96k-char file using `shutil.move()`:
- Patch 1: Condensed table in section 二十五 → used `content[table_start:table_end]` + `shutil.move()` → landed ✓
- Patch 2: Expanded section 二十五 with new 判断 content → `old_string` from `content` read before patch 1 → **matched wrong position** (patch 1 shifted section boundaries)
- Patch 3: Version bump → `old_string` from stale `content` → **matched wrong position** again

**Fix:** Before each patch, always re-read: `content = pathlib.Path(skill_path).read_text()` fresh. Never reuse the `content` variable across patches in the same session. Alternatively, build all replacements in memory first, apply as one combined atomic write.

**Critical distinction:** This is NOT the persistence failure (41d). Writes persist correctly with the temp-file workaround. The failure is using stale in-memory text for `old_string` in subsequent patches.

**Rule:** For multi-patch sequences on large (>80k) files, either (a) re-read before every patch, or (b) compute all changes in one pass and write once.

---

## Pitfall 41d: `pathlib.write_text()` Does Not Persist to Disk

In some WSL configurations, `pathlib.Path(path).write_text(new_content)` reports success and Python re-reads confirm the new content in-memory — but `git diff` shows no changes. The file on disk reverts to HEAD after the session. This is distinct from **filesystem caching staleness** (pitfall 31), where writes land correctly but `wc -c` is stale. Here, writes do **not** land on disk.

**Detection:**
```bash
git diff skills/<category>/<name>/SKILL.md
# Returns empty despite confirmed Python write
```

**Do NOT use for verification:**
- `pathlib.read_text()` re-read — can show modified in-memory state that was never flushed to disk
- `wc -c` from terminal — unrelated to persistence, only measures staleness
- `git status` — shows the right state but doesn't distinguish caching from persistence failure

**The only reliable detection in WSL sandbox environments:**
```bash
git diff skills/<category>/<name>/SKILL.md
```
If diff is empty after a confirmed Python write, the write did not persist.

## The Workaround

Write to a temp file first, then `shutil.move()`:

```python
import pathlib, shutil

skill_path = "/opt/data/skills/productivity/ai-money-maker/SKILL.md"
temp_path = "/tmp/ai-money-maker-SKILL.md"

new_content = build_new_content()

# Write to temp path (bypasses WSL filesystem layer)
pathlib.Path(temp_path).write_text(new_content)

# Atomic move
shutil.move(temp_path, skill_path)

# Verify with git diff
import subprocess
result = subprocess.run(['git', 'diff', skill_path], capture_output=True, text=True)
if not result.stdout:
    print("WARNING: git diff empty — write may not have persisted")
```

**Why this works:** Writing to `/tmp/` first bypasses whatever WSL filesystem layer causes `write_text()` to report success without flushing to the host filesystem. `shutil.move()` then atomically replaces the target.

**Do NOT use `subprocess.run(['mv', ...])`** — it inherits the same WSL persistence issue. Use Python's `shutil.move()`.

## Exception: user-local tree

For user-local skills at `/opt/data/skills/` (which is not a git repo), git diff silently fails regardless. For these skills, **Python `pathlib.read_text()` re-read is the only authoritative verification** — it will correctly show the on-disk content even when git is inapplicable.

```python
# User-local skill — verify with Python re-read, not git
pathlib.Path(skill_path).write_text(new_content)
verify = pathlib.Path(skill_path).read_text()
assert "TARGET_SECTION" in verify  # Only way to confirm persistence in user-local tree
```

---

## Pitfall 41f: `shutil.move()` Produces Corrupted Output in Cron execute_code Environment (breakup-recovery Run 9)

**The problem:** In a cron job context where `execute_code` is the only available writing tool, `shutil.move()` was used as the documented workaround for WSL persistence. The write appeared to succeed (no Python exception), but the resulting file was **corrupted** — link lines were duplicated, and content from one section bled into another. This is a distinct failure mode from:
- 41d: write reports success, file on disk unchanged
- 41e: write lands but `old_string` becomes stale for next patch
- **41f (this case):** write lands but content is corrupted — duplicate link lines, malformed sections

**Real case (breakup-recovery Run 9 cron session):** Used `execute_code` with `pathlib.Path(temp_path).write_text(new_content)` + `shutil.move(temp_path, skill_path)` for three consecutive patches (somatic-anger-compendium.md, internal-working-model.md, brain-chemistry-breakup.md). Each patch returned no exception. Verification with `pathlib.read_text()` immediately after move showed the intended new link lines. However, `git diff` revealed the file on disk was corrupted: `brain-chemistry-breakup.md` appeared twice, and link lines from different sections were mixed together in ways that didn't match any of the three intended replacements. File restored via `git checkout HEAD --`.

**Detection:** The corruption only becomes visible via `git diff` or when a subsequent section-content assertion fails. A single `pathlib.read_text()` immediately after `shutil.move()` in the same tool call shows the intended content — but `git diff` from a later tool call reveals the on-disk corruption. This suggests the Python sandbox's `/tmp/` write persists within the sandbox's view of the filesystem, but `shutil.move()` from that sandbox's `/tmp/` to the actual skill path produces a malformed file at the OS level that only `git diff` can detect.

**Workaround for cron sessions:**
1. Write to `/tmp/` and `shutil.move()` as usual
2. **Immediately** run `git diff <path>` via terminal in the same session — if diff shows unexpected content, restore via `git checkout HEAD --` before attempting another write
3. For critical updates, after `shutil.move()`, read with `pathlib.Path(skill_path).read_text()` and assert expected content matches — if assertion fails, `git checkout HEAD --` immediately

**Rule:** The combination of `execute_code` + `shutil.move()` + `git diff` verification in a cron session is the minimum reliable write path. Never skip the `git diff` check after using `shutil.move()` in a cron context.
