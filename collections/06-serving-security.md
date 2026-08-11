---
title: "06 Serving、基准、安全与应用"
description: "把 speculative decoding 放进真实系统：dynamic batching、goodput、SLA、MoE、RL rollout、统一基准，以及输出不变但计算成本崩溃的攻击。"
---

# 06 Serving、基准、安全与应用

<div class="kb-section-lead" markdown>

把 speculative decoding 放进真实系统：dynamic batching、goodput、SLA、MoE、RL rollout、统一基准，以及输出不变但计算成本崩溃的攻击。

</div>

<div class="kb-inline-stats">
  <span><strong>11</strong> 篇核心论文</span>
  <span><strong>190</strong> 页核读</span>
  <span>更新至 <strong>2026</strong></span>
</div>

## 读完这一类，应能回答

- 为什么 batch=1 的最高 speedup 不能代表生产 serving？
- 怎样用 non-anticipating scheduler 给全 batch 分配 draft / verify 预算？
- 如何隔离 acceptance-collapse 攻击并给出最坏额外成本上界？

## 推荐阅读路线

1. **[The Synergy of Speculative Decoding and Batching in Serving Large Language Models](../papers/06-serving-benchmarks-security-applications/2023--synergy-of-sd-and-batching.md)** — arXiv preprint，2023。
2. **[Speculative Decoding: Performance or Illusion?](../papers/06-serving-benchmarks-security-applications/2026--performance-or-illusion-mlsys-2026.md)** — MLSys 2026，2026。
3. **[SPEED-Bench: A Unified and Diverse Benchmark for Speculative Decoding](../papers/06-serving-benchmarks-security-applications/2026--speed-bench-icml-2026.md)** — ICML 2026，2026。
4. **[Adversarial Prompts for Acceptance Collapse in Speculative Decoding](../papers/06-serving-benchmarks-security-applications/2026--adsd.md)** — arXiv preprint，2026。

## 全部精读

| 年份 | 论文 | Venue | 核读页码 |
|---:|---|---|---:|
| 2023 | [The Synergy of Speculative Decoding and Batching in Serving Large Language Models](../papers/06-serving-benchmarks-security-applications/2023--synergy-of-sd-and-batching.md) | arXiv preprint | 1-9 |
| 2025 | [Speculative Streaming: Efficient and Scalable Speculative Decoding with Multi-Stream Attention](../papers/06-serving-benchmarks-security-applications/2025--speculative-streaming-emnlp-2025.md) | EMNLP 2025 | 1-24 |
| 2026 | [Accelerating Large-Scale Reasoning Model Inference: Self-Speculative Decoding with Sparse Attention (SparseSpec)](../papers/06-serving-benchmarks-security-applications/2026--specgen-mlsys-2026.md) | MLSys 2026 | 1-15 |
| 2026 | [AcceptMoE: Commitment-Weighted Self-Sizing Verifier Expert Sets for Efficient MoE Speculative Decoding](../papers/06-serving-benchmarks-security-applications/2026--acceptmoe.md) | arXiv preprint | 1-10 |
| 2026 | [Adversarial Prompts for Acceptance Collapse in Speculative Decoding](../papers/06-serving-benchmarks-security-applications/2026--adsd.md) | arXiv preprint | 1-15 |
| 2026 | [Lossless but Not Free: An Empirical Anatomy of Speculative Decoding on Consumer Hardware](../papers/06-serving-benchmarks-security-applications/2026--lossless-but-not-free.md) | arXiv preprint | 1-15 |
| 2026 | [Mistletoe: Stealthy Acceleration-Collapse Attacks on Speculative Decoding](../papers/06-serving-benchmarks-security-applications/2026--mistletoe.md) | arXiv preprint | 1-14 |
| 2026 | [PRISM: Parametrically Refactor Inference for Speculative Decoding Draft Models](../papers/06-serving-benchmarks-security-applications/2026--prism-mlsys-2026.md) | MLSys 2026 | 1-14 |
| 2026 | [SpecRoll: Fast-Slow Verifier-Feedback Adaptation for Speculative Reinforcement Learning Rollouts](../papers/06-serving-benchmarks-security-applications/2026--specroll.md) | arXiv preprint | 1-23 |
| 2026 | [Speculative Decoding: Performance or Illusion?](../papers/06-serving-benchmarks-security-applications/2026--performance-or-illusion-mlsys-2026.md) | MLSys 2026 | 1-23 |
| 2026 | [SPEED-Bench: A Unified and Diverse Benchmark for Speculative Decoding](../papers/06-serving-benchmarks-security-applications/2026--speed-bench-icml-2026.md) | ICML 2026 | 1-28 |

<div class="kb-footer-cta" markdown>

### 继续横向比较

读完单篇后回到方法矩阵，检查正确性保证、proposal 结构和系统工作区间是否可直接比较。

[打开跨论文比较](../COMPARISON.md){ .md-button .md-button--primary }
[返回全部目录](../README.md){ .md-button }

</div>
