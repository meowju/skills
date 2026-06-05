# WSL Restricted-Session Skill Update Workaround

**Problem:** Session is in WSL, has `write_file` but no `execute_code`, and needs to update a skill.

**Symptom:** `write_file` reports success, but `git diff` shows no changes. The file on disk reverts to HEAD after the session ends.

**Root cause:** WSL filesystem caching makes `write_file` report success before the write actually persists to durable storage. The tool believes it succeeded; the data is not durable.

**Solution:** Use `skill_manage(action='patch')` with the exact existing section content as `old_string` and the new content as `new_string`. The patch tool operates via the skill manager's file handler, which correctly persists through WSL's caching layer.

**Procedure:**
1. Read the existing SKILL.md via `skill_view(name)` to get current content
2. Identify the exact `old_string` — the section or block you want to replace (must be byte-for-byte identical to what's on disk)
3. Compose the `new_string` — the replacement content
4. Call `skill_manage(action='patch', name='<skill>', old_string=old_string, new_string=new_string)`

**Why this works:** The `patch` tool writes through the skill manager's file handler, which uses the correct WSL-compatible I/O path. `write_file` writes to a temp location and relies on filesystem cache durability before the move, which WSL may not guarantee.

**When to use which workaround:**

| Session has | Use |
|-------------|-----|
| `execute_code` | `pathlib.write_text()` to temp + `shutil.move()` |
| `write_file` only (no `execute_code`) | `skill_manage(action='patch')` with exact `old_string` |
| Both absent | `skill_view` + `skill_manage(action='patch')` — read-only view is sufficient |

**Real case:** breakup-recovery skill Run 3 — session had no `execute_code`, `write_file` reported success but `git diff` was empty after every write. Switched to `skill_manage(action='patch')` with the full Quick Scripts section as `old_string` and the expanded 10-item version as `new_string`. Patch landed in one pass; `git diff` confirmed changes; file verified at 98,644 chars post-write.

**Precaution:** Before patching, always confirm the target string is unique via `skill_view(name)` (count occurrences in the displayed content). Patch replaces all occurrences of `old_string` unless `old_string` is truly unique — anchor to section headers + opening lines to ensure uniqueness.