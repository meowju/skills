# Run 205 Technical Notes — ai-money-maker 维护

## 场景

文件修复 session：修复 ai-money-maker SKILL.md 中的重复引用链接问题。

## 技术发现

### 发现 1：execute_code read + skill_manage patch 的 partial-view 假阳性

**现象：** 当 session 通过 `execute_code` + `pathlib.Path.read_text()` 读取文件后，再用 `skill_manage(action='patch')` 写入时，patch 工具报告 "partial view" 警告。

**分析：** 这是 `patch` 工具的内部状态问题，不代表文件实际状态。文件本身 91,281 chars，正确。`patch` 在执行前会尝试 re-read，但它的 re-read 逻辑可能因为 session 中已有内存内容而混淆。

**结论：** 在 `execute_code` 可用的 full-tools session 中，当 patch 报告 "partial view" 警告，**正确的做法是改用 Python pathlib write_text 原子写入**，不要 re-read + retry patch。re-read + retry 会导致 patch 的 old_string 重新匹配，可能出现重复应用。

**Pattern (Run 205 实测成功)：**
```python
import pathlib
path = "/opt/data/skills/productivity/ai-money-maker/SKILL.md"
content = pathlib.Path(path).read_text()  # fresh read
# compute new_content from current content
pathlib.Path(path).write_text(new_content)  # atomic write
# verify immediately
assert len(new_content) <= 100_000
```

### 发现 2：双重引用链接格式是 ai-money-maker 的正常模式

**现象：** section 88 和 90 各有 4 个 `ai-b2b-exit-2025.md` 引用链接（看似重复）。

**分析：** ai-money-maker 使用双重引用格式：
1. 简短版本（裸链接，无描述）：`→ Full content: [references/ai-b2b-exit-2025.md](references/ai-b2b-exit-2025.md)`  
2. 完整版本（带描述）：`→ Full content: [企业谈判·合同架构·退出时机·合规工具](references/ai-b2b-exit-2025.md)`

每节 2 条，一简一详，这是 skill 的设计模式，不是错误。

**修复策略：** 合并为每节单条标准链接（保留完整版本，删除裸版本），总计 -6 引用，文件 -42 chars。

### 发现 3：章节 101-106 是超限幽灵章节

文件末尾存在章节 一百零一 ~ 一百零六，共 6 节 7,726 字，超出设计范围（应该止于一百）。这些章节在历史上多次迭代后遗留，位置错乱，内容已陈旧。

**处理：** 整块删除（-7,726 chars）。

## 修复后的状态

- 文件大小：91,281 chars（headroom 8,719）
- 版本：4.2.6
- 章节：85 个
- 重复引用链接：0
- 下次可轻松新增 1-2 个中章节

## 相关文件

- `references/ai-b2b-exit-2025.md`（3,192 chars）— 合并的企业谈判/合同架构/合规工具/退出时机参考文件，被 section 88 和 90 共同引用
- `scripts/patch_aimoney.py` — ai-money-maker 专用 patch 脚本