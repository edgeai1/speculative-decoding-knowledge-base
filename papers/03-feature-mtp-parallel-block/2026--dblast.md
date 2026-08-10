---
id: 2026--dblast
title: "DBLast: Dependent Block Drafting for Stochastic Speculative Decoding"
authors: [Amirmohammad Karimi, Chao Gao, Negar Hassanpour]
year: 2026
venue: arXiv preprint
status: deep_read_complete
primary_source: https://arxiv.org/abs/2608.05448
version_read: arXiv:2608.05448
pages_read: 1-12
pdf_sha256: ae3ef8e946c666c97578a20fa6f79863c0d420052232131b2316a496008bc5c2
---

# DBLast 精读

## 核心定位

DBLast 专门研究非 greedy/high-entropy 时 parallel block marginals 的失配。它在 DFlash hidden上学习低秩 latent mixture，让同一个 latent category跨位置耦合 token选择，从而采到一致的 joint block；并用接受长度 surrogate而非只用 NLL训练。目标是提高 proposal依赖性，最终 target distribution仍由标准 speculative verifier保持。

## 方法与训练

base DFlash每位置给 hidden/logits；expander（当前实验仅一层线性）产生少数 latent categories的权重/低秩修正。先采/选共享 category，再在该条件下生成各位置，故位置不再独立，却避免全词表高阶 joint。verification按条件 proposal概率运行 greedy-branch dependent流程。

接受长度满足 prefix survival之和；作者构造基于每位置 target/draft overlap的可微 surrogate，强调前缀乘积，并做 threshold truncation避免训练初期极小概率梯度消失。Tulu3 SFT prompts由 target生成 response，从公开5层 DFlash初始化，联合训练1 epoch；Qwen3-4/8B，在 GSM8K、MT-Bench、HumanEval与creative writing考察 target sampling entropy。

结果显示温度/entropy增大时独立 DFlash接受长显著下降，DBLast在各设置更稳；category数存在收益饱和，接受导向loss和推理时 drafter stochasticity均有独立消融。论文没有摘要式统一 wall-clock最高倍数，重点证据是 matched baseline接受长，不能自行换算成通用速度。

## 边界与研究价值

低秩 mixture只近似 joint，category collapse和额外采样成本可能出现；训练绑定固定 target sampling配置，换 temperature/top-p需检查；greedy任务未必需要 latent。严格复现应报告 entropy、category数、joint q计算、surrogate truncation和端到端 latency，并以分布统计验证 lossless。它开启的问题是：如何用可精确求 proposal概率的低成本 latent结构，直接优化 stochastic acceptance而非 top-1准确率。

原文第 3–5 页模型/接受loss，第 5–8 页结果/消融，第 9–12 页验证算法、超参数与限制。
