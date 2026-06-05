# Pitfall 46: Anchor String Overlaps with `content[anchor_pos:]`

## The Pattern

When inserting new content before a section header using positional slicing:

```python
# WRONG: anchor includes the target header line itself
anchor_pos = content.find("\n## Framework: Career Capital")
old_string = content[anchor_pos:]  # starts with \n## Framework: Career Capital
# OR equivalently, old_string ends at/with the header line
new_content = content[:anchor_pos] + new_frankl + old_string  # DUPLICATES header
```

The anchor `old_string` and `content[anchor_pos:]` both contain the target section header → garbled output.

## Real Case

purpose-finder Run 2: attempted to insert Frankl section before `## Framework: Career Capital`.
Anchor string was:
```
→ Full content: [references/motivation-and-drive.md](references/motivation-and-drive.md)\n\n## Framework: Career Capital
```
Including the header line in the anchor. After inserting new content and appending `content[anchor_pos:]`, output was:
```
...PTG reference link
## Framework: Career Capital## Framework: The Psychology of Meaning — Viktor Frankl's Logotherapy
...Career Capital section body...
```

Two headers merged into one line.

## The Fix

```python
import pathlib

skill_path = "/opt/data/skills/productivity/purpose-finder/SKILL.md"
content = pathlib.Path(skill_path).read_text()

# Step 1: find where the target header STARTS (the \n before #)
target = "\n## Framework: Career Capital"
header_start = content.find(target)  # returns position of the \n
assert header_start >= 0, "Target header not found"

# Step 2: anchor is everything BEFORE the \n, not including it
# This means new content is inserted AT the \n, pushing the header forward
anchor_end = header_start  # the \n byte is the insertion point
# new content goes into content[:anchor_end], header line is content[anchor_end:]

new_frankl = "..."  # new section text

new_content = content[:anchor_end] + new_frankl + content[anchor_end:]
pathlib.Path(skill_path).write_text(new_content)
```

## Key Rule

The `old_string` for a positional-slicing insert must **not** include the text you're inserting before. The anchor is the byte position just before the target header's `\n`. `content[anchor_pos:]` starts at that `\n`, preserving the header intact. No duplication.

## Detection of Garbled Pattern

```python
# Scan for two consecutive ## headers with no newline between
import re
garbled = re.findall(r'## [^\n]{1,80}## [^\n]+', content)
# If any matches, garbling occurred
```

Also: `git diff` shows the target section header appearing twice — once in "context" and once in the added content block.

## Prevention

Always use a **unique anchor text** that ends **before** the `\n` of the target section header. Prefer an anchor that combines:
1. The last line of the preceding section's body (unique phrase)
2. The trailing `\n\n` before the section header

```python
# Safe anchor: unique end-of-preceding-section text + trailing \n\n
# Example: if section before Career Capital ends with "...motivation-and-drive.md)"
# anchor = content[anchor_start:header_start] where anchor_start is found from a unique phrase in the preceding paragraph
```