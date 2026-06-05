# SKILL.md 补丁技术参考（满文件修复流程）

> 当 SKILL.md 达到 100,000 字符硬上限时，按以下流程修复。

---

## 修复决策树

```
SKILL.md 当前大小？
├── < 95,000 chars → 直接 patch，可多次
├── 95,000–100,000 chars → 单次 full-build，不拆分多次
└── = 100,000 chars → 必须先迁移章节到 references/，再 patch
```

---

## 预备检查（每次 patch 前）

```python
import pathlib, re

path = "/opt/data/skills/productivity/ai-money-maker/SKILL.md"
content = pathlib.Path(path).read_text()
current_size = len(content)
print(f"Current size: {current_size:,} / 100,000")
```

**触发条件：** `current_size + new_content_estimate > 98,000`（约 2k 缓冲）→ 使用 full-build，不拆分两次。

---

## Full-Build 流程（满文件）

用于：文件已 > 95k，或单次 patch 后 size > 98k。

### Step 1：确认迁移目标

```python
import re

sections = [(m.start(), m.group()) for m in re.finditer(r'\n## [一二三四五六七八九十]+、', content)]
# 找最大章节（content 最长，或最独立可迁移）
for pos, name in sections:
    next_pos = sections[sections.index((pos,name))+1][0] if sections.index((pos,name))+1 < len(sections) else len(content)
    section_len = next_pos - pos
    print(f"{name.strip()}: {section_len:,} chars")
```

### Step 2：迁移章节到 references/

将目标章节完整内容移动到 `references/<topic>.md`，SKILL.md 内替换为：

```markdown
## <章节名>

（本节已迁移至 → [references/<topic>.md](references/<topic>.md)）
```

### Step 3：计算最终大小

```python
new_size = len(new_content)
print(f"New content: {new_size:,} chars")
print(f"Final size: {current_size - migrated_section_len + new_size:,} / 100,000")
assert current_size - migrated_section_len + new_size <= 100_000
```

### Step 4：Python 验证（权威）

```python
import re

content = pathlib.Path(path).read_text()

assert content.startswith("---"), "Missing leading ---"
m = re.search(r'\n---\n', content[3:])
assert m, "Missing closing ---"
end_pos = 3 + m.start() + m.end() - 3

fm_text = content[3:end_pos-3]
assert 'name:' in fm_text and 'description:' in fm_text
assert re.search(r'version:\s*["\']?(.+?)["\']?\s*\n', fm_text), "Missing version"

desc_match = re.search(r'description:\s*["\']?(.+?)["\']?\s*\n', fm_text)
assert desc_match and len(desc_match.group(1)) <= 1024, f"Description too long: {len(desc_match.group(1))}"

assert len(content) <= 100_000, f"OVER LIMIT: {len(content):,}"
assert content[end_pos:].strip(), "Empty body"

print(f"PASS: {len(content):,} chars, frontmatter valid")
```

### Step 5：写回文件

```python
pathlib.Path(path).write_text(new_content)
```

---

## 常规 Patch（文件 < 95k 时）

```python
skill_manage(
    action='patch',
    name='ai-money-maker',
    old_string='exact old content',
    new_string='exact new content',
    mode='replace'
)
```

**必须后置：**
```python
# Python 读，权威
content = pathlib.Path(path).read_text()
assert len(content) <= 100_000
assert content.startswith("---")
```

---

## 常见陷阱

| 陷阱 | 原因 | 解法 |
|------|------|------|
| `wc -c` 显示旧大小 | WSL 文件系统缓存 | 用 Python `pathlib.read_text()` |
| `patch` 后 size 微超 | 多 patch 累积字节漂移 | 先 check，>98k 用 full-build |
| 描述超 1024 | YAML 行内 apostrophe 导致截断 | 双引号字符串 |
| `---` 在描述值里 | YAML 解释为文档分隔符 | 改写绕开或转义 |
| `git add` 无响应 | 目标目录不是 git repo | `git -C <dir> status` 先确认 |
| 并发 race（多 agent 同时 patch） | 多个 cron subagent 同时编辑同一文件 | 永远用原子写入（见下节） |

