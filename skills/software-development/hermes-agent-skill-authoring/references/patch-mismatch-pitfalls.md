# Patch Mismatch: When patch Reports N matches for a String That Is Unique (v2)

> Real case: ai-money-maker Run 57. The `patch` tool reported "Found 42 matches" for a string Python confirmed was unique (`content.count(old_string) == 1`). Patch debugging consumed 5 tool calls before switching to Python `pathlib` string replacement, which succeeded in one pass.

## The Core Problem

The `patch` tool's internal matching algorithm normalizes whitespace and handles Unicode differently than Python's `str.count()`. A string confirmed as unique by Python can be reported as "42 matches" or "10 matches" by `patch`.

## The Decision Tree

1. `patch` reports "Found N matches" for an `old_string` you confirmed is unique via Python `content.count(old_string) == 1`
2. **Do NOT debug `patch`** — switch to Python `pathlib` string replacement immediately
3. The `patch` debugging consumed 5 tool calls before the switch in the real case — those calls were wasted

## The Reliable Approach: Python String Replacement

```python
import pathlib
path = "/opt/data/skills/.../SKILL.md"
content = pathlib.Path(path).read_text()

# Confirm uniqueness
assert content.count(old_string) == 1, f"Found {content.count(old_string)} matches"

# Replace
new_content = content.replace(old_string, new_string, 1)

# Verify
assert len(new_content) <= 100_000
assert "TARGET_SECTION" in new_content
assert "NEXT_SECTION" in new_content

# Atomic write
pathlib.Path(path).write_text(new_content)
```

## When to Use patch vs. Python Replacement

| Situation | Approach |
|----------|----------|
| Small typo, end-of-file append | `patch` is fine |
| String confirmed unique by Python `count()` but `patch` reports N matches | Python immediately |
| Multi-insertion into large file | Python — compute all deltas in memory first |
| Condensation with unique boundary anchors | Python slicing |

## Three-Newline Anchor Uniqueness Failure (breakup-recovery Run 8)

When condensing, the `old_string` boundary was cut at `\n\n\n` — which appears 6+ times in the file as part of section transitions. `content.count(old_string) == 1` passed on the wrong string (it matched the first occurrence), then the replacement landed in an unexpected section, creating duplicate sections. Prevention: always anchor `old_string` to the section header line plus opening paragraph — text that is unique by construction.

## 47. V2 Link-Text Double-Counting Trap: `[filename.md](references/filename.md)` Inflates Reference Counts

**Pattern:** Many skills use the V2 link format: `[filename.md](references/filename.md)` — the link text is the bare filename, identical to the URL path. When composing a new section that also uses a V2-formatted link, the string `filename.md` appears **twice** in the new section text: once in the link text and once in the URL. This causes `new_section.count("filename.md") == 2`, which then inflates `new_content.count("filename.md")` by 1 relative to the actual number of links.

**Real case (breakup-recovery Run 9):** `new_sec6` started with:
```markdown
→ Full content: [internal-working-model.md](references/internal-working-model.md)
```
`new_sec6.count("internal-working-model.md")` returned 2 — one for the link text, one for the URL.

**Fix — use descriptive link text:**
```markdown
→ Full content: [internal working model deep dive](references/internal-working-model.md)
```
`new_sec.count("internal-working-model.md") == 1` (only the URL in the parentheses) — no inflation.

**Rule:** When inserting new sections into a file where existing links use the V2 format, use descriptive link text in your new sections. Alternatively, count actual link *lines* rather than raw string occurrences.

## 48. `ellipsis` Placeholder (`...`) in execute_code Silently Fails on String Write

**Pattern:** When composing new skill content in `execute_code` and using `pathlib.write_text(new_content)` where `new_content` was assigned via `final = ...` (Python Ellipsis object as placeholder), the write silently fails with `TypeError: data must be str, not ellipsis`. The error surfaces inside `execute_code`.

**Real case:** Run 128 — `execute_code` block ended with `final = ...` followed by `tmp_path.write_text(final)` → `TypeError`. The session hit the iteration limit before the write could be corrected.

**Rule:** When building content in `execute_code` for a skill file, use explicit string variables. Never leave `...` as a stand-in for actual content in a variable passed to `write_text()`.

## 49. Raw Substring Count Returns 2× for Complete Markdown Links

**Pattern:** `content.count("filename.md")` returns 2 for each complete link `[text](references/filename.md)` — one in the link text `[]`, one in the URL `()`. This makes raw substring count useless for "exactly 1 link" assertions.

**Real case (breakup-recovery Run 8):** `anger-therapeutic-value.md.count(...)` returned `2` for exactly 1 link.

**The correct verification:**
```python
complete_links = re.findall(r'\)]\((references/[^)]+\.md)\)', content)
url_counts = {}
for url in complete_links:
    url_counts[url] = url_counts.get(url, 0) + 1
assert url_counts.get('references/X.md', 0) == 1
```

## 53. Git Restore Invalidates `old_string` From Prior V2 Link-Fix State

**Pattern:** A session V2-fixes a bare filename link (`[ptg-breakup.md]` → `[PTG Breakup research]`) in SKILL.md and composes a patch `old_string` referencing the fixed text. The patch fails (size, mismatch, or concurrent write). The session runs `git checkout HEAD -- path` to restore the file. On the next patch attempt using the pre-restore `old_string`, the string is not found — because the restored file reverted to the committed bare filename link text.

**Real case (breakup-recovery Run 4–5):** Session V2-fixed `[ptg-breakup.md]` link text to descriptive. First patch failed. `git checkout HEAD --` restored the file. Second patch attempt used the post-V2-fix `old_string` — but the restored file had `[ptg-breakup.md]` bare filename again, so `content.find(old_string)` returned -1 and the patch silently failed.

**Prevention:** After `git checkout HEAD -- path`, always re-verify the exact link text before composing `old_string`. Store the on-disk string, not a previously-in-memory string, as the anchor:
```python
content = pathlib.Path(path).read_text()
# Verify the link text you plan to target — if this fails, restore reverted to bare filename
assert "[PTG Breakup research]" in content
# Adapt old_string to match actual on-disk text
```
