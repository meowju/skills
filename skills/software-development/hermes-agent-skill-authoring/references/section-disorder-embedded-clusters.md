# Section Disorder: Embedded Cluster Detection & Repair

> Real case: ai-money-maker v3.1.4. Section 七十二、` was found at byte position 60,717 — between sections 三十六 and 四十 — instead of after 七十一. The gap between 五十九 (pos 60,661) and 三十五 (pos 63,874) was 3,213 chars. Chinese numerals jumped backward (五十九 → 三十五), immediately flagging the swap. The embedded block also contained displaced sections 六十二 and 六十一 swapped in position.

## The Core Problem

In skills with Chinese numeral section headers (`## 一、` through `## 七十二、`), sections can appear in the file at the **wrong byte position** while the human reader doesn't notice — because we read Chinese numbers in logical order, not file-order. This breaks any patching that relies on sequential position assumptions.

**Why it happens:** Multi-session editing with sequential `patch` calls on large files. Patch N inserts content at a byte position; Patch N+1 computes its position from the original file, not the post-patch file. After enough sessions, sections drift from their intended positions.

## Detection: The Gap Scan (Primary Signal)

The gap between consecutive section headers reveals disorder before any number-comparison scan. When a gap between section N and section N+1 is **>3× the average section size**, it flags a displaced section.

```python
import re, pathlib
content = pathlib.Path("SKILL.md").read_text()
headers = [(m.start(), m.group(1)) for m in re.finditer(r'\n## ([^\\n]+)、', content)]

avg_size = sum(headers[i+1][0] - headers[i][0] for i in range(len(headers)-1)) / len(headers)
print(f"Average section size: {avg_size:.0f} chars")

for i in range(len(headers)-1):
    gap = headers[i+1][0] - headers[i][0]
    if gap > avg_size * 3:
        print(f"⚠️  LARGE GAP between '{headers[i][1]}' (pos {headers[i][0]}) "
              f"and '{headers[i+1][1]}' (pos {headers[i+1][0]}): {gap} chars "
              f"(avg={avg_size:.0f})")
```

## Detection: Number-Order Scan (Confirms the Swap)

```python
chinese_to_int = {
    '一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,'十':10,
    '十一':11,'十二':12,'十三':13,'十四':14,'十五':15,'十六':16,'十七':17,'十八':18,
    '十九':19,'二十':20,'二十一':21,'二十二':22,'二十三':23,'二十四':24,'二十五':25,
    '二十六':26,'二十七':27,'二十八':28,'二十九':29,'三十':30,'三十一':31,'三十二':32,
    '三十三':33,'三十四':34,'三十五':35,'三十六':36,'三十七':37,'三十八':38,'三十九':39,
    '四十':40,'四十一':41,'四十二':42,'四十三':43,'四十四':44,'四十五':45,'四十六':46,
    '四十七':47,'四十八':48,'四十九':49,'五十':50,'五十一':51,'五十二':52,'五十三':53,
    '五十四':54,'五十五':55,'五十六':56,'五十七':57,'五十八':58,'五十九':59,'六十':60,
    '六十一':61,'六十二':62,'六十三':63,'六十四':64,'六十五':65,'六十六':66,'六十七':67,
    '六十八':68,'六十九':69,'七十':70,'七十一':71,'七十二':72
}

# Check file-position order vs logical number order
for i in range(len(headers)-1):
    curr_num = chinese_to_int.get(headers[i][1].strip())
    next_num = chinese_to_int.get(headers[i+1][1].strip())
    if curr_num and next_num and curr_num > next_num:
        print(f"⚠️  REVERSAL: '{headers[i][1]}' (pos {headers[i][0]}) "
              f"→ '{headers[i+1][1]}' (pos {headers[i+1][0]}) — "
              f"should be {curr_num} → {next_num}")
```

## The Embedded Cluster Pattern

A "duplicate" section number found by the header scan is often **not a true duplicate** — it's an embedded cluster. The block between two consecutive section headers may contain multiple top-level `## N、` headers that have no other home in the file.

**Critical pre-removal check** (before deleting any suspected "duplicate" block):
```python
block_start = headers[i][0]
block_end = headers[i+1][0]
block_text = content[block_start:block_end]

inner_toplevel = re.findall(r'\n## ([^\\n]+)、', block_text)
if inner_toplevel:
    print(f"⚠️  BLOCK at pos {block_start} is an EMBEDDED CLUSTER — NOT a duplicate.")
    print(f"These sections exist nowhere else: {inner_toplevel}")
    print(f"Do NOT remove this block. Extract the inner ## headers instead.")
```

**Real case:** ai-money-maker had `### 五十九、` inside a block between `## 三十三、` and `## 三十五、`. The block also contained `## 二十六、` through `## 三十五、` — 10 legitimate top-level sections with no other location. A session tried to "remove the duplicate 五十九" and deleted 10 real sections + ~18k chars. Recovery: `git checkout`.

