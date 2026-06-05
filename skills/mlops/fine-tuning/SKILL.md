---
name: fine-tuning
description: LLM 微调（Fine-tuning）— SFT / LoRA / QLoRA / DPO 的完整流程、模型选型、数据准备、训练技巧、评估与部署。when the user asks about fine-tuning an LLM, or questions about LoRA, QLoRA, SFT, RLHF, DPO, model training, or model customization.
triggers:
  - LLM 微调
  - LoRA
  - QLoRA
  - SFT
  - RLHF
  - DPO
  - 模型训练
  - PEFT
category: mlops
tags: [fine-tuning, lora, qlora, sft, dpo, llm, training, peft]
version: 1.0
created: 2026-06-05
---

# LLM Fine-tuning 实战技能

## 微调方法谱系

```
全参数微调（Full Fine-tune）
  └─ 资源需求：GPU 显存 ∝ 6 × 参数规模（FP16）
  └─ 例：7B 模型 ≈ 140GB VRAM（单卡不可行）

PEFT（参数高效微调）
  ├─ LoRA / QLoRA（主流）
  ├─ Adapter
  └─ Prefix Tuning
```

---

## 1. 方法对比与选型

| 方法 | 显存占用 | 精度 | 训练速度 | 适用场景 |
|---|---|---|---|---|
| **Full SFT** | ~ 7B: 140GB | 最高 | 慢 | 有 8x A100 的场景 |
| **LoRA** | ~ 7B: ~24GB | 略低于 full | 快 | 通用场景首选 |
| **QLoRA** | ~ 7B: ~10GB | 略低于 LoRA | 较快 | 单卡/消费级 GPU |
| **DoRA** | 同 QLoRA | 略优于 LoRA | 相近 | 对精度更敏感的 |
| **DPO** | 同 LoRA | 偏好对齐好 | 快 | 偏好优化/RLHF 替代 |

**选型原则：**
- 8x A100+ → 全参数 SFT
- 单卡 A100 / 4090 → LoRA
- 消费级 3090/4090 → QLoRA（4-bit NF4）
- 只要对齐质量 → DPO（替代 RLHF）

---

## 2. 模型选择

### 2.1 主流开源基座（2024-2025）

| 模型 | 参数量 | 优势 | 中文支持 |
|---|---|---|---|
| **Llama 3.1** | 8B / 70B / 405B | 开源生态最全 | 中 |
| **Qwen 2.5** | 7B / 14B / 72B | 中文最强开源 | ✅✅ |
| **DeepSeek-V3** | 236B | 推理效率高 | ✅ |
| **Mistral Nemo** | 12B | 欧洲模型，多语言 | 中 |
| **GLM-4** | 9B / 32B | 中文优化 | ✅✅ |
| **Yi-1.5** | 6B / 34B | 中英双语 | ✅ |

**推荐：**
- 中文任务 → `Qwen2.5-7B-Instruct` / `GLM-4-9B`
- 英文为主 → `Llama-3.1-8B-Instruct`
- 追求精度 → `DeepSeek-V3`（如果资源够）

### 2.2 量化基座（QLoRA 用）

| 量化格式 | 精度 | 用途 |
|---|---|---|
| **NF4**（4-bit NormalFloat） | 最高质量 4-bit | QLoRA 推荐 |
| **Int8** | 8-bit | LoRA（不降太多质量） |
| **Int4** | 4-bit | 极致压缩，质量损失大 |

---

## 3. 数据准备（核心！）

### 3.1 数据格式（SFT）

```json
[
  {
    "messages": [
      {"role": "system", "content": "你是一个专业的金融分析师。"},
      {"role": "user", "content": "请分析一下苹果公司2024年Q3财报。"},
      {"role": "assistant", "content": "【分析开始】...【结论】..."}
    ]
  },
  {
    "messages": [
      {"role": "user", "content": "解释一下什么是RAG。"},
      {"role": "assistant", "content": "RAG（检索增强生成）是一种..."}
    ]
  }
]
```

