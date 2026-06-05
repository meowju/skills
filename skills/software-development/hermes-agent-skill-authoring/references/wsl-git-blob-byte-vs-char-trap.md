# WSL Git Byte-Count vs Python Char-Count Trap

> **Category:** Skill Authoring / WSL Environment Pitfall  
> **Severity:** High — causes incorrect repair attempts on clean files  
> **Trigger:** Chinese-heavy skill files in WSL environments

## The Problem

When analyzing a skill file, you may run:
```bash
git cat-file -s skills/productivity/ai-money-maker/SKILL.md
# → 190,583
```

And in Python:
```python
len(pathlib.Path("skills/.../SKILL.md").read_text())
# → 92,143
```

The file appears to have **grown by ~98k bytes** — looks like severe corruption or accidental bulk insert. You attempt repairs.

**Nothing is wrong.** The git command reports **raw UTF-8 bytes**. Python `read_text()` decodes to **Unicode characters**. Chinese characters are 3 bytes each in UTF-8. A 92k-char Chinese skill ≈ 190k bytes — not a problem, just encoding.

## The Misdiagnosis Chain

1. Assistant sees 190k bytes vs 92k chars → "file is 2x oversize, must be corrupted"
2. Attempts corrective operations using position coordinates computed from byte-count assumptions
3. Operations would write corrupted intermediate file
4. `git checkout HEAD -- path` correctly restores — but only because the pre-edit state was clean
5. Session reports no changes made — the "fix" was a no-op and consumed the session

**The real fix:** Recognize the byte/char ratio for what it is. A 2x ratio for Chinese-heavy content is expected, not a corruption signal. Python `len()` is authoritative; git byte counts cannot be compared directly to it.

## The Ratio Is Predictable

| Content Type | Byte/Char Ratio |
|---|---|
| Pure ASCII (English) | ~1.0x |
| Mixed ASCII + CJK | 1.5–2.0x |
| Chinese-heavy (90%+ CJK) | 1.8–2.2x |
| Binary content | >3x (anomaly) |

## How to Verify Correctly

```python
import pathlib

path = "/opt/data/skills/productivity/ai-money-maker/SKILL.md"
char_count = len(pathlib.Path(path).read_text())
byte_count = pathlib.Path(path).stat().st_size

print(f"Characters: {char_count:,} / 100,000 (limit)")
print(f"Bytes: {byte_count:,}")
print(f"Ratio: {byte_count / char_count:.2f}x")

# Normal for Chinese: 1.8–2.2x
# Anomaly: >2.3x → check for binary; <1.5x → mostly ASCII
```

## The Checkout Verification Pattern

When restoring from git and wanting to confirm the working copy matches HEAD:
```python
import subprocess, pathlib

path = "/opt/data/skills/productivity/ai-money-maker/SKILL.md"
# Restore
subprocess.run(["git", "checkout", "HEAD", "--", path],
              cwd="/opt/data/skills/productivity/ai-money-maker")

# Verify
working = pathlib.Path(path).read_text()
working_size = len(working)

git_bytes = int(subprocess.check_output(
    ["git", "cat-file", "-s", "HEAD:SKILL.md"],
    cwd="/opt/data/skills/productivity/ai-money-maker"
).strip())

git_chars = len(subprocess.check_output(
    ["git", "show", "HEAD:SKILL.md"]
).decode("utf-8"))

print(f"Working copy: {working_size:,} chars")
print(f"HEAD blob: {git_bytes:,} bytes / {git_chars:,} chars")
print(f"Match: {working_size == git_chars}")  # Should be True
```

## Rule: Never Compare Git Bytes to Python Chars Without Ratio Check

```
git_bytes → compare to pathlib.stat().st_size (byte count)
Python chars → compare to 100,000 (char limit)

These measure different things. Cross-comparison causes misdiagnosis.
```

## Real Case (ai-money-maker session, Run 20/21)

- Git HEAD blob: **190,583 bytes**
- Python `read_text()`: **92,143 chars**
- Ratio: **2.07x** (normal for Chinese-heavy content)
- Session: incorrectly interpreted as "file is oversized" → attempted section swap
- Would have written corrupted intermediate at wrong position coordinates
- Correctly aborted via `git checkout HEAD -- path` → no changes made
- Lesson: git bytes ≠ Python chars. Ratio is the signal, not the absolute values.