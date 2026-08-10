---
id: 2026--revisiting-lossy-verification
title: "Revisiting Lossy Verification in Speculative Decoding: Mechanisms, Trade-offs, and Failure Modes"
authors: [Tianyu Wang, Yuxuan Zhou, Wenbin Wang, Heng Li, Zikai Xiao, Junyuan Shang]
year: 2026
venue: arXiv preprint
status: deep_read_complete
primary_source: https://arxiv.org/abs/2607.26627
version_read: arXiv:2607.26627
pages_read: 1-20
pdf_sha256: e318afa118a808823c7e2613f4f3ea23bc7150ba764ad8c227f74129f9b151e3
---

# Revisiting Lossy Verification 精读

## 核心价值

这篇不是再提一个阈值，而是推导 lossy verifier实际诱导的分布，把看似不同方法归为两类：**truncation-based**（只允许 target“典型/高概率”集合中的 draft token）与 **collaborative**（以 draft和target共同构造一个新验证目标）。结论是速度来自主动重写分布，必须与该新分布的真正直接采样基线比较。

## 两类机制与失败模式

Typical acceptance等 truncation规则常被口头解释为“近似 target truncation sampling”，但 sequential accept/reject、draft proposal和首错 residual共同诱导的分布并不等于先对 target做 top-p/typical truncation再采。论文构造诊断任务显示，它甚至可显著差于真正 truncation baseline；因此质量下降不能简单归因于“少了尾部概率”。

Collaborative verifier可等价为从某个融合分布采样。关键风险不是抽象的 p/q距离，而是 draft对低质量 token的概率 **overshoot** target：放宽 `min(1,p/q)`后，这部分过量质量容易直接进入输出。控制 `q/p`过冲比单纯增加 target权重或全局lenience更稳定；表中消融显示同速度附近质量可大幅不同。

## 如何使用本论文

评 lossy SD至少有四条 baseline：strict target sampling；相同 target truncation的直接采样；相同 collaborative目标的直接采样；对应SD实现。分别报告与哪个分布的KL/TV、任务质量、speed/τ，并覆盖低熵 factual、math/code和高熵creative。只与原 greedy/target质量比较会混淆 decoding-policy改变与 speculative实现误差。

论文的诊断仍受选定模型、judge和任务限制，不能证明所有放宽都必然差；它提供的是分布分析工具。对 MARS/ASD这类 greedy regret verifier，还需另建 trajectory-regret框架。官方 `ZhouYuxuanYX/Fast-HSD`。原文第 2–5 页统一推导，第 5–10 页 collaborative overshoot，第 10–15 页 truncation陷阱，第 16–20 页补充。
