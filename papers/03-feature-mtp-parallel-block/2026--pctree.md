---
id: 2026--pctree
title: "From Chains to Trees: Parent-Conditioned Drafting for Semi-Autoregressive Speculative Decoding"
authors: [Zixian Li, Tong Li, Chi Xie, Xiaohui Song, Haonan Lu]
year: 2026
venue: arXiv preprint
status: deep_read_complete
primary_source: https://arxiv.org/abs/2608.02123
version_read: arXiv:2608.02123v1 (2026-08-03)
pages_read: 1-18
pdf_sha256: adfade9aff11a63b1fd904f660d59af948e50c80fbc63ad47ff94752011f5f25
---

# PCTree 精读

## 核心贡献

DSpark 已学会 `base_logits(depth)+Markov(parent)`，却只采一条 chain，早错使后缀全废。PCTree 在不重训、不增加 parallel backbone forward 的条件下，对每个 concrete parent批量调用同一 Markov head，得到 parent-specific children；按 joint path probability逐层保留 top-k frontier，最后在固定 N verification节点预算中全局选祖先闭包树。

这与从 marginal logits盲目建树不同：同一深度不同 parent的 child分布由 `W1[parent]W2` 改写。算法阶段 d复用 backbone第 d位 base logits，批量计算 frontier所有 parent correction、更新累计 log-score、layer prune；global top-N因父 path score不低于子而保持树。target tree attention一次验证。

Qwen3-4/8/14B、九基准、单 H20。B=7 相对 matched DSpark 的 AR-speedup增幅 `3.1%–29.5%`；Qwen3-4B GSM8K、B=16，τ `9.41→11.16`，三次平均 speedup `6.14×→6.60×`。部分 DSpark值为论文复现/引用而非完全同 run，作者有标注。大树收益任务依赖，构树/校验开销使 τ增幅不会等比例转为速度。

greedy strict tree verify无损；stochastic多候选仍需合法 tree rejection sampler。局限是一阶 parent条件、N/top-k硬件敏感、动态树对 CUDA graph/continuous batch不友好。它的重要研究启发是：已有半 AR head蕴含“免费分支能力”，可进一步做成本感知 frontier和跨请求全局树预算。原文第 3–6 页算法，第 7–12 页结果/延迟，第 13–18 页伪码与补充。

## 树构造的关键不变量

每个 frontier 项应保存 `(node_id, parent_id, depth, token, cumulative_logq)`。扩展某父节点时，共享该深度的 backbone base logits，只重新计算由 concrete parent token 决定的低秩修正；对子节点加上条件 log-prob 后做 layer-wise pruning。最终 global top-N 不能简单截断普通排序结果：实现必须加入所有已选节点的祖先，或利用“子路径概率不高于父路径概率”的条件保证前缀闭包。若量化/长度惩罚破坏该单调性，就需显式闭包并重新核算 N。

验证阶段要把紧凑树映射成 target 输入顺序、position ids 与 ancestor-only attention mask，再依据已验证 token 沿唯一可提交路径推进。建议用极小词表枚举所有深度 2–3 的树，将构造器选出的节点与穷举 joint probability 排名对照；再对 chain 模式设 `top-k=1`，确认逐 token 输出、KV 与 DSpark 基线完全一致。性能报告应分离 Markov 批量 matmul、frontier top-k、mask 打包和 target kernel；否则接受长增加但动态构树更慢的情况会被平均 speedup 掩盖。
