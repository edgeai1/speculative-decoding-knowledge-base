---
id: 2024--speculative-decoding-survey-and-spec-bench-acl-findings-2024
title: "Unlocking Efficiency in Large Language Model Inference: A Comprehensive Survey of Speculative Decoding"
authors: [Heming Xia, Zhe Yang, Qingxiu Dong, Peiyi Wang, Yongqi Li, Tao Ge, Tianyu Liu, Wenjie Li, Zhifang Sui]
year: 2024
venue: Findings of ACL 2024
status: deep_read_complete
primary_source: https://aclanthology.org/2024.findings-acl.456/
version_read: ACL Anthology proceedings
pages_read: 1-17
pdf_sha256: e1514736ae0cbaa3592be40d4ec0fd3ac13d12a54866977d9c4c832bb4e49041
---

# ACL 2024 Survey 与 Spec-Bench 精读

## 核心定位

这是首批系统梳理 speculative decoding 的综述，并贡献了 Spec-Bench：用统一 Vicuna-7B、单 RTX 3090、batch=1 环境，在对话、翻译、摘要、QA、数学和 RAG 六类任务上比较 EAGLE、SpS、Medusa、PLD、REST、Lookahead。它最重要的历史作用是建立 draft / verify / alignment 三部分语言和第三方 benchmark；局限是时间截点早、主要只测低并发单卡。

## 1. 综述框架

论文把 SD 定义为：低成本生成若干未来 candidates，target 用一次并行前向验证，首个 bifurcation 后的 token 丢弃。方法沿三条主线组织：

- **Drafting**：independent drafter（小 LM/NAR/retrieval）与 self-drafting（heads、early exit、Jacobi 等）；
- **Verification**：strict greedy、distribution-preserving speculative sampling、token-tree verification；
- **Alignment**：sequence-level KD、distribution KD、online query adaptation。

表 1/2 给出各 drafting/verification 数学形式，表 3 对当时代表方法的 drafter 类型、alignment、sampling 支持和声称速度作对照。该 taxonomy 很适合入门，但到 2026 需再增加并行 causal block、serving scheduler、长上下文 KV、MoE 与 security 等正交轴。

## 2. Spec-Bench 怎样构造

六个子任务各随机取 80 个实例，共 480：MT-Bench 多轮对话、WMT14 De-En、CNN/DailyMail、Natural Questions、GSM8K、DPR/RAG。主实验为 Vicuna-7B FP16、单 RTX 3090 24GB、batch=1，同一实现环境重复 3 次。附录给 composition、prompt/output 长度与 A100/model-scale 补充。

这个设计的价值是控制硬件和 target；六类任务覆盖了不同 repetition/entropy。它不是 production serving benchmark：样本量较小、只有英文主导数据、无 continuous batching、arrival trace、SLO 或长上下文分层。

## 3. 核心结果

- greedy 下 EAGLE 在多数任务最快，约 1.8–2.4×，GSM8K 接近 2.4×；原因是复用 target feature/KV 且 AR feature drafter 比并行独立 heads 稳定。
- PLD 在 input-output 高重复的摘要上约 2.4×，但翻译/QA 仅约 1.1–1.3×，说明 training-free lookup 强依赖 workload redundancy。
- 温度升高普遍降低速度。综合 Spec-Bench tokens/s，EAGLE 从 T=0 的 2.08× 降至 T=.5 的 1.91×、T=1 的 1.74×；SpS 约 1.77/1.64/1.49×；REST 约 1.39/1.36/1.35×。

论文把高温下降部分归于 speculative sampling criterion 的额外成本，但更根本也包括 draft/target 分布变平后接受率下降。跨方法数字必须结合其具体 sampling implementation 解读。

## 4. 论文提出的未解问题

1. drafter accuracy 与 latency 的平衡，尤其应优先优化 early-position tokens；
2. batched inference 中请求接受长度不齐和额外 verifier compute；
3. 与 continuous batching、vLLM、FlashAttention、NAR 的集成；
4. text 以外的 image/audio/video speculation。

这些问题后来分别演化为 HASS/DistillSpec、TETRIS/DSpark/AngelSpec、production benchmark，以及多模态 speculative streaming。

## 5. 使用这篇论文时的注意点

- 这是截至 2024 初的快照，不含 EAGLE-2/3、PARD、DFlash、DSpark 和 2026 verification/systems 大量工作。
- “reported speedup”表混合原论文环境，只有 Spec-Bench 部分是统一第三方测试。
- batch=1 上的 latency 优势不能外推 throughput；作者在 Limitations 明确说因缺少 batched implementation 未评估。
- 各方法支持的 strict greedy 与 stochastic correctness 不同，不能只按速度柱状图排名。
- Spec-Bench 的 80 samples/task 更适合方法筛选，精细 tail-latency 与显著性结论需更大 trace。

## 6. 复用建议

新工作至少保留 Spec-Bench 六类 workload 作为短上下文 method-level 回归集，并补充高温、不同 batch、ISL/OSL、真实引擎和硬件。报告每 task 的 accepted length、draft/verify latency、end-to-end TPS，而不是只给均值 speedup。若训练数据包含这些 benchmark，应披露/去重，避免 drafter 对常见 continuation 的记忆造成虚高。

## 审读导航

| 内容 | 页码 |
|---|---:|
| 历史与动机 | 1–3 |
| 正式定义和 taxonomy | 3–5 |
| drafting / verification | 5–7 |
| alignment | 8 |
| Spec-Bench 与结果 | 8–9 |
| 挑战、结论和限制 | 9–10 |
| 数据构成、完整表、硬件/模型规模补充 | 14–17 |

## 原始来源

- https://aclanthology.org/2024.findings-acl.456/
- benchmark/论文列表：https://github.com/hemingkx/SpeculativeDecodingPapers

