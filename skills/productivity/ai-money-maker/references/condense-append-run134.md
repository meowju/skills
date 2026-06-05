# 扩深循环案例库：Condense + Append 原子写入

> Run 134 新增（v3.30）。补充 Run 121 的「迁移优先」模式。

## 模式识别

当 SKILL.md 处于以下状态时，使用 Condense + Append 而非直接新增：

1. `headroom < 2,000` 且所有研究轮次方向已覆盖
2. 有现成 reference 链接的大章节（≥2.5k chars）可压缩
3. 新内容与现有 reference 文件已有对应关系

## 核心公式

```
目标文件大小 = 现有大小 - (压缩章节大小 - 压缩后摘要大小) + 新章节大小
```

**Condense + Append 原子写入三步：**

1. **选章节** — 找有 ≥1 个 reference 链接、≥2.5k chars 的大章节
2. **算净差** — 压缩后应净增 headroom ≥1,500
3. **原子写** — 读全文→计算新内容→一次 `write_text`（不是多次 patch）

## Run 134（v3.29.0→v3.30.0）案例

**初始状态：** 99,394 chars / 60 sections / 1,606 headroom

**目标：** 添加 Cursor AI + Micro-SaaS 新章节（约 1,400 chars）

**分析：** 直接新增会超限。Section 六十八（B2B AI 成交深化 2，3,264 chars）已有 `→ 完整内容：[ai-b2b-deal-mechanics.md](references/ai-b2b-deal-mechanics.md)`，可压缩。

**操作：**
- Condense §六十八（3,264→523 chars，−2,741）
- Append §七十七（+1,375 chars）

**结果：** 98,028 chars，1,972 headroom，零 orphan，零结构损坏

```python
# 精确实施
import pathlib, re
skill_path = "/opt/data/skills/productivity/ai-money-maker/SKILL.md"
content = pathlib.Path(skill_path).read_text()

condensed_68 = """## 六十八、B2B AI 成交深化 2：谈判力学·合同结构·规模化路径

> v3.16 新增。本节收录 B2B AI 成交中常被忽视的三个维度：谈判红黑榜（合同里的真实博弈）、行业 Deal Size 地图（不同行业 AI 合同的真实数字）、规模化路径（从第一个客户到 10 个的正反馈循环设计）。

> 2025 深化版精简直播。完整内容含谈判红黑榜表格、4种权力角色工具、6条绕过否决者路径、行业 Deal Size 地图、规模化三层次详解。

→ 完整内容：[ai-b2b-deal-mechanics.md](references/ai-b2b-deal-mechanics.md)

---

### 验证清单

- [ ] 记住了免费 POC 转化率（67%）是技术评测（23%）的 3 倍
- [ ] 记住了"退出权"比"满意保证"续约率高 37%
- [ ] 记住了合同里必须留：知识产权、年度涨价权、算法变更权
- [ ] 记住了金融行业主流 Deal ¥80-250 万，是最高的赛道之一
- [ ] 记住了 Q1 签约比 Q4 大 17%——时间窗口是战略资源
- [ ] 记住了规模化三层次：产品化→漏斗化→生态化

"""

new_sec77 = """
## 七十七、 Cursor AI + Micro-SaaS：无代码时代的10x生产器（2025深化版）

> v3.30 新增。本节收录 Cursor AI 时代的最新 Micro-SaaS 打法：无代码构建、多端变现、真实案例。

...（新章节完整内容）...
"""

pos68 = content.find("## 六十八、B2B AI 成交深化 2：谈判力学·合同结构·规模化路径")
next_69 = content.find("\n## 六十九", pos68)

new_content = content[:pos68] + condensed_68 + content[next_69:] + new_sec77
new_content = new_content.replace("version: 3.29.0", "version: 3.30.0", 1)

pathlib.Path(skill_path).write_text(new_content)

# 立即验证
size = len(pathlib.Path(skill_path).read_text())
assert size <= 100_000
assert "## 七十七" in new_content
assert "version: 3.30.0" in new_content
```

## 与 Run 121 的差异

| 维度 | Run 121（v3.18.0） | Run 134（v3.30.0） |
|------|-------------------|-------------------|
| 触发条件 | headroom 45（hard limit） | headroom 1,606（警戒区） |
| 压缩章节 | §七（3,930→1,348） | §六十八（3,264→523） |
| 新增方式 | 插入（split）现有章节之间 | 追加（EOF）新章节 |
| headroom 策略 | 目标 ≥3,000 | 目标 ≥1,500 |

## 警示：V2 链接未在本轮修复

本次检测到 70 个 V2-malformed 链接（`[references/X.md](references/X.md)` 格式），但 headroom 仅 1,972，无法同时修复。**V2 修复需 ≥2,000 headroom** — 下轮有 headroom 时优先处理。

**V2 检测代码：**
```python
import re
v2 = re.findall(r'\[(references/[^]]+\.md)\]\((references/[^)]+\.md)\)', content)
print(f"V2 instances: {len(v2)}")
```

## headroom 状态机

| headroom | 状态 | 动作 |
|----------|------|------|
| ≥5,000 | 绿色 | 直接新增研究内容 |
| 2,000–5,000 | 黄色 | 小幅深化，检查触顶风险 |
| 1,000–2,000 | 橙色 | Condense + Append（当前档位） |
| <1,000 | 红色 | 必须迁移，下轮禁止直接新增 |