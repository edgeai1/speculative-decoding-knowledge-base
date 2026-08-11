---
title: "05 Training-free、自推测与长上下文"
description: "无需独立神经 drafter 或专门训练，利用跳层、自身稀疏 KV、历史检索与窗口化 MTP，应对长上下文中的 KV 读取税。"
---

# 05 Training-free、自推测与长上下文

<div class="kb-section-lead" markdown>

无需独立神经 drafter 或专门训练，利用跳层、自身稀疏 KV、历史检索与窗口化 MTP，应对长上下文中的 KV 读取税。

</div>

<div class="kb-inline-stats">
  <span><strong>10</strong> 篇核心论文</span>
  <span><strong>182</strong> 页核读</span>
  <span>更新至 <strong>2026</strong></span>
</div>

## 读完这一类，应能回答

- 如何让 self-draft 变快而不破坏完整 target cache？
- 长上下文中应该使用 window、retrieval、sparse KV 还是层级 proposal？
- 历史复用带来的内存、隐私、污染与租户隔离成本是什么？

## 推荐阅读路线

1. **[Draft & Verify: Lossless Large Language Model Acceleration via Self-Speculative Decoding](../papers/05-training-free-self-spec-long-context/2024--draft-verify-self-speculative-decoding-acl-2024.md)** — ACL 2024，2024。
2. **[TriForce: Lossless Acceleration of Long Sequence Generation with Hierarchical Speculative Decoding](../papers/05-training-free-self-spec-long-context/2024--triforce.md)** — COLM 2024，2024。
3. **[MagicDec: Breaking the Latency-Throughput Tradeoff for Long Context Generation with Speculative Decoding](../papers/05-training-free-self-spec-long-context/2024--magicdec.md)** — ICLR 2025，2024。
4. **[LongSpec: Long-Context Lossless Speculative Decoding with Efficient Drafting and Verification](../papers/05-training-free-self-spec-long-context/2025--longspec.md)** — arXiv preprint，2025。
5. **[Windowed-MTP: Removing the Full-Context Draft-KV Tax at Million-Token Context](../papers/05-training-free-self-spec-long-context/2026--windowed-mtp.md)** — arXiv preprint，2026。

## 全部精读

| 年份 | 论文 | Venue | 核读页码 |
|---:|---|---|---:|
| 2024 | [Break the Sequential Dependency of LLM Inference Using Lookahead Decoding](../papers/05-training-free-self-spec-long-context/2024--lookahead-decoding-icml-2024.md) | ICML 2024 | 1-20 |
| 2024 | [Draft & Verify: Lossless Large Language Model Acceleration via Self-Speculative Decoding](../papers/05-training-free-self-spec-long-context/2024--draft-verify-self-speculative-decoding-acl-2024.md) | ACL 2024 | 1-20 |
| 2024 | [MagicDec: Breaking the Latency-Throughput Tradeoff for Long Context Generation with Speculative Decoding](../papers/05-training-free-self-spec-long-context/2024--magicdec.md) | ICLR 2025 | 1-16 |
| 2024 | [REST: Retrieval-Based Speculative Decoding](../papers/05-training-free-self-spec-long-context/2024--rest-naacl-2024.md) | NAACL 2024 | 1-14 |
| 2024 | [SuffixDecoding: Extreme Speculative Decoding for Emerging AI Applications](../papers/05-training-free-self-spec-long-context/2024--suffixdecoding.md) | NeurIPS 2025 | 1-22 |
| 2024 | [TriForce: Lossless Acceleration of Long Sequence Generation with Hierarchical Speculative Decoding](../papers/05-training-free-self-spec-long-context/2024--triforce.md) | COLM 2024 | 1-16 |
| 2025 | [LongSpec: Long-Context Lossless Speculative Decoding with Efficient Drafting and Verification](../papers/05-training-free-self-spec-long-context/2025--longspec.md) | arXiv preprint | 1-19 |
| 2025 | [SpecExtend: A Drop-in Enhancement for Speculative Decoding of Long Sequences](../papers/05-training-free-self-spec-long-context/2025--specextend.md) | arXiv preprint | 1-12 |
| 2026 | [Oilbird: Training-Free Speculative Decoding with Keys the Verifier Already Computes](../papers/05-training-free-self-spec-long-context/2026--oilbird.md) | arXiv preprint | 1-18 |
| 2026 | [Windowed-MTP: Removing the Full-Context Draft-KV Tax at Million-Token Context](../papers/05-training-free-self-spec-long-context/2026--windowed-mtp.md) | arXiv preprint | 1-25 |

<div class="kb-footer-cta" markdown>

### 继续横向比较

读完单篇后回到方法矩阵，检查正确性保证、proposal 结构和系统工作区间是否可直接比较。

[打开跨论文比较](../COMPARISON.md){ .md-button .md-button--primary }
[返回全部目录](../README.md){ .md-button }

</div>
