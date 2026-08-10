---
id: 2024--hydra
title: "Hydra: Sequentially-Dependent Draft Heads for Medusa Decoding"
authors: [Zachary Ankner, Rishab Parthasarathy, Aniruddha Nrusimha, Christopher Rinard, Jonathan Ragan-Kelley, William Brandon]
year: 2024
venue: COLM 2024
status: deep_read_complete
primary_source: https://arxiv.org/abs/2402.05109
version_read: COLM 2024 paper
pages_read: 1-17
pdf_sha256: c531e10ad363f2498865efee1b89864bf7a5c6ad239836a80f756f0f137cb71c
---

# Hydra 精读

## 核心结论

Hydra 对 Medusa 做了一个小但决定性的修改：第 `i` 个 draft head 不仅看目标模型隐藏状态，还看候选路径上前 `i-1` 个草稿 token。于是未来位置不再条件独立。基础 Hydra 已增加接受长度；将更深 heads、teacher distillation 和一个上下文 decoder layer 组合成 Hydra++ 后，论文报告相对 Medusa 最多 `1.31×`、相对自回归最多 `2.70×` 吞吐。

## 1. 为什么条件独立是瓶颈

给定前缀，“The capital of France is” 的下一词也许很确定，但再下一个词依赖上一草稿到底选了 `Paris` 还是别的词。Medusa 的所有 future heads 只看同一基础 hidden state，相当于估计不同 horizon 的边缘分布；把各头 top-k 直接组合会产生互不协调的路径。Hydra 估计条件分布：

`q_i(x_{t+i} | h_t, x_{t+1:t+i-1})`。

每条候选路径的 token embedding 被送入后续 head。代价是 heads 在路径内要顺序运行，但它们远小于目标 LLM，且多条 beam 可以批量处理；收益是草稿概率更接近真正的链式联合分布。

## 2. 从 Hydra 到 Hydra++

基础 Hydra 是 Medusa 的 drop-in replacement：仍从目标顶层特征起步，仍产生树并用原模型 tree attention 校验，改变的是 draft head 的条件输入。论文系统搜索三个轴：

- **结构深度**：多层 MLP 比单层头更能融合隐藏状态和已草稿 token；过深则草稿成本抵消收益。
- **训练目标**：除硬 token CE 外，用目标模型 soft logits 做 distillation，提供 top-1 之外的相对概率信息。
- **上下文建模**：增加一个小 transformer decoder layer，对已验证序列表示再编码后供 heads 使用，而不是完全依赖一个顶层 token 表示。

三者的调优组合称 Hydra++。论文将“基础 Hydra 的因果条件化贡献”和“更大/更强 draft module 的贡献”分别做了消融，不能把全部增益都归于一个名字。

## 3. 解码与正确性边界

Hydra 继承 Medusa 的候选树、祖先 attention mask、目标模型一次验证和 KV 路径裁剪。严格 greedy 校验时可保持目标模型 greedy 序列；配合标准 residual rejection 可保持采样分布。论文非零温度实验还使用 Medusa 的 typical acceptance，这一放宽规则不严格保持分布。因此应该把“draft head 更准”视为可与不同 verifier 组合的性质，而不是由 Hydra 本身自动保证无损。

顺序依赖并不等于目标模型调用也顺序增加：新增顺序发生在很小的 heads/RNN 式草稿组件中，昂贵目标模型仍一次验证树。实际收益取决于 draft heads 的 kernel 启动和小矩阵效率。

## 4. 实验与证据强度

实验以 Vicuna/MT-Bench 等为主，并考察 greedy、batch 和 typical acceptance。基础 Hydra 相对 Medusa 的平均接受长度最多增加约 `0.46` token，端到端最多约 `1.10×`；Hydra++ 的更强结构把相对 Medusa 提升推至 `1.31×`，相对 AR 最多 `2.70×`。这些是特定 GPU、树预算和 batch 下的端点，不是任意服务负载的通用比例。

最有说服力的证据是相同 tree/verifier 下替换 heads 的配对比较；较弱处是任务和 backbone 覆盖有限、训练与推理资源成本没有统一折算、typical acceptance 下质量只做经验比较。若扩大 batch，目标模型本身计算利用率上升，小 head 的串行部分按 Amdahl 定律更显眼。

## 5. 复现与实现

官方代码为 `zankner/Hydra`。复现时应固定 Medusa baseline 的树、节点预算、acceptance 和 kernel，只替换 head：为每个候选路径缓存先前草稿 token embeddings；head 输出后做 beam/top-k 展开；Hydra++ 再加入小 decoder 与蒸馏 logits。训练 labels 是目标序列的未来位置，teacher logits 必须与温度/截断设置一致。

至少报告：平均接受长度、每轮候选节点数、heads 草稿时间、目标验证时间、KV 整理时间、峰值显存、batch 和 acceptance。只报告接受长度会掩盖 Hydra++ 本身更贵。

## 6. 局限和启发

- 条件化改善联合一致性，却重新引入 draft-side 串行深度；最优 head 数与硬件相关。
- 仍与特定 backbone 表示绑定，模型升级需要重新训练。
- 一个顶层 hidden state 是否足够承载长 horizon 信息仍存疑，这直接引出 EAGLE-3 的多层特征融合。
- 树预算固定时应选择“单位草稿/验证成本带来的预期接受 token”，而不只是 draft likelihood；这是可继续研究的成本感知路径选择问题。

原文第 3–6 页给出方法与 Hydra++ 设计，第 6–10 页为主实验和消融，第 11–17 页包含训练、超参数及补充结果。
