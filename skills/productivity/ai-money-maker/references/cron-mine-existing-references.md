# Cron-Batch 研究失败时的降级策略：Mine Existing References

> Run 31 新增。本文档记录 cron-batch 循环研究任务在 web search 失败时的标准降级路径。

---

## 触发条件

**什么时候触发降级：**
- `delegate_task` 或 `web_search` 返回 HTTP 404 或网络不可用
- Cron job 正在执行周期性研究任务（如 ai-money-maker 的垂直行业轮换）
- 没有人工可以询问下一步

**什么时候 NOT 降级：**
- 工具成功返回数据，只是内容不够详细 → 补充现有数据，不要降级
- 人类在环（非 cron）→ 可以询问用户
- Headroom > 5,000 chars 且新研究已成功获取 → 直接写入

---

## 降级策略：Mine Existing References

### Step 1: 清点现有 references/ 内容

```python
import pathlib, re
skill_path = "/opt/data/skills/productivity/ai-money-maker/SKILL.md"
ref_dir = pathlib.Path(skill_path).parent / "references"

# 按关键字搜索相关文件
target_keyword = "被动收入"  # 当前垂直
matches = []
for f in ref_dir.glob("*.md"):
    if target_keyword in f.read_text():
        matches.append(f.name)
print(f"相关文件: {matches}")
```

### Step 2: 读取最相关的文件，提取具体数字和案例

优先选择：
- 有具体收入数字的文件（`$XX,000 MRR`、`¥XX万/月`）
- 有时间线路径的文件（Month 1-3 → 阶段描述）
- 有对比表的文件（启动成本、天花板、核心壁垒）

不要选择：
- 纯方法论描述文件（没有数字）
- 已经大量引用过的文件（避免重复）

### Step 3: 从 reference 文件提取具体内容

本次 Run 31 实际使用的文件：
- `ai-case-stories-deep.md` (5,450 chars) → 提取了 AI邮件插件订阅案例（$25,000 MRR）和 AI Newsletter 订阅制案例（$18,000 MRR）
- `ai-old-masters-deep.md` (2,777 chars) → 提取了前法官合同审查AI案例（月收入12万）

### Step 4: 综合+合成，不只是复制

**错误做法：** 直接复制粘贴 reference 文件内容作为新章节
**正确做法：** 从多个 reference 文件提取相关片段，组合成一个连贯的新 subsection，加上自己的分析句

本次 Run 31 合成的分析句：
> "**核心：不是发明技术，是减少现有工具之间的摩擦。工具类产品的护城河不在技术，在工作流集成深度。**"

> "**壁垒不是'AI写的内容'，是前基金分析师的判断力被AI放大的专业背书。**"

### Step 5: 原子写入

```python
import pathlib, re
skill_path = "/opt/data/skills/productivity/ai-money-maker/SKILL.md"
content = pathlib.Path(skill_path).read_text()

# 确认 old_string 唯一
assert content.count(old_section_exact) == 1

new_content = content[:sec_start] + new_section + content[sec_end:]
pathlib.Path(skill_path).write_text(new_content)

# 验证
verify = pathlib.Path(skill_path).read_text()
assert "新案例名称" in verify
assert len(verify) <= 100_000
```

---

## 本次 Run 31 执行记录

| 步骤 | 操作 | 结果 |
|------|------|------|
| delegate_task web search | HTTP 404 | 失败 |
| 检查 headroom | 988 chars | 太紧 |
| 确定策略 | mine existing references | 降级 |
| 定位相关文件 | ai-case-stories-deep + ai-old-masters-deep | 找到 |
| 提取案例 | 3个具体案例（插件、Newsletter、合同AI） | 提取 |
| 合成 subsection | 更新第十四节 | 完成 |
| 版本号 | 3.1.2 → 3.1.3 | 更新 |
| 最终大小 | 99,697 chars | 安全 |

---

## 关键规则

> **不要让工具失败产生空跑。** 在 cyclical cron-batch 场景中，references/ 目录本身就是内容资产，可以跨周期重复挖掘。每次运行都应该比上一次更深地合成已有内容，而不是每次都从零开始。