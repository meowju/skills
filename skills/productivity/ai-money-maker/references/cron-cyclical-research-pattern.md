# 近限文件扩深循环模式

## 触发条件

当 SKILL.md 满足以下任一条件，切换为「迁移优先」而非「新增优先」：

1. `100000 - len(content) < 2000` — headroom < 2,000 chars
2. 所有 8 个研究轮次垂直方向已覆盖（无新主题可加）
3. 下一次插入需要超过可用 headroom

## 决策树

```
当前 headroom ≥ 5,000?
  → 是：直接新增研究内容
  → 否：检查是否所有垂直方向已覆盖？
      → 是：执行迁移优先循环
      → 否：寻找最小插入点（<300 chars）
```

## 迁移优先三步

### Step 1：识别可压缩章节

按字节大小排序，找出 >3.5k 的章节：

```
四十、AI资产构建（5,931 chars）→ 目标压缩至 ≤1,500
十七、B2B信任销售（4,086 chars）→ 目标压缩至 ≤1,500
二十四、AI买家心理学（4,361 chars）→ 目标压缩至 ≤1,500
十八、谈判话术（3,848 chars）→ 目标压缩至 ≤1,500
```

### Step 2：执行原子迁移

**已有ref-link章节（本次session模式）：** 章节中已有 `→ Full content:` 或 `→ 完整内容:` 链接时，只替换 inline 部分（链接之前的内容），引用行原样保留：

```python
ref_line_start = section_text.find('→ Full content:')
if ref_line_start == -1:
    ref_line_start = section_text.find('→ 完整内容:')
ref_line_end = section_text.find('\n', ref_line_start) + 1
old_inline = section_text[:ref_line_start]   # 压缩目标（通常 2-3k）
new_inline = condensed_summary               # 通常 300-500 chars
new_section = new_inline + section_text[ref_line_start:]  # ref行原样保留
```

**无ref-link章节：** 将整个章节内容（含标题和所有子内容）移至 references/，在原位置替换为：
- 新标题（删「详解」等冗词）
- 1-2句核心总结（≤150 chars）
- `→ 完整内容：[references/XXX.md](references/XXX.md)` 链接

迁移后文件应减少 ≥2,500 chars，headroom ≥3,000。

**真实案例（本session，Run 157）：** Section 八十一（2,707 chars，有ref-link）→ 压缩inline至358 chars，保留 `→ Full content: [ai裂变传播私域资产化.md]`；Section 八十九（2,838 chars，无ref-link）→ 新建 `references/industry-masters-ai-season4.md`，inline压缩至465 chars；合计 freed 4,550 chars，v3.57.0。

**Rule：不要重建已存在的reference文件。** 如章节已有对应ref文件（本次八十一的情况），只需压缩inline不要创建重复ref文件。

### Step 3：验证后新增

迁移完成后立即验证：
```python
size = len(pathlib.Path(skill_path).read_text())
assert size <= 97000, f"迁移后仍然过大: {size:,}"
```

然后执行下一轮深化内容插入。

## 8轮研究轮次（循环深化）

| 轮次 | 垂直方向 | 章节 |
|------|----------|------|
| 1 | 传统行业老法师 + AI | 二、行业老法师 |
| 2 | B2B AI 销售心理学 | 十七、信任销售 |
| 3 | 垂直 AI 产品案例 | 十三、行业垂直 |
| 4 | 复利型 AI 资产 | 四十、资产构建 |
| 5 | 高信任关系销售 | 十七（扩展）|
| 6 | 信息差套利 | 二十五 |
| 7 | 合规即护城河 | （新增章节）|
| 8 | AI 买家心理学 | 二十四 |

所有8个方向均已覆盖后，下一循环应做「深化」而非「新加」：
- 从 references/ 挖掘已有案例，加入新分析视角
- 将2-3个相关小节合并为一个更深的综合节
- 将分散的同类内容（各行业的AI案例）合并为统一的「跨行业AI创富」

## 参考文件挖掘模式（研究失败时的fallback）

当 delegate_task 返回 HTTP 404（web search 不可用）时：

1. 扫描 `references/` 下已有文件，寻找目标垂直的现有内容
2. 从引用文件中提取具体数字和案例（不只是链接）
3. 添加合成分析段落，结合多个已有 reference 的洞察
4. 版本号 +0.0.1（内容深化而非新增主题）

**关键原则：不让工具失败产生空跑。**

## 头部空间安全公式

```
可用 = 100000 - len(content)
安全阈值 = 1500  # 正常新增阈值
紧急阈值 = 300   # 仅插入极短内容

新增风险 = 新增内容估计长度 + 200（缓冲）
if 可用 < 新增风险 + 安全阈值:
    → 执行迁移优先，或跳过本轮
```

## 真实案例记录

### ai-money-maker v3.1.3→3.1.4（本session）

- **前：** 99,697 chars，303 headroom
- **问题：** headroom 仅够 257 chars，无法新增实质性内容
- **解法：** 在现有 section 六十 尾部追加 核心公式+红黑榜（257 chars），版本 3.1.3→3.1.4
- **限制：** 文件已到 99,953（47 headroom），下一轮必须迁移才能继续

### purpose-finder v4.45.0（参考案例）

- **前：** 99,996 chars，4 headroom
- **问题：** 所有8个研究轮次已覆盖，但文件已达极限
- **解法：** Founder Mode inline + Quick Scripts 压缩 + Decision Frameworks 分拆 → 下一循环需迁移才能继续
- **教训：** 确认「所有主题已覆盖」时，必须同时确认「有 headroom 新增深化内容」，两者缺一不可

→ Full content: [references/migrate-first-at-limit.md](references/migrate-first-at-limit.md) — ai-money-maker Run 121 极限迁移案例：99,955 chars + 45 headroom → condense七 + append七十一 → 96,884 chars + 3,116 headroom

### ai-money-maker v2.77（参考挖掘案例）

- **前：** 96,530 chars，3,470 headroom
- **问题：** delegate_task 全部 HTTP 404
- **解法：** 从 `industry-masters-ai-season2.md` 提取3个案例 + 从 `ai-old-masters-cases.md` 提取ROI框架
- **结果：** 98,840 chars，1,160 headroom，零新增研究