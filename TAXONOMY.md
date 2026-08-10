# 方法谱系与分类

## 1. 先用统一抽象看全部方法

一轮 speculative decoding 可分成五个对象：

1. **Proposal**：drafter 在已确认前缀 `x_<t` 上给出 token、链或树以及 proposal probability `q`。
2. **Budgeting**：决定草稿深度、分支和提交给 target 的节点数。
3. **Verification**：target 一次并行计算这些节点条件下的 `p`。
4. **Acceptance / correction**：按严格或近似规则提交一个连续前缀，并在拒绝处补一个 target token。
5. **Serving**：管理两套 KV、动态 batch、kernel、并发、offload、SLA 和硬件成本。

论文常只创新其中一项，却把总速度写成一个数字。研究比较时应先指出它改变了哪一项，其他四项是否相同。

## 2. 按 proposal 来源分类

| 家族 | 代表论文 | 优点 | 固有代价/风险 |
|---|---|---|---|
| 独立小 LM | Leviathan、Chen、Big Little Decoder、DistillSpec | 因果概率清楚，容易接标准拒绝采样 | 另一个模型、KV、tokenizer/领域对齐成本 |
| 目标隐藏特征 head | Medusa、Hydra、EAGLE 系列、HASS、PRISM | draft小、接受率高 | checkpoint专用训练；需要侵入target hidden |
| 内置/并行 MTP | PARD、P-EAGLE、DFlash、DFLARE | 一次预测长block，权重读取少 | position marginals缺候选内因果性 |
| 半自回归修正 | Domino、DSpark、DeLS-Spec、xPress、DBLast | 并行backbone加低成本因果一致性 | 小顺序环或迭代；proposal概率/校正需谨慎 |
| 自推测 | Draft & Verify、TriForce、MagicDec、SparseSpec、Windowed-MTP | 无独立权重，target一致性强 | draft仍读大权重/KV；cache与系统复杂 |
| 检索/复用 | REST、SuffixDecoding、Oilbird | 无神经draft forward，重复文本上极快 | 索引、历史存储、隐私、exact-key可达性 |
| Jacobi/固定点 | Lookahead、xPress refinement | 用并行迭代替代逐token | 额外FLOPs；有限轮随机分布问题 |
| 多模型/多候选组合 | SpecInfer、Multi-Candidate、Sequoia、Global Resolution | 更好覆盖 target support | 树节点、残差账本、动态shape复杂 |

## 3. 按候选内依赖结构分类

### 3.1 独立 horizon marginals

Medusa heads、PARD、DFlash 初始 block在一次 forward 中预测不同未来位置，但第 `k` 位没有看到本次已经采到的 `x_{t+1:t+k-1}`。它们适合低熵、格式化延伸，长 horizon 会出现 multi-modal collision：每个 token 单看都合理，拼在一起不合理。

### 3.2 完整自回归 proposal

独立小 LM、EAGLE、ReDrafter 的 `q(x_1:K)=∏q(x_k|x_<k)` 语义清楚，采样校正最直接，但 draft latency随深度增加。

### 3.3 半自回归 proposal

DSpark/DeLS/Domino 先一次算位置表示或 base logits，再用 Markov/RNN/GRU 小头左到右加 bias。昂贵部分 O(1)，条件部分 O(K) 但常是小矩阵。PCTree进一步把同一 parent-conditioned head从chain展开成tree。

### 3.4 一次并行的 tree-causal proposal

JetSpec 在训练/推理节点上用 ancestor-only mask，使同一 forward 的节点看到各自具体祖先；TreeFlash先建规则树，再批量按 parent修正。它们试图兼得 branch causality和并行性，代价是需要预先给出树模板或两阶段搜索。

### 3.5 迭代 refinement / latent joint

xPress用严格因果refiner做Jacobi fixed-point；DBLast用共享低秩latent category耦合位置。二者都说明“并行”不必等于“独立”，但随机采样时必须能计算本次候选的条件/联合 `q`，否则标准 residual correction无从定义。

## 4. 按正确性保证分类

| 类型 | 需要满足 | 代表 |
|---|---|---|
| Greedy-exact | 每个提交token与原target在真实prefix下argmax相同 | Blockwise、Draft & Verify、Windowed-MTP |
| Distribution-preserving | 接受概率、拒绝残差与proposal `q`共同保证输出边缘为target `p` | 两篇2023奠基论文、SpecTr、Sequoia、Block Verification |
| Model-preserving但策略改变 | 相对微调后target无损，但不等于原checkpoint | Medusa-2、Speculative Streaming shared mode |
| Lossy / approximate | 主动接受target非首选或修改router/目标分布 | MARS、ASD、AcceptMoE、Medusa typical acceptance |

“target最后会验证”本身不够。若接受规则放宽、树上多候选任取、调度看到了未来candidate，或target MoE路由被限制，均可能改变分布。

## 5. 按系统工作区间分类

| 区间 | 主要瓶颈 | 更有希望的方法 |
|---|---|---|
| 短上下文、batch 1、dense GPU | target权重带宽 | EAGLE/Medusa/parallel block、小树 |
| 高并发 | target verify算力与batch capacity | 小block、DSpark/D-cut/HeteroSpec式预算、continuous batching协同 |
| 长输入 | draft/target KV读 | MagicDec、TriForce、LongSpec、SpecExtend、Windowed-MTP |
| 长 reasoning 输出 | 动态KV、attention、policy drift | SparseSpec、SpecRoll |
| target offload | 权重PCIe/SSD搬运 | SpecExec、Sequoia大树、TriForce |
| MoE | tree节点触发expert union | DFlash需计专家激活；AcceptMoE以近似路由降traffic |
| 高重复 agent | 历史序列可复用 | SuffixDecoding、REST、Oilbird |

## 6. 时间线：问题如何演化

- **2018–2023**：从 blockwise未来头到精确 speculative sampling；建立 `p/q`接受与 residual correction。
- **2023–2024**：独立小模型对齐、多候选树、Medusa/EAGLE feature heads、self-speculation和retrieval。
- **2024–2025**：动态/最优树、Block Verification、长上下文KV、serving与训练—推理context alignment。
- **2025–2026上半年**：EAGLE-3数据scaling，PARD/DFlash并行block，PRISM参数重构，统一benchmark与生产engine反思。
- **2026年中至8月**：Domino/DSpark/TreeFlash/JetSpec/xPress等集中修复并行marginal的因果缺失；verification走向全batch hardware-aware调度；同时出现acceptance-collapse攻击、lossy verifier审计与RL/MoE应用。

这条时间线表明，前沿问题已经从“有没有小模型”转向 **proposal joint structure、严格验证、硬件成本和动态请求共同优化**。
