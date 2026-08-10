---
id: 2023--staged-speculative-decoding
title: "Accelerating LLM Inference with Staged Speculative Decoding"
authors: [Benjamin Spector, Christopher Ré]
year: 2023
venue: ICML 2023 workshop / arXiv
status: deep_read_complete
primary_source: https://arxiv.org/abs/2308.04623
version_read: arXiv:2308.04623v1
pages_read: 1-6
pdf_sha256: 138febf14cb78afc03cb9e9ffac4fad48649986e60d80b4150c4e1f42ea92590
---

# Staged Speculative Decoding 精读

## 核心定位

本文将 speculation 递归化：oracle 由小 Transformer 起草，小 Transformer 又由 n-gram 起草；同时把长单链候选改成宽树。GPT-2-Large 762M / 40M GPT-2 / Katz trigram 在 RTX 4090、HumanEval 上，greedy 475 tok/s（3.16× AR、1.36× vanilla SD），top-k sampling 298 tok/s（1.98× AR）。

## 1. 为什么树比长链好

长链全部依赖早期 token，命中概率随深度快速衰减。把相同 node budget 从深部移到浅部、加入第 2/3 高概率分支，可提升目标路径被覆盖的概率。树的内部节点才需要 drafter forward，叶子候选近似“免费”；同一深度 nodes 又能 batch，使小模型生成树的串行步数接近 tree depth。

target tree verification 通过 position ids 与 tree-causal mask 完成：每个节点只看祖先；候选 KV 单独存储，验证后仅把采样路径对应 slices 追加主 KV。这是后来 SpecInfer/Medusa tree attention 的核心工程模式。

## 2. 第二级 speculation

常规 SD 构造大 candidate batch 时，drafter 可能反过来占主要时间。因此加第三个 `draft2` 加速 drafter，形成 oracle→draft→n-gram 的 cascade。每一级仍由上一级验证；采用合法 rejection sampling 时最终 oracle distribution 不变。最底层 Katz trigram 从 40M model 在 T=1.5 生成的 120M tokens 训练。

## 3. 实验解读

目标 GPT-2-L 762M、draft 40M，Python Stack fine-tune，164 HumanEval prompts，RTX 4090。相对内存带宽：greedy vanilla SD .31、staged .23；top-k 分别 .48/.35。吞吐：AR 150，vanilla 350/219，staged 475/298 tok/s（greedy/top-k k=50,T=1）。实现仍有约 35% Python overhead。

单 prompt 收益分布很宽，现实样本约 2× 到 10×；空白/缩进等低熵 token 可从 n-gram 阶段通过，控制流后的关键高熵 token 往往需 oracle。这不是模型层“难度标签”的严格证明，只是 origin visualization。

## 4. 局限与复现

- 很短的 6 页 workshop paper；tree construction heuristic/batch size 细节主要依赖代码，消融不足。
- 仅 762M code model、batch=1 和单 4090，不能外推 70B 或高并发。
- tree nodes 与 staging 增加 FLOPs/cache/控制流；必须计入 tree build、mask、KV gather。
- top-k 的分布保持需确保每一级都对调整后的 sampling distribution 正确校正。

复现时先实现单层 tree verification 的路径一致性，再加入 draft2；分别关闭 tree 与 stage 做 2×2 消融，并报告 target nodes、draft passes、带宽、吞吐和 Python/kernel overhead。

## 审读导航

- 第 2–3 页：roofline、tree mask/KV、staging。
- 第 3–4 页：模型、数据、完整吞吐/带宽结果。
- 第 4–5 页：样本差异、限制与未来方向。

## 原始来源

- https://arxiv.org/abs/2308.04623

