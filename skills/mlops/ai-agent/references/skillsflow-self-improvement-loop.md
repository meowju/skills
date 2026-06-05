# SkillsFlow 自改进循环

**SkillsFlow** 是一种让 agent 持续自我改进的闭环模式：LLM 生成内容 → 严格模式匹配评估 → 失败模式追加到 Skill 文件 → 重复直到达标。

## 架构

```
┌─────────────────────────────────────────────┐
│  1. SKILL.md（风格指南/规则/示例）            │
│     ↓ 注入 prompt                           │
│  2. LLM Generator（生成候选内容）            │
│     ↓ 对比                                   │
│  3. Pattern Matcher Eval（严格规则校验）     │
│     ↓ 无 LLM 评判，无 fail-open              │
│  4. 失败分析 → 追加到 SKILL.md               │
│     ↓ 通过率 100%？                          │
│     是 → 推送 GitHub                         │
│     否 → 回到步骤 1                          │
└─────────────────────────────────────────────┘
```

## 关键设计原则

### Eval 必须严格（no fail-open）

**永远不要让 eval 调用 LLM 来判断内容质量。** LLM-as-judge 不可靠——它会因为情感共鸣给不及格的内容打高分，或者在内容勉强可接受时就放行。正确做法是：

- **纯 pattern matching**：正则、字符集检测、关键词存在性
- **客观可枚举的检查项**：字数限制、繁體字、禁止词、时间设定、比喻词汇
- **不允许任何 fail-safe**：`eval() { ... || return 1 }` 这种在 LLM 调用失败时默认通过的设计必须禁止

### Bad Sample 验证

在写完 eval 后，用故意违规的"坏样本"验证 eval 确实会 FAIL：

```python
BAD_SAMPLES = {
    't1': "永远爱你到天荒地老海枯石烂",  # 禁忌词
    't2': "你是我的小可爱我想你想你",    # 简体+超长
    't3': "想你想到心痛",                 # 简体+无比喻
}
for name, lyrics in BAD_SAMPLES.items():
    score, _ = eval(name, lyrics, CHECKS)
    assert score < 1.0, f"{name} should fail but got {score}"
```

如果 bad sample 没被拒绝，eval 有问题。

### 失败模式累积

每次 epoch 的失败模式追加到 SKILL.md，格式：

```markdown
### ⚠️ 常见失败模式提醒（自动追加）

#### Epoch 2026-06-05
- 繁體中文：出现简体字（现、里、面、么、什）
- 句長限制：英文词 Oh/Baby/Yeah 单独成行时 <3 字符被误判
- 引用句：需要「哪怕...但...」结构
- 情感張力：需要「明明...不...」+「哭了/發燙」双重结构
```

### 生成器需要足够大的 max_tokens

Anthropic-M2-7-7 的 extended thinking 模式会消耗大量 output token。`max_tokens=50` 时模型全花在 thinking 上，输出为空。解决：设置 `max_tokens=1200+` 并加 `"extra_body": {"enable_thinking": False}`。

## 完整实现模板

