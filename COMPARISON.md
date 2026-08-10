# 跨论文比较与下一步研究问题

## 1. 2026年8月的前沿不再是“再做一个小模型”

当前最强方法的竞争集中在三个耦合量：proposal是否能用一次/少数forward表达候选内因果性；verifier是否在严格分布保证下最大化prefix推进；serving是否把有限target batch容量给最有价值的节点。DFlash把draft cost降下去，Domino/DSpark/TreeFlash/JetSpec/xPress再修复其marginal缺陷；DSpark/AngelSpec把问题推进到全batch预算；SPEED-Bench和*Performance or Illusion?*说明只做batch1算法表已经不够。

## 2. 代表方法矩阵

| 方法 | Proposal结构 | 训练/状态 | 严格采样 | 系统强项 | 主要空白 |
|---|---|---|---|---|---|
| 标准SD | 独立小LM AR chain | target/draft现成 | 是 | 简单、证明清楚 | draft模型/每步成本 |
| EAGLE-3 | target feature、AR tree | 每target长训练 | 是 | 高接受、小batch | target绑定、draft多step |
| PARD | 一次parallel marginals | family小模型适配 | 需核对parallel q | 恒定draft带宽 | family边界、联合分布 |
| DFlash | 一次block diffusion marginals | 每target feature训练 | 外层可严格 | 长block、serving | intra-block causality |
| Domino | parallel+GRU logit residual | 端到端重训 | 是，q因果 | 高τ、fused loop | TF exposure、顺序head |
| DSpark | parallel+Markov/RNN；confidence | 端到端+校准 | 是，含调度条件 | 生产load-aware verify | profiler近似、突发负载 |
| JetSpec | 一次tree-causal head | target蒸馏 | 是 | 大tree budget scaling | 动态树显存/批容量 |
| xPress | causal refiner+Jacobi | co-train | greedy fixed-point清楚 | 并行因果修复 | 有限轮stochastic q |
| Windowed-MTP | native MTP但draft KV窗口化 | training-free | 是 | million-token成本 | 远程依赖的q退化 |
| Suffix/Oilbird | lexical/semantic历史检索 | 历史索引/hidden store | greedy严格 | agent重复流量 | 隐私、内存、采样化 |
| Block Verification | 联合接受整个chain prefixes | 无训练 | 是且类内最优 | verifier免费小增益 | 广义树/parallel proposal |
| MARS/ASD | 放宽greedy verifier | 无训练 | 否 | 快、可控近似 | regret与语义质量关系 |

## 3. 最值得进入的五个问题

### A. Parallel joint proposal 的严格 stochastic verification

**问题**：并行block给的是marginals，半AR/latent/refinement给出不同形式的依赖。怎样在一次或常数次draft forward内产生可精确计算 `q(x_1:K)` 的joint proposal，并与Block Verification/多候选树严格组合？

**为什么尚未解决**：DSpark的局部AR q最清楚但仍有顺序loop；xPress证明greedy fixed point，不等同有限轮随机joint；DBLast开始做latent mixture但规模/系统证据有限；PARD式parallel logits的标准residual语义仍需统一。

**可做起点**：低秩state-space/triangular normalizing proposal，一次生成latent、并行条件token；给出可求joint log-prob和unbiased residual；在T=0/0.7/1、creative/chat/math上对DFlash/DSpark/xPress，报告TV正确性、τ和真实kernel。

### B. 有严格因果保证的全batch verification scheduler

**问题**：在jagged CUDA graph capacity、异长context、MoE expert union、突发arrival和SLA下，如何动态分配每请求depth/tree nodes，既non-anticipating又优化goodput？

**为什么尚未解决**：DSpark用两步历史capacity形成causal barrier，D-cut离散profile，HeteroSpec按复杂度分层；都没有覆盖负载突变、context/MoE成本与多SLA的统一证明。

**可做起点**：把每个prefix extension建模为带survival概率、token FLOPs、expert union增量和deadline价值的online admission；以primal-dual/robust MPC给regret或competitive guarantee；在SGLang/vLLM replay真实trace。

### C. 跨checkpoint、跨语言而不掉acceptance的可迁移drafter

**问题**：能否避免EAGLE/DFlash每target重训，又比family-only PARD和独立小LM更准？

**证据**：Curse of Multilinguality显示共享drafter容量在语言间冲突；PARD仅同family；DeLS local head可跨DFlash checkpoint但long expert仍target-specific。

**可做起点**：共享因果prior + 极小target calibration层；用feature-space transport/low-rank router处理checkpoint差异；训练目标以TV/接受而非CE；跨Llama/Qwen同tokenizer微调、跨tokenizer另做映射。

### D. Acceptance-collapse鲁棒性与成本隔离

**问题**：Mistletoe/ADSD证明输出正常也能让SD成本DoS。怎样给最坏输入的额外成本上界，同时保留普通输入收益？

**可做起点**：请求级circuit breaker在预计 `τ` 低于break-even时切AR；训练confidence的conformal lower bound；共享batch按风险隔离；建立攻击者成本、P99影响和false fallback的benchmark。

### E. 长上下文native MTP的统一cache设计

**问题**：Windowed-MTP、SparseSpec、MagicDec分别用window、动态top-k和retrieval；何时该选哪一个，能否随位置切换且不额外存draft KV？

**可做起点**：将draft KV selection视为在接受损失约束下最小化bytes-read；用target verify已产生的attention/hidden做无额外forward的selector；覆盖dense、hybrid、NoPE、MoE和事实needle/CoT。

## 4. 推荐优先级

| 方向 | 新颖性 | 可验证性 | 系统/理论双贡献 | 起步成本 | 建议 |
|---|---:|---:|---:|---:|---|
| A 严格parallel joint proposal | 5 | 4 | 5 | 4 | **首选算法题** |
| B non-anticipating serving scheduler | 5 | 4 | 5 | 5 | **有系统资源时首选** |
| D robustness/cost isolation | 4 | 5 | 4 | 3 | 快速形成完整论文 |
| C transferable drafter | 4 | 4 | 4 | 5 | 训练资源充足再做 |
| E long-context KV | 4 | 4 | 5 | 5 | 需长上下文硬件 |

## 5. 我最推荐的具体下一步

先做一个 **“严格可校正的半并行 joint drafter + hardware-aware block verifier”** 小型原型：

1. 选Qwen3-4B/8B和公开DFlash/DSpark checkpoint，避免先烧大训练。
2. 在同一parallel hidden上设计能并行计算、又输出规范化joint/conditional q的低秩因果层。
3. 先在toy词表和真实模型做distribution equivalence gate，再追速度。
4. 接Block Verification；将节点准入限制为non-anticipating，profile B=1–64。
5. 用SPEED-Bench的math/code/chat与throughput split，和DFlash、DSpark、xPress做同engine/同数据比较。

这个题同时击中2026年最密集的研究冲突：DFlash的并行效率、DSpark的因果性、Block Verification的严格最优性与生产调度的真实成本；即使端到端速度没有全面胜出，关于“parallel proposal何时能严格校正”的理论和负结果本身也有研究价值。
