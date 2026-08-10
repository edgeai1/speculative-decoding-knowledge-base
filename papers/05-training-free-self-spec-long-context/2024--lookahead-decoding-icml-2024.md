---
id: 2024--lookahead-decoding-icml-2024
title: "Break the Sequential Dependency of LLM Inference Using Lookahead Decoding"
authors: [Yichao Fu, Peter Bailis, Ion Stoica, Hao Zhang]
year: 2024
venue: ICML 2024
status: deep_read_complete
primary_source: https://proceedings.mlr.press/v235/fu24a.html
version_read: ICML 2024 proceedings
pages_read: 1-20
pdf_sha256: b04a936f01543226ba4803a7316b4c10edea9840b0ea5aa684b926d81b4c0eb4
---

# Lookahead Decoding 精读

## 核心思想

Jacobi decoding随机初始化未来 W个位置，每轮用同一 LLM并行更新所有位置；严格因果保证最多输出长度轮收敛到 greedy fixed point，但普通Jacobi正确 token常在错误位置、下一轮又被覆盖，实际不加速。Lookahead保留最近 N−1轮×W位置的二维轨迹，从对角线收集大量 N-grams进池；另一 verification branch每轮取 G条以当前 token开头的 n-gram，由同一 LLM并行验证，提交最长匹配前缀。

W控制每轮探索位置，N控制gram长度，G控制并行候选；lookahead与verification query用特殊 mask合成一个 forward，并可跨GPU强扩展。池中的 n-gram由目标模型自身Jacobi轨迹生成，不需训练/外部datastore。greedy下严格 equality保持输出。

采样时论文把 n-gram generation视为 deterministic/one-hot proposal，逐位置残差验证多条候选，避免为整个池保存词表分布，并给出正确性证明；实现必须忠实执行算法，简单“选最长target高分gram”不保分布。

## 结果与成本

MT-Bench最高约 `1.8×`，多GPU代码任务强扩展可至 `4×`；单GPU不同模型常约1.4–2.3×。代价是每轮多算 W探索token和G验证候选，FLOPs增加而串行step减少，适合 memory-bound/空闲算力，不适合已compute-bound的大batch。sampling接受低于greedy，速度下降。

复现锁定 W/N/G、池淘汰、mask/position ids与并行布局；报告总processed tokens/输出token和实际step，而不只latency。局限是 n-gram pool locality、长动态mask、显存和continuous batching；与SuffixDecoding区别在于候选来自同次Jacobi轨迹而非历史请求。原文第 2–6 页算法，第 7–9 页成本模型，第 9–14 页实验，第 15–20 页证明/附录。

## 二维轨迹如何落地

可把 lookahead state 表示成 `W × (N-1)` 环形缓冲：一次并行更新产生新列，从相邻轮次的对角线抽取连续 n-gram，按首 token 建索引供 verification branch 查询。联合 forward 的 attention mask 必须同时满足：各 Jacobi 位置只看已知 prefix 与规定的旧迭代状态；每条验证候选只看其祖先；不同候选互不可见。任何越界注意都会造成“看见答案”的虚高接受率，因此应在小矩阵上直接可视化 mask 并与逐支独立 forward 的 logits 对照。

性能上，串行步数下降与总 token 计算膨胀是两条不同曲线。建议扫 W/N/G 时同时报告每输出 token 的模型处理 token 数、forward 次数、GPU 利用率、峰值 KV 和 TPOT；在 batch 已饱和时尤其要验证是否倒退。采样模式还应使用小词表 Monte Carlo 检验边缘分布，不能借用 greedy 一致性结论。候选池命中高但 target 验证分支过多时，系统可能需要按预计提交长度/节点成本而非纯路径频率选择 G。
