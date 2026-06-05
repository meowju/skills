# Skill Authoring Pitfalls 60–61

> Sourced from hermes-agent-skill-authoring/SKILL.md — Run 142 additions.

---

## 60. Extract Exact Section Boundaries via Positional Slicing — Never Reconstruct from Memory

When replacing a section in a large multi-section skill (50+ sections), always extract the exact current content via positional slicing, not by manually composing the `old_string` from memory:

```python
# SAFE: extract exact section boundaries from the actual file
sec_start = content.find('## 三十八、AI Agent 商业化')
sec_end = content.find('\n## 三十九、', sec_start)  # find the NEXT section header
old_sec = content[sec_start:sec_end]
assert content.count(old_sec) == 1, "Not unique!"
# Replace using the exact old section boundaries
new_sec = build_new_section()
new_content = content[:sec_start] + new_sec + content[sec_end:]
```

**Why this matters:** A manually composed `old_string` will not exactly match the file if the section has been modified by prior sessions. Any character difference (a different space, Chinese punctuation variant, extra newline) causes the replacement to fail or land in the wrong section. Positional slicing of the **actual file** guarantees the anchor matches exactly.

**Real case (ai-money-maker Run 142):** Section 三十八 was 987 chars. Positional slicing via `content.find('## 三十八、')` + `content.find('\n## 三十九、', sec_start)` extracted the exact 987-char block, confirmed unique by `content.count(old_sec) == 1`, and the replacement landed correctly in one pass.

**Rule for multi-section skills:** After reading a large file (>80k chars, 40+ sections), always use positional slicing for any replacement targeting a specific section. Never reconstruct a section from memory or prior context — always read the exact boundaries from the file itself.

---

## 61. `patch` Reports "Found 3 Matches" for Unique Content — Sibling Reference Files Are the Culprit

When `patch` reports "Found 3 matches" (or any N>1) for a string that is visually unique in SKILL.md (confirmed by Python `content.count() == 1`), the `patch` tool is matching the **same content** from one or more `references/` files that are linked via `→ Full content:` references. SKILL.md body text appears verbatim inside the linked reference files, and `patch` searches across all matched files simultaneously.

**Real case (ai-money-maker Run 142):** The block starting with "## 57. Execution Mandate..." appeared 3 times — once in SKILL.md body, and twice in two `→ Full content:` reference files (`references/patch-mismatch-pitfalls.md` and `references/atomic-multi-subsection-insert.md`) that contain the same pitfall text. `patch` reported "Found 3 matches" even though the string is unique in SKILL.md.

**Diagnosis:** Run `python -c "import pathlib; c=pathlib.Path('SKILL.md').read_text(); print(c.count('UNIQUE_ANCHOR'))"` to confirm the string is actually unique in SKILL.md. If count==1 but `patch` reports N>1, the other matches are in linked reference files.

**Resolution:** Two options:
1. Use Python `pathlib` string replacement directly — the Python count already confirmed uniqueness within SKILL.md
2. Add more surrounding context to `old_string` to differentiate the SKILL.md instance from the reference-file instances (e.g., include the adjacent section header that only exists in SKILL.md)

**Prevention:** When adding numbered pitfalls to `hermes-agent-skill-authoring`, add them to SKILL.md first, then separately update reference files. Do not copy-paste the same numbered section into both SKILL.md and a reference file — that creates the duplication that triggers this pitfall. Reference files should reference SKILL.md content by pointer, not duplicate it verbatim.

---