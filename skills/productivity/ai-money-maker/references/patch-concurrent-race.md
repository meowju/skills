# 并发多智能体 Skill 文件编辑：竞态条件与原子写入

> 本文件记录 ai-money-maker Run 51-52 真实并发事故的根因分析与应对方案。

---

## 事故经过

### Run 51：两个 Subagent 同时编辑同一个 Skill 文件

**背景：** ai-money-maker SKILL.md 约 98k chars，多个 cron-batch subagent 并发运行。

**发生了什么：**
1. Subagent A 读取文件（pathlib.read_text），找到插入点
2. Subagent B 也读取文件（同一时间点或极短间隔后）
3. Subagent A 构造 patch old_string 并调用 patch
4. Subagent B 的 old_string 基于其读取时的文件内容（已过时），patch 写入错误位置
5. 结果：部分 section 消失、错位、或嵌入错误父 section

**症状：** patch 工具报错 "Found N matches"（N>1），或 section 消失，或大小异常。

**真实数据：**
- 文件从 ~98k chars 开始
- patch 后大小异常（过大或过小）
- 部分 section 重复或丢失
- 最终恢复方式：`git checkout` 恢复原始内容

---

## 根因：Read-Then-Write 竞态

```
Time    Subagent A              Subagent B
──────────────────────────────────────────
T1      read() file v1         
T2                             read() file v1  
T3      compute patch          
T4      patch(v1+delta)         
T5                             compute patch (using v1)
T6                             patch(v1+delta_B) 
        ↑ B's old_string 指向 v1，文件已变成 v1+delta_A
```

patch 工具不做 re-read，直接用 old_string 匹配。匹配时文件可能已被 A 修改。

---

## 缓解方案（按可靠性排序）

### 方案 1：原子写入（最可靠，推荐）

所有修改在内存中完成，一次性 write_text，不留竞态窗口。

```python
import pathlib
path = "/opt/data/skills/productivity/ai-money-maker/SKILL.md"
content = pathlib.Path(path).read_text()  # 一次性读取

# 在内存中计算所有变更
# new_content = content.replace(...) + new_section + ...

pathlib.Path(path).write_text(new_content)  # 一次性写入

# 立即验证
assert len(new_content) <= 100_000
assert "TARGET_SECTION" in new_content
```

适用场景：任何多-agent 并发场景。

---

### 方案 2：Git 锁（需要 git）

```bash
# 获取文件独占锁
git add skills/productivity/ai-money-maker/SKILL.md
# 其他 agent 尝试 add 会失败（stage 冲突）
```

**缺点：** cron job 环境中 git 可能不可用或路径不对。

---

### 方案 3：文件修改时间检测（补救机制）

在 patch 前检查 mtime：

```python
import pathlib, time
path = "/opt/data/skills/productivity/ai-money-maker/SKILL.md"
mtime_before = pathlib.Path(path).stat().st_mtime

# ... read and patch ...

mtime_after = pathlib.Path(path).stat().st_mtime
if mtime_after > mtime_before:
    print("WARNING: File was modified by another process")
    # 重新读取并验证，或放弃本次编辑
```

**缺点：** mtime 分辨率有限，高并发下可能检测不到。

---

## Run 52：二次修复时的发现

第一次并发修复后，文件中存在一个 ~5,240 char 的"孤儿岛"（orphan island）：

- 位置：sections 三十一 和 三十七 之间
- 内容：包含一个重复的 section 三十一（损坏版本）、一个格式错误的 section 三十六（缺少 `、`）
- 大小：~5,240 chars（约 5% 文件）
- 发现方式：扫描大段非 section 内容

**修复：** 原子写入整个文件，重新定位所有 section。

---

## 经验教训

1. **永远不要相信单次 patch 是安全的** 在并发环境中，至少在 patch 后立即验证大小和内容。
2. **孤儿 section 是并发写入的指纹** 并发 patch 失败后遗留的碎片。
3. **大小异常是第一报警信号** 文件大小超出预期范围立即检查。
4. **git checkout 是最后防线** 不确定时就恢复，不尝试修复已损坏的文件。

---

## 检测脚本

```python
import re, pathlib

def detect_orphan_sections(path):
    """检测非 section 内容的孤立岛"""
    content = pathlib.Path(path).read_text()
    
    # 找所有 top-level section 位置
    sections = [(m.start(), m.group(1)) for m in re.finditer(r'\n##\s+([一二三四五六七八九十零]+)[、(]', content)]
    sections.append((len(content), "EOF"))
    
    orphans = []
    for i in range(len(sections) - 1):
        gap = sections[i+1][0] - sections[i][0]
        # 正常 gap 应该很小（header + 几行），大 gap 是孤儿
        if gap > 5000:
            orphans.append((sections[i][1], sections[i+1][1], gap))
    
    return orphans

# 用法
path = "/opt/data/skills/productivity/ai-money-maker/SKILL.md"
orphans = detect_orphan_sections(path)
if orphans:
    print(f"ORPHAN ISLANDS DETECTED:")
    for before, after, size in orphans:
        print(f"  {before} -> {after}: {size} chars orphan")
else:
    print("No orphan islands")
```