---
id: 2026--dflash-icml-2026
title: "DFlash: Block Diffusion for Flash Speculative Decoding"
authors: [Jian Chen, Yesheng Liang, Zhijian Liu]
year: 2026
venue: ICML 2026
status: deep_read_complete
primary_source: https://arxiv.org/abs/2602.06036
version_read: ICML 2026 proceedings
pages_read: 1-13
pdf_sha256: ffa514e6ce180eb1f7a39c49372f3b8170b99f8bc142d4a4daa0f087bf2ceb91
---

# DFlash 精读

## 核心思想

DFlash 用 3–8 层轻量 block-diffusion adapter 一次预测 10–16 个位置，彻底去掉 EAGLE 的逐 token draft loop；关键不是单独训练一个 diffusion LM，而是把目标模型多个层的 context features 持久注入 **每一层 drafter 的 KV**。目标知识提高草稿质量，并行块保持低延迟，论文在 Qwen3 上最高 `6.1×` lossless 加速。

## 架构和训练

目标 prefill/上一轮校验产生 anchor token，同时从浅到深均匀抽 5 层 hidden，拼接投影、RMSNorm 得 `H_ctx`。每个 draft layer 将其投影后与 block hidden 一起组成 K/V：`K_i=[W_i^K H_ctx;W_i^K H_d]`，V 同理。与只在输入融合一次相比，KV injection 防止深层稀释 target signal。输入为 anchor 加 masks，block 内双向 attention，一次输出所有位置；共享且冻结 target embedding/LM head。

训练序列由 target 重新生成。随机选 response anchors，将每个 anchor 后的 block mask；不同块互不可见、块内双向可见、均可见相应 target context，使用 FlexAttention 一次训练多个块。早期错误会废掉后缀，因此第 k 位 CE 权重 `w_k=exp(-(k-1)/γ)`。约 800k Nemotron-v2+CodeAlpaca 样本；默认 Qwen 5 层/block16，Coder 8 层，LLaMA block10。固定每序列 anchor 数使长上下文成本有界。

## 校验与实验

一轮成本 `L=(T_draft+T_verify)/τ`。DFlash 的 `T_draft` 对中等 block 基本不随 γ 线性增长，因而可用更深 drafter；但各 mask 的最终 token 是同一 prefix 条件下的边缘预测，尚无候选内因果性。候选仍由目标模型逐前缀接受并做 residual rejection，因此输出分布由 verifier 保持，而不是 diffusion head 自身保证。

H200/Transformers、T=0 时 Qwen3-4B/8B 七任务均值约 `4.91×/τ6.54` 与 `4.86×/6.49`；T=1 为 `4.24×/5.69`、`4.03×/5.48`。EAGLE-3 tree16 仅约 1.7–1.8×，tree60 约 2×，但不同 head 训练与 kernel 仍影响公平性。Thinking 模式约 3.6–4.6×。SGLang/B200/FA4 在 concurrency 1–32 均有收益，Qwen3-8B Math500 从 `5.1×` 降至 `2.8×`，说明并发增大仍侵蚀优势。

深度消融：8 层接受长最高，5 层平均 speedup 最佳；5 个 target features 优于 3 个但离线存储更大。4K 训练的 base 在 16–32K 退化，用 1.6k LongAlign-10K 样本微调 3 epochs 可恢复，不能据此声称天然长上下文泛化。

## 实现、局限与研究问题

实现需缓存 target features 与 draft KV、严格构造块间隔离 mask、保留每位置 proposal logits供随机校正，并测 context fusion/draft/verify/cache 各阶段。官方项目 `dflash.z-lab.ai` 提供代码和模型。

局限是每个 target 专属训练和多层 feature 存储；平行 marginals 会产生“每词合理、组合不合理”的 block，chat/T=1 最明显；固定 block16 也会把低置信 suffix 塞入 batch。Domino、DSpark、TreeFlash、xPress 分别以顺序 head、调度、树和并行 refinement 修补这一缺陷。原文第 3–6 页为方法，第 6–9 页为结果/serving，第 9–13 页为消融和实现。
