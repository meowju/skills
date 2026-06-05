# Section Tail Corruption — Detection & Repair (Real Cases)

## Pattern A: Section Tail Bleed (Section Boundary Lost)

**What it looks like:**
A section's body ends normally, but content from a different section bleeds in — no `---` separator between them. The bleed-in contains:
1. A copy of the section's own verification checklist (duplicate)
2. Off-topic content (another section's subsection headers, FAQ blocks)
3. A second copy of the same checklist again

**Real case (ai-money-maker v3.05, section 四十):**
- Section 四十 ends with `→ Full content: [references/ai-china-local-market.md](references/ai-china-local-market.md)`
- Next section header is 四十一 at pos 57,862
- Gap between them: 5,097 chars — far too large for a normal section
- Inside the gap: duplicate checklist + `### 七、快速启动` subsection + duplicate FAQ block + second checklist
- Total orphaned tail: 746 chars of corruption

**Detection signal — the gap scan:**
```python
headers = [(m.start(), m.group(1), m.group(2).strip())
           for m in re.finditer(r'\n## ([一二三四五六七八九十]+)、([^\n]+)', content)]
for i in range(1, len(headers)):
    gap = headers[i][0] - headers[i-1][0]
    if gap > 3000:  # threshold lowered from 4000 — catches more cases
        print(f"LARGE GAP {gap:,} chars between {headers[i-1][1]} and {headers[i][1]}")
        gap_text = content[headers[i-1][0]:headers[i][0]]
        subs_in_gap = re.findall(r'\n## ([一二三四五六七八九十]+)、', gap_text)
        if subs_in_gap:
            print(f"  Inner ## headers in gap: {subs_in_gap}")
```

**Why it happens:**
In multi-session skills with sequential section numbers, a section added at the wrong position creates a "ghost" block between two legitimate section headers. Overwrites during patch operations can also leave orphaned content behind.

**Fix — exact boundary anchoring:**
```python
last_clean_marker = '→ Full content: [references/ai-china-local-market.md](references/ai-china-local-market.md)'
pos = content.find(last_clean_marker)
corruption_start = content.find('\n', pos + len(last_clean_marker)) + 1
next_header_pos = content.find('\n## 四十一、', pos)
new_content = content[:corruption_start] + '\n\n---\n\n' + content[next_header_pos:]
```

**Key insight:** This corruption does NOT require a `---` divider to form — a paragraph truncated mid-word followed immediately by a `## ` header creates the embedded section. Always anchor patch `old_string` to include the full paragraph text before the section boundary, not just the truncated tail.

---

## Pattern B: Intra-Subsection Sentence Duplication (Structure Intact)

**What it looks like:**
A subsection's tail ends with a sentence that repeats twice consecutively — no `---` divider, no section boundary loss, section structure remains intact but content is corrupted with an intra-subsection duplication. Different from Pattern A where section N+1 content bleeds into section N.

**Real case (wealth-mindset v1.144.0, "Unstoppable Execution" → Jocko Willink subsection):**
- Subsection ends with: `The person who executes reliably for 30 years beats the brilliant person who starts and stops。\n`
- Immediately followed by (duplicate): `beats the brilliant person who starts and stops。\n\n`
- Second occurrence is a raw duplicate of the final sentence; section boundary (next `###` header) remains intact
- Size: 49 chars of silent garbage

**Detection signal:** Repeated sentence pattern at subsection tail — use `rfind()` on the duplicated sentence fragment:
```python
dup_line = "beats the brilliant person who starts and stops。\n"
if content.count(dup_line) > 1:
    dup_pos = content.rfind(dup_line)  # last occurrence is the duplicate
    print(f"Duplicate at pos {dup_pos}: {repr(content[dup_pos-30:dup_pos+40])}")
```

**More general detection — repeated line anywhere in subsection tail:**
```python
# Scan for any line that appears consecutively twice at subsection end
import re
# Find subsection tails
subsections = [(m.start(), m.group(0)) for m in re.finditer(r'\n### ([^\n]+)', content)]
for sub_pos, sub_title in subsections:
    # Get 200 chars before next subsection or section
    next_sub = content.find('\n### ', sub_pos + 10)
    next_sec = content.find('\n## ', sub_pos)
    end = min(s for s in [next_sub, next_sec] if s > sub_pos)
    tail = content[sub_pos:end]
    # Look for duplicate lines
    lines = tail.split('\n')
    for i in range(len(lines) - 1):
        if lines[i] and lines[i] == lines[i+1]:
            print(f"Duplicate line in '{sub_title[:30]}': {repr(lines[i][:50])}")
```

**Fix:**
```python
dup_line = "beats the brilliant person who starts and stops。\n"
dup_pos = content.rfind(dup_line)
fixed = content[:dup_pos] + "\n" + content[dup_pos + len(dup_line):]
```

**Key distinction from Pattern A:**
- Pattern A: section boundary is lost — content from section N+1 bleeds into section N (ghost sections, displaced headers, section number swaps)
- Pattern B: subsection tail has a repeated sentence — section structure intact, only content is duplicated

**Why it's invisible:** The duplicate is at the end of a subsection, not at a section boundary. It reads as a complete (if repetitive) ending. Only a character-level scan of subsection tails catches it. The subsection still ends at the correct position; the content itself is just garbage.

---

## Related: Section Disorder (Section Swap)

**Pattern:** A later-numbered section appears earlier in the file than an earlier-numbered section.

**Detection:**
```python
chinese_order = {'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,'十':10,
                 '十一':11,'十二':12,'十三':13,'十四':14,'十五':15,'十六':16,'十七':17,
                 '十八':18,'十九':19,'二十':20}
headers = [(m.start(), m.group(1), m.group(2).strip())
           for m in re.finditer(r'\n## ([一二三四五六七八九十]+)、([^\n]+)', content)]
positions = [h[0] for h in headers]
numbers = [h[1] for h in headers]
for i in range(len(headers)-1):
    curr_val = chinese_order.get(numbers[i], 0)
    next_val = chinese_order.get(numbers[i+1], 0)
    if next_val < curr_val:
        print(f"DISORDER: {numbers[i]} (pos {positions[i]:,}) → {numbers[i+1]} (pos {positions[i+1]:,})")
```

**Real case (ai-money-maker v3.05):** 六十四 (pos 60,400) sits between 四十一 and 四十二 — the Chinese numerals go backward (六十四 = 64 > 四十一 = 41). This is a section swap, not a simple misplacement.

**Fix:** Extract both section blocks, reassemble in correct file order, write once atomically.

## Reference

- Original detection (Pattern A): ai-money-maker Run 24 (v3.05.1→3.05.2)
- Pattern A file: `/opt/data/skills/productivity/ai-money-maker/SKILL.md`
- Corrupted section: 四十 (position 57,116 after reference link anchor)
- Gap that flagged it: 5,097 chars (normal section pairs average <2,000 chars)
- Pattern B detection: wealth-mindset v1.144.0 (this session)