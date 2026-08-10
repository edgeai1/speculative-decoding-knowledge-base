---
id: 2026--not-a-bandit-iclr-2026
title: "Not-a-Bandit: Provably No-Regret Drafter Selection in Speculative Decoding for LLMs"
authors: [Hongyi Liu, Jiaji Huang, Zhen Jia, Youngsuk Park, Yu-Xiang Wang]
year: 2026
venue: ICLR 2026
status: deep_read_complete
primary_source: https://arxiv.org/abs/2510.20064
version_read: arXiv:2510.20064v2 / ICLR 2026
pages_read: 1-27
pdf_sha256: d8b089f553d95c46e271f792b008aa18a8abdd39d8f76e170b6a031f3427202f
---

# Not-a-Bandit / HedgeSpec（ICLR 2026）精读

## 核心定位

多 drafter 在线选择过去被当 multi-armed bandit：只看到被选专家反馈。HedgeSpec 观察到 lossless target trajectory 对所有 drafters 都是合法反事实样本；只需让每个轻 drafter prefill 已验证 token，就能估计每个专家的 acceptance/EAL，不需额外 target call。于是用 full-information Hedge/NormalHedge，regret 对专家数从 bandit 的坏依赖降为 `√log N`。

## 1. 反事实反馈

对每个 verified target prefix，计算候选 drafter i 的条件接受概率 `γ_t[i]`。vanilla single draft 中是 `1-TV(p,q_i)`；EAGLE tree 中是 target token 落进该 drafter子节点集合的总概率。无需实际沿 q_i rollout。

给 depth K，论文构造 EAL 无偏估计：

`Σ_{k=1}^{K+1} k(1-γ_k) Π_{j<k}γ_j`（令 `γ_{K+1}=0`）。

它只用一条 target trajectory，却在期望上等于任意 drafter 的 accepted length；值域 [1,K+1]，方差≤K²/4，不随 N 增长。BanditSpec importance estimator 方差则为 O(NK²)。

## 2. Censoring 与 no-regret

当前被选 drafter 若早拒绝，尚看不到反事实专家可能继续接受的后续 target tokens，不能立刻算完整 K-depth loss。HedgeSpec 把它建模为 delayed feedback，等积累足够后更新；忽略 censoring 会偏向早停专家。

用 Hedge/NormalHedge + delayed reduction，平均 TAP regret 为 `O(sqrt(K logN/T))`，EAL 为 `O(sqrt((K+1)^3 logN/T))`，与事后最佳固定 drafter 竞争。保证不是与每一步 oracle-best dynamic expert 竞争。

## 3. 实验

三个 target（Llama-3.1-8B-IT、Qwen3-8B/32B），每个 7 个 EAGLE-3 domain drafters（Python/Math/Biology/Chemistry/MedQA/CNN-DM/SQL），共 21。8×A100/NVLink、FP16、batch=1。

Llama 单个专家只在域内好、跨域很差；HedgeSpec 七域均值 MAT 7.15、90.41 tok/s，generic EAGLE 5.69/74.34，UCB/EXP3 更低。Qwen8B 为 6.37/69.44 vs 4.23/47.53；Qwen32B 为 6.21/40.41 vs 2.88/20.76。SQL/Qwen8B 对 EAGLE tok/s 提高 83.7%；混合请求平均最高声称 46.1%。

target forward 75.7ms、单 EAGLE eval 2.497ms、hedge update .413ms；一个额外 MAT 理想上可抵约 25 个串行 expert eval，并可并行。轻微 prompt 改写使 offline BERT router 对 MedQA/Math 误路由 98%/90%；HedgeSpec 利用生成期反馈仍保持，最多比 router 2.34×。

## 4. 边界

- no-regret 对事后最佳固定专家，不保证 nonstationary 每 token oracle；不同请求需重置/延续权重是系统选择。
- “无额外 target query”不等于免费：N 个 drafter prefill、权重驻留和 KV 明显占资源，高并发需按预算抽样专家。
- 专家均是同 target 的 EAGLE-3，跨 tokenizer/独立 LM 的反馈成本不同。
- 实验专家事先按测试域构建，实际服务能否覆盖未知域决定上限。
- output correctness 由底层 SD 保证，selection theorem 只管效率。

## 审读导航

| 内容 | 页码 |
|---|---:|
| metrics/full-information estimator | 4–5 |
| censoring、delay、regret | 6–7 |
| 专家集、开销和主结果 | 7–10 |
| proofs/算法和扩展实验 | 12–27 |

## 原始来源

- https://arxiv.org/abs/2510.20064

