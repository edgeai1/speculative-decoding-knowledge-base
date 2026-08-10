---
id: 2026--global-resolution-iclr-2026-oral
title: "Global Resolution: Optimal Multi-Draft Speculative Sampling via Convex Minimization"
authors: [Rahul Krishna Thomas, Arka Pal]
year: 2026
venue: ICLR 2026 Oral
status: deep_read_complete
primary_source: https://openreview.net/forum?id=gpsczXOsHn
version_read: arXiv:2511.15898v1 / ICLR 2026
pages_read: 1-34
pdf_sha256: d6144c28e5ccf1883c23e88ebc057c8526f0f1bb70d22e491f5c6c3dec0c340d
---

# Global Resolution（ICLR 2026 Oral）精读

## 核心定位

SpecTr 的 multi-draft optimal-transport LP 有 `V^n` 级变量，理论最优但不可运行。本文针对 **n 个来自同一 draft distribution 的 i.i.d. token**，将指数 OTLP 先转为 max-flow，再借 polymatroid/互补松弛压到至多 V 维的截断凸优化；精度可由 `τ` 控制。Llama-3/Gemma-2 实验在 100ms/token 求解预算内把最优接受率推到约 90%，multi-step 端到端接近再提 2×。

## 1. 问题边界

研究的是 single-step multi-draft：同一位置并行采 `n≥2` 个 token，target score 每个候选后的下一分布；verification coupling 必须输出 target marginal，并最大化输出落在候选集合的概率。它不是直接设计候选 tree/head，也不是一般 `n` 个不同/相关 drafters 的完整解。

此前 SpecTr 的 OTLP 精确变量指数大；K-SEQ 只有 `1-1/e` 近似。canonical decomposition、importance sampling 和 subset selection 能给最优 acceptance value 的表述，却没有给可采样的完整 transport plan。本文先证明这些表述等价于一个仍指数大的 relaxed OTLP，再反向构造可恢复 coupling 的求解器。

## 2. 方法链条

1. 从 subset constraints 恢复 relaxed OTLP 的 max-flow 网络；source 到 draft multisets、再到 output vocabulary 的容量编码 membership feasibility。
2. 通过 complementary slackness 找出决定最优解的 active subset `H*`。
3. 利用 polymatroid 结构，source-edge feasible flow 可贪心近线性求得，不必显式枚举所有 multisets。
4. 把 outer residual 与 inner allocation 化为词表维凸问题；对低概率 vocabulary 截断，形成 Global Resolution。
5. 解出的 transport conditional 用来从给定候选 multiset 采 target-valid output；若命中候选，可复用对应 target continuation。

容差 `τ` 带来可量化近似：文中实现 target marginal 的 L1 偏差至多 `15τ`，接受率距最优至多 `10τ`。所以标题中的“optimal”是任意精度可逼近，而 `τ>0` 实现并非位级 exact。

## 3. 实验数字

模型对为 Llama-3 70B/8B 与 Gemma-2 27B/2B，改变 draft top-k 与候选数 n。接受率随 k 到约 1000 显著升高，此后边际下降；n 增大持续改善。i.i.d. 在 k≥100 时比 greedy candidate construction 高约 2%。

Llama-3 求解例：`(k,n)=(10,4)` 的通用 LP >4000ms/token，优化 max-flow 约 74ms，GR `τ=1e-3/1e-4` 为 40.30/54.84ms；`(10,5)` 其他精确解 >10s，而 GR 为 70.75/94.79ms。更大 k 时 GR 可能早停，表中同时报告 success rate。

在固定 10ms/token 预算下，Llama-3 的 general LP/max-flow/GR(1e-3) 最佳接受率为 82.53/83.94/85.65%；100ms 下为 83.94/89.01/90.04%。Gemma-2 100ms 为 80.69/85.83/86.60%。低温 `<0.8` 时分布集中，k 从 10 墠大很少再提高接受率，简单 solver 也更可行。

扩展进 SpecTr multi-step 后，作者报告相对 baseline wall-clock 近 2× 改善；这不是“在优化过的 vanilla SD 上再 2×”的统一结论，具体 baseline/失败 fallback 和 tree budget 要看附录 R。

## 4. 复现要点

- 仅在 i.i.d. `p_draft^⊗n` 使用简化；相关候选不可直接套公式。
- 对 target/draft distribution 做一致 top-k/temperature 处理，构造 active set、outer/inner residual。
- 实现 max-flow 小规模 oracle，与通用 LP 对照验证 marginal、acceptance 和 transport sampling。
- 逐级降低 `τ`，实测 L1 marginal error、optimality gap、failure rate 与 solve time。
- 端到端计入 CPU↔GPU logits 传输和 verifier batch；若 OT solver 100ms 而 target decode 更快，算法收益会被完全吞掉。

## 5. 局限与研究意义

- 适用假设较窄：同一步、同分布 i.i.d. drafts；多 drafter/without-replacement/branch-conditioned 只在附录讨论扩展性。
- vocabulary convex solve 仍是明显在线开销，且 success 受温度、截断和数值稳定性影响。
- 边际接受率提高不保证高并发 goodput：并行 n 候选占 verifier batch slots。
- `τ` 误差虽有界，若应用要求严格 target distribution，应使用足够精度/精确 fallback，并报告累计多步误差。

论文最重要的理论推进，是将“最优多候选 coupling 只能写成指数 LP”变成了一个可计算、可校准精度的对象；同时也暴露 verification optimization 与系统 latency 之间仍有一道鸿沟。

## 审读导航

| 内容 | 页码 |
|---|---:|
| OTLP、subset formulation 与贡献 | 1–3 |
| canonical decomposition | 4–5 |
| max-flow / complementary slackness | 5–7 |
| convex/global resolution 与误差 | 7–9 |
| 主实验与结论 | 9–10 |
| 完整证明与算法 | 11–27 |
| multi-step、非 i.i.d. 扩展与补充实验 | 28–34 |

## 原始来源

- https://openreview.net/forum?id=gpsczXOsHn
- https://arxiv.org/abs/2511.15898

