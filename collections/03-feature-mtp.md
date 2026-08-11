---
title: "03 Feature head、MTP 与并行块草稿"
description: "方向最密集的主线：从 Medusa / EAGLE feature heads 到 DFlash 并行块，再到 Domino、DSpark、PCTree 对候选内因果性与生产调度的修复。"
---

# 03 Feature head、MTP 与并行块草稿

<div class="kb-section-lead" markdown>

方向最密集的主线：从 Medusa / EAGLE feature heads 到 DFlash 并行块，再到 Domino、DSpark、PCTree 对候选内因果性与生产调度的修复。

</div>

<div class="kb-inline-stats">
  <span><strong>20</strong> 篇核心论文</span>
  <span><strong>336</strong> 页核读</span>
  <span>更新至 <strong>2026</strong></span>
</div>

## 读完这一类，应能回答

- parallel marginals 为什么不是一个合法的 joint proposal？
- 怎样用低成本 Markov / RNN / tree conditioning 修复 block 内依赖？
- proposal 质量、draft latency 与 verification capacity 应如何联合优化？

## 推荐阅读路线

1. **[MEDUSA: Simple LLM Inference Acceleration Framework with Multiple Decoding Heads](../papers/03-feature-mtp-parallel-block/2024--medusa.md)** — ICML 2024，2024。
2. **[EAGLE: Speculative Sampling Requires Rethinking Feature Uncertainty](../papers/03-feature-mtp-parallel-block/2024--eagle-icml-2024.md)** — ICML 2024，2024。
3. **[DFlash: Block Diffusion for Flash Speculative Decoding](../papers/03-feature-mtp-parallel-block/2026--dflash-icml-2026.md)** — ICML 2026，2026。
4. **[Domino: Decoupling Causal Modeling from Autoregressive Drafting in Speculative Decoding](../papers/03-feature-mtp-parallel-block/2026--domino.md)** — arXiv preprint，2026。
5. **[DSpark: Confidence-Scheduled Speculative Decoding with Semi-Autoregressive Generation](../papers/03-feature-mtp-parallel-block/2026--dspark.md)** — arXiv preprint，2026。
6. **[From Chains to Trees: Parent-Conditioned Drafting for Semi-Autoregressive Speculative Decoding](../papers/03-feature-mtp-parallel-block/2026--pctree.md)** — arXiv preprint，2026。

## 全部精读

| 年份 | 论文 | Venue | 核读页码 |
|---:|---|---|---:|
| 2024 | [EAGLE-2: Faster Inference of Language Models with Dynamic Draft Trees](../papers/03-feature-mtp-parallel-block/2024--eagle-2-emnlp-2024.md) | EMNLP 2024 | 1-12 |
| 2024 | [EAGLE: Speculative Sampling Requires Rethinking Feature Uncertainty](../papers/03-feature-mtp-parallel-block/2024--eagle-icml-2024.md) | ICML 2024 | 1-14 |
| 2024 | [Hydra: Sequentially-Dependent Draft Heads for Medusa Decoding](../papers/03-feature-mtp-parallel-block/2024--hydra.md) | COLM 2024 | 1-17 |
| 2024 | [MEDUSA: Simple LLM Inference Acceleration Framework with Multiple Decoding Heads](../papers/03-feature-mtp-parallel-block/2024--medusa.md) | ICML 2024 | 1-27 |
| 2024 | [Recurrent Drafter for Fast Speculative Decoding in Large Language Models](../papers/03-feature-mtp-parallel-block/2024--redrafter.md) | arXiv preprint | 1-14 |
| 2025 | [EAGLE-3: Scaling up Inference Acceleration of Large Language Models via Training-Time Test](../papers/03-feature-mtp-parallel-block/2025--eagle-3-neurips-2025.md) | NeurIPS 2025 | 1-20 |
| 2025 | [PARD: Accelerating LLM Inference with Low-Cost Parallel Draft Model Adaptation](../papers/03-feature-mtp-parallel-block/2025--pard.md) | arXiv preprint | 1-18 |
| 2026 | [AngelSpec: Towards Real-World High Performance Inference with Speculative Decoding](../papers/03-feature-mtp-parallel-block/2026--angelspec.md) | arXiv preprint | 1-26 |
| 2026 | [CURE: Local Uncertainty Repair for Block-Parallel Speculative Decoding](../papers/03-feature-mtp-parallel-block/2026--cure.md) | arXiv preprint | 1-9 |
| 2026 | [DBLast: Dependent Block Drafting for Stochastic Speculative Decoding](../papers/03-feature-mtp-parallel-block/2026--dblast.md) | arXiv preprint | 1-12 |
| 2026 | [DeLS-Spec: Decoupled Long-Short Contexts for Parallel Speculative Drafting](../papers/03-feature-mtp-parallel-block/2026--dels-spec.md) | arXiv preprint | 1-17 |
| 2026 | [DFLARE: Scaling Up Draft Capacity for Block Diffusion Speculative Decoding](../papers/03-feature-mtp-parallel-block/2026--dflare.md) | arXiv preprint | 1-12 |
| 2026 | [DFlash: Block Diffusion for Flash Speculative Decoding](../papers/03-feature-mtp-parallel-block/2026--dflash-icml-2026.md) | ICML 2026 | 1-13 |
| 2026 | [Domino: Decoupling Causal Modeling from Autoregressive Drafting in Speculative Decoding](../papers/03-feature-mtp-parallel-block/2026--domino.md) | arXiv preprint | 1-11 |
| 2026 | [DSpark: Confidence-Scheduled Speculative Decoding with Semi-Autoregressive Generation](../papers/03-feature-mtp-parallel-block/2026--dspark.md) | arXiv preprint | 1-33 |
| 2026 | [From Chains to Trees: Parent-Conditioned Drafting for Semi-Autoregressive Speculative Decoding](../papers/03-feature-mtp-parallel-block/2026--pctree.md) | arXiv preprint | 1-18 |
| 2026 | [JetSpec: Breaking the Scaling Ceiling of Speculative Decoding with Parallel Tree Drafting](../papers/03-feature-mtp-parallel-block/2026--jetspec.md) | arXiv preprint | 1-21 |
| 2026 | [P-EAGLE: Parallel-Drafting EAGLE with Scalable Training](../papers/03-feature-mtp-parallel-block/2026--p-eagle.md) | arXiv preprint | 1-13 |
| 2026 | [TreeFlash: Parallel AR-Approximation for Faster Speculative Decoding](../papers/03-feature-mtp-parallel-block/2026--treeflash.md) | arXiv preprint | 1-13 |
| 2026 | [xPress: Parallel Refinement for Diffusion Drafters in Speculative Decoding](../papers/03-feature-mtp-parallel-block/2026--xpress.md) | arXiv preprint | 1-16 |

<div class="kb-footer-cta" markdown>

### 继续横向比较

读完单篇后回到方法矩阵，检查正确性保证、proposal 结构和系统工作区间是否可直接比较。

[打开跨论文比较](../COMPARISON.md){ .md-button .md-button--primary }
[返回全部目录](../README.md){ .md-button }

</div>
