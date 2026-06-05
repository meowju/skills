# Pitfall 41f: Size Gate Passes But Write Never Persisted — Silent 400-Char Overwrite

**Real case:** break-recovery Run 4. Skipped grief section condensation patch on a 99,102-char file with 898-char headroom. New section = 1,322 chars, condensation target = 432 chars, delta = +890, expected total = **99,992 chars** (8-char headroom). Python size check passed. The `shutil.move()` from `/tmp/` reported success. Re-read showed **100,414 chars** — 414 over limit. The write had partially failed silently.

**Root cause:** The `assert len(new_content) <= 100_000` checked the in-memory `new_content` variable — which was correctly 99,992 chars. But the `shutil.move()` from `/tmp/` to the target path partially failed (or the source temp file was corrupted before the move), resulting in a 100,414-char file on disk. The size gate passed in-memory because the Python variable was correct; it said nothing about whether the write actually succeeded.

**Why this is distinct from pitfall 41d:** Pitfall 41d covers writes that don't persist at all (file reverts to HEAD). This case covers writes that **partially persist** — landing on disk but with wrong byte count. `git diff` shows changes (unlike 41d's empty diff), but the wrong content landed.

**Why this is distinct from pitfall 31 (WSL caching staleness):** Caching staleness means `wc -c` reports wrong size while the file is correct on disk. This case means the file on disk is actually wrong — the write itself was corrupt.

**Detection:**
```python
import pathlib
skill_path = "/opt/data/skills/productivity/breakup-recovery/SKILL.md"
temp_path = "/tmp/breakup-recovery-SKILL.md"

# ... build new_content ...
# new_content is confirmed 99,992 chars

pathlib.Path(temp_path).write_text(new_content)
shutil.move(temp_path, skill_path)

# WRONG: re-read in same call shows the correct in-memory state
# RIGHT: verify via git diff AND byte count
import subprocess, pathlib
git_result = subprocess.run(['git', 'diff', skill_path], capture_output=True, text=True)
disk_size = len(pathlib.Path(skill_path).read_text())
print(f"Git diff lines: {len(git_result.stdout.splitlines())}")
print(f"Disk size: {disk_size}")
assert disk_size <= 100_000, f"Disk size {disk_size} exceeds limit"
assert len(git_result.stdout) > 0, "git diff empty — write may not have persisted"
```

**The real verification is TWO checks, not one:**
1. `len(pathlib.Path(skill_path).read_text()) <= 100_000` — confirms correct size on disk
2. `len(git_result.stdout) > 0` — confirms the write actually reached the git-tracked file

**Never shortcut:** If either check fails, the write is not confirmed. A passed `assert len(new_content) <= 100_000` on the in-memory variable is **not a confirmed write**.
