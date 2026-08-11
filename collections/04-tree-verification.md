---
title: "04 Tree、多候选与 verification"
description: "用树和多候选扩大 target support 覆盖，同时维护严格 residual 账本；也系统审视 block verification 与 lossy verifier 的收益边界。"
---

# 04 Tree、多候选与 verification

<div class="kb-section-lead" markdown>

用树和多候选扩大 target support 覆盖，同时维护严格 residual 账本；也系统审视 block verification 与 lossy verifier 的收益边界。

</div>

<div class="kb-inline-stats">
  <span><strong>9</strong> 篇核心论文</span>
  <span><strong>167</strong> 页核读</span>
  <span>更新至 <strong>2026</strong></span>
</div>

## 读完这一类，应能回答

- 多候选为何不能各自独立接受后任取一个成功项？
- 固定 verification 节点预算下，怎样选择最有价值的前缀闭包树？
- 近似接受应如何量化 regret、轨迹偏离和序列级质量风险？

## 推荐阅读路线

1. **[SpecInfer: Accelerating Large Language Model Serving with Tree-based Speculative Inference and Verification](../papers/04-tree-multi-draft-verification/2023--specinfer.md)** — ASPLOS 2024，2023。
2. **[SEQUOIA: Scalable and Robust Speculative Decoding](../papers/04-tree-multi-draft-verification/2024--sequoia.md)** — arXiv preprint，2024。
3. **[Block Verification Accelerates Speculative Decoding](../papers/04-tree-multi-draft-verification/2025--block-verification-iclr-2025.md)** — ICLR 2025，2025。
4. **[Revisiting Lossy Verification in Speculative Decoding: Mechanisms, Trade-offs, and Failure Modes](../papers/04-tree-multi-draft-verification/2026--revisiting-lossy-verification.md)** — arXiv preprint，2026。

## 全部精读

| 年份 | 论文 | Venue | 核读页码 |
|---:|---|---|---:|
| 2023 | [SpecInfer: Accelerating Large Language Model Serving with Tree-based Speculative Inference and Verification](../papers/04-tree-multi-draft-verification/2023--specinfer.md) | ASPLOS 2024 | 1-18 |
| 2024 | [Multi-Candidate Speculative Decoding](../papers/04-tree-multi-draft-verification/2024--multi-candidate-speculative-decoding.md) | arXiv preprint | 1-15 |
| 2024 | [SEQUOIA: Scalable and Robust Speculative Decoding](../papers/04-tree-multi-draft-verification/2024--sequoia.md) | arXiv preprint | 1-27 |
| 2024 | [SpecExec: Massively Parallel Speculative Decoding for Interactive LLM Inference on Consumer Devices](../papers/04-tree-multi-draft-verification/2024--specexec.md) | arXiv preprint | 1-20 |
| 2025 | [Block Verification Accelerates Speculative Decoding](../papers/04-tree-multi-draft-verification/2025--block-verification-iclr-2025.md) | ICLR 2025 | 1-30 |
| 2025 | [HeteroSpec: Leveraging Contextual Heterogeneity for Efficient Speculative Decoding](../papers/04-tree-multi-draft-verification/2025--heterospec.md) | arXiv preprint | 1-17 |
| 2026 | [Approximate Speculative Decoding](../papers/04-tree-multi-draft-verification/2026--approximate-speculative-decoding.md) | arXiv preprint | 1-8 |
| 2026 | [MARS: Unleashing the Power of Speculative Decoding via Margin-Aware Verification](../papers/04-tree-multi-draft-verification/2026--mars-margin-aware-verification.md) | arXiv preprint | 1-12 |
| 2026 | [Revisiting Lossy Verification in Speculative Decoding: Mechanisms, Trade-offs, and Failure Modes](../papers/04-tree-multi-draft-verification/2026--revisiting-lossy-verification.md) | arXiv preprint | 1-20 |

<div class="kb-footer-cta" markdown>

### 继续横向比较

读完单篇后回到方法矩阵，检查正确性保证、proposal 结构和系统工作区间是否可直接比较。

[打开跨论文比较](../COMPARISON.md){ .md-button .md-button--primary }
[返回全部目录](../README.md){ .md-button }

</div>