```python
import urllib.request, json, re, datetime
from pathlib import Path

BASE_URL = "http://localhost:8402/anthropic/v1"  # gateway 地址
MODEL = "Anthropic-M2-7-7"

# ── LLM 生成 ──────────────────────────────────────────────────────────────
def chat(prompt, system=None, max_tokens=1200):
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    body = {
        "model": MODEL,
        "messages": messages,
        "max_tokens": max_tokens,
        "extra_body": {"thinking_budget": 0, "enable_thinking": False}  # 禁用 extended thinking
    }
    req = urllib.request.Request(
        f"{BASE_URL}/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        d = json.load(resp)
    # 处理 multi-block 响应（text + thinking blocks）
    return "".join(c["text"] for c in d.get("content", []) if c.get("type") == "text")

# ── 严格 Pattern Eval ──────────────────────────────────────────────────────
def eval(scenario_id, lyrics_text, checks):
    lines = [l.strip() for l in lyrics_text.strip().split('\n') if l.strip()]
    results = []
    for name in checks:
        fn = EVAL_CHECKS.get(name)
        ok, reason = fn(lines, lyrics_text) if fn else (False, f"Unknown:{name}")
        results.append((name, ok, reason))
    passed = sum(1 for _, ok, _ in results if ok)
    return passed / len(results), [(n, r) for n, ok, r in results if not ok]

# ── 场景定义 ──────────────────────────────────────────────────────────────
SCENARIOS = [
    {
        'id': 's1',
        'prompt': '主题：凌晨三点的失眠想念。写一首 Lo-fi R&B 歌词。',
        'checks': ['繁體中文', '妳而非你', '句長限制', '具象比喻', '英文點綴',
                   '無禁忌詞', '時間設定', '情緒弧線']
    },
    # 更多场景...
]

# ── 主循环 ─────────────────────────────────────────────────────────────────
def main():
    skill_md = Path("SKILL.md").read_text()
    results = []
    all_failures = []

    for sc in SCENARIOS:
        lyrics = gen_lyrics(sc, skill_md)  # 调用 LLM 生成
        score, failures = eval(sc['id'], lyrics, sc['checks'])
        results.append({'id': sc['id'], 'score': score, 'failures': failures, 'lyrics': lyrics})
        all_failures.extend([(sc['id'], n, r) for n, r in failures])

    pass_rate = sum(r['score'] for r in results) / len(results)
    print(f"Pass rate: {pass_rate:.0%}")

    if all_failures:
        skill_md = refine_skill(all_failures, skill_md)
        Path("SKILL.md").write_text(skill_md)
        print(f"Skill updated with {len(set(f for _, _, f in all_failures))} failure patterns")

    if pass_rate == 1.0:
        git_push()  # 推送 GitHub

# ── 坏样本验证（每次修改 eval 后运行）──────────────────────────────────────
def verify_eval_strict():
    BAD = {
        't1': "永远爱你到天荒地老海枯石烂",  # 禁忌词
        't2': "你是我的小可爱我想你想你",    # 简体+超长
        't3': "想你想到心痛",                 # 简体+无比喻
    }
    GOOD = {
        'g1': "對妳的愛像血液\n流淌在靜脈裡\n每分每秒為妳\n在心臟裡輸送",
    }
    for name, lyrics in {**BAD, **GOOD}.items():
        score, failures = eval(name, lyrics, CHECKS_LIST)
        icon = "✓" if (name.startswith('g') and score == 1.0) or (name.startswith('t') and score < 1.0) else "✗"
        print(f"{icon} {name}: {score:.0%} — {failures[:2] if failures else 'PASS'}")
```

## 常见坑

1. **`max_tokens` 太小** → 模型输出为空（extended thinking 吃光 token）。解决：`max_tokens=1200` + `enable_thinking: False`

2. **共享字符误判**：`裡/面/么/裡` 等字符是繁體和简体共享的，不应加入 simplified set

3. **英文词行被误判**：单独成行的 `Yeah`（1词）、`Oh Baby`（2词）被 `c_len` 判为"太短"。解决：`elif n < 3 and not re.search(r'[a-zA-Z]{1,}', l)` 允许有英文词的短行

4. **`ollama` 不存在导致 fail-open**：不要写 `try: ollama() except: PASS`。永远用纯 pattern matching

5. **Bad sample 全过**：eval 有问题。必须确保 bad sample 被拒绝

## 适用场景

- **歌词/文案风格学习**：用真实语料库建立风格规则，LLM 生成 + eval 评分
- **代码生成质量关卡**：模式匹配检测安全漏洞、风格违规、复杂度超标
- **内容合规检测**：敏感词、版权内容、格式规范

**不适用**：需要 LLM 主观判断质量的任务（如"这首诗写得好不好"）—— 此类任务需要 LLM-as-judge，但这正是 fail-open 的高危区。