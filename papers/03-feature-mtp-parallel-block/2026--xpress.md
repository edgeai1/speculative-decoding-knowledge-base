---
id: 2026--xpress
title: "xPress: Parallel Refinement for Diffusion Drafters in Speculative Decoding"
authors: [Zheng Wang, Davis Wertheimer, Yu Chin Fabian Lim, Mudhakar Srivatsa, Raghu K. Ganti, Minjia Zhang, Naigang Wang]
year: 2026
venue: arXiv preprint
status: deep_read_complete
primary_source: https://arxiv.org/abs/2608.02438
version_read: arXiv:2608.02438v1 (2026-08-03)
pages_read: 1-16
pdf_sha256: 3062447be736f1a4d6ee94a6ddb06c1fa98a75828035642d42009a980542b1e1
---

# xPress 精读

## 核心思想

xPress 不用 DSpark式逐 token loop，而给 DFlash block加一个低秩 causal refiner，再用 Jacobi同时更新所有位置约6轮。refiner输入每位置 hidden、全 block mean hidden和上一 token id，均投到 r=256；严格下三角、按 channel的线性 mixer传播 prefix信号，r-space MLP后由低秩 head输出 additive logit bias。它定义了因果 `p_r(x_1:B|h)=∏p_k(x_k|x_<k,h)`，却能整块矩阵化更新。

Jacobi从 DFlash argmax block开始，第 j轮所有 k并行用上一轮 prefix重算。因依赖严格因果且 hidden固定，第1位置一轮固定、第k位置至多k轮固定；唯一 tie规则下最多 B轮等于顺序 greedy fixed point。实践约6轮已达到15步 sequential refinement的接受长。注意这是 greedy fixed-point证明，不自动证明有限轮随机 sampling的 proposal与顺序分布相同。

训练用三项：teacher-forced refiner loss、保持 base drafter不漂移的 anchor loss、以 drafter argmax自条件再跑一次的 consistency loss。每项含 hard CE + target/draft L1(TV)并对早位置指数加权。Qwen3-8B/DFlash block16/Open-PerfectBlend，AdamW `6e-4`；与 Markov head用同数据/步数公平比较。

七个 math/code/chat基准，接受长平均约 +30%、最高 +56%，T=1也约 +19–58%；端到端相对原 DFlash约 `1.3×`、最高 `1.7×`。多轮 refiner虽并行仍有 kernel/LM低秩投影成本，最优轮数依硬件和 block。严格 target output需外层 standard verifier；公开结果的 stochastic实现应区分 deterministic Jacobi seed与 q probability。

复现需验证 lower-triangular mixer无未来泄漏、固定 hidden、tie规则、每轮变化率；分别报告 K=1…B的 τ/latency及三项loss消融。研究空间包括 learned early stop、随机Jacobi的精确校正、refiner量化和跨block状态。原文第 4–9 页架构/定理，第 9–13 页训练实验，第 14–16 页补充。
