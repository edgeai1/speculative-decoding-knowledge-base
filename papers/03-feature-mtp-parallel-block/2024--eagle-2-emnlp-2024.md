---
id: 2024--eagle-2-emnlp-2024
title: "EAGLE-2: Faster Inference of Language Models with Dynamic Draft Trees"
authors: [Yuhui Li, Fangyun Wei, Chao Zhang, Hongyang Zhang]
year: 2024
venue: EMNLP 2024
status: deep_read_complete
primary_source: https://aclanthology.org/2024.emnlp-main.422/
version_read: EMNLP 2024 proceedings
pages_read: 1-12
pdf_sha256: 922fb0ff609792d6a50e43d35c45edb69a3194f4b69b1f87176c65d04ab65cad
---

# EAGLE-2 精读

## 核心贡献

EAGLE-2 不训练新的 predictor，而是重做 EAGLE 的树搜索：不同上下文难度不同，固定树会在容易请求上不够深、在困难请求上浪费宽度；EAGLE draft 的 confidence 又恰好与接受概率较好校准，因此可在线把节点预算分配给最可能存活的路径。论文报告 `3.05–4.26×` 加速，相对 EAGLE-1 提升 `20%–40%`，并继续使用严格校验保持目标分布。

## 1. 动态树算法

对某候选节点，令其局部 confidence 为 draft softmax 中所选 token 的概率；节点的 **value** 定义为根到该节点各局部 confidence 的乘积，近似“整条前缀都被目标接受”的概率。算法分两阶段：

1. **Expansion**：逐层运行 draft，每轮从当前可扩展节点中取 value 最高的 top-k，生成孩子；这允许高信心路径更深、低信心处更宽或尽早停止。
2. **Reranking**：将所有已生成节点放在一起，选 value 最高的 `m` 个用于目标验证，同分时偏向浅层。因为父节点 value 不小于子节点，top-m 集合天然保持祖先闭包，仍是一棵连通树。

选中节点再展平，构造祖先 attention mask 与按深度 position ids；目标模型一次前向评分。算法优化的是固定验证节点预算下的预计接受量，而非盲目增加 draft 候选数。

## 2. confidence 为什么可用、又为什么不是证明

论文画出的校准统计显示：confidence 小于 0.05 的候选接受率约 0.04，高于 0.95 时约 0.98，故它是有用 proxy。但 speculative acceptance 取决于目标概率 `p` 与 draft 概率 `q` 的关系，单独 `q` 并不充分；乘积还近似忽略沿路径误差相关性。因而 EAGLE-2 的排序是经验有效的启发式，**分布正确性来自后续 verifier，不来自 value 的概率解释**。

## 3. 实验和消融

实验覆盖 Vicuna、LLaMA2-Chat、LLaMA3-Instruct 三个系列和六类任务。MT-Bench、温度 0 下，Vicuna-13B 六任务均值约 `4.04×`、接受长度 `4.65`，LLaMA2-13B 约 `4.10×/4.68`；温度 1 对应约 `3.65×/4.26` 与 `3.88×/4.51`。具体任务会偏离均值，因此不能只引用最高 `4.26×`。

关键消融（Vicuna-7B/MT-Bench）依次为：既不用 value 又不用 reranking 约 `2.81×/3.92`；去 value 约 `3.21×/4.39`；去 reranking 约 `3.48×/4.86`；完整方法约 `3.62×/4.98`。说明“生成时扩展”和“验证前全局重排”都有独立贡献。论文的公平点是使用同一个 EAGLE predictor；不足是主要仍为小 batch latency、校准分布迁移没有系统压力测试。

## 4. 实现与保证

复现不需重训 EAGLE：维护节点 token、父指针、深度、draft KV 和 log-value（实践中应用 log 避免长路径下溢）；每轮批量扩展 top-k；全局 top-m 后按父指针生成 mask。严格 greedy 验证保持原 greedy 输出，标准 residual rejection 保持采样分布。树排序错误只会降低速度，不应改变输出；若实现为了方便直接按 confidence 接受，就失去了这一性质。

需报告 expansion 次数、候选池/验证树大小、排序与 cache gather 时间，以及校准曲线随任务、温度、量化和模型微调的变化。动态树会造成请求间形状不一，持续批处理系统可能需要 padding 或专门调度。

## 5. 局限与研究问题

- confidence calibration 可能因领域、temperature、top-p、量化或 draft/target 更新而漂移。
- value 没有纳入节点深度带来的 token 收益、树验证的非线性 kernel 成本和 batch 干扰。
- 固定 `k/m` 仍需人工设定；理想策略应以实时硬件代价和剩余输出长度做停止决策。
- EAGLE-2 改善搜索，不解决 feature predictor 的数据 scaling 上限；这由 EAGLE-3 处理。

原文第 2–5 页为动态树和校准依据，第 5–9 页为主实验/消融，第 10–12 页给算法细节和补充结果。
