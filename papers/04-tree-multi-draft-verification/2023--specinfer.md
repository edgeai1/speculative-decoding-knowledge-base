---
id: 2023--specinfer
title: "SpecInfer: Accelerating Large Language Model Serving with Tree-based Speculative Inference and Verification"
authors: [Xupeng Miao et al.]
year: 2023
venue: ASPLOS 2024
status: deep_read_complete
primary_source: https://arxiv.org/abs/2305.09781
version_read: arXiv:2305.09781 / ASPLOS 2024
pages_read: 1-18
pdf_sha256: 38764bfe741d39c9a309d1b715e8dc2cea6ea6c965337752b3562b1785afd9f1
---

# SpecInfer 精读

## 核心定位

SpecInfer 是早期把“多草稿序列”系统化为 token tree 的 serving系统：一个或多个小 speculator产生多条候选，共享前缀合成树；目标模型用 tree attention一次评分全部节点；tree-based parallel decoding再从多分支中接受路径。它同时覆盖分布式 target与 CPU/GPU offloading，是后来 Sequoia、SpecExec和 EAGLE树验证的直接系统前身。

## 方法与系统

论文的 learned speculator是小 Transformer/SSM式模型，可并行/分步产生多个候选；也支持不同小模型形成 ensemble。候选序列插入 trie去重。线性化树的 attention mask仅允许节点看祖先，position id按深度；目标 forward输出每节点在其真实 branch prefix条件下的 logits。runtime将 speculation与目标权重/层搬运重叠，并管理树 KV到 accepted path KV的映射。

验证不是“选 target分数最高的整条 beam”这么简单。对每个 parent可依次尝试多个 draft child，以 draft/target概率做拒绝校正，拒绝后更新 residual，最终从目标剩余分布采样，目标是保持 target token分布。多候选算法的正确性依赖尝试顺序、更新后的 q/p和 residual；简单从树中取任一命中会引入偏差。

## 实验证据

论文在 OPT等模型、分布式与 offloading设置中比较标准 decoding和单序列 speculation；树宽提高接受，但草稿、树 attention和cache开销随节点数增长。offloading时一次 target pass的权重 I/O远大于处理数百 token计算，故大树最划算；纯 GPU/较大batch的最佳树更小。论文另测多步 speculative sampling，可用已缓存树连续走多次，直到离开覆盖路径。

## 局限和复现

独立候选序列共享根后很快重复/分散，树规模扩大时预计接受长有上限；Sequoia后用DP最优分配节点。动态树 kernel、speculator ensemble和分布式通信使复现复杂。按今天标准还应补充 temperature/top-p下的统计正确性测试、continuous batching和严格 matched kernel baseline。

复现需实现：candidate trie与父索引；ancestor mask/深度 position；target tree forward；逐 parent的多候选 residual verifier；accepted path cache compact；分别 profile speculation、构树、目标、verification和通信。原文第 3–5 页 speculator，第 6–9 页 tree verifier，第 9–11 页系统，第 11–15 页实验，第 16–18 页细节。
