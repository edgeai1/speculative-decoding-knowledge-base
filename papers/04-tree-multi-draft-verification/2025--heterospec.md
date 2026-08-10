---
id: 2025--heterospec
title: "HeteroSpec: Leveraging Contextual Heterogeneity for Efficient Speculative Decoding"
authors: [Siran Liu, Yang Ye, Qianchao Zhu, Zane Cao, Yongchao He]
year: 2025
venue: arXiv preprint
status: deep_read_complete
primary_source: https://arxiv.org/abs/2505.13254
version_read: arXiv:2505.13254
pages_read: 1-17
pdf_sha256: 61d4d309f104bee98082a157cfe83aa434dcca4fefdcb23b957375031a9279bb
---

# HeteroSpec 精读

## 核心思想

HeteroSpec 在 EAGLE-3动态树之上观察到 verification heterogeneity：少数高置信节点贡献多数被接受路径，统一 depth/pruning会浪费 target节点。它以 draft分布熵衡量当前上下文复杂度，按数据分位 stratify请求，再为不同层联合选择 draft depth与pruning threshold；无需重训。

方法先 profile entropy/terminal confidence rank与最大接受长关系：低熵请求可走深而窄，高熵请求需要更保守预算。在线 quantifier将请求落入复杂度层，查/调每层 `(depth,threshold)`；树节点仍按路径 acceptance value排序，target一次 tree verification。正确性来自未改变标准 verifier：裁掉候选只降低proposal coverage，不改变 target residual。

四个 LLM、五基准摘要报告平均 `4.24×` decoding speedup并称胜 EAGLE-3；这一表述需结合正文确认是“相对 AR达到4.24×”，而不是“比 EAGLE-3再快4.24倍”。主要证据是相同 backbone下自适应比固定超参减少节点且保持接受长；跨硬件 profile迁移是风险。

实现应记录 entropy定义/temperature、strata边界、每层depth/threshold、实际节点和 target kernel曲线；与固定同平均budget比较。局限是 entropy未必预测 p/q重叠、静态分位会领域漂移、每请求动态形状影响 batching。它可视为 DSpark/D-cut之前的请求异质性调度，但没有后者显式 engine SPS和全 batch效用目标。

原文第 3–4 页现象，第 4–7 页复杂度与自适应框架，第 7–12 页结果/消融，第 13–17 页细节。

## 控制器应如何复现

离线阶段应在代表性请求上记录每一轮 draft entropy、树深、pruning threshold、实际节点、接受长和各 kernel 时间，再为每个复杂度分层选择端到端时延最低而非接受率最高的配置。在线阶段只允许使用当前可见的 proposal 统计，不能偷看本轮 target 结果；配置查表后仍需设全局节点上限，防止高熵请求生成异常大树。熵的计算必须注明是首节点、整层均值还是路径加权值，并固定 temperature，因为这三点都会改变分层边界。

公平比较应让固定配置基线拥有相同平均节点预算，并单独报告“oracle 知道真实难度”的上界，避免把额外 target work 当作自适应收益。部署中还要测分层阈值从校准域迁移到代码、数学、对话后的漂移，以及 continuous batch 中不同树形状造成的 padding 和图捕获代价。一个直接反例是高熵但多个候选都被 target 接受的上下文：熵高不必然表示低 overlap，因此更强控制器应直接预测单位验证成本带来的可提交 token。
