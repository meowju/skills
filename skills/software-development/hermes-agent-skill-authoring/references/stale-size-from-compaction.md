# Stale Size from Context Compaction

## Context Compaction Summaries Carry Stale Size Figures

When a skill is compacted (condensed, migrated to references/, etc.), the context compaction summary written by the model reflects the file state at the time of the write — but the file may be written to disk at a slightly different size due to byte-level differences in how the new content fits together. More critically, the size figures in the summary can become stale across sessions.

**Real case:** Context summary said `99,701 chars / 299 headroom`. Actual file size was `44,492 chars` — a 2x difference. The summary was written during a compaction session but reflected an intermediate state, not the final on-disk state.

**Rule:** Always re-verify with `pathlib.read_text()` in the current session before making patching decisions. Never trust size figures from prior context summaries.

**Correct size gate pattern:**
```python
import pathlib
skill_path = "/opt/data/skills/productivity/<name>/SKILL.md"
current_size = len(pathlib.Path(skill_path).read_text())
print(f"Current file size: {current_size:,} chars")
print(f"Headroom: {100_000 - current_size:,} chars")
```

**WSL filesystem caching:** `wc -c` and tool metadata hints can be stale by up to 2x in WSL. Python `pathlib.read_text()` is authoritative.
