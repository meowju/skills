---
name: ai-agent
description: AI Agent（智能体）设计、开发与生产落地 — 架构模式、工具调用（Tool Use）、多Agent协作、记忆系统、规划与反思、任务循环控制。when the user asks about building/deploying/debugging an AI agent, or questions about agent frameworks, tool calling, multi-agent systems, or agent orchestration.
triggers:
  - AI Agent 开发
  - Agent 架构
  - 工具调用
  - Multi-Agent
  - Agent 规划
  - ReAct / CoT
  - Agent 落地
category: mlops
tags: [agent, llm, tool-use, orchestration, planning, memory, multi-agent]
version: 1.0
created: 2026-06-05
---

# AI Agent 实战技能

## Agent 核心架构

```
User Query
  └─→ Planning（规划）
  │      └─ 任务分解 / 目标识别
  └─→ Memory（记忆）
  │      ├─ Short-term：当前对话上下文
  │      └─ Long-term：历史经验/知识
  └─→ Tools（工具）
  │      └─ 代码执行 / API调用 / 检索
  └─→ Action（执行）
  │      └─ Tool calls → Observation → Loop
  └─→ Reflection（反思）
         └─ 结果评估 → 自我修正
```

---

## 1. 核心设计模式

### 1.1 ReAct（Reasoning + Acting）

交替执行：思考 → 行动 → 观察，循环直到完成任务。

```python
def react_agent(query, tools, max_steps=10):
    history = []
    observation = ""
    
    for step in range(max_steps):
        # Think：分析当前状态，决定下一步
        thought = llm_think(
            prompt=f"Query: {query}\nHistory: {history}\nObservation: {observation}\nWhat to do next?"
        )
        
        # Parse：提取 action + action_input
        action, action_input = parse_action(thought)
        
        if action == "finish":
            return action_input
        
        # Act：执行工具
        if action in tools:
            observation = tools[action](**action_input)
        else:
            observation = f"Unknown tool: {action}"
        
        history.append({
            "step": step,
            "thought": thought,
            "action": action,
            "observation": observation
        })
    
    return "Max steps reached"
```

### 1.2 Plan-and-Execute

先规划，后执行 — 适合复杂多步任务：

```
规划阶段：LLM 将任务拆解为有序子任务
执行阶段：依次执行每个子任务
评估阶段：汇总结果，必要时重规划
```

### 1.3 Memory-Augmented Agent

三层记忆架构：

| 层次 | 内容 | 生命周期 |
|---|---|---|
| **感官记忆** | 当前 user message | 单轮 |
| **工作记忆** | 最近 N 轮对话摘要 | 会话级 |
| **长期记忆** | Vector DB / KG 检索结果 | 跨会话 |

---

## 2. 工具调用（Tool Use）

### 2.1 工具定义格式（OpenAI JSON Schema style）

```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "搜索互联网获取实时信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索关键词"
                    },
                    "max_results": {
                        "type": "integer",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_code",
            "description": "在沙箱中执行 Python 代码",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {"type": "string"},
                    "language": {"type": "string", "enum": ["python", "bash"]}
                },
                "required": ["code"]
            }
        }
    }
]
```

### 2.2 工具调用循环

```python
messages = [{"role": "user", "content": query}]

while True:
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )
    
    msg = response.choices[0].message
    
    if msg.tool_calls:
        # 执行所有 tool calls
        for tc in msg.tool_calls:
            tool_name = tc.function.name
            args = json.loads(tc.function.arguments)
            
            result = execute_tool(tool_name, args)
            
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})
    else:
        # 最终回复
        return msg.content
```

### 2.3 工具调用失败处理

```python
def execute_tool_with_fallback(tool_name, args, max_retries=2):
    for attempt in range(max_retries):
        try:
            return tool_registry[tool_name](**args)
        except ToolExecutionError as e:
            if attempt == max_retries - 1:
                return f"[Tool Error] {tool_name} failed after {max_retries} attempts: {e}"
            # 重试一次，换参数
            args = refine_args(args, error=str(e))
```

---

## 3. Multi-Agent 系统

### 3.1 协作模式

| 模式 | 描述 | 适用场景 |
|---|---|---|
| **串行管道** | A → B → C，输出依次传递 | 顺序处理流水线 |
| **并行分发** | 1 个 Orchestrator → N 个 Worker | 独立子任务并行 |
| **层级嵌套** | Manager → Sub-manager → Workers | 复杂任务分解 |
| **讨论协商** | N 个 Agent 讨论 → 共识决策 | 需要多视角的场景 |

### 3.2 并行分发示例（Orchestrator → Workers）

