# V2-malformed 链接审计报告

> ai-money-maker Run 138 发现。9处 V2-malformed 链接待修复。

## 什么是 V2-malformed 链接

格式：`[references/X.md](references/X.md)` — 链接文本以 `references/` 开头，但 `→ Full content:` 前缀缺失。显示时显示为 `references/X.md` 而非简洁文件名。

**正确格式：** `[ai-microsaas.md](references/ai-microsaas.md)` — 链接文本无 `references/` 前缀

**V2-malformed：** `→ Full content: [references/ai-compliance-moat-deep.md](references/ai-compliance-moat-deep.md)` — 链接文本多了 `references/` 前缀

## 全部 9 处 V2-malformed 链接

| # | 文件 | 位置（章节） | 修复后 |
|---|------|-------------|--------|
| 1 | `ai-compliance-moat-deep.md` | 待查 | `[ai-compliance-moat-deep.md](references/ai-compliance-moat-deep.md)` |
| 2 | `ai-ai自由职业实战手册.md` | 待查 | `[ai-ai自由职业实战手册.md](references/ai-ai自由职业实战手册.md)` |
| 3 | `ai-buyer-psychology-deep.md` | 待查 | `[ai-buyer-psychology-deep.md](references/ai-buyer-psychology-deep.md)` |
| 4 | `ai-arbitrage-population-profile.md` | 待查 | `[ai-arbitrage-population-profile.md](references/ai-arbitrage-population-profile.md)` |
| 5 | `ai-physical-industry.md` | 待查 | `[ai-physical-industry.md](references/ai-physical-industry.md)` |
| 6 | `ai-b2b-deal-mechanics.md` | 待查 | `[ai-b2b-deal-mechanics.md](references/ai-b2b-deal-mechanics.md)` |
| 7 | `ai-info-arbitrage-v2.md` | 待查 | `[ai-info-arbitrage-v2.md](references/ai-info-arbitrage-v2.md)` |
| 8 | `industry-masters-ai-season2.md` | 待查 | `[industry-masters-ai-season2.md](references/industry-masters-ai-season2.md)` |
| 9 | `industry-masters-ai-season3.md` | 待查 | `[industry-masters-ai-season3.md](references/industry-masters-ai-season3.md)` |

## 批量修复模式

使用正则替换（Python）：
```python
import re, pathlib
content = pathlib.Path(skill_path).read_text()

# 修复 V2-malformed: [references/X.md](references/X.md) → [X.md](references/X.md)
# 只改链接文本部分（第一个 [] 内），不改变 URL 部分（第二个 () 内）
v2_pattern = re.compile(r'\[(references/([^]]+\.md))\]')
fixed = v2_pattern.sub(lambda m: f'[{m.group(2)}]', content)

# 验证：修复后 V2 链接应为 0
remaining = re.findall(r'\[(references/[^]]+\.md)\]\((references/[^)]+\.md)\)', fixed)
print(f"Remaining V2-malformed: {len(remaining)}")
```

## 修复优先级

| 优先级 | 原因 | 文件 |
|--------|------|------|
| P1 | 正在本次会话编辑的章节附近 | 待定位 |
| P2 | 内容较大（>3k chars）的 reference 文件 | ai-compliance-moat-deep.md, ai-buyer-psychology-deep.md |
| P3 | 其他 | 剩余5个 |

## 检测脚本（下次审计用）

```python
import re, pathlib
content = pathlib.Path("/opt/data/skills/productivity/ai-money-maker/SKILL.md").read_text()
v2_links = re.findall(r'\[(references/[^]]+\.md)\]\((references/[^)]+\.md)\)', content)
print(f"V2-malformed count: {len(v2_links)}")
for text, url in v2_links:
    print(f"  [{text}]({url})")
```

## 与重复链接的区别

- **V2-malformed**：同一文件被引用两次，其中一条是 V2 格式，一条是正确格式
- **重复链接**：同一文件的正确格式链接出现两次（无 V2）
- **本次 Run 138 修复的是后者**：section 十六 同一文件两个正确格式的链接（后者是 V2）→ 删除了 V2 版本，保留正确格式