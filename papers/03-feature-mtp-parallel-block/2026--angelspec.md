---
id: 2026--angelspec
title: "AngelSpec: Towards Real-World High Performance Inference with Speculative Decoding"
authors: [Hong Liu, Rui Cen, Junhan Shi, Guangshuo Qin, Jiebin Zhang, Tianyu Liu, Runzhi Fan, Guoliang Zhao, Ruobing Xie, Kai Zhang, Song Liu, Guanghua Yu, Jianchen Zhu]
year: 2026
venue: arXiv preprint
status: deep_read_complete
primary_source: https://arxiv.org/abs/2607.25852
version_read: arXiv:2607.25852v2 (2026-07-29)
pages_read: 1-26
pdf_sha256: 5eac19e3ac72136bdeab1f4d18e83c9e7a99ec34babe63514b812efebb69e324
---

# AngelSpec 精读

## 论文定位

AngelSpec 不是单一算法，而是 Tencent/Hy3 的训练与 serving方案：高熵开放对话使用轻量 MTP；可预测的 code/math 使用长 block diffusion；新 DFly drafter和 D-cut scheduler分别改善草稿质量与负载自适应验证。它的核心判断是“不存在所有 workload 都最优的统一 drafter”。

## DFly 与训练目标

DFly 将 DFlash 的 shared context和每层不同 target views结合成 hybrid conditioning backbone；其 hidden-correction head输入本位置 draft hidden与具体 predecessor embedding，经 SwiGLU修正 hidden再过 LM head，比固定低秩 Markov transition更上下文相关。主体 5 层/block8并行，只有很小 correction顺序。

训练先以 D-PACE动态位置权重的 hybrid LK loss冷启动：用 supervised token confidence构造“该深度及以后 prefix存活”的乘积权重，detach后加权每位置 loss；模型已对齐后改用 end-to-end TV objective，直接优化多深度预计接受。数据也按结构专门化：MTP吃广泛 conversation，DFly补500k code+200k math且由 Hy3重生成；16-token overlap过滤评测泄漏。thinking/no-thinking hidden分布不同，匹配训练测试 τ 4.79，错配可降到3.29，因此分别部署 checkpoint。

Qwen3-8B T=1/no-thinking 六任务 τ：MTP 3.24、DFlash4.57、DSpark5.32、DFly5.41；Hy3-A21B MTP3.00、DFlash3.69、DFly4.79。Hy3消融 DFlash3.77→DFly backbone4.40→Markov4.56→hidden4.60→领域数据4.75。增加 5→7 draft layers无收益，block5→8明显提高。

## D-cut serving

对请求 i、保留深度 n，预计推进 `1+Σ_{k≤n}∏_{t≤k}c_it`。D-cut把所有请求的 prefix-survival score排序，只选保持 prefix闭包的 top-K；K不固定，而在 `{25,50,75,100%}` budgets中用启动时 profile 的 runtime table比较“预计 batch progress/step latency”。因此 verify是全 batch共享资源，低负载多留、高负载裁剪。这与 DSpark scheduler思想相近，AngelSpec采用较离散、部署友好的预算搜索。

Hy3-A21B concurrency 4–64，DFly在所有点达到最高平均 throughput，相对 AR `1.98–2.40×`，比 DFlash高 `10.5–11.8%`；摘要的“接受长约 +30%”与 throughput增幅不能混用。输出分布仍由标准 rejection verifier保持。

## 局限与复现

工作同时改变数据、架构、loss、scheduler，必须按消融区分贡献；Hy3与线上 kernel公开程度限制独立复现；双 checkpoint增加运维和请求路由错误成本；confidence与profile会随领域/负载漂移。官方 `Tencent/AngelSpec` 与文档可复现公开部分。应报告 workload router、thinking mode、τ、draft/verify latency、concurrency与 budget分布。可研究软 mixture而非硬路由、在线 domain识别、公平SLA调度和跨模式通用 drafter。

原文第 2–6 页 MTP训练，第 6–12 页 DFly，第 12–17 页 D-cut，第 17–26 页系统实验与附录。
