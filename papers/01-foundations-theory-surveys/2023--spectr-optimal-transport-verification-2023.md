---
id: 2023--spectr-optimal-transport-verification-2023
title: "SpecTr: Fast Speculative Decoding via Optimal Transport"
authors: [Ziteng Sun, Ananda Theertha Suresh, Jae Hun Ro, Ahmad Beirami, Himanshu Jain, Felix Yu]
year: 2023
venue: NeurIPS 2023
status: deep_read_complete
primary_source: https://arxiv.org/abs/2310.15141
version_read: arXiv:2310.15141v2
pages_read: 1-21
pdf_sha256: 282933bead429a13c239f739376490365d724e124fc9b1a4737be27e8c80bfc4
---

# SpecTr（NeurIPS 2023）精读

## 核心定位

SpecTr 将单候选 speculative sampling 解释成“最大耦合/最优传输”，再把验证扩展到同一位置的 `K` 个 draft candidates：输出仍严格服从 target，但目标是让输出尽可能落在候选集合中，以便复用已并行计算的后续 logits。精确 OT 线性规划随 `K` 指数爆炸，论文提出近线性时间的 K-SEQ，接受概率至少达到最优值的 `1-(1-1/K)^K ≥ 1-1/e`。

## 1. 从 maximal coupling 到 membership-cost OT

单候选时，draft `X~p`、输出 `Y~q`。所有边缘分布分别为 `p/q` 的联合分布都是 coupling；成本 `1{Y≠X}` 最小时，就最大化 `P(Y=X)`。经典 speculative sampling 正是 maximal coupling，最优接受率为：

`Σ_x min(p(x),q(x)) = 1-TV(p,q)`。

多候选时输入变为 `X=(X₁,…,X_K)~P`，输出仍需为 `q`。成本改为 membership cost：`1{Y∉S(X)}`，其中 `S(X)` 是候选 token 集。最优 transport 最大化“输出是任一候选”的概率。若候选 i.i.d. 来自 `p`，`P=p^⊗K`。

不能把单候选接受测试独立做 K 次：例如 `p=Bernoulli(1)`、`q=Bernoulli(1/2)`，每个全为 1 的候选若都以 1/2 独立尝试，最终输出 1 的概率至少 `1-2^{-K}`，已经偏离 target。多候选必须联合分配概率质量。

## 2. 精确 OTM 与 K-SEQ

离散 OTM 可写成 LP，但有 `|V|^{K+1}` 个 transport variables、`|V|^K+|V|` 个等式约束，实用上不可解。论文证明最优接受率随 K 单调；当 draft support 覆盖 target support，K→∞ 时趋于 1。

K-SEQ 对候选逐次构造残差/选择，相当于高效的合法 coupling；计算量对 vocabulary 近线性、对 K 为对数/线性量级，并有 `(1-1/e)` 乘法近似保证。它可能不是最优，但与无形式保证的启发式不同，任何输出都保持 target marginal。

## 3. 从 token 集合扩展到候选序列

每轮从小模型独立采 K 条、每条长 L 的序列；target 对所有 tree/prefix 条件分布沿 batch 和 time 轴并行计算。验证从根开始：

1. 在当前节点用 OTM/K-SEQ 从所有首 token 选一个 target-valid token `Y`；
2. 若 `Y` 出现在候选中，只保留首 token 等于 `Y` 的子序列，递归到下一层；
3. 若 `Y` 不在候选集合，说明发生 correction，立即结束该轮；
4. 到最后一层仍命中时，用已算好的 target conditional 再采一个 bonus token。

Theorem 2 证明：无论随机停止长度是多少，新输出 prefix 的每个条件分布都等于 target。注意算法并非“选分数最高路径”，而是在每层通过 coupling 采一个合法 token，再筛选能继续该 token 的 branches。

## 4. 实验

LM1B，small=PaLM-2 Gecko、target=PaLM-2 Bison，1000 prompts、3 seeds：

| 方法 | K | L | block efficiency | wall-clock speedup |
|---|---:|---:|---:|---:|
| AR | – | – | 1.0 | 1.0× |
| vanilla SD | 1 | 4 | 2.4 | 1.67× |
| SpecTr | 8 | 4 | 3.1 | 2.08× |
| vanilla SD | 1 | 8 | 2.9 | 1.56× |
| SpecTr | 8 | 8 | 4.0 | 2.13× |

最佳相对 vanilla SD 的墙钟提升为 `2.13/1.56≈1.37×`。block efficiency 明显高于墙钟加速，因为 small-model sampling、batch/time 并行并非免费，另有 OT selection 和模型切换开销。论文附录用 97M/6M transformer 拆分 time-axis 与 batch-axis latency，强调其 O(1) 计算模型只是近似。

## 5. 实现清单

- 生成 K×L candidates 并保留每个节点 draft distribution；把共同前缀组织成树，避免重复 target score。
- 构造合法 transport plan；K-SEQ 需严格按残差更新，不能用 K 次独立 rejection 代替。
- target 一次对所有 candidate nodes 使用 tree/causal attention；验证时递归过滤 branches。
- 缓存已验证节点 logits，全部命中时提交 bonus token；拒绝后只提交 correction。
- 分别报告 total nodes、tree depth、block efficiency、OT CPU/GPU 时间、target batch 扩张和端到端时间。

## 6. 边界与影响

- 理论保证是输出分布正确，不保证 K-SEQ 达到最优接受率；其下界在某些分布上可能松。
- `K×L` target nodes 会迅速变贵；高并发下 batch axis 不再近似免费。
- 所有候选 i.i.d. 并不利用互补 drafter 或主动 diverse construction；扩展虽允许一般 `P`，求解更难。
- OT LP 的词表/候选指数维度正是 2026 Global Resolution 要解决的问题。

SpecTr 的长期价值是把 verification 从“某条 heuristic”提升为 coupling optimization：正确性由 marginal constraints 管，性能由 membership cost 管。这成为 multi-draft verification 的统一数学语言。

## 审读导航

| 内容 | 页码 |
|---|---:|
| 单候选 maximal coupling | 3–4 |
| 多候选 OT 定义与指数 LP | 5–7 |
| K-SEQ 与近似保证 | 8 |
| sequence-level SpecTr 算法/正确性 | 9–10 |
| PaLM-2 结果 | 10 |
| 证明、延迟拆解、补充实验 | 12–21 |

## 原始来源

- https://arxiv.org/abs/2310.15141