**关键要求：**
- 格式严格一致（不统一格式会训练崩）
- 对话要有完整的 system / user / assistant 结构
- 避免太长 context（建议 max 4096 tokens，超过要截断）

### 3.2 数据质量检查

```python
# 检查项
def validate_dataset(path):
    issues = []
    for i, item in enumerate(dataset):
        msgs = item["messages"]
        # 1. 角色顺序检查（必须 user→assistant，不能 user→user）
        roles = [m["role"] for m in msgs]
        if roles[0] not in ["system", "user"]:
            issues.append(f"Row {i}: must start with system or user")
        
        # 2. assistant 不能为空
        if msgs[-1]["role"] != "assistant" or not msgs[-1]["content"].strip():
            issues.append(f"Row {i}: assistant is empty")
        
        # 3. 不能有 assistant→user 乱序
        for j in range(len(msgs)-1):
            if msgs[j]["role"] == "assistant" and msgs[j+1]["role"] == "assistant":
                issues.append(f"Row {i}: double assistant")
    
    return issues
```

### 3.3 数据量估算

| 任务类型 | 最低数据量 | 推荐数据量 |
|---|---|---|
| 指令微调（通用） | 1k-5k | 10k-50k |
| 领域适应（金融/医疗） | 500-1k | 3k-10k |
| 风格迁移 | 100-500 | 1k-3k |
| 长上下文适应 | 500-1k | 3k-5k |

**注意：** 质量 > 数量。高质量 1k 条 > 低质量 10k 条。

---

## 4. LoRA 训练（最常用）

### 4.1 环境准备

```bash
pip install transformers peft bitsandbytes accelerate sentencepiece
# 或用 vLLM + axoltl 简化（推荐）
pip install axolotl
```

### 4.2 配置文件（Qwen2.5-7B 示例）

```yaml
# qlora_7b.yaml
base_model: Qwen/Qwen2.5-7B-Instruct
model_type: qwen2

load_in_qlora: true
qlora:
  lora_r: 16
  lora_alpha: 32
  lora_dropout: 0.05
  target_modules: q_proj k_proj v_proj o_proj gate_proj up_proj down_proj

dataset_prepared_path: ./data/processed
val_set_size: 0.05

output_dir: ./outputs/qwen2.5-7b-lora
num_epochs: 3
micro_batch_size: 2
gradient_accumulation_steps: 8
optimizer: adamw_torch
lr_scheduler: cosine
learning_rate: 2e-4
warmup_ratio: 0.1

bf16: true
gradient_checkpointing: true
logging_steps: 10
save_steps: 500
eval_steps: 500
save_total_limit: 3

# NF4 量化
compute_dtype: bfloat16
```

### 4.3 关键参数解释

| 参数 | 含义 | 调参建议 |
|---|---|---|
| `lora_r` | rank，越大越强但显存增加 | 8-64，推荐 16 |
| `lora_alpha` | scaling factor，通常 = 2×rank | 32 |
| `target_modules` | 要加 LoRA 的层 | 全包（q,k,v,o+mlp） |
| `lr` | 学习率 | 2e-4 ~ 5e-5（LoRA 用更高） |
| `batch_size` | micro_batch × grad_acc | 合计 16-32 |
| `epochs` | 训练轮数 | 1-3，通常 2 就够 |

### 4.4 启动训练

```bash
# 直接用 axolotl
axolotl train qlora_7b.yaml

# 或手动
python -m torch.distributed.run \
    --nproc_per_node=2 \
    train.py --config qlora_7b.yaml
```

---

## 5. DPO 训练（偏好对齐）

### 5.1 DPO 数据格式

```json
[
  {
    "prompt": "解释量子纠缠",
    "chosen": "量子纠缠是量子力学中的一种现象...",
    "rejected": "量子纠缠就是两个粒子连在一起..."
  }
]
```

### 5.2 DPO vs RLHF

