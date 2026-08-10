---
id: 2024--medusa
title: "MEDUSA: Simple LLM Inference Acceleration Framework with Multiple Decoding Heads"
authors: [Tianle Cai, Yuhong Li, Zhengyang Geng, Hongwu Peng, Jason D. Lee, Deming Chen, Tri Dao]
year: 2024
venue: ICML 2024
status: deep_read_complete
primary_source: https://proceedings.mlr.press/v235/cai24b.html
version_read: ICML 2024 proceedings / arXiv:2401.10774
pages_read: 1-27
pdf_sha256: 93d98f2e858c87ee04be440ee81ab8ad93700652ed759227d25fcf75cfdd5ef0
---

# MEDUSA 精读

## 一句话定位

MEDUSA 不再维护一整个独立小模型，而是在目标 LLM 最后一层表示上挂多个轻量 future-token heads，并把各头的 top-k 组合成一棵候选树，一次目标模型前向同时校验多条延伸。它把“多 token 草稿”变成目标模型的一个小附件，形成后来 Hydra、多种 MTP head 和树验证系统的共同起点。

## 1. 问题、假设与真正创新

标准 speculative decoding 的小模型必须与目标模型在 tokenizer、领域和输出分布上足够接近；训练、保存和部署另一套权重也有成本。MEDUSA 的假设是：目标模型当前隐藏状态已经包含相当多未来信息，用极小的头即可恢复未来若干位置的高概率 token。创新由三部分组成：多头并行预测、将头部候选组织成稀疏树、用 tree attention 在一次目标前向中验证整棵树。

它没有消除未来 token 的不确定性。各头都只从同一个 `h_t` 独立预测，越远的头越容易受到“前一个未来 token 尚未知”的影响；树搜索只是保留多条可能路径。Hydra 和 EAGLE 正是沿着这个缺陷继续发展的。

## 2. 模型与训练

第 `k` 个头预测位置 `t+k+1`：

`p_t^(k) = softmax(W_2^(k)(SiLU(W_1^(k)h_t) + h_t))`。

`W_2` 从原 LM head 初始化，`W_1` 零初始化，因此初始时近似复用原表示。推理通常用 5 个头。Medusa-1 冻结 backbone，仅训练 heads，损失是各未来位置交叉熵的加权和，论文实现常取 `λ_k=0.8^k`；目标模型本身不变，维护代价低。论文给出的 Vicuna-7B/60k ShareGPT 示例约需单张 A100 PCIe 5 小时。

Medusa-2 联合微调 backbone 与 heads：加入原始 next-token loss、为 backbone 和 heads 使用不同学习率并预热 heads。它能增加接受长度，但得到的是一个新的模型 checkpoint；“能力基本保持”来自训练配方和评测，而不是与原 checkpoint 逐 token 相同。无真实训练集时，作者让原模型生成训练响应做 self-distillation；联合训练还以原模型 logits 做 KL teacher，并用可开关 LoRA 保存冻结 teacher 路径。

## 3. 草稿树、tree attention 与校验

每个头保留若干 top token，其笛卡尔积对应多条候选。直接逐条校验会重复相同前缀，故将共同前缀合并成树。树节点线性打包到一个序列：attention mask 只允许节点看到根到自身的祖先，position id 使用树深而非打包下标。目标 LLM 因而一次得到所有节点 logits；随后选择被接受的最长路径，KV cache 只保留这条路径。

论文还用校准集估计各头 top-r 命中率，在近似独立假设下为树节点评分，再在固定节点预算中挑高价值形状。这个独立性并不严格成立，因此它是工程优化而非最优树证明。

## 4. “无损”与 typical acceptance 必须分开

严格模式可按目标模型 greedy token 校验，Medusa-1 此时保持原模型 greedy 输出；也可嵌入标准 speculative sampling 的拒绝校正以保持采样分布。论文主要推广的 **typical acceptance** 则放宽条件：候选 token 的目标概率高于与熵有关的阈值 `min(ε, δ exp(-H(p)))` 即可接受，首 token 保底接受。在温度 0 时它退化为 greedy；非零温度下通常不是目标分布的精确采样，只能依据下游评测声称质量相近。比较速度时必须标出采用哪种 acceptance。

## 5. 实验结论应该怎样读

论文在 Vicuna 等模型上报告 Medusa-1 超过约 `2.2×`、Medusa-2 约 `2.3–2.8×` 的生成加速。结果集中在小 batch、对话生成和特定 GPU；速度由树节点数、接受长度、额外 logits/attention 计算和 kernel 实现共同决定。联合训练与 typical acceptance 的最高数字不能直接解释为“原模型精确输出的免费加速”。

主要消融支持：更多头先提高后因草稿/验证开销饱和；合理树形优于简单链或盲目扩大笛卡尔积；联合训练和放宽接受均提高接受长度；量化冻结 backbone 可以进一步降低 Medusa-1 成本，但联合训练不宜直接套用同一量化策略。

## 6. 实现清单

1. 从 backbone 取最后 token 的顶层 hidden state，挂 4–5 个残差 MLP heads，并复用/初始化 LM projection。
2. 训练时按偏移构造 labels，冻结模式只优化 heads；联合模式保留原 next-token loss、分离学习率和 warmup。
3. 离线确定每层 top-k 与总树节点预算；生成树 mask、tree position ids 和展平/还原索引。
4. 目标模型一次 prefill 树节点，按严格 greedy、标准拒绝采样或明确标为近似的 typical acceptance 选路径；压缩 KV cache。
5. 基准必须同时报告 acceptance length、draft/verify 各自耗时、batch/上下文/输出长度、温度和 acceptance 类型。

官方代码为 `FasterDecoding/Medusa`；复现风险主要在不同框架的 tree-attention kernel、KV cache 搬运以及论文版本间默认树和阈值变化。

## 7. 局限与研究接口

- 未来 heads 条件独立，远期预测存在结构性歧义；树宽扩大后验证成本迅速上升。
- 每个 backbone 要单独训练 heads；模型更新后需要重新适配。
- typical acceptance 的质量经验保证不能替代分布保证。
- 小 batch latency 获益不自动转化为持续批处理吞吐收益。
- 值得研究的是按请求动态选择树/接受规则、用校准而非独立近似估算节点价值，以及把多头训练与 serving scheduler 联合优化。

## 8. 原文定位

方法总览与 heads 见第 2–4 页；tree attention、接受与树优化见第 4–7 页；Medusa-1/2 和 self-distillation 见第 7–10 页；实验、消融与系统设置见第 10–17 页；附录中的训练配方、树结构和更多质量结果见第 18–27 页。
