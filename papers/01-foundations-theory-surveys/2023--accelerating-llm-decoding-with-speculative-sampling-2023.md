---
id: 2023--accelerating-llm-decoding-with-speculative-sampling-2023
title: "Accelerating Large Language Model Decoding with Speculative Sampling"
authors: [Charlie Chen, Sebastian Borgeaud, Geoffrey Irving, Jean-Baptiste Lespiau, Laurent Sifre, John Jumper]
year: 2023
venue: arXiv technical report
status: deep_read_complete
primary_source: https://arxiv.org/abs/2302.01318
version_read: arXiv:2302.01318v1
pages_read: 1-11
pdf_sha256: ffa03c6ae46f3122570bacd7da358cae8659b6421162bbc25088622fd4889c37
---

# Accelerating LLM Decoding with Speculative Sampling（2023）精读

## 一句话定位

DeepMind 与 Leviathan et al. 同期独立提出严格的修改版 rejection sampling，并首次把它扩展到 70B Chinchilla 的 16 TPU-v4 分布式 serving：4B、仅 8 层的宽 drafter 每轮起草 4 token，XSum/HumanEval 上把 14.1 ms/token 降到约 7.5/5.7 ms，同时保持 target 分布（硬件数值误差范围内）。

## 1. 与同期 ICML 论文的异同

核心概率算法相同：draft 分布记作 `p`、target 记作 `q`（符号正好与 Leviathan 常用写法相反）；草稿 token 以 `min(1,q(x)/p(x))` 接受，拒绝后从 `(q-p)_+` 归一化分布补采，全部接受时从 target 的下一位置再采一个 token。本文的独特价值不在另一套理论，而在大模型分布式工程解释和 draft architecture 选择。

## 2. 为什么一次 score 多 token 接近一次 decode

作者把大模型小 batch latency 分为三块（第 4 页）：

- **Linear layers**：单 token GEMM 受权重内存带宽限制；短块增加算术但未必增加权重读取时间。
- **Attention/KV**：历史 KV cache 的读取占主导，短块并没有把历史 cache 放大 `K` 倍。
- **All-reduce**：Megatron-style tensor parallel 每层通信；少量 token 时常为 latency-bound，小幅增加 activation size 不显著增加时延。

所以 target 对 `K+1` 个 prefix 位置的 causal scoring 可以接近单 token decode 延迟。这是 regime-dependent 假设：`K`、batch 或上下文足够大后，矩阵计算、KV 写入和通信 payload 会变成新瓶颈。

## 3. 修改版 rejection sampling

对 draft token `x~p`，接受概率为 `min(1,q(x)/p(x))`。接受分支对 token `x` 提供 `min(p(x),q(x))` 的概率质量；总拒绝概率等于 `Σ_x(q(x)-p(x))_+`。拒绝后从 `(q-p)_+ / Σ(q-p)_+` 采样，二者相加恰为 `q(x)`。第 10–11 页给出逐式证明。

算法逐 token 检查，首个拒绝后其右侧 candidate 全部失效；若全接受，target 已同时算好第 `K+1` 个分布，因此额外提交一个 token。top-k、nucleus、temperature 应先各自作用于 draft/target 分布，再执行校正。文中声称分布在硬件 numerics 内保持；不同计算图和 RNG 消费次序意味着两次运行不必逐样本相同。

## 4. Drafter 为何设计成“宽而浅”

Chinchilla 70B 通常在 16 TPU-v4 上以 14.1 ms/token 服务。一个常规 7B 模型的最佳拓扑可能仅需 4 TPU；若跨设备单独部署，会闲置 target 设备或引入切换；若硬塞到 16 TPU，通信开销反而增大。

作者训练 4B drafter，`d_model=6144`、48 heads、仅 8 layers；target 是 `d_model=8192`、64 heads、80 layers。浅层数减少每层 all-reduce 次数，宽度利用同一 16 TPU 拓扑，达到 1.8 ms/token。该 drafter 与 target 使用同 tokenizer 和训练数据。它说明部署拓扑比参数量本身更决定 `draft latency`。

## 5. 实验结果与正确读法

设置为 batch=1、`K=4`：

| 任务 / policy | 指标（AR→SpS） | token 时间 | 加速 |
|---|---|---:|---:|
| XSum nucleus `p=.8` | ROUGE-2 .112→.114 | 14.1→7.52 ms | 1.92× |
| XSum greedy | ROUGE-2 .157→.156 | 14.1→7.00 ms | 2.01× |
| HumanEval 100-shot, `p=.95,T=.8` | pass 45.1%→47.0% | 14.1→5.73 ms | 2.46× |

XSum 生成 11,305 个、最长 128-token 样本；HumanEval 生成 16,400 个、最长 512-token 样本。任务分数小幅波动不是算法改善/退化的证据，而是从同一分布重新抽样的有限样本方差与数值差异。

代码的重复模板使 HumanEval 更易预测，接受率和加速高于摘要。`K` sweep 表明更长草稿会让单轮时间近似线性增大、有效接受比例下降；XSum nucleus 在 `K=3` 已最优。`K` 还会增加整段生成时间方差，因此均值略快并不保证 P90/P99 更好（第 7–8 页）。

## 6. 复现要点

1. 保留 draft 每一步 logits/probability；target 对整段做 causal parallel score。
2. 采用同 tokenizer；对 nucleus/temperature 处理后的概率执行 ratio 和 residual，而非混用原 logits。
3. 记录 target `K+1` scoring latency 随 K 的曲线，不假设恒定。
4. drafter 要与 target 的实际 device mesh 联合设计；分别测层数导致的 collective latency 和宽度利用率。
5. 正确处理 accepted KV、rejected suffix 回收及全部接受时 bonus token。
6. 分布验证使用大量样本的 token/任务统计；greedy 可另做精确输出检查。随机 sampling 下相同 seed 不同序列不等于错误。

## 7. 限制与后续启示

- 仅测 batch=1 latency-critical 场景；高 batch 下 target 从 bandwidth-bound 转 compute-bound 后未必受益。
- 4B drafter 需要额外训练、权重和内存；文中未给出训练总成本。
- benchmark 只有 XSum 与 HumanEval，domain-dependent acceptance 的覆盖有限。
- 尾延迟只通过 K sweep 讨论，未给 production arrival process / SLO goodput。
- “突破 AR memory-bandwidth 理想上限”成立是因为一次权重读取提交多个 token，不代表突破整个系统的 FLOP/通信上限。

它预示了三个后续方向：hardware-aware drafter（宽浅结构）、按 domain/request 动态 K、以及把 acceptance 与 tail latency 而非平均 token time 联合优化。现代系统比较仍应保留这个论文最清楚的原则：target、drafter 和设备拓扑是一个共同设计问题。

## 8. 审读导航

| 内容 | PDF 页码 |
|---|---:|
| 动机、算法伪代码 | 1–3 |
| 并行 score 的系统原因、接受规则 | 4–5 |
| drafter 拓扑与主实验 | 5–7 |
| K/接受率/均值与尾延迟权衡 | 7–8 |
| 超参数与概率证明 | 10–11 |

## 原始来源

- https://arxiv.org/abs/2302.01318
