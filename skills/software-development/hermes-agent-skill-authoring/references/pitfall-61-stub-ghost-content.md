# Pitfall 61: Stub Section with Ghost Content — Real Body Trapped in Wrong Section

## Pattern

A section header exists in the file but the body is only a reference link (~100-200 chars). The substantive content that should belong to that section is actually trapped inside a different section — often a Pitfalls or Framework section that received stray copy-pasted content. The donor section may also have broken or truncated text where the bleed-in occurred.

**Stub section example:**
```
## Framework: Values Clarification (ACT-Inspired)

→ Full content: [Values Clarification](references/values-clarification.md)
```
Body: ~127 chars. The section "exists" but has no actual content.

**Ghost content hiding in donor section:**
```
13. **Natsukashii misread as backward-looking.** *Natsukashii*
Framework: Values Clarification (ACT-Inspired)

→ Full content: [Values Clarification](references/values-clarification.md)

ACT distinguishes values (qualities of engagement you keep moving toward...) [TRUNCATED MID-SENTENCE]
```
The ACT content starts after `*Natsukashii*` with no paragraph break — the text that should be in the Values Clarification section bleeds directly into the pitfall.

---

## Real Case

**purpose-finder v4.80.0 → v4.81.0 (Run 10):**

The `## Framework: Values Clarification (ACT-Inspired)` section was a 127-char stub. Its 519-char ACT values-vs-goals content lived inside Pitfalls #13 (`## Common Pitfalls`), merged mid-sentence with the Natsukashii pitfall text. The pitfall entry started with `*Natsukashii*Framework: Values Clarification...` — no newline, no paragraph break, just back-to-back section titles. The pitfall text was also truncated mid-word.

**Four separate corruptions in one file:**
1. Values Clarification section body: ghost content missing (stub only)
2. Pitfalls #13: ghost content embedded + broken text
3. Duplicate reference link: Values Clarification link appeared twice (in stub + in pitfall)
4. Mid-word truncation: pitfall text cut off at `suffer` in `suffering is the work`

---

## Detection — Stub Section Scan

```python
import re, pathlib
content = pathlib.Path(skill_path).read_text()

sections = [(m.start(), m.group(1), m.group(2).strip())
           for m in re.finditer(r'\n## ([一二三四五六七八九十百千万VI]+)、(.+)', content)]

for i, (pos, num, title) in enumerate(sections):
    end = sections[i+1][0] if i+1 < len(sections) else len(content)
    body_size = end - pos - len(f"## {num}、{title}") - 1
    if body_size < 200:
        print(f"STUB: ## {num}、{title} — body only {body_size} chars")
```

**Additional check — pitfall body scan for ghost section titles:**
```python
pitfalls_pos = content.find("## Common Pitfalls")
if pitfalls_pos >= 0:
    pitfalls_end = content.find("\n## ", pitfalls_pos + 10)
    if pitfalls_end < 0:
        pitfalls_end = len(content)
    pitfalls_body = content[pitfalls_pos:pitfalls_end]

    # Look for section-title patterns that should not be in Pitfalls
    ghost_titles = re.findall(r'\n## ([一二三四五六七八九十]+[、、][^\n]{5,50})', pitfalls_body)
    for t in ghost_titles:
        print(f"GHOST TITLE in Pitfalls: {t}")
```

---

## Fix — Atomic Four-Step

When ghost content is detected in Pitfalls and the stub section exists:

```python
import pathlib

path = "/opt/data/skills/productivity/purpose-finder/SKILL.md"
content = pathlib.Path(path).read_text()

# Step 1: Extract ACT content from Pitfalls #13 donor
# The ghost block starts after the pitfall number/title and ends at next --- divider
donor_start = content.find("13. **Natsukashii")
donor_end = content.find("\n---\n", donor_start)
donor_block = content[donor_start:donor_end]

# Find where ACT content begins (after the duplicate header line)
act_start = donor_block.find("ACT distinguishes")
act_end = donor_block.find("\n", act_start + 300)  # cut at paragraph end (~519 chars)
ghost_act = donor_block[act_start:act_end]

# Step 2: Fix the pitfall text — replace the ghost block with clean pitfall text
old_pitfall13 = donor_block
new_pitfall13 = ("13. **Natsukashii misread as backward-looking.** *Natsukashii* is reliable "
                 "not because the past is the destination, but because what you cling to reveals "
                 "what genuinely matters. The insight is about *what you would choose again*, "
                 "not about returning to what was.\n\n"
                 "> **Values Clarification:** ACT distinguishes values (ongoing qualities of "
                 "engagement) from goals (achievable outcomes). See: "
                 "[Values Clarification](references/values-clarification.md)\n")

# Step 3: Inject ghost content into stub section
stub_marker = "## Framework: Values Clarification (ACT-Inspired)\n\n→ Full content: [Values Clarification](references/values-clarification.md)"
stub_replacement = stub_marker + "\n\n" + ghost_act

# Step 4: Compute all deltas, write once
new_content = content.replace(old_pitfall13, new_pitfall13, 1)
new_content = new_content.replace(stub_marker, stub_replacement, 1)

pathlib.Path(path).write_text(new_content)
print(f"New size: {len(new_content):,} — Headroom: {100_000 - len(new_content):,}")
```

**Net delta example:** −333 (pitfall cleanup) +519 (stub populated) −243 net, ~256 headroom on a file that started at 99,987.

---

## Prevention Checklist

After any session that touches reference links:
- [ ] Verify every section has body content > 200 chars (not just a reference link line)
- [ ] Scan Pitfalls section for ghost section titles (`## ` patterns that shouldn't be there)
- [ ] Confirm no section starts mid-sentence with a different section's title
- [ ] Run orphan audit — a reference file referenced only from a Pitfall (not its home section) may indicate ghost content