## Fix: Extract + Reorder (Never Delete the Block)

When an embedded cluster is confirmed:

1. **Extract** each inner `## N、` block to its own top-level section at the correct chronological position
2. **Extract** any inner `### N、` subsections as their own `## N、` top-level sections  
3. **Only then** remove the now-empty shell block
4. **Write once atomically** — never sequential patches for reorder operations

```python
import pathlib, re

path = "SKILL.md"
content = pathlib.Path(path).read_text()

# Step 1: Map all section positions
headers = [(m.start(), m.group(1)) for m in re.finditer(r'\n## ([^\\n]+)、', content)]
chinese_to_int = { ... }  # as above

# Step 2: Find disordered sections
for i in range(len(headers)-1):
    curr_num = chinese_to_int.get(headers[i][1].strip())
    next_num = chinese_to_int.get(headers[i+1][1].strip())
    if curr_num and next_num and curr_num > next_num:
        print(f"Swap detected: {headers[i][1]} (pos {headers[i][0]}) should be after {next_num}")

# Step 3: Extract both blocks, swap their file positions
# (Extract by character position, reassemble in correct order)
# Write once atomically
```

## Six-Step Structural Survey (Mandatory Before Any Edit on >80k File)

```python
# Step 1: File size + version
size = len(content)
print(f"Size: {size:,} chars, headroom: {100_000-size:,}")

# Step 2: All section positions
headers = [(m.start(), m.group(1)) for m in re.finditer(r'\n## ([^\\n]+)、', content)]
print(f"Sections: {len(headers)}")

# Step 3: Duplicate check
from collections import Counter
nums = [h[1] for h in headers]
dupes = {k: v for k, v in Counter(nums).items() if v > 1}
print(f"Duplicates: {dupes if dupes else 'NONE'}")

# Step 4: Average section size + large gap scan
avg = sum(headers[i+1][0]-headers[i][0] for i in range(len(headers)-1)) / len(headers)
for i in range(len(headers)-1):
    gap = headers[i+1][0]-headers[i][0]
    if gap > avg * 3:
        print(f"⚠️ GAP: '{headers[i][1]}'→'{headers[i+1][1]}': {gap} chars")

# Step 5: Number-order scan
for i in range(len(headers)-1):
    c = chinese_to_int.get(headers[i][1].strip())
    n = chinese_to_int.get(headers[i+1][1].strip())
    if c and n and c > n:
        print(f"⚠️ REVERSAL: {headers[i][1]} (pos {headers[i][0]}) before {headers[i+1][1]}")

# Step 6: Subsection embedding scan
subsections = [(m.start(), m.group(1)) for m in re.finditer(r'\n### ([^\\n]+)、', content)]
for sub_pos, sub_num in subsections:
    parent = next((f"## {num}" for sec_pos, num in headers if sec_pos < sub_pos), "NONE")
    print(f"  ### {sub_num}、 inside: {parent}")
```

## Variant: Single Section Displacement at EOF (Not an Embedded Cluster)

The embedded cluster pattern (multiple sections sandwiched between two headers) is documented above. A distinct variant is **single section displacement** — one section that lands at EOF instead of at its correct chronological position, while all other sections remain in sequential order.

**Detection:** The number-order reversal scan (`curr_num > next_num`) does **not** catch this case, because the displaced section's number is *larger* than the sections that precede it in file order — not smaller. In ai-money-maker v3.46: section 八十 (pos 83,455) → 七十九 (pos 95,048 at EOF) → 八十一 (pos 86,254). The number 79 is *greater* than 80, so no reversal is flagged. The tell is the EOF placement combined with a large gap between the preceding section and its logical successor.

**Detection code (beyond reversal scan):**
```python
# Single-section displacement: section N appears after sections > N
headers = [(m.start(), m.group(1)) for m in re.finditer(r'\n## ([^\n]+)、', content)]
nums_ordered = [(pos, chinese_to_int[h.strip()]) for pos, h in headers if h.strip() in chinese_to_int]

for i, (pos, num) in enumerate(nums_ordered):
    later_smaller = [(p, n) for p, n in nums_ordered[i+1:] if n < num]
    if later_smaller:
        print(f"Single displacement: ## {num}、 at pos {pos} after smaller numbers: {[n for _, n in later_smaller]}")
```

**Fix (zero-byte-delta):** Extract all sections from the disordered region to EOF, compute their exact byte ranges, reassemble in correct chronological order. Write once atomically. In ai-money-maker v3.46: extracted 80→79→81→82→83 as five pieces, reassembled as 80→79→81→82→83. File size unchanged (97,583 chars before and after), only byte positions changed.

**Rule:** Reordering is always zero-byte-delta — it changes positions, not content length. Never skip reordering because "headroom is tight." Reordering never worsens headroom.

## Headroom Safety

If the file is **>85k chars** and the fix requires reordering (which preserves byte count), verify headroom after reordering is complete. If the file is **<85k**, reordering is always safe — it changes positions, not content length.