```
RLHF：需要训练 reward model + PPO 步骤（复杂，不稳定）
DPO：直接用 preference 对比训练（简单，效果好）
```

### 5.3 DPO 训练配置

```yaml
# dpo.yaml
base_model: ./outputs/qwen2.5-7b-lora  # 从 SFT LoRA 开始
dataset_path: ./data/dpo_pairs.json

output_dir: ./outputs/qwen2.5-7b-dpo

beta: 0.1  # KL penalty 系数，0.05-0.3
lr: 1e-5
epochs: 1  # DPO 通常 1 epoch 就够
micro_batch_size: 2
```

---

## 6. 评估方法

### 6.1 自动化评估指标

| 指标 | 工具 | 说明 |
|---|---|---|
| **Perplexity** | `transformers` | 文本流畅度，越低越好 |
| **ROUGE-L** | `rouge` | 生成与参考的重叠度 |
| **BERTScore** | `bert_score` | 语义相似度 |
| **MT-Bench** | 自己部署 | 多轮对话评估 |
| **LlamaFactory** | 内置 benchmark | 支持多个标准评估 |

### 6.2 主观评估

- **采样对比**：同 prompt 对比 base vs fine-tuned 输出
- **红队测试**：输入边界/对抗输入，检查输出质量
- **领域专家评审**：金融/医疗等领域需人工审核

### 6.3 早停（Early Stopping）

```python
from transformers import TrainerCallback

class EarlyStoppingCallback(TrainerCallback):
    def on_evaluate(self, args, state, control, metrics):
        if metrics["eval_loss"] > state.best_metric:
            control.should_training_stop = True
```

---

## 7. 合并与部署

### 7.1 合并 LoRA 权重

```python
from peft import PeftModel, LoraConfig
from transformers import AutoModelForCausalLM

base = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-7B-Instruct")
model = PeftModel.from_pretrained(base, "./outputs/qwen2.5-7b-lora")
merged = model.merge_and_unload()
merged.save_pretrained("./outputs/qwen2.5-7b-merged")
```

### 7.2 量化导出（GGUF / AWQ）

```bash
# 导出为 Q4_K_M GGUF
python transformers/examples/quantize/quantize.py \
    --model ./outputs/qwen2.5-7b-merged \
    --output ./outputs/qwen2.5-7b-Q4_K_M.gguf \
    --quantization_method q4_k_m
```

### 7.3 部署

```bash
# vLLM 部署
vllm serve ./outputs/qwen2.5-7b-merged \
    --tensor-parallel-size 2 \
    --quantization awq \
    --port 8000

# llama.cpp 部署（本地）
./llama-cli -m ./outputs/qwen2.5-7b-Q4_K_M.gguf \
    -n 2048 -c 4096 --temp 0.7 -p "你是AI助手"
```

---

## 8. 常见问题与解决

| 问题 | 原因 | 解决 |
|---|---|---|
| **loss 不下降** | 数据格式错误 / 标签全零 | 检查数据格式，验证 dataset |
| **过拟合** | 数据太少 / epochs 太多 | 加数据，加 dropout，加早停 |
| **灾难性遗忘** | 全参数微调 / LR 太高 | 用 LoRA，降低 LR |
| **输出乱码** | tokenizer 不匹配 / 采样温度太高 | 检查 tokenizer，加重复惩罚 |
| **训练爆显存** | micro_batch 太大 | 降 micro_batch，增 grad_acc |
| **DPO 训练崩** | beta 参数不对 / 数据质量差 | 降 beta 到 0.05，数据清洗 |

---

## 验证步骤

1. **数据验证**：运行格式检查脚本
2. **小规模试跑**：先 1% 数据跑通，验证 loss 下降
3. **中间 checkpoint**：每 500 step 采样对比
4. **最终评估**：用 MT-Bench / 自建评测集
5. **合并导出**：LoRA → merged → GGUF
6. **A/B 测试**：线上对比 base vs fine-tuned