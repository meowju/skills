# Pre-Flight Git HEAD Check — Catch Corruption Before Starting

## The Pattern

Before any cron session edits a large user-local skill (>80k chars), do a 3-step pre-flight in this exact order:

1. `git status` — is the file already modified on disk vs. HEAD?
2. `git diff HEAD -- <path>` — what uncommitted changes already exist?
3. If uncommitted changes exist: read them carefully before composing new content

**This 3-step check catches the three silent corruption modes that waste sessions:**

| Signal | What it means | Action |
|--------|--------------|--------|
| `git diff` is empty + `git status` clean | File is at HEAD — safe to proceed | Continue |
| `git diff` is empty + `git status` shows modified | WSL filesystem caching — Python read is authoritative | Re-read via `pathlib` |
| `git diff` shows non-empty changes | Uncommitted prior session edits exist | Read diff BEFORE planning |

## Why the Order Matters

1. `git status` tells you whether the file differs from HEAD at all
2. `git diff` shows exactly what those differences are — before you plan new work
3. Acting on the diff before reading it ensures you don't:
   - Add content that already exists (wasted session)
   - Duplicate sections that already exist
   - Miss that a prior run already bumped the version
   - Target V2 link corruption already partially fixed by a prior session

## Real Case — ai-money-maker Run 178

Session started intending to add new content + fix V2 links. `git diff` revealed:
- 2 V2 malformed links already identified and targeted by a prior session's diff
- Section 九十八 had been expanded in the uncommitted diff (content already on disk, not yet committed)
- Version had been bumped in the uncommitted diff

Without the pre-flight check, the session would have:
- Attempted to fix V2 links that were already in the diff's fix plan
- Potentially overwritten the existing section 九十八 expansion
- Bumped version redundantly

## The Silent Mode: Prior Session Partial Fix

The most dangerous case: a prior session partially fixed a skill file (e.g., fixed V2 links but didn't commit), then another session runs `patch` targeting the same sections. The second session's `old_string` no longer matches the current content at that position — because the first session's patch partially landed. The result: section embedding, content in wrong sections, silent corruption.

**Mitigation:** Always run `git diff HEAD -- <path>` before any patch plan on a file that might have uncommitted changes from concurrent subagents.

## Run 211: When Pre-Flight Was Skipped But Succeeded (False Security)

**Session:** ai-money-maker Run 211 — adding section 一百零一 (AI渠道分销商, 5,116 chars) to a 92,296-char file.

**What happened:** Session read the skill via `pathlib.read_text()`, computed the new section, verified size headroom (2,588 chars), patched, version-bumped, and wrote successfully. The 3-step pre-flight git check was skipped entirely.

**Why it worked:** No concurrent sibling subagent was modifying the file during the session. The on-disk state matched what the session read. Pre-flight would have been clean anyway.

**Why the skill still required it:** On a file at 92,296 chars (high corruption risk), a concurrent subagent can modify the file between the moment this session reads it and the moment it writes — within the same session window. The pre-flight is not about whether the session's own read was clean — it's about catching what OTHER sessions may have left behind. Skipping it on a large file is a calculated risk, not proof that pre-flight is unnecessary.

**Rule:** The pre-flight git diff is NOT optional on files >80k in cron-batch contexts, even when the session's own reads look clean. Run 211 worked despite skipping it. The next session that skips it on a file with concurrent sibling modifications will corrupt silently. The fix after corruption (`git checkout` + clean atomic write) costs more than the 30 seconds the pre-flight takes.

**Key insight:** A clean `git status` output does NOT mean the file is at HEAD — it only means there are no uncommitted changes staged in the index. A concurrent subagent that did `git checkout` mid-session or wrote a partial patch without committing leaves no trace in `git status` but corrupts the file on disk. Only `git diff HEAD` catches this.

## Quick 3-Step Template

```python
import subprocess, pathlib

path = "/opt/data/skills/productivity/ai-money-maker/SKILL.md"

# Step 1: git status
status = subprocess.run(['git', 'status', '--porcelain', path], 
                        capture_output=True, text=True, cwd='/opt/data')
if status.stdout.strip():
    print(f"WARNING: File has uncommitted changes:\n{status.stdout}")

# Step 2: git diff
diff = subprocess.run(['git', 'diff', 'HEAD', '--', path],
                     capture_output=True, text=True, cwd='/opt/data')
if diff.stdout.strip():
    print(f"Uncommitted diff found ({len(diff.stdout)} chars):")
    print(diff.stdout[:500])
    print("...")

# Step 3: Proceed based on what you found
content = pathlib.Path(path).read_text()  # Python read is authoritative
```

## Key Rule

> A clean `git status` is not sufficient — use `git diff HEAD`. A session that opened a skill file and made changes (even if the patch failed) may have partially written content that is invisible to `git status` but present on disk.

## Headroom Safety Discount Reminder

When doing the pre-flight on near-limit files (>95k), remember the **headroom safety discount**: 
- Available headroom < 2,000 chars → assume true headroom is 50% of measured (WSL caching may inflate reported headroom by up to 2x)
- Available headroom < 500 chars → treat as critically tight, migrate-first before adding

See: `references/headroom-safety.md`