---

## 并发多 Subagent 竞态条件（Run 51-52 真实事故）

### 事故链

当多个 cron subagent 并发运行于同一大文件（>80k chars）时：

```
T1  Subagent A: read() → content_A (v1)
T2  Subagent B: read() → content_B (v1, 同一版本)
T3  Subagent A: patch() → 文件变成 v1+delta_A
T4  Subagent B: patch() → old_string 基于 v1，指向错误位置
   结果: section 消失/错位/嵌入错误父 section
```

### 症状

- patch 报错 "Found N matches"（N>1）
- 文件大小异常（过大或过小）
- section 重复或丢失
- ~5,240 char 的"孤儿岛"出现在两个 section 之间

### 修复：原子写入（所有并发场景的唯一可靠方案）

```python
import pathlib

path = "/opt/data/skills/productivity/ai-money-maker/SKILL.md"
content = pathlib.Path(path).read_text()  # 一次性读取

# 所有变更在内存中完成
new_content = content[:insert_pos] + new_section + content[insert_pos:]

pathlib.Path(path).write_text(new_content)  # 一次性写回，无竞态窗口

# 立即验证
assert len(new_content) <= 100_000
assert "TARGET_SECTION" in new_content
assert "NEXT_SECTION" in new_content
```

### 孤儿岛检测脚本

```python
import re, pathlib

def detect_orphan_sections(path):
    content = pathlib.Path(path).read_text()
    sections = [(m.start(), m.group(1)) for m in re.finditer(
        r'\n##\s+([一二三四五六七八九十零]+)[、(]', content)]
    sections.append((len(content), "EOF"))
    
    orphans = []
    for i in range(len(sections) - 1):
        gap = sections[i+1][0] - sections[i][0]
        if gap > 5000:  # 正常 gap 应 <500
            orphans.append((sections[i][1], sections[i+1][1], gap))
    
    return orphans

orphans = detect_orphan_sections(path)
if orphans:
    print(f"ORPHAN ISLANDS: {orphans}")
```

### 经验教训

1. **永远不要相信单次 patch 在并发环境中是安全的**
2. **文件大小异常 = 第一报警信号**，立即检查
3. **孤儿 section = 并发写入失败的指纹**
4. **git checkout 是最后防线**，不确定时先恢复，不尝试修复

→ 完整分析：[references/patch-concurrent-race.md](references/patch-concurrent-race.md)

---

## 场景：连续 Run 的补丁策略

连续 cron job 每个 Run 都可能添加章节。策略：

1. **每个 Run 前**：检查 size，若 > 95k，本 Run 以 full-build 迁移 + 添加代替单纯 patch
2. **迁移优先级**：找最大、最独立、已有 references/ 对应物的章节先迁
3. **版本号策略**：每个 Run 完成后 `X.YY.Z → X.YY+1.0`（迁移 Run）或 `X.YY.Z → X.YY.Z+1`（纯内容更新）

当前状态（Run 12 前）：
- size: 100,000（已满）
- 下一步：迁移 1-2 个章节到 references/ → 添加新内容

---

## 临界 headroom 扩展策略（Run 97 教训）

当 SKILL.md headroom < 2,000 chars 时，扩展薄弱章节（如 <2KB 的 stub 节）会被 size 硬上限阻挡。

**Run 97 真实案例：**
- section 十：只有 260 chars（指向 `references/ai-case-stories-deep.md` 的 stub）
- 扩展到 1,104 chars（+844 chars）后，文件：99,641 / 100,000
- headroom 仅剩 359 chars——本 Run 的扩展消耗了 94% 的剩余空间

**前置检查流程（每次扩展前必做）：**

```python
size = len(pathlib.Path(path).read_text())
headroom = 100_000 - size
print(f"Size: {size:,} / 100,000 | Headroom: {headroom:,}")

if headroom < 2000:
    print("⚠️ CRITICAL: Headroom < 2,000 — 扩展会触发 size 上限")
    print("先迁移章节到 references/，再扩展")
    # 见下方 "迁移优先级" 找最大章节
```

