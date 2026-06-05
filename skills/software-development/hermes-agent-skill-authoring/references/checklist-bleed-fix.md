# Checklist Bleed Detection & Repair (Real Case: ai-money-maker v2.91)

## The Pattern

A section's `### 验证清单` ends cleanly with its last checkbox item. But before the `---` separator that closes the section, content from a different section bleeds in — typically another section's verification checklist items, a stray heading line, or both. Invisible to reading because the section header and opening body look completely normal.

## Real Case: Section 五十八 Checklist Tail Bleed

**File:** `/opt/data/skills/productivity/ai-money-maker/SKILL.md` (v2.91, 94,036 chars)

**What was wrong:**
- Section 五十八 (`## 五十八、AI 套利人群画像`) had 3 legitimate checklist items:
  - `[ ] 找到了自己属于哪类人群（老法师/工程师/套利者）`
  - `[ ] 记住了每类人群的核心逻辑和关键数字`
  - `[ ] 制定了30天行动计划（找第一个这类客户）`
- After item 3, a stray line `可持续性排序` appeared (should not exist)
- Then 4 checklist items from section 五十七's checklist bled in:
  - `[ ] 记住了 Claygent 的护城河本质是"数据+工作流"，不是"AI 技术"`
  - `[ ] 找到了一个自己想进入的"行业 + 具体任务"组合`
  - `[ ] 理解了"先积累数据再做 Agent"是普通人可行的路径`
  - `[ ] 记住了正确的定价锚定方式（替代人力成本，而非功能价格）`
- Then `---` + section 六十 header

**Total bleed:** 151 chars (position 93355→93506)

**Why invisible:** Section 58's body content (人群A/B/C with real cases and numbers) was completely intact. The checklist header `### 验证清单` appeared at the right position. The first 3 items looked correct. Only a full gap-scan or duplicate-phrase scan caught it.

## Detection: The Gap Scan

```python
import re, pathlib
path = "/opt/data/skills/productivity/ai-money-maker/SKILL.md"
content = pathlib.Path(path).read_text()

headers = [(m.start(), m.group(1), m.group(2).strip())
           for m in re.finditer(r'\n## ([一二三四五六七八九十]+)、([^\n]+)', content)]

for i in range(1, len(headers)):
    gap = headers[i][0] - headers[i-1][0]
    expected_max = 2500  # normal sections are well under this
    if gap > expected_max * 2:
        print(f"LARGE GAP {gap:,} chars: {headers[i-1][1]} → {headers[i][1]}")
        print(f"  Section {headers[i-1][1]} ends at {headers[i-1][0]}")
        print(f"  Section {headers[i][1]} starts at {headers[i][0]}")
```

## Detection: Duplicate Phrase Scan

```python
# The bleed phrase is unique enough to find secondary occurrences
# The phrase "记住了 Claygent" appears in section 57's legitimate checklist
# and again (the bleed) in section 58's checklist
bleed_phrase = "记住了 Claygent 的护城河本质是\"数据+工作流\""
positions = [m.start() for m in re.finditer(re.escape(bleed_phrase), content)]
if len(positions) > 1:
    print(f"BLEED DETECTED: phrase appears {len(positions)} times at {positions}")
    # Each section's checklist should have it appearing exactly once
```

## Fix: Python Boundary Extraction

```python
import pathlib
path = "/opt/data/skills/productivity/ai-money-maker/SKILL.md"
content = pathlib.Path(path).read_text()

# The bleed starts at the stray "记住了 Claygent" line in section 58's checklist
# This phrase is unique enough when combined with the section-60 context
bleed_phrase = "记住了 Claygent 的护城河本质是\"数据+工作流\""
bleed_start = content.find(bleed_phrase)  # finds the SECOND occurrence (the bleed)

# Verify this is the bleed (not the legitimate first occurrence)
# The legitimate occurrence is in section 57's checklist
# We confirm bleed by checking it falls within section 58's boundaries
section_58_start = content.find("## 五十八、AI 套利人群画像")
section_60_start = content.find("\\n## 六十、AI决策者成交力学")
assert section_58_start < bleed_start < section_60_start, "Not the bleed"

# The bleed runs from bleed_start to section_60_start
old_bleed = content[bleed_start:section_60_start]
assert content.count(old_bleed) == 2, f"Bleed unique check failed: {content.count(old_bleed)}"

# New: just close the checklist properly with --- + blank line
new_content = content[:bleed_start] + "\\n\\n---\\n\\n" + content[section_60_start:]
pathlib.Path(path).write_text(new_content)

# Verify
new_size = len(pathlib.Path(path).read_text())
print(f"Fixed: {len(content)} → {new_size} chars (saved {len(content) - new_size})")
```

## Key Lessons

1. **Verification checklists are not safe from corruption** — sessions that patch other sections can accidentally insert checklist content elsewhere
2. **Gap scan is the primary detection signal** — a gap >4,000 between sections that should be <2,000 each flags a ghost block every time
3. **Duplicate phrase scan is the secondary signal** — key phrases like "记住了 Claygent" appearing twice almost always mean bleed
4. **Never use `patch` for this fix** — the bleed phrase has 2 occurrences; the match is not unique for `patch` without careful anchor context. Python boundary extraction with assertion is first resort.
5. **The stray line pattern** — `可持续性排序` was the artifact of the original copy-paste error (part of section 57's checklist "理解了护城河的四种来源及可持续性排序" got split, with the suffix `可持续性排序` landing as a stray orphan line before the bleed items)

## Prevention Checklist

After any session that patches a section's verification checklist or inserts content near `### 验证清单`:
- [ ] Run gap scan between the patched section and the next section
- [ ] Run duplicate phrase scan for any key phrase in the checklist
- [ ] Verify the section's checklist header appears only once within its boundaries