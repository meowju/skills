# Pitfall 60: Orphan Tail — Section Closes with Broken Reference Link Text

## Pattern

A section body ends with a malformed fragment — not a valid markdown link, not a `→ Full content:` reference, just a stray suffix that looks like the tail of a broken reference link. The section appears intact to reading. The corruption is invisible without scanning for broken link patterns.

**What it looks like:**
```
 ...the rational choice is to act.

 -- extended risk frameworks, Taleb's barbell strategy, Howard Marks' second-level thinking, and the complete probability frameworks reference.
```

The ` -- extended risk frameworks...` text was meant to be a `→ Full content:` reference link line but lost its `→ Full content: [` prefix. The `---` that follows is a section divider that now appears orphaned, not attached to any link.

---

## Real Case

**wealth-mindset v1.110.5, Risk section (section 十):**

The Risk and Probability Thinking section ended with the decision framework paragraph, then a blank line, then:
```
 -- extended risk frameworks, Taleb's barbell strategy, Howard Marks' second-level thinking, and the complete probability frameworks reference.
```

This was the orphan tail of a prior failed edit — the text that was meant to be the beginning of a reference link line, but the `→ Full content: [` prefix was lost. The section *looked* complete because the decision framework paragraph above it was intact.

**Detection:** The gap scan flagged this indirectly — the section was 4,470 chars when a properly condensed version would be ~1,700 chars. But the direct detection is the orphan tail scan.

---

## Detection — Orphan Tail Scan

```python
import re, pathlib
skill_path = "/opt/data/skills/productivity/wealth-mindset/SKILL.md"
content = pathlib.Path(skill_path).read_text()

# Find all top-level sections
sections = [(m.start(), m.group(1), m.group(2).strip())
           for m in re.finditer(r'\n## ([一二三四五六七八九十百千万VI]+)、(.+)', content)]

for i, (sec_pos, sec_num, sec_title) in enumerate(sections):
    sec_end = sections[i+1][0] if i+1 < len(sections) else len(content)
    tail = content[sec_end-300:sec_end]
    
    # Pattern 1: text after --- that looks like a reference link fragment
    orphan_fragments = re.findall(r'---\s*\n([^\n]{20,})', tail)
    for frag in orphan_fragments:
        if not frag.startswith('→') and not frag.startswith('#') and ('.' in frag or 'reference' in frag.lower()):
            print(f"ORPHAN TAIL in section {sec_num}、{sec_title}: {frag[:100]}")
    
    # Pattern 2: bare "-- " dashes at section end
    bare_dashes = re.findall(r'\n\n-- ([^\n]{30,})', tail)
    for d in bare_dashes:
        if 'reference' in d.lower() or '.md' in d:
            print(f"BARE DASHES at end of section {sec_num}: -- {d[:80]}")
```

---

## Fix

1. Identify what the orphan tail was meant to be (a reference to an existing or new reference file).
2. Either create the reference file (if content exists to populate it) or treat the orphan tail as a sign the content needs condensing.
3. Replace the orphan tail + any trailing `---` with a proper `→ Full content:` link.

**wealth-mindset fix:**
1. Created `references/risk-probability-thinking.md` with the extended risk frameworks content (7,142 chars).
2. Replaced the orphan tail with `→ Full content: [risk-probability-thinking.md](references/risk-probability-thinking.md)`.
3. Also condensed the inline Risk section from 4,470 chars (with orphan tail) to 1,673 chars (clean summary + proper link).

---

## Prevention

After any edit that removes a reference link line, always verify the section still ends with a valid link or proper paragraph — not a fragment. The check:

```python
# At end of any session that touches reference links
tail_200 = content[sec_end-200:sec_end]
if '-- ' in tail_200 and '→ Full content:' not in tail_200:
    print(f"WARNING: section {sec_num} ends with orphan dash fragment")
```

When migrating a section to references/, replace the full section body (header through verification checklist) with a summary paragraph plus the new reference link — never leave a dangling orphan tail behind.