**临界 headroom 下的扩展策略：**

1. **扫描所有 <2KB 的薄弱章节**（正常应 2-7KB）：
   ```python
   import re
   headers = [(m.start(), m.group(1), m.group(2)) for m in re.finditer(
       r'\n## ([一二三四五六七八九十]+)、([^\n]+)', content)]
   thin = []
   for i, (pos, num, title) in enumerate(headers):
       next_pos = headers[i+1][0] if i+1 < len(headers) else len(content)
       sz = next_pos - pos
       if sz < 2000:
           thin.append((num, title.strip(), sz))
   print(f"Thin sections: {thin}")
   ```
2. **找最大可迁移章节**（给薄弱节腾空间）：优先迁移 >4KB 且有对应 `references/` 文件的章节
3. **迁移 + 扩展 = 一次 full-build**：临界 headroom 下拆分多次 patch 会累积字节漂移（见上方"字节漂移"节）

**经验教训：** section 十的前身是 references/ 的 stub（260 chars），扩展到 ~1KB 后 headroom 骤降。扩展前必须先算 headroom，<2KB 时先迁移再扩展，不能本末倒置。

---

## 参考：各章节典型大小

| 章节 | 估计大小 |
|------|---------|
| 十二、真实案例库（第一批） | ~4-5k |
| 十五、AI副业大地图（赛道分类） | ~4-5k |
| 二十二、AI + 电商实战 | ~4-5k |
| 三十六、收入报告（Run 11 新增） | ~2k |
| 其余章节 | ~1-3k 各 |

> 迁移最佳候选：内容较独立、与其他章节耦合度低的章节（如 电商 vs B2B销售，耦合度低）。

---

## 关键 Lesson（Run 15）：压缩重建的正确顺序

**错误的做法（浪费 2 次迭代才理解）：** 尝试用 `end-to-start + reverse` 的方式构建 body。逻辑复杂且极易出错——`prev_end` 在 reverse 后指向 tail（应该在前），导致 body 变成 170k 而非 65k。

**正确的做法（简单直接）：**

```python
# sections_to_compress 是 START→END 顺序
result_parts = []
prev_end = 0
for start, end, title, ref_file in sections_to_compress:
    stub = make_stub(title, ref_file)
    if prev_end < start:
        result_parts.append(body[prev_end:start])   # 中间内容
    result_parts.append(stub)                       # stub 紧跟 header
    prev_end = end                                  # 下个 section 的起点
result_parts.append(body[prev_end:])               # 最后 section 之后的 tail
new_body = "".join(result_parts)                   # 无需 reverse
```

**为什么不需要 reverse：** 每个 iteration 直接把 `body[prev_end:start]`（section 前的中间内容）追加到结果里，然后追加 stub。顺序本身就是正确的。

**关键前提：** `start` 和 `end` 必须是 section header 的绝对 body 位置（而非 content offset）。从 git show HEAD 提取，然后用 regex 找到每个 header 的实际偏移：

```python
headers = [(m.start(), m.group().strip()) for m in re.finditer(r'\n## [一二三四五六七八九十三十百千万\d]+、', body)]
pos_map = {}
for i, (pos, name) in enumerate(headers):
    pos_map[name] = (pos, headers[i+1][0] if i+1 < len(headers) else len(body))
```

**已验证的正确位置（git HEAD，body offset）：**
| 章节 | header pos | next section pos | size |
|------|-----------|-----------------|------|
| ## 十二、 | 16,092 | 21,711 | 5,619 |
| ## 十六、 | 28,860 | 35,749 | 6,889 |
| ## 二十一、 | 50,440 | 56,176 | 5,736 |
| ## 二十六、 | 71,338 | 79,975 | 8,637 |
| ## 二十九、 | 85,364 | 91,627 | 6,263 |

> 注意：不同 git 提交版本的绝对偏移可能不同。每次重建前都要从 HEAD 重新提取，不要用之前记录的值。