# Concurrent Patch Recovery

## The Warning

When `patch` returns: `"file was modified since you last read it on disk (external edit or unrecorded writer)"` — this is NOT a "re-read and retry" signal. It is a conflict indicator: another writer modified the file between your read and your write. Retrying with the same old_string will fail or corrupt.

## The Failure Mode

Real case (ai-money-maker Run 201):
1. Session A reads file at size 96,774
2. Session A calls `patch` with old_string anchored to section 101's closing checklist
3. Meanwhile Session B (a sibling/concurrent agent) writes the same file from a different state
4. Session A's patch lands — but the old_string matched the wrong position in Session B's version, creating duplicate sections (section 102 appeared twice)
5. Session A receives the "modified since you last read" warning

Session A's error: re-read and retry `patch` with the old string from the old read. The file has already been partially written by Session B. The old_string no longer matches the current content at that position.

## The Correct Protocol

```
Step 1: git checkout HEAD -- <path>          # Restore to clean state
Step 2: pathlib.read_text() fresh           # Read from restored file
Step 3: Recompute old_string from fresh read # Position may have shifted
Step 4: patch once, verify size immediately  # Atomic write check
```

Do NOT re-read using the same tool/method that produced the stale read. Use Python `pathlib` directly.

## Detection

After ANY `patch` call on a file >80k chars in a concurrent environment:
1. Check file size: `len(pathlib.Path(path).read_text())`
2. Check target section exists at expected position
3. Check following section is still intact

If any check fails: `git checkout HEAD -- <path>`, then recompute and patch again.

## Prevention

For large user-local skills (>80k chars) that may be targeted by concurrent cron agents:
- Use atomic Python `pathlib.write_text()` instead of `patch` when possible
- Compute all positions from a single fresh read
- Write once, verify once

The `patch` tool does NOT re-read before writing. It uses the `old_string` as provided — if the file changed, the patch lands at the wrong position silently.