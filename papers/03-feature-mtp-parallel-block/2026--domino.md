---
id: 2026--domino
title: "Domino: Decoupling Causal Modeling from Autoregressive Drafting in Speculative Decoding"
authors: [Jianuo Huang, Yaojie Zhang, Qituan Zhang, Hao Lin, Hanlin Xu, Linfeng Zhang]
year: 2026
venue: arXiv preprint
status: deep_read_complete
primary_source: https://arxiv.org/abs/2605.29707
version_read: arXiv:2605.29707
pages_read: 1-11
pdf_sha256: 321128dbada12c8dd7c41b497a031d1b34929d81ceb88ef95266cbba8ed24ade
---

# Domino 精读

## 核心思想

Domino 将“强因果建模”与“昂贵 AR transformer forward”解耦：DFlash 5 层 backbone 一次给 block16 的 base logits；一个很小的 GRU 顺序读取已经采样的草稿 token，再用低秩 logit residual 修正每位置分布。于是主体并行、只有便宜的因果校正串行。

对位置 i，GRU 状态 `S_{i-1}=GRU(E_≤i-1)`；`ΔL_i=W2 SiLU(W1[H_i;S_i-1])`，最终 `L_i=L_i^base+ΔL_i`。GRU hidden 1024、bottleneck r=256。修正在 logit space，避免每个顺序步重新跑巨大的 target LM head；Triton+CUDA Graph 将 head loop 从 2.64ms 降至 1.20ms。

## 训练为何用 teacher forcing

作者认为 verifier 只有在所有前 token 正确时才会走到位置 i，因此 causal head 只需擅长“已接受 prefix”状态；用真 token teacher forcing 比把早期错误 rollout 喂回更贴合这个条件。直接 TF 又会让 head 走捷径、backbone 退化，故使用 base-anchored curriculum：`L=(1-λ_t)L_final+λ_t L_base`，λ 从 1 线性降至 0，并对远期位置指数降权。消融 TTT/TF/TF+curr 接受长约 3.80/3.96/4.19，支持两步设计，但未覆盖错误 prefix 下 proposal calibration。

## 结果和边界

1.42M Open-PerfectBlend prompts 由 target 重生成；A100，Qwen3-4B/8B。T=0 八任务均值分别 `5.47×/τ7.08`、`5.49×/7.17`，DFlash 为 `4.70×/6.11`、`4.66×/6.06`；T=1 Domino 为 `4.61×/6.00`、`4.46×/5.91`。SGLang concurrency 2–32 也普遍领先，最高约 `5.8×` throughput。结构化 math 的提升大于开放对话，符合 intra-block dependency 的作用。

输出无损仍依赖标准 verifier。Domino head 给出明确因果 proposal factorization，适合 residual rejection；但最高数字需连同 temperature、backend、block、重新生成的训练数据读。训练数据量也大于部分基线，论文另做 ShareGPT same-data 比较以缓和而未完全消除系统差异。

## 复现与研究接口

先训练/加载 target-specific DFlash；base LM-head 一次并行，GRU 每步只做低秩 residual；融合 loop kernel并保留 q logits。测 head latency、base/final loss、位置接受曲线和大 batch。风险包括 TF exposure gap、词表投影仍贵、GRU 串行随 block 增长，以及 checkpoint 专用训练。可研究并行化 causal correction、接受导向 curriculum 和动态 block 调度。

原文第 4–6 页为架构/训练，第 6–8 页为结果，第 8–11 页为消融与附录。
