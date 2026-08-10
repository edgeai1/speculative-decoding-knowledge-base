---
id: 2024--sequoia
title: "SEQUOIA: Scalable and Robust Speculative Decoding"
authors: [Zhuoming Chen, Avner May, Ruslan Svirschevski, Yuhsun Huang, Max Ryabinin, Zhihao Jia, Beidi Chen]
year: 2024
venue: arXiv preprint
status: deep_read_complete
primary_source: https://arxiv.org/abs/2402.12374
version_read: arXiv:2402.12374v3
pages_read: 1-27
pdf_sha256: 4e93904ae0a2a8b1813767e8a67c6709833b8affd60aff927c30619c37e4e7f8
---

# SEQUOIA 精读

## 两个独立贡献

SEQUOIA 同时优化 **树的拓扑** 和 **一个 parent下多 child的采样/验证**。前者解决独立序列树随预算饱和；后者解决 SpecInfer在低温度反复抽到同一个错误高 q token、top-k在高温度覆盖不足的问题。

## DP最优树

在 positional acceptance假设下，第 k个 child被接受概率只依赖 rank k，记向量 `p_k`。节点 v的存活分数是路径上各 child-rank概率乘积 `f(v)=∏p_i`，整树预计每轮生成 `F(T)=Σ_v f(v)`。DP状态 `T[n,b]` 表示 n节点、根有b个孩子的最佳值，递推把第b个 child子树大小 m分出：

`T[n,b]=max_m T[n-m,b-1]+P[b] max_j T[m,j]`。

可扩展最大深度和 depth-dependent acceptance matrix；离线运行，推理只用固定拓扑。在 rejection probability具 power-law时，最优树预计生成量下界近 `Ω(b log n/log log n)`；该结论依赖位置/rank同质假设，实际上下文自适应树可能更好。

## Without-replacement verifier

在同一 parent依次从 q不放回采样。候选拒绝后将其 q质量清零，并把 target residual更新为 `norm((R-D)_+)`；q支持耗尽则在未尝试词上均匀。它满足单候选 optimal-transport property（接受 `1-TV(p,q)`）和 cover property（覆盖 target support时有限候选必接受），而 SpecInfer/SpecTr只具前者、朴素 top-k只具后者。残差校正证明保持 target distribution。

## 结果与系统含义

A100上 Llama2-7/13B、Vicuna33B最高 `4.04×/3.73×/2.27×`；L40单卡offload Llama3-70B约 .60 s/token、相对 DeepSpeed-Zero-Inference `9.5×`。tree512相对16条独立序列平均多生成约33%。低温/高温均优于对比 verifier。巨大 offload倍数源于一次权重搬运可验证大树，不能外推到常驻GPU高batch。

## 复现与局限

先在校准集按 depth/rank估 acceptance matrix，DP生成树；draft按拓扑和 without-replacement构造节点；target tree attention；严格 residual verifier。报告 tree size/depth、draft steps、unique nodes、温度与 target pass曲线。静态平均 acceptance忽略上下文；大树增加KV/attention与continuous-batch干扰；uniform fallback词表操作需高效。EAGLE-2等后来用请求级confidence动态树，系统上补齐此处静态性。

原文第 3–7 页DP和鲁棒验证，第 7–11 页端到端/树扩展，第 12–27 页证明、伪码和更多硬件结果。
