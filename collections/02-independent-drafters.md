---
title: "02 独立 drafter、对齐与在线选择"
description: "研究独立小模型如何与 target 对齐、蒸馏、在线更新和动态选择，并揭示跨语言、跨领域与模型族迁移的边界。"
---

# 02 独立 drafter、对齐与在线选择

<div class="kb-section-lead" markdown>

研究独立小模型如何与 target 对齐、蒸馏、在线更新和动态选择，并揭示跨语言、跨领域与模型族迁移的边界。

</div>

<div class="kb-inline-stats">
  <span><strong>7</strong> 篇核心论文</span>
  <span><strong>147</strong> 页核读</span>
  <span>更新至 <strong>2026</strong></span>
</div>

## 读完这一类，应能回答

- 什么训练目标真正优化接受率，而不只是 next-token accuracy？
- 什么时候在线适应的收益能覆盖更新成本？
- 一个 drafter 能否跨 checkpoint、语言和 tokenizer 迁移？

## 推荐阅读路线

1. **[Speculative Decoding with Big Little Decoder](../papers/02-independent-drafters-alignment-selection/2023--big-little-decoder.md)** — NeurIPS 2023，2023。
2. **[DistillSpec: Improving Speculative Decoding via Knowledge Distillation](../papers/02-independent-drafters-alignment-selection/2023--distillspec.md)** — ICLR 2024，2024。
3. **[Learning Harmonized Representations for Speculative Sampling](../papers/02-independent-drafters-alignment-selection/2025--hass-iclr-2025.md)** — ICLR 2025，2025。
4. **[Speculative Decoding and the Curse of Multilinguality](../papers/02-independent-drafters-alignment-selection/2026--curse-of-multilinguality.md)** — arXiv preprint，2026。

## 全部精读

| 年份 | 论文 | Venue | 核读页码 |
|---:|---|---|---:|
| 2023 | [Accelerating LLM Inference with Staged Speculative Decoding](../papers/02-independent-drafters-alignment-selection/2023--staged-speculative-decoding.md) | ICML 2023 workshop / arXiv | 1-6 |
| 2023 | [Speculative Decoding with Big Little Decoder](../papers/02-independent-drafters-alignment-selection/2023--big-little-decoder.md) | NeurIPS 2023 | 1-21 |
| 2024 | [DistillSpec: Improving Speculative Decoding via Knowledge Distillation](../papers/02-independent-drafters-alignment-selection/2023--distillspec.md) | ICLR 2024 | 1-40 |
| 2024 | [Online Speculative Decoding](../papers/02-independent-drafters-alignment-selection/2024--online-speculative-decoding-icml-2024.md) | ICML 2024 | 1-16 |
| 2025 | [Learning Harmonized Representations for Speculative Sampling](../papers/02-independent-drafters-alignment-selection/2025--hass-iclr-2025.md) | ICLR 2025 | 1-22 |
| 2026 | [Not-a-Bandit: Provably No-Regret Drafter Selection in Speculative Decoding for LLMs](../papers/02-independent-drafters-alignment-selection/2026--not-a-bandit-iclr-2026.md) | ICLR 2026 | 1-27 |
| 2026 | [Speculative Decoding and the Curse of Multilinguality](../papers/02-independent-drafters-alignment-selection/2026--curse-of-multilinguality.md) | arXiv preprint | 1-15 |

<div class="kb-footer-cta" markdown>

### 继续横向比较

读完单篇后回到方法矩阵，检查正确性保证、proposal 结构和系统工作区间是否可直接比较。

[打开跨论文比较](../COMPARISON.md){ .md-button .md-button--primary }
[返回全部目录](../README.md){ .md-button }

</div>
