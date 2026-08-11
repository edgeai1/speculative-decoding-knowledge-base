---
title: "01 基础、理论与综述"
description: "从 blockwise parallel decoding 到严格 speculative sampling、最优传输、多 draft 凸优化与接受率理论，建立整个方向的数学底座。"
---

# 01 基础、理论与综述

<div class="kb-section-lead" markdown>

从 blockwise parallel decoding 到严格 speculative sampling、最优传输、多 draft 凸优化与接受率理论，建立整个方向的数学底座。

</div>

<div class="kb-inline-stats">
  <span><strong>9</strong> 篇核心论文</span>
  <span><strong>166</strong> 页核读</span>
  <span>更新至 <strong>2026</strong></span>
</div>

## 读完这一类，应能回答

- 为什么一次 target forward 可以无损提交多个 token？
- greedy-exact 与 distribution-preserving 分别需要什么条件？
- 接受率、期望提交长度与真实 wall-clock speedup 如何区分？

## 推荐阅读路线

1. **[Blockwise Parallel Decoding for Deep Autoregressive Models](../papers/01-foundations-theory-surveys/2018--blockwise-parallel-decoding-2018.md)** — NeurIPS 2018，2018。
2. **[Fast Inference from Transformers via Speculative Decoding](../papers/01-foundations-theory-surveys/2023--fast-inference-from-transformers-via-speculative-decoding-icml-2023.md)** — ICML 2023，2023。
3. **[SpecTr: Fast Speculative Decoding via Optimal Transport](../papers/01-foundations-theory-surveys/2023--spectr-optimal-transport-verification-2023.md)** — NeurIPS 2023，2023。
4. **[Global Resolution: Optimal Multi-Draft Speculative Sampling via Convex Minimization](../papers/01-foundations-theory-surveys/2026--global-resolution-iclr-2026-oral.md)** — ICLR 2026 Oral，2026。

## 全部精读

| 年份 | 论文 | Venue | 核读页码 |
|---:|---|---|---:|
| 2018 | [Blockwise Parallel Decoding for Deep Autoregressive Models](../papers/01-foundations-theory-surveys/2018--blockwise-parallel-decoding-2018.md) | NeurIPS 2018 | 1-10 |
| 2022 | [Speculative Decoding: Exploiting Speculative Execution for Accelerating Seq2seq Generation](../papers/01-foundations-theory-surveys/2022--speculative-decoding-for-seq2seq-2022.md) | arXiv / ICLR 2023 submission | 1-17 |
| 2023 | [Accelerating Large Language Model Decoding with Speculative Sampling](../papers/01-foundations-theory-surveys/2023--accelerating-llm-decoding-with-speculative-sampling-2023.md) | arXiv technical report | 1-11 |
| 2023 | [Fast Inference from Transformers via Speculative Decoding](../papers/01-foundations-theory-surveys/2023--fast-inference-from-transformers-via-speculative-decoding-icml-2023.md) | ICML 2023 | 1-13 |
| 2023 | [SpecTr: Fast Speculative Decoding via Optimal Transport](../papers/01-foundations-theory-surveys/2023--spectr-optimal-transport-verification-2023.md) | NeurIPS 2023 | 1-21 |
| 2024 | [Unlocking Efficiency in Large Language Model Inference: A Comprehensive Survey of Speculative Decoding](../papers/01-foundations-theory-surveys/2024--speculative-decoding-survey-and-spec-bench-acl-findings-2024.md) | Findings of ACL 2024 | 1-17 |
| 2025 | [Decoding Speculative Decoding](../papers/01-foundations-theory-surveys/2025--decoding-speculative-decoding-naacl-2025.md) | NAACL 2025 | 1-14 |
| 2026 | [Global Resolution: Optimal Multi-Draft Speculative Sampling via Convex Minimization](../papers/01-foundations-theory-surveys/2026--global-resolution-iclr-2026-oral.md) | ICLR 2026 Oral | 1-34 |
| 2026 | [When Is a Draft Accepted? A Theory of Acceptance in Speculative Decoding](../papers/01-foundations-theory-surveys/2026--when-is-a-draft-accepted-2026.md) | arXiv preprint | 1-29 |

<div class="kb-footer-cta" markdown>

### 继续横向比较

读完单篇后回到方法矩阵，检查正确性保证、proposal 结构和系统工作区间是否可直接比较。

[打开跨论文比较](../COMPARISON.md){ .md-button .md-button--primary }
[返回全部目录](../README.md){ .md-button }

</div>
