---
id: 2025--block-verification-iclr-2025
title: "Block Verification Accelerates Speculative Decoding"
authors: [Ziteng Sun, Uri Mendlovic, Yaniv Leviathan, Asaf Aharoni, Jae Hun Ro, Ahmad Beirami, Ananda Theertha Suresh]
year: 2025
venue: ICLR 2025
status: deep_read_complete
primary_source: https://openreview.net/forum?id=frsg32u0rO
version_read: ICLR 2025 paper
pages_read: 1-30
pdf_sha256: e328b76b55cebeab8cfa6a5828ac675ffc1a7137e8759c456b66259bccb7c250
---

# Block Verification 精读

## 反直觉核心

标准 token verifier在第一个拒绝处 `break`，即使 target已经并行算完整个 block。Block Verification为每个 prefix长度 i独立产生接受事件，最后选 **最长被接受子块**；事件概率与 residual经过联合设计，仍精确保持 target分布。它证明在论文定义的可插拔 verifier信息/接口类中，期望每固定轮数生成 token数最优，且不劣于标准算法。

## 算法

对已采 draft `X_1:γ`，递推 prefix保留上界

`p_i=min(p_{i-1}·M_b(X_i|c,X_<i)/M_s(X_i|c,X_<i),1)`，`p_0=1`。

每个 i用论文式(5)的 `h_i^block`独立判定，遍历不在拒绝时停止，τ取成功事件最大 i。若 τ<γ，校正分布为

`r_i(x) ∝ max(p_i M_b(x|prefix_i)-M_s(x|prefix_i),0)`；

全接受则从 target下一个分布采 bonus。与 token residual `(p-q)_+`相比，多出的 `p_i`正是联合 prefix被保留概率的质量账本。

Theorem 1证明有效性；Theorem 2证明任何接收 draft prefix并加一个 correction token、仅使用 sample path上 p/q 的 valid verifier，在任意迭代数下其期望累计生成量不超过 Block Verification。保证不是“所有可能解码算法的绝对最优”：若改变外层状态/让后续轮依赖accept history，可构造其他过程，论文附录也讨论 greedy block变体。

## 实验与实践

PaLM2 S/XXS/XXXS和 SpecBench/Vicuna上，相对标准 token verifier额外 wall-clock约 `5%–8%`，block efficiency更稳定提高；γ增大理论接受继续增但实际速度在4或更近位置峰值，因 target块计算增长。实现只改采样逻辑，无额外 target forward，是很适合作为默认的“低风险小增益”。

复现必须使用同一 draft samples/p/q配对比较，注意式(5)数值稳定、`p_i`和 residual归一；用Monte Carlo验证序列分布。树、多候选、并行 marginal proposal能否直接套用需重新确认其 q factorization与接口，不可只复制伪码。原文第 2–6 页算法/直觉，第 6–8 页定理，第 8–11 页结果，第 12–30 页完整证明。
