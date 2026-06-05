# 结构性修复模式参考

本文档记录 ai-money-maker 多会话维护中发现的结构性损坏模式及修复方法。

## 边界损坏类型一：链接后换行不足

**症状：** `→ Full content:` markdown 链接后只有单 `\n` 就直接跟 `##` 标题，导致渲染为链接+标题合并。

**检测方法（错误）：**
```python
# 这种检测会误报
for m in re.finditer(r'→ Full content:[^\n]+\)', content):
    link_end = m.end()  # regex 匹配结束位置，不是 ) 的位置
    next_nl = content.find('\n', link_end)
    next_header = content.find('\n## ', link_end)
    between = content[next_nl:next_header]
    # 误报原因：m.end() 不一定等于 ) 位置
```

**正确检测：**
```python
import re
corrupted = []
for m in re.finditer(r'→ Full content:.*?\)\s*\n', content):
    # 找 ) 的实际位置
    link_text = m.group(0)
    paren_pos = m.start() + link_text.index(')')  # ) 的真实偏移
    after_link = content[m.end():m.end()+3]
    if not after_link.startswith('\n\n'):
        corrupted.append((m.start(), 'missing double newline'))
```

**真实案例：** ai-money-maker v3.6.1 有 5 处：22069、35225、36027、56006、69925。

**56006 特殊性：** 链接带中文括号旁注 `）` 而非 markdown `)`，需单独检测。

**修复原则：** 插入 `\n\n` 在 `)` 和 `\n##` 之间。

---

## 边界损坏类型二：链接文本路径缺失

**症状：** 链接文本写成 `[ai-venture-exit-deep.md]` 而非 `[references/ai-venture-exit-deep.md]`。

**检测：**
```python
# 找所有 → Full content: 链接的文本部分
for m in re.finditer(r'→ Full content:\s*\[([^\]]+)\]\(([^()]+\.md)\)', content):
    link_text = m.group(1)
    if not link_text.startswith('references/'):
        print(f"Missing references/ prefix at {m.start()}: {link_text}")
```

**真实案例：** 69925 位置，`[ai-venture-exit-deep.md]` 应为 `[references/ai-venture-exit-deep.md]`。

---

## 边界损坏类型三：section header 前双换行变三换行

**症状：** `)\n\n\n##` 中间多了一个 `\n`。`\n\n\n##` 比 `\n\n##` 多一字节。

**检测：**
```python
bad = re.findall(r'\)\n\n\n##', content)
print(f"Triple-newline corruptions: {len(bad)}")
```

**原因：** 修复时如果替换 `\"\\n\\n\"` 而不是保持原有换行数，会累积。

---

## Orphan Reference Audit（孤立引用检测）

```python
import pathlib, re
from collections import Counter

skill_path = "/opt/data/skills/productivity/ai-money-maker/SKILL.md"
ref_dir = pathlib.Path(skill_path).parent / "references"
content = pathlib.Path(skill_path).read_text()

existing_files = {f.name for f in ref_dir.glob("*.md")}

# 三种链接格式都要检测
full_links = re.findall(r'→ Full content:\s*\[([^\]]+)\]\(([^()]+\.md)\)', content)
related_links = re.findall(r'→ Related:\s*\[([^\]]+)\]\(([^()]+\.md)\)', content)
backtick_links = re.findall(r'`(references/[^`]+)`', content)

all_linked = {p for _, p in full_links + related_links} | set(backtick_links)
link_basenames = {p.replace('references/', '') for p in all_linked}
orphans = sorted(existing_files - link_basenames)
print(f"Orphans: {orphans}")

# 重复链接检测
dups = [(k, v) for k, v in Counter(re.findall(r'→ (?:Full content|Related):\s+[^\n]+', content)).items() if v > 1]
print(f"Duplicate link lines: {dups}")
```

**真实案例：** 29 个孤立文件未被 SKILL.md 引用（54 个参考文件总数）。

---

## Subsection 嵌入检测（24b 修复）

大型多会话技能中，`### N、` subsection 可能嵌入在错误位置。

```python
import re, pathlib
skill_path = "/opt/data/skills/productivity/ai-money-maker/SKILL.md"
content = pathlib.Path(skill_path).read_text()

sections = [(m.start(), m.group(1), m.group(2).strip()) for m in re.finditer(
    r'\n## ([一二三四五六七八九十VI]+)、(.+)', content)]
subsections = [(m.start(), m.group(1)) for m in re.finditer(
    r'\n### ([一二三四五六七八九十VI]+)、', content)]

for sub_pos, sub_num in subsections:
    # 注意：sections 是 3 元素，(pos, num, title)，不是 2 元素
    parent = next(
        (f"## {num} at pos {pos}" for pos, num, _ in sections if pos < sub_pos),
        "NONE"
    )
    print(f"### {sub_num}、 inside: {parent} at pos {sub_pos}")
```

**关键：** `for pos, num, _ in sections` 解包 3 元素，不是 2 元素。错误解包导致所有 subsection 报告 `"NONE"`。

---

## 修复优先级

1. 先做 size gate：`len(pathlib.Path(path).read_text())` + estimated_delta < 100_000
2. 再扫描边界损坏（孤立引用检测）
3. 最后做内容修改