```python
def parallel_agents(query, workers, max_workers=3):
    # 1. 规划：分解为独立子任务
    subtasks = llm_plan_split(query, n=max_workers)
    
    # 2. 并行执行 workers
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(worker.run, subtask): subtask
            for subtask in subtasks
        }
        results = [f.result() for f in as_completed(futures)]
    
    # 3. 聚合：整合 worker 结果
    final_answer = llm_synthesize(query, results)
    return final_answer
```

### 3.3 Agent 间通信协议

```python
class AgentMessage:
    def __init__(self, sender, receiver, content, metadata=None):
        self.sender = sender
        self.receiver = receiver  # "all" for broadcast
        self.content = content
        self.metadata = metadata or {}  # priority, deadline, ttl
```

---

## 4. 规划与反思（Planning & Reflection）

### 4.1 任务分解（Task Decomposition）

```python
def decompose(task):
    prompt = f"""
    Task: {task}
    Break it down into 3-7 concrete sub-tasks.
    Each sub-task should be atomic and actionable.
    
    Format:
    1. [sub-task]
    2. [sub-task]
    ...
    """
    result = llm_generate(prompt)
    return parse_list(result)
```

### 4.2 自我反思（Self-Reflection）

关键时机：工具调用结果异常 / 任务完成后验证

```python
def reflect(result, goal):
    assessment = llm_generate(f"""
    Goal: {goal}
    Result: {result}
    
    Rate 0-10 how well did we achieve the goal?
    If < 8, what went wrong and how can we improve?
    If >= 8, what confirmed success?
    """)
    
    if "needs_retry" in assessment:
        return "retry_with_changes", assessment
    return "success", result
```

### 4.3 错误恢复策略

```python
def with_error_recovery(agent_fn, max_retries=3):
    for attempt in range(max_retries):
        try:
            return agent_fn()
        except AgentError as e:
            logger.warning(f"Attempt {attempt+1} failed: {e}")
            if attempt == max_retries - 1:
                raise
            # 给 agent 提供错误信息，让它换策略
            set_context(error_context=str(e))
```

---

## 5. 生产部署检查清单

### 5.1 必需功能

- ✅ **超时控制**：单步 max 30s，总任务 max 5min
- ✅ **预算控制**：max tool calls 50，防止无限循环
- ✅ **幂等性**：重复调用同一 tool 产生相同结果
- ✅ **日志审计**：每次 tool call 记录 input/output/success
- ✅ **优雅降级**：tool 不可用时返回友好错误，不卡死

### 5.2 Agent 评测

| 维度 | 指标 | 评估方法 |
|---|---|---|
| 成功率 | Task Completion Rate | 100 条测试任务 |
| 效率 | Avg Steps / Cost | 统计 tool calls |
| 准确性 | Answer Correctness | LLM-as-Judge |
| 安全性 | Harmful Output Rate | 对抗样本测试 |

### 5.3 常见失败模式

| 模式 | 症状 | 解决 |
|---|---|---|
| 循环调用 | 相同 tool 被反复调用 | 加 step count limit + 状态检测 |
| 工具乱选 | 选了不相关的 tool | 优化 tool description / 加 examples |
| 幻觉指令 | agent 幻觉了一个不存在的 tool | 限制 tool registry + validation |
| 上下文溢出 | 长对话后开始乱 | 加 summarization / context window management |

---

## 6. 主流框架选择

| 框架 | 场景 | 特点 |
|---|---|---|
| **LangGraph** | 生产级复杂 agent | 有状态图，循环控制强 |
| **CrewAI** | Multi-Agent 协作 | 角色定义清晰，pipeline 友好 |
| **AutoGen** | 微软生态，多Agent讨论 | 讨论模式强 |
| **SmolAgents** | 轻量/快速原型 | 简单，支持本地模型 |
| **DSPy** | 编程式 agent | 声明式，模块化程度高 |

**选型建议：**
- 单 agent / 简单 pipeline → `SmolAgents`
- Multi-Agent / 需要循环控制 → `LangGraph`
- 需要多角色协作 → `CrewAI`
- 需要与微软生态集成 → `AutoGen`

---

## 验证步骤

1. 用 10 条有陷阱的 query 测试（空结果、模糊查询、多跳）
2. 观察 agent 是否进入无限循环（step count 监控）
3. 检查 tool 调用是否有不必要的冗余
4. 验证失败时 agent 是否能自我恢复或优雅降级
5. 做对抗测试：故意传错误参数给 tools

---

## 参考：SkillsFlow 自改进循环

自改进 agent 的一种具体实现模式：**用真实 LLM 生成内容 + 严格模式匹配评估（无 LLM 评判，无 fail-open）+ 结果写回 Skill 文件**。适用于歌词生成、文案创作、代码生成等可量化评估的内容生产任务。

详见 `references/skillsflow-self-improvement-loop.md`。