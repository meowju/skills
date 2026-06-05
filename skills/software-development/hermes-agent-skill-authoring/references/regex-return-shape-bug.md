# Regex `findall` vs `finditer` Return-Shape Bug

> New pitfall added in session that ran ai-money-maker Run 167.

## The Bug

`re.findall(r'\n## ([一二三四五六七八九十百千万VI]+)、(.+)', content)` returns **2-element tuples** `[(num, title), ...]` — not 3-element. The regex has two capture groups `()` and `()`, so `findall` returns a list of 2-tuples, not 3-tuples.

The code that tried to unpack 3 elements:
```python
section_headers = re.findall(r'\n## ([一二三四五六七八九十百千万VI]+)、(.+)', content)
section_nums = [n for _, n, _ in section_headers]  # ValueError: not enough values to unpack
```

The correct pattern uses `finditer` (which yields match objects, not tuples) with a regex that captures title as a third group:
```python
sections = [(m.start(), m.group(1), m.group(2).strip())
            for m in re.finditer(r'\n## ([一二三四五六七八九十百千万VI]+)、([^\\n]+)', content)]
section_nums = [num for _, num, _ in sections]  # 3-element unpack — correct
```

## Why the Error Is Silent

`ValueError: not enough values to unpack` fires on the first iteration of the list comprehension — but `execute_code` shows the full traceback, so the bug is catchable. The script fails immediately and Python prints the error, which is how the bug was caught in this session. Without `execute_code` (in a restricted session using only `skill_manage` and `memory`), the failure would be invisible — you'd get a "not enough values to unpack" error but no context about why the section scanning was broken.

## Rule

Always verify tuple shape immediately after writing a structural survey script:
```python
sections = [(m.start(), m.group(1), m.group(2).strip())
            for m in re.finditer(r'\n## ([一二三四五六七八九十百千万VI]+)、([^\\n]+)', content)]
print(f"Sample section: {sections[0]}")  # Must be 3 elements: (pos, num, title)
assert len(sections[0]) == 3, "Wrong tuple shape — regex capture groups mismatch"
```

If the regex uses `findall` with 2 capture groups, the output is 2-tuples and any 3-element unpack raises immediately. If the regex uses `finditer` but only 2 groups (missing the title group), the unpack also raises. Both cases are caught by printing the first element before using it in downstream logic.