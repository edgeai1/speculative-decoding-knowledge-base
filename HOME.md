---
title: 首页
description: 截至 2026-08-10 的 Speculative Decoding 研究地图与 66 篇核心论文全文精读。
hide:
  - navigation
  - toc
---

<section class="kb-hero" markdown>

<div class="kb-hero__content" markdown>

<span class="kb-eyebrow">RESEARCH KNOWLEDGE BASE · 2026</span>

# 把 Speculative Decoding 的论文森林，变成一张可以行动的地图

从严格采样理论到 DSpark、DFlash 与生产级调度：这里不是摘要合集，而是一套可追溯、可比较、可复现的中文研究知识库。

[浏览 66 篇精读](README.md){ .md-button .md-button--primary }
[查看研究空白](landscape/research-gaps-shortlist.md){ .md-button }

</div>

<div class="kb-hero__signal" aria-hidden="true">
  <div class="kb-signal__ring kb-signal__ring--one"></div>
  <div class="kb-signal__ring kb-signal__ring--two"></div>
  <div class="kb-signal__core">q → p</div>
  <span class="kb-token kb-token--a">draft</span>
  <span class="kb-token kb-token--b">verify</span>
  <span class="kb-token kb-token--c">accept</span>
</div>

</section>

<div class="kb-stats" markdown>

<div class="kb-stat"><strong>66</strong><span>篇核心论文</span></div>
<div class="kb-stat"><strong>1,188</strong><span>页全文核读</span></div>
<div class="kb-stat"><strong>6</strong><span>条研究主线</span></div>
<div class="kb-stat"><strong>1,260</strong><span>条高召回候选</span></div>

</div>

## 先选你的入口

<div class="grid cards" markdown>

-   :material-map-search:{ .lg .middle } __第一次进入方向__

    ---

    用统一的 proposal—verification—serving 抽象建立全局坐标，再沿时间线理解问题如何演化。

    [:octicons-arrow-right-24: 打开方法谱系](TAXONOMY.md)

-   :material-flask-outline:{ .lg .middle } __准备做算法研究__

    ---

    横向比较 joint proposal、严格校正、树验证与 lossy verifier，直接进入尚未解决的问题。

    [:octicons-arrow-right-24: 查看跨论文比较](COMPARISON.md)

-   :material-server-network:{ .lg .middle } __准备做系统研究__

    ---

    聚焦 batch、KV、MoE、动态预算、SLA 与真实 serving，避免被 batch=1 的最高数字误导。

    [:octicons-arrow-right-24: 进入 Serving 专题](collections/06-serving-security.md)

-   :material-scale-balance:{ .lg .middle } __核对 Lossless / Lossy__

    ---

    区分 greedy-exact、distribution-preserving、模型保持与有界近似，明确每个速度数字的正确性代价。

    [:octicons-arrow-right-24: 打开术语与边界](GLOSSARY.md)

</div>

## 六条研究主线

<div class="kb-track-grid" markdown>

<a class="kb-track kb-track--01" href="collections/01-foundations/">
  <span class="kb-track__num">01</span>
  <strong>基础、理论与综述</strong>
  <small>9 篇 · 从 blockwise 到严格 speculative sampling</small>
</a>

<a class="kb-track kb-track--02" href="collections/02-independent-drafters/">
  <span class="kb-track__num">02</span>
  <strong>独立 Drafter 与对齐</strong>
  <small>7 篇 · 蒸馏、在线适应与跨语言边界</small>
</a>

<a class="kb-track kb-track--03" href="collections/03-feature-mtp/">
  <span class="kb-track__num">03</span>
  <strong>Feature Head、MTP 与并行块</strong>
  <small>20 篇 · EAGLE、DFlash、Domino、DSpark</small>
</a>

<a class="kb-track kb-track--04" href="collections/04-tree-verification/">
  <span class="kb-track__num">04</span>
  <strong>Tree、多候选与 Verification</strong>
  <small>9 篇 · 分支覆盖、残差账本与近似验证</small>
</a>

<a class="kb-track kb-track--05" href="collections/05-self-spec-long-context/">
  <span class="kb-track__num">05</span>
  <strong>Training-free、自推测与长上下文</strong>
  <small>10 篇 · 检索复用、KV 稀疏与 million-token</small>
</a>

<a class="kb-track kb-track--06" href="collections/06-serving-security/">
  <span class="kb-track__num">06</span>
  <strong>Serving、基准、安全与应用</strong>
  <small>11 篇 · Goodput、攻击、RL rollout 与 MoE</small>
</a>

</div>

## 当前研究前沿

!!! tip "最值得进入的交叉点"

    2026 年的核心冲突不再是“再训练一个更小的模型”，而是如何同时获得 **可精确计算的 joint proposal、严格 verification、硬件成本感知的动态预算**。本库推荐从“严格可校正的半并行 joint drafter + non-anticipating block scheduler”切入。

=== "算法优先"

    设计一次或常数次 forward 即可计算规范化联合概率的并行 proposal，并与 Block Verification / 多候选树组合；先通过 toy-vocabulary distribution gate，再追求速度。

=== "系统优先"

    在真实 arrival、异长 context、MoE expert union 和多 SLA 下，为全 batch 动态分配 verification 节点，并给出 non-anticipating 或 regret 保证。

=== "快速成题"

    围绕 acceptance-collapse 做请求级 cost isolation：低收益自动回退 AR、共享 batch 风险隔离、最坏额外成本上界与 false fallback 评估。

[阅读完整研究建议](COMPARISON.md){ .md-button .md-button--primary }

## 每个结论如何进入知识库

```mermaid
flowchart LR
  A[高召回检索<br/>1,260 条候选] --> B[相关性筛选<br/>66 篇核心]
  B --> C[逐页全文核读<br/>1,188 页]
  C --> D[实现级解读<br/>公式·流程·局限]
  D --> E[一致性审计<br/>版本·页码·SHA-256]
  E --> F[跨论文比较<br/>研究空白]
```

<div class="kb-footer-cta" markdown>

### 不从摘要开始，从问题开始

进入论文目录，按研究问题而不是发表年份阅读；每篇解读都保留官方入口、已读版本、页码与哈希。

[开始阅读](README.md){ .md-button .md-button--primary }
[查看证据标准](METHODOLOGY.md){ .md-button }

</div>
