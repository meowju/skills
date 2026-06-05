# Boundary Corruption Detection — Correct Method

## The Regex Is Wrong

The pattern `\s*\n##` used in older boundary scans:
- `\s` matches `[ \t\f\r\v]` but NOT `\n`
- At `)\n\n##`, `\s*` matches zero chars; literal `\n` matches first `\n` → passes
- At `)\n##` (corrupt), `\s*` matches zero chars; literal `\n` matches first `\n` → also passes
- **Result:** cannot distinguish correct from corrupt

## The Correct String-Operation Method

```python
# CORRECT detection via string operations
for m in re.finditer(r'→ Full content:[^\n]+\)', content):
    link_end = m.end()
    next_nl = content.find('\n', link_end)
    next_header = content.find('\n## ', link_end)
    between = content[next_nl:next_header]
    if not between.startswith('\n\n'):
        corrupted.append(f"→ Full content: link at pos {m.start()} missing blank line before ##")
```

The key check: `not between.startswith('\n\n')` — any single newline or missing blank line is corruption.

## False Positive Case (purpose-finder)

The detection script flagged 13 corruption positions. Manual trace revealed:

1. The script's `m.end()` landed *inside* the `.md)` string (e.g., at the `m` of `.md)`)
2. The look-ahead window captured 5 chars of `references/` text instead of newlines
3. Every flagged position was a false positive

**Real case:** purpose-finder v4.77 — the string-ops method (correctly implemented) found all 11 reference links had proper `\n\n` before section headers. The file was structurally clean. The regex approach would have "found" all 11 as false positives and triggered 11 unnecessary patches, each potentially introducing corruption. This is why the regex method was abandoned and the string-operation method codified in this reference.

**Actual state:** Only 1 real corruption — `failure-purpose.md` link before `## Framework: Founder Mode`.

## Subsection Header False Positive

When the link immediately precedes a `###` subsection (not `##` top-level), the look-ahead for `\n## ` finds the `\n` inside `###` instead of a top-level section break. The `between` window includes `## ` from the subsection header, producing another class of false positive.

**Fix:** Scan for `\n##  ` (two trailing spaces) to match only top-level headers, not `### ` subsection markers.

## False Positive Class 3: Decorative `---` Dividers

The string-operation scan uses `content.find('\n## ', link_end)` to find the next top-level header. But Chinese-language skills often use decorative `---` dividers between sections, and these dividers frequently contain inline section labels like `## 二十六、` as visual separators. The bare `## ` (no space requirement) matches the decorative `## N、` embedded inside `---` blocks, giving a position *before* the real section header.

Real case (ai-money-maker Run 64): 6 positions flagged as boundary corruption — all false positives. Each had a `---` divider with a Chinese section number between the reference link and the actual top-level header. The look-ahead found `##` inside the divider, not the real section boundary.

Fix: use `\n##  ` (two trailing spaces) for the look-ahead, or filter out positions that fall inside `---...---` blocks:

## False Positive Class 4: `###` Subsection Immediately After Link (breakup-recovery v4.69 Real Case)

When a `→ Full content:` link line is followed by a blank line and then a `###` subsection header (valid structure), the look-ahead for `\n## ` matches the `##` inside `\n### ` — the two characters exist in `###`, not `## `. This makes `between` start with `## ` (not `\n\n`), and the corruption check fires falsely. All 14 positions flagged in breakup-recovery v4.69 were this false positive.

**Fix:** Use two trailing spaces to match only top-level section headers:
```python
for m in re.finditer(r'→ Full content:[^\n]+\)', content):
    link_end = m.end()
    next_nl = content.find('\n', link_end)
    next_toplevel = content.find('\n##  ', link_end)  # two trailing spaces
    between = content[next_nl:next_toplevel]
    if not between.startswith('\n\n'):
        # Check: is the next header actually a ### subsection?
        check_pos = next_nl
        while check_pos < len(content) and content[check_pos] in ' \t':
            check_pos += 1
        if content[check_pos:check_pos+4] == '\n### ':
            continue  # Valid: link → blank → subsection, not corruption
        corrupted.append(f"Real boundary issue at pos {m.start()}")
```
Real case (this session): purpose-finder v4.77 produced 11 false positives from the regex approach. String-operation verification confirmed all 11 links had proper `\n\n` before section headers — the file was structurally clean. A naive agent acting on the regex output would have corrupted 11 correct boundaries.

**Lesson:** The `\s*\n##` regex always produces false positives at reference links. String operations are the only reliable method.

## Revised Code Pattern (All False Positive Classes Resolved)

```python
for m in re.finditer(r'→ Full content:[^\n]+\)', content):
    link_end = m.end()
    next_nl = content.find('\n', link_end)
    next_toplevel = content.find('\n##  ', link_end)  # two trailing spaces
    if next_toplevel == -1:
        next_toplevel = len(content)
    between = content[next_nl:next_toplevel]
    if not between.startswith('\n\n'):
        # Check: is the next header actually a ### subsection?
        check_pos = next_nl + 1
        while check_pos < len(content) and content[check_pos] in ' \t':
            check_pos += 1
        if content[check_pos:check_pos+4] == '\n### ':
            continue  # Valid: link → blank → subsection, not corruption
        # Is it inside a --- divider block?
        prev_dash = content.rfind('\n---', 0, next_nl)
        next_dash = content.find('\n---', next_nl)
        if prev_dash != -1 and next_dash != -1 and prev_dash < next_nl < next_dash:
            continue  # Inside a ---...--- block
        corrupted.append(f"Real boundary issue at pos {m.start()}")
```

This version handles: bare `\n\n## ` (correct), `### ` subsections (valid), decorative `---` dividers (false positive class 3), and missing blank lines (real corruption).