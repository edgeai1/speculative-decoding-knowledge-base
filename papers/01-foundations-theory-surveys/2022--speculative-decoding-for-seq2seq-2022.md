---
id: 2022--speculative-decoding-for-seq2seq-2022
title: "Speculative Decoding: Exploiting Speculative Execution for Accelerating Seq2seq Generation"
authors: [Heming Xia, Tao Ge, Peiyi Wang, Si-Qing Chen, Furu Wei, Zhifang Sui]
year: 2022
venue: arXiv / ICLR 2023 submission
status: deep_read_complete
primary_source: https://arxiv.org/abs/2203.16487
version_read: arXiv:2203.16487v6
pages_read: 1-17
pdf_sha256: 04a326ee22342c42a2bc6b1d5262053b1f42b8c321cd2463a70bf0c114c92e07
---

# Speculative Decoding for Seq2seq（2022）精读

## 一句话定位

本文把 draft–then–verify 从多头小实验扩展成一个专门面向 encoder–decoder 任务的系统：用深 encoder、浅 decoder 的非自回归 `Spec-Drafter` 一次提出最多 `k` 个 token，再用目标 AR 模型并行验证。它提出“drafter 能力”和“drafter 延迟”必须同时优化，并报告约 5× 加速；但最佳配置使用 top-β 与 log-prob gap 的放宽验证，**不是现代意义上保持目标采样分布的 lossless speculative sampling**。

## 1. 研究问题与真实贡献

Blockwise Parallel Decoding 的额外 heads 很快，却因共享同一 attention query、容量有限而很难准确预测远期 token。本文认为已有工作过度压缩 drafter，忽视“草稿越准，target 调用轮数越少”。作者把总延迟写成：

`T = (L / Tok) · t_d + (L / Tok) · t_v`，

其中 `Tok` 是每轮平均接受数，`t_d/t_v` 是单轮 draft/verify 延迟。由此得到两个原则：

- Capability Principle：drafter 必须有足够能力，提高 `Tok`；
- Latency Principle：每轮 draft 又必须足够快，降低 `t_d`。

贡献由两个部分组成：专门训练的并行 `Spec-Drafter`，以及有损放宽的 `Spec-Verification`。前者是这篇论文更耐久的贡献；后者以任务指标近似不变为依据接受非 target-top-1 token，保证边界应谨慎描述。

## 2. Spec-Drafter 的结构、训练与推理

### 2.1 深 encoder、浅 decoder

Spec-Drafter 是独立 encoder–decoder。给定 source `x` 和已确认 target prefix，它在 prefix 后附加 `k` 个 `[MASK]`，使用 mask-predict 一次并行输出整块。每个 mask 位置有不同 query，可关注不同 source/context token，避免 Blockwise heads 只能共享当前位置隐藏状态的问题。

作者把 decoder 层数压低、把容量转移到 encoder：encoder 对一个 source 只算一次，decoder 却每轮重复运行。因此 12-layer encoder + 2-layer decoder 比相同总层数的均衡 6+6 更适合低延迟推理。主实验中 target 是 6+6 Transformer-base，embedding/FFN 为 512/2048；drafter 是 12+2（第 5 页）。

### 2.2 训练目标

训练时随机采样 target prefix 长度 `p`，追加 `k` 个 mask，并对真实的 `y_{p+1:p+k}` 求并行 log-likelihood。作者还使用 glancing curriculum，并用目标 AR teacher 的 sequence-level knowledge distillation 数据训练，使 drafter 输出风格更贴近 verifier。推理时所有 mask 同时 argmax，所以 draft cost 不是 `k` 次 AR pass。

这里存在两类对齐：蒸馏对齐 target 的序列模式；不同 mask query 对齐不同 future position 的注意力需求。它仍是位置边际的并行预测，块内 token 不显式互相条件化。

## 3. 验证规则：精确版与论文主推版不要混淆

vanilla verification 逐位置比较 target greedy token，只接受首个不一致之前的连续前缀，并在分叉点采用 target token。这可保持 target greedy 序列。

Spec-Verification 则在前面 token 已接受的条件下，若草稿 token：

1. 位于 target 的 top-`β` 候选；且
2. 与 target top-1 的 log-prob 差不超过 `τ`，

便继续接受。论文选择 `β=3, τ=1.0`。这会让输出偏离 target greedy；它没有使用 `min(1,p/q)` 接受概率和 `(p-q)_+` 残差重采样，所以也不保持 target stochastic distribution。“质量与 beam search 可比”是任务层经验结论，不是分布无损证明。

## 4. 实验设置与结果

### 4.1 设置

- 机器翻译：WMT14 En↔De（4.5M pairs）、WMT16 En↔Ro（610K pairs），32K joint BPE；
- 摘要：CNN/DailyMail，目标为 BART-base；
- fairseq / PyTorch 1.10.1 / CUDA 11.1；单张 P100 16GB，batch=1；
- 加速基线主要是 beam size 5，而非只与 greedy 对比。

### 4.2 机器翻译主结果

在 6+6 Transformer-base 上，`k=25` 的 SpecDec 对四个翻译方向分别报告 5.1×、5.5×、4.6×、4.8×，BLEU 与 beam-search baseline 相近或略高；Blockwise `k=10/25` 约 1.2–2.0×。若 target 本身已改成低延迟 12+2，SpecDec 的相对收益降到 2.5–3.3×，说明 baseline 架构强弱会显著改变加速数字（第 6 页）。

block size sweep 在 dev set 上显示：`k=10/15/20/25/30` 的平均接受数为 6.05/6.93/7.41/7.89/7.67，速度为 3.99×/4.54×/4.72×/5.04×/4.82×。`k=30` 已出现预测难度和计算成本导致的回落。

### 4.3 消融

第 6 页的关键消融：

| Drafter | 平均接受数 | 单轮 draft 时间 | 速度 |
|---|---:|---:|---:|
| head-based | 2.32 | 0.81 | 1.7× |
| 缩小容量（破坏能力原则） | 7.05 | 2.29 | 4.4× |
| 6+6（破坏延迟原则） | 8.21 | 10.87 | 4.0× |
| 完整 Spec-Drafter | 8.23 | 5.21 | 5.1× |

这证明接受数和 draft latency 必须联合看：6+6 的接受数几乎一样，却因为重复 decoder 更慢而损失加速。

验证放宽从 vanilla 的 6.41 accepted tokens / 26.62 BLEU，变为 top-3、`τ=1` 的 7.89 / 26.97（5.0×）；放宽到 top-5、`τ=5` 时达到 11.01、约 6.8×，但 BLEU 回落到 26.58。不能只选最大接受率配置。

### 4.4 摘要、行为一致性与能耗

CNN/DM 上 `k=25` 报告 5.1×，ROUGE-1/2/L 与 BART-base 相近，而 NAR baselines 虽达 14× 左右却明显掉点。论文另用“输出相对 target 的 BLEU”衡量行为一致性：SpecDec 86.52，NAR/Deep-Shallow 约 59–65；这仍不等于逐 token identity。附录在 WMT14 En-De 上估算 P100 功耗从 86W 升至 110W，但运行时间从 0.27h 降到 0.05h，对应能耗/碳约降 4.2×（第 16 页）。

## 5. 忠实复现路线

1. 固定 target checkpoint、tokenizer 和 greedy/beam reference。
2. 构建独立 encoder–decoder drafter；source encoder 输出可跨轮 cache，decoder 采用少层。
3. 生成 target 的 sequence-level distilled training set；随机 prefix + `k` masks，加入 glancing schedule。
4. 推理中将已确认 prefix 与 mask block 输入 drafter；得到并行提案。
5. 用 target 对 prefix+draft teacher-force 一次，逐位置计算 rank 与 top-1 gap。
6. 若要求精确 greedy，只使用 top-1 matching；复现论文主结果才采用 `β/τ`，并明确标注有损。
7. 分别记录 `t_d`、`t_v`、accepted length、端到端速度和质量；同时用 6+6 与 12+2 target 检查基线敏感性。

## 6. 局限与容易误读之处

- 最佳 5× 来自 seq2seq、batch=1、P100、beam-search latency baseline，不能直接外推 decoder-only LLM serving。
- 主验证规则改变输出；论文将“comparable quality”称作 lossless 容易与后来的 distribution-preserving 术语混淆。
- drafter 需要单独模型、蒸馏数据和训练，并增加显存；并非 off-the-shelf 零训练方案。
- source encoder 很适合做“一次算完”的容量承载，但 decoder-only LLM 没有同样免费的 encoder 阶段。
- 论文重视 latency-throughput curve，但未覆盖现代 continuous batching、KV page 管理和高并发 verifier compute saturation。

## 7. 后续影响与研究启示

它确立了 `drafter accuracy × drafter latency` 的联合设计观，直接连接到 DistillSpec/HASS 的对齐训练和后来的 hardware-aware scheduler。深 encoder、浅 decoder 的思想说明“参数量不是 drafter cost 的充分代理”，结构、并行拓扑和调用频率同样重要。它的 mask-predict block 又是 PARD、DFlash 等并行草稿路线的早期参照；其位置独立性恰好成为 2026 年 Domino、DSpark、JetSpec 等试图修复的问题。

## 8. 审读导航

| 内容 | PDF 页码 |
|---|---:|
| 框架、vanilla 分叉验证 | 1–2 |
| 两个 drafter 原则、延迟分解 | 3–4 |
| 结构、mask 训练、Spec-Verification 公式 | 4–5 |
| 设置、主结果、完整消融 | 5–7 |
| CNN/DM、行为一致性 | 7–8 |
| 限制与结论 | 9 |
| 训练细节、指标补充、T5-XXL 对比 | 12–15 |
| 能耗与生成案例 | 16–17 |

## 原始来源

- https://arxiv.org/abs/2203.16487
- 代码：https://github.com/hemingkx/SpecDec

