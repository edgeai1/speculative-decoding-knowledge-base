# Speculative Decoding 全景调研

**截止日期：2026-08-10（Asia/Shanghai）**  
**检索执行日期：2026-08-10**  
**对象：以大语言模型推理为主，同时覆盖 reasoning/RL rollout、多模态、语音、视觉生成和端侧等已经形成独立分支的工作。**

> 状态说明：本文把“已经同行评审发表/接收”和“arXiv 预印本”分开看待。2026 年 6–8 月的大量结果仍是预印本，表中的数值均是论文作者报告值，不应视作跨论文可直接比较的统一榜单。检索日是 8 月 10 日；当时 arXiv API 可见的最新一批相关投稿日期为 8 月 6 日。

## 0. 结论先行

1. **Speculative decoding（SD）已经从单一算法演变成完整的算法—模型—kernel—serving 协同设计问题。** 2023 年的主问题是“能否用小模型起草、由大模型无损验证”；2024–2025 年转向 feature drafter、树验证、模型内多头、检索和长上下文；2026 年最活跃的主线则是：如何同时得到**一次并行起草的低成本、块内/分支内因果一致性、以及多请求下不过度浪费验证预算**。
2. **DSpark 是必须单列的关键工作，但不是孤立终点。** 它位于 DFlash 的全块并行起草和 autoregressive drafter 之间：用并行 backbone 预测整个 block，再用低秩 Markov/RNN head 引入很便宜的顺序依赖，并用 prefix-survival confidence 做硬件和负载感知的验证长度调度。其 DeepSeek-V4 线上结果很强；与此同时，PCTree、xPress、DBLAST、DeLS-Spec、CURE、AngelSpec 等紧接着暴露或修补了 chain early-failure、独立边缘分布、随机采样、局部不确定性和跨请求预算等问题。
3. **“accepted length 更高”不等于“更快”。** 端到端每 token 延迟近似为
   \[
   L_{tok}=\frac{T_{draft}+T_{verify}+T_{schedule}+T_{misc}}{\mathbb E[\tau]},
   \]
   其中 \(\tau\) 是一次 target verification 后实际前进的 token 数。batch、上下文长度、树宽、KV 读写、MoE expert union、CUDA Graph 形状以及调度开销都会改变分子；因此 batch=1、Transformers backend 上的 6–9×不能直接外推到高并发 serving。
4. **“lossless”有三个容易混淆的含义。** greedy 下输出 token 序列完全一致；随机采样下输出分布严格等于 target 分布；语义/任务质量基本不变。只有前两者属于严格 lossless。MARS、fuzzy/relaxed verification、ASD、AcceptMoE 等改变接受规则、路由或目标分布的工作，需要单独报告质量和分布偏差，不能与严格验证混在同一列。
5. **到今天仍值得研究的，不是泛泛的“训练一个更准的 draft model”，而是几个交叉空白：** 分布漂移下可校准的 prefix-survival 调度；随机采样下具有联合因果结构、但仍能并行执行的 block drafter；拒绝之后 verifier 已算后缀的严格无损复用；多租户 goodput/SLO 下的验证资源分配；acceptance-collapse 的鲁棒防御；长上下文 hybrid/linear-attention target 中 draft KV 的独立设计。
6. **推荐优先切入的题目**是“**分布漂移鲁棒、带风险控制的 confidence-scheduled lossless SD**”。它可以直接以 DSpark 为强基线，输出仍由 target 严格决定，研究变量集中在 calibration、online shift detection 和 goodput regret；相较再做一个 block head，赛道拥挤度更低、系统价值更明确，也更容易构造可证伪的实验。

## 1. 调研范围与可复现检索

### 1.1 检索源

- arXiv API：用于高召回检索、去重、获取版本日期/作者/摘要；
- 官方论文集：PMLR（ICML）、ACL Anthology、NeurIPS Proceedings、MLSys Proceedings；
- OpenReview/ICLR 官方页面；
- 官方实现/文档：vLLM、SGLang、TensorRT-LLM、Transformers，以及作者公开仓库；
- 只把博客和搜索结果用于发现线索，技术判断尽量回到论文、官方代码或官方文档。

### 1.2 检索式与数量

执行的 arXiv 高召回检索式包括：

```text
"speculative decoding"       "speculative sampling"
"assisted decoding"          "assisted generation"
"draft-and-verify"           "draft and verify"
"multi-token prediction"     "parallel decoding"
"lookahead decoding"         "blockwise parallel decoding"
```

去重后得到 **1,260 条候选记录**。自动初筛标记为 `probable_core` 703 条、`adjacent` 22 条、`screen_out` 535 条。这个数字不是“703 篇 SD 论文”的主张：高召回检索会收进只在摘要中把 SD 当 baseline 的论文，也会漏掉标题和摘要不使用上述术语的相关系统。因而本调研采用两层产物：

- [`literature_candidates.csv`](../metadata/literature_candidates.csv)：1,260 条可搜索候选，保留摘要、检索式、自动 track 标签和筛选理由；
- 本文：人工确认并综合主干、分支、反例、系统落地与 2026 年前沿。

目录由本次检索流水线生成。自动标签仅用于检索，不应替代全文阅读。

### 1.3 纳入与排除原则

纳入：直接提出或分析 draft–verify、multi-draft/tree verification、MTP/多头起草、self-speculation、retrieval/lookahead 起草、验证规则、serving 调度、长上下文/MoE/异构词表，以及 SD 在 RL rollout、多模态、语音和视觉生成中的扩展。

排除：仅把 “speculative” 当普通英语、与语言/生成推理无关的 speculative execution、只在 related work 中提及 SD 且贡献不相关的模型，以及纯粹更快的 autoregressive kernel（除非其作用会系统性改变 SD 的成本模型）。

### 1.4 完整性的边界

“完整”在这里表示：检索式、候选集、筛选边界和主要分支均可追溯，而不是声称互联网上不存在遗漏。尤其 2026 年论文增长很快、同一工作可能多次改名或更新版本；正式选题前，应对目标子方向再做一次 citation chaining（参考文献向后追、Google Scholar/Semantic Scholar 向前追）和代码仓库 issue 检查。

## 2. 基本形式化：哪些量真正决定收益

设 target 分布为 \(p(\cdot\mid x_{<t})\)，draft 分布为 \(q(\cdot\mid x_{<t})\)，一次提出 \(\gamma\) 个 token。对单 draft token 的经典随机验证：

\[
y\sim q,\qquad P(accept\ y)=\min\left(1,\frac{p(y)}{q(y)}\right).
\]

若拒绝，则从归一化残差 \((p-q)_+\) 中重采样。逐位置执行该规则可严格恢复 target 的采样分布。greedy 模式则保留与 target argmax 一致的最长前缀，并由 target 补一个 token。树方法把单链候选扩展为多个路径，但“最终 token 是否由 target 的严格规则决定”仍是无损性的核心。

常见的 i.i.d. 简化中，若每个位置接受率为 \(\alpha\)，一次期望前进 token 数为

\[
\mathbb E[\tau]=\frac{1-\alpha^{\gamma+1}}{1-\alpha}.
\]

若 draft 每步相对 target 的成本是 \(c\)，经典链式近似 speedup 为

\[
S\approx \frac{1-\alpha^{\gamma+1}}{(1-\alpha)(1+\gamma c)}.
\]

这个式子解释了 2026 年竞争的本质：autoregressive EAGLE 具有较好的 path conditioning，但 \(\gamma c\) 随深度增大；DFlash 把 draft 近似压成一次 pass，使 \(c\) 很小，但独立的 position marginals 令远端 \(\alpha_i\) 快速下降；DSpark、Domino、JetSpec、xPress、DBLAST 分别尝试用不同结构同时压低 \(c\) 并维持条件一致性。

实际 serving 至少还要分解：

\[
S_{e2e}=\frac{T_{AR}(B,L,H)}{T_{draft}(B,L,\gamma)+T_{verify}(B,L,N_{tree})+T_{schedule}+T_{KV}+T_{kernel}},
\]

其中 \(B\) 是并发/batch，\(L\) 是上下文长度，\(H\) 表示硬件和 engine。低并发时 target decoding 往往 memory-bound，一次验证多个 token 的边际代价较小；高并发时 verifier 更接近 compute-bound，额外候选会挤占 batch capacity，SD 甚至可能减速。

## 3. 统一分类框架

一篇工作最好沿五个正交维度定位，而不是只问“属于哪一种 SD”。

| 维度 | 主要选项 | 代表方法 |
|---|---|---|
| proposal 来源 | 独立小 LM；target feature/head；原模型浅层；检索/复制；原生 MTP | Leviathan/Chen；EAGLE；Draft & Verify；REST/Oilbird；DeepSeek/Qwen native MTP |
| proposal 执行 | autoregressive chain；多头并行；block/diffusion；semi-AR；parallel causal tree | EAGLE；Medusa/PARD；DFlash；DSpark/Domino；JetSpec/xPress |
| 候选拓扑 | chain；宽度固定 tree；动态 tree；retrieval graph；多 drafter | vanilla；SpecInfer/Medusa；EAGLE-2/Sequoia；REST/SpecExec；Global Resolution |
| verification | exact greedy；exact stochastic；block/tree；稀疏/分层；relaxed/lossy | 标准 longest prefix；rejection sampling；SpecInfer；Block Verification/Dustin；MARS/ASD |
| 系统策略 | 固定长度；per-request 自适应；batch-level 预算；SLO/load aware；在线选择/适配 | fixed-\(\gamma\)；EAGLE-2；TETRIS/D-cut；DSpark/AngelSpec；Online SD/Not-a-Bandit |

另外还有三个贯穿维度：是否需要训练/每个 target 单独训练，是否共享 tokenizer/vocabulary，是否对 target 架构（dense/MoE/MLA/hybrid attention）有假设。

## 4. 发展时间线

### 4.1 2018–2023：从 blockwise prediction 到严格 draft–verify

- [Blockwise Parallel Decoding (2018)](https://arxiv.org/abs/1811.03115) 已经提出用多输出 heads 一次预测一个 block，可视为后续 MTP/Medusa 的先声。
- [Speculative Decoding: Exploiting Speculative Execution for Accelerating Seq2seq Generation (2022)](https://arxiv.org/abs/2203.16487) 和 [Fast Inference from Transformers via Speculative Decoding (2022)](https://arxiv.org/abs/2211.17192) 建立早期框架。
- [Leviathan et al., ICML 2023](https://proceedings.mlr.press/v202/leviathan23a.html) 与 [Chen et al.](https://arxiv.org/abs/2302.01318) 奠定现代严格 speculative decoding/sampling：小模型 sequential draft，大模型一次并行 score，拒绝采样保持 target 分布。
- [SpecInfer](https://arxiv.org/abs/2305.09781) 把多个候选组织为 tree，并以 tree attention/verification 面向 serving。
- [Draft & Verify](https://arxiv.org/abs/2309.08168) 发展 self-speculative decoding；[Online Speculative Decoding](https://arxiv.org/abs/2310.07177) 让 drafter 根据在线流量适配；[DistillSpec](https://arxiv.org/abs/2310.08461) 系统研究蒸馏目标；[SpecTr](https://arxiv.org/abs/2310.15141) 从 optimal transport 推导多候选验证；[REST](https://arxiv.org/abs/2311.08252) 证明检索 datastore 也能起草。

### 4.2 2024：feature drafter、树、检索和系统化评测

- [EAGLE](https://proceedings.mlr.press/v235/li24bt.html) 不再让小 LM 从头建模，而是使用 target hidden feature 预测未来，并显式处理 feature uncertainty；[EAGLE-2](https://aclanthology.org/2024.emnlp-main.422/) 用置信度动态构树。
- [Medusa](https://arxiv.org/abs/2401.10774) 用多个 decoding heads 并行预测不同未来位置；[Hydra](https://arxiv.org/abs/2402.05109) 在多头之间加入顺序依赖；[ReDrafter](https://arxiv.org/abs/2403.09919) 结合 recurrent drafter 与动态 tree。
- [Sequoia](https://arxiv.org/abs/2402.12374) 共同优化 sampling、tree construction 与 systems；[SpecExec](https://arxiv.org/abs/2406.02532) 研究大规模并行 speculative execution。
- 训练免费方向包括 [Lookahead Decoding](https://arxiv.org/abs/2402.02057)、[REST（NAACL 2024）](https://aclanthology.org/2024.naacl-long.88/)、Token Recycling、Ouroboros、prompt lookup/n-gram 和后来的 [SuffixDecoding](https://arxiv.org/abs/2411.04975)。
- 长上下文方向形成 [TriForce](https://arxiv.org/abs/2404.11912)（分层 draft/KV retrieval）与 [MagicDec](https://arxiv.org/abs/2408.11049)（长上下文下 verification 的相对成本优势）。
- [Spec-Bench/ACL 2024 survey](https://aclanthology.org/2024.findings-acl.456/) 给出六类任务的统一基准，标志着研究开始从单一 benchmark 的 acceptance rate 转向可比评测。

### 4.3 2025：EAGLE-3、训练目标、异构性和 production serving

- [EAGLE-3](https://proceedings.neurips.cc/paper_files/paper/2025/hash/c7b5a35ea98b62512a869c19ea7b03cb-Abstract-Conference.html) 放弃 EAGLE-1/2 的显式 feature prediction，改为直接 token prediction，并融合 target 多层 features、让训练时输入更接近推理轨迹；它成为 2025–2026 最常见强基线之一。
- [HASS（ICLR 2025）](https://openreview.net/forum?id=T9u56s7mbk) 针对 draft-head 与 target 的上下文/分布对齐；[Block Verification（ICLR 2025）](https://openreview.net/forum?id=frsg32u0rO) 重新设计验证单位；PARD、FR-Spec、CORAL、DReSD 等分别探索并行 draft、特征选择、结构化训练和更高效验证。
- [PARD](https://arxiv.org/abs/2504.18583) 用 Conditional Drop-token 把 AR drafter 低成本适配为并行预测，并追求同一 drafter 适配 target family；这条路线在 2026 年延伸为 P-EAGLE。
- [LongSpec](https://arxiv.org/abs/2502.17421)、[SpecExtend](https://arxiv.org/abs/2505.20776)、异构 tokenizer/vocabulary、[SAM](https://aclanthology.org/2025.acl-long.595/)、[Fuzzy SD](https://aclanthology.org/2025.findings-acl.1346/) 和 TETRIS 等把上下文、词表映射、verification sparsity 与 serving scheduling 推向独立问题。
- [Decoding Speculative Decoding（NAACL 2025）](https://aclanthology.org/2025.naacl-long.328/) 等分析性工作开始质疑只看平均接受率的惯例。

### 4.4 2026：parallel drafting 的因果性修复与 serving 资源化

2026 年的中心变化是把 proposal block 看成一个“既要一次/少数次生成、又要近似 target joint autoregressive factorization”的对象，而不再只是独立的 \(K\) 个 future-token heads。

- [P-EAGLE](https://arxiv.org/abs/2602.01469)：learnable shared hidden state + parallel MTP；解决 20K 长序列并行预测训练的 mask 和 sequence partitioning 问题。
- [DFlash](https://arxiv.org/abs/2602.06036)：轻量 block-diffusion head，以 target fused features 为条件，一次 forward 生成整个 draft block。
- [Domino](https://arxiv.org/abs/2605.29707)、[TreeFlash](https://arxiv.org/abs/2606.03819)、DFlare：分别用轻量 causal correction、两阶段 AR approximation、layer-wise target feature fusion 修复 DFlash 的表达/因果瓶颈。
- [JetSpec](https://arxiv.org/abs/2606.18394)：用 block-level causal attention 一次生成 branch-conditioned candidate tree，使大 tree budget 真正转化为更长接受前缀。
- [DSpark](https://arxiv.org/abs/2607.05147)：parallel backbone + 低秩 Markov/RNN head + prefix survival confidence + hardware/load-aware scheduler，在 DeepSeek-V4 live traffic 中验证。
- DSpark 之后很快出现 [PCTree](https://arxiv.org/abs/2608.02123)、[xPress](https://arxiv.org/abs/2608.02438)、[DBLAST](https://arxiv.org/abs/2608.05448)、[CURE](https://arxiv.org/abs/2608.00531)、[DeLS-Spec](https://arxiv.org/abs/2607.07409) 与 [AngelSpec](https://arxiv.org/abs/2607.25852)，表明“并行但有条件依赖”的设计空间尚未收敛。
- 系统面，[Performance or Illusion?（MLSys 2026）](https://proceedings.mlsys.org/paper_files/paper/2026/hash/554e056fe2b6d9fd27ffcd3367ae1267-Abstract-Conference.html) 和 [SPEED-Bench](https://arxiv.org/abs/2604.09557) 把 production engine、batch、ISL 和 verifier bottleneck 放到中心；DSpark、AngelSpec、D-cut 则开始把 verification token 当作多请求共享资源。

## 5. 各技术分支的深入比较

### 5.1 独立小模型 drafter：最清楚的理论，未必是最好的系统结构

经典 drafter–target 方案的优点是模块化：target 不需改权重，任意便宜模型都可作为 \(q\)，随机 rejection sampling 的正确性清楚。核心困难是：

- drafter 过小，\(q\) 与 \(p\) 分布差、接受率低；过大则 draft latency 和额外权重/KV 带宽吃掉收益；
- tokenizer/vocabulary 不同会让 token-level verification 和残差采样变复杂；
- reasoning、代码和低资源语言上，小 drafter 与 target 能力差距并不均匀；
- 同一个最优 draft length 会随请求、temperature、batch 和硬件改变。

代表性的修复包括 DistillSpec/HASS 的分布对齐、Online SD 的流量适配、cascade/staged drafting、多 drafter 选择，以及 [Not-a-Bandit](https://arxiv.org/abs/2510.20064) 对在线 drafter selection 的 no-regret 解法。[Speculative Decoding and the Curse of Multilinguality](https://arxiv.org/abs/2605.30580) 则给出重要负面证据：小模型在低资源语言上的能力瓶颈会系统性降低 SD 效果，任务内蒸馏也未必跨任务泛化。

### 5.2 Feature drafter 与 EAGLE 系列：让 target 的表示替 drafter 完成“理解”

EAGLE 的关键不是简单加一个 head，而是让 drafter 读取冻结 target 的上下文 feature，因此小得多的模块也能预测未来。演化过程是：

1. **EAGLE-1**：预测下一时刻的 feature distribution，再由 target LM head 映射到 token；指出 feature uncertainty 不能忽略。
2. **EAGLE-2**：根据 candidate confidence 动态扩展/裁剪 draft tree，减少固定树对预算的浪费。
3. **EAGLE-3**：直接进行 token-level training，融合 target 浅/中/深层 features，并采用更贴近推理分布的训练策略；速度与易部署性使其成为生产框架的默认强 baseline。

局限也很明确：传统 EAGLE 起草仍是 autoregressive，tree depth 越深需要越多小 head passes；每个 target/checkpoint 通常需要特定训练；feature 接口、LM head/vocab 和 target architecture 造成强耦合。P-EAGLE、DFlash 和 DSpark 都可视为“保留 target-conditioned 小模块，但消除其顺序 pass”的不同答案。

### 5.3 Multi-head/MTP：原生能力、后训练 head 与并行位置独立性

Medusa 给每个未来 offset 一个 head，能在一次 target-like context 上并行产生候选；Hydra 让后续 head 依赖前面候选，缓和独立 head 不一致；ReDrafter 将轻量 recurrent 模型与 tree 结合。原生 MTP 则在 base model 预训练/中训练时加入 future-token heads，DeepSeek、Qwen/Nemotron 等模型已经把它作为部署接口的一部分。

MTP 的系统优势是无需加载独立完整 LM，但“head 很小”不代表长上下文下便宜：[Windowed-MTP](https://arxiv.org/abs/2607.21535) 指出，在百万 token context，native MTP head 每个 draft step 读取 full-context KV，成本会反客为主，尤其 target 使用 hybrid/linear attention 时 verifier 更便宜，draft full attention 更显眼。其仅对 draft attention 使用 sliding window + attention sink，target 仍完整验证，因此保持严格分布正确性。

P-EAGLE 的共享 hidden state 让多个 MTP 位置一次计算，并以 mask 预计算、序列内 gradient accumulation/partitioning 把训练扩展到 20K context。论文在 vLLM 上报告相对 autoregressive EAGLE-3 的 1.10–1.36×；这个相对增益比 DFlash 的宣传数字小，却更接近“在已有强系统上再消除 sequential drafting”的实际问题。

### 5.4 Tree、多候选与 proposal topology

单链的第一个错误会使后缀全部作废。tree 用宽度换取至少一条 path 命中的概率，但代价是 target 需要 score 更多 nodes、tree attention 需要定制 kernel、MoE 会激活更大的 expert union。

- SpecInfer：多 drafter/候选 tree + tree-based parallel verification；
- Medusa/Hydra：多 offset heads 形成 candidate tree；
- Sequoia：从 sampling、tree topology 到 system kernel 联合优化；
- EAGLE-2：confidence-adaptive tree；
- SpecExec：用大规模 speculative execution 扩展候选；
- [Global Resolution（ICLR 2026 oral）](https://openreview.net/forum?id=gpsczXOsHn)：把 i.i.d. multi-draft 的最优 transport 从指数变量问题化为至多 vocabulary 维的凸优化；
- JetSpec：不再从互相独立的 position marginals 拼树，而是直接训练 branch-wise causal parallel tree head；
- PCTree：无需重训，把 DSpark 已学到的 parent-conditioned Markov 能力从 chain 转成 tree。

树不是免费午餐。相同“draft length”可能指 depth、总 nodes 或实际 target-scored nodes，跨论文必须统一 node budget。高并发时，扩大 tree 常常只增加 verifier compute 而不增加 goodput；这也是 TETRIS、D-cut、DSpark scheduler 和 AngelSpec 转向 batch-level budget 的原因。

### 5.5 Training-free：检索、n-gram、lookahead、suffix 与 verifier keys

REST、prompt lookup、n-gram、SuffixDecoding、Token Recycling、Lookahead/Ouroboros 的共同点是从当前 prompt、历史生成、外部 datastore 或 Jacobi trajectory 中找到可能的 continuation。优势是零训练、几乎零额外参数、领域内重复高时收益突出；缺点是 exact matching 的 coverage 和 addressing 很脆弱，开放式高熵生成较弱，索引/匹配本身也会有 CPU/GPU 与调度成本。

[Oilbird](https://arxiv.org/abs/2608.03839) 是这条线截至检索日最值得关注的更新之一：它观察到 tool-calling 中正确 continuation 常已在 pool 中，但 exact suffix 因少量 request-specific values 而无法寻址；于是使用 verifier 在已提交 token 上本来就计算出的 hidden states 作为 semantic keys，并把 semantic candidates 合并进 lexical drafter tree。它代表一个更一般的方向：**重用 target 已付费产生的中间表示来改进 training-free addressing**。

### 5.6 Self-speculative / early exit：共享权重，承担表示错位

Draft & Verify/LayerSkip 类方法用 target 的早期层或跳层子网起草，再由完整层验证。它们无需额外模型权重，适合显存受限场景；但 draft 与 target 共享的 KV/hidden states 是否可复用、早层 LM head 是否校准、跳层后的表示是否足够稳定，都会决定收益。此线后来发展出动态 exit、sparse glimpse、MoE expert subset/self-speculation 等变体。

其理论正确性仍来自“完整 target 最终决定接受”，而不是早退网络本身。若为了省 verifier 成本而限制 target layers/experts，就从 lossless proposal optimization 跨到了 approximate target computation，需要重新报告分布和质量。

### 5.7 Verification：严格规则、稀疏计算与有损放宽

验证侧至少有四个不同问题：

1. **严格随机验证**：残差采样保证输出分布为 target；多候选时涉及 coupling/optimal transport。
2. **严格 greedy/tree coverage**：看 target argmax 是否在 chain/tree 中，直到第一条不可接受边；[When Is a Draft Accepted?](https://arxiv.org/abs/2606.30265) 为 greedy、relaxed、top-m 和 tree coverage 给出 margin/KL certificates。
3. **减少 verifier 的实际工作量**：Block Verification、hierarchical/sparse verification、Dustin、D-cut 等不只是改变规则，还要使 kernel 真正少算或少搬数据。
4. **relaxed/lossy**：fuzzy/top-k/margin/semantic 接受、ASD 和 collaborative verification 用质量换接受长度。

[Revisiting Lossy Verification](https://arxiv.org/abs/2607.26627) 把已有方法归为 truncation-based 和 collaborative verification，并指出“看似只放宽一点”也可能因诱导分布失真而严重降质；collaborative 类必须控制 draft probability 相对 target 的 overshoot。[Approximate SD (ASD)](https://arxiv.org/abs/2608.03447) 在 DSpark 上用 local target-logit regret、block exception cap 和 request-level regret budget 选择性跨过 mismatch，并复用其后的 target-greedy suffix；它有清楚的零预算严格退化点，但非零预算仍是近似算法。

### 5.8 长上下文：proposal accuracy 与 KV/verification cost 同时变化

长上下文不是简单把短上下文 benchmark 的 \(L\) 调大：

- 小 drafter 的 attention/KV 容量不足，target 与 draft 的 relevant context 不一致；
- target verification 一次处理多个 token 的相对成本可能随 \(L\) 更有利（MagicDec），也可能被 KV bandwidth/attention kernel 吞没；
- tree mask、position、KV append/rollback 和 prefix sharing 变成主要系统成本；
- native MTP 自身可能有 full-context KV tax。

TriForce 用 draft hierarchy 与 retrieval KV；LongSpec 训练轻量 long-context speculator；SpecExtend 用 target attention scores 为 draft 做 cross-model retrieval/KV eviction；Windowed-MTP 限制 draft-only attention；Dustin 做长上下文稀疏 verification。这些工作说明未来应把 **target context、draft context、verification context** 当作三个可独立设计的对象。

## 6. 2026 parallel/block drafter 族谱

| 方法 | draft 执行 | 块内/分支依赖 | 候选拓扑 | 调度 | 严格性 | 当前主要限制 |
|---|---|---|---|---|---|---|
| PARD | 一次 parallel MTP | shared context，位置间弱/间接 | chain/tree | 固定 | target 严格验证 | standalone/family 适配；长序列训练困难 |
| P-EAGLE | shared hidden state + parallel positions | 由 attention/position 编码，非已采样 prefix 条件 | chain | 固定 \(K\) | 严格 | 长序列训练已改善；joint dependency 仍有限 |
| DFlash | block diffusion head 一次 pass | 主要是 position marginals/bidirectional block 表示 | chain 或从 marginals 拼 tree | 固定 block | 严格 | tokens 单独合理但 joint sequence 不一致 |
| Domino | parallel backbone + 轻量 Domino causal head | prefix-dependent correction | chain | 固定 | 严格 | 校正结构/训练需与 backbone 联训 |
| TreeFlash | 一次 backbone + 两阶段 MLP approximation | previous-token conditioned AR approximation | tree | 固定 budget | 严格 | 近似依赖能力和 tree kernel 仍受 budget 约束 |
| JetSpec | causal parallel tree head 一次 pass | block-level causal attention，branch-conditioned | tree | tree scoring/budget | 严格 | 大树在高并发 verifier 侧可能不划算 |
| DSpark | parallel backbone + 极轻低秩 Markov/RNN sequential head | first-order/轻状态的 intra-block dependency | 原始为 chain | prefix-survival + load/hardware scheduler | 严格 | chain early failure；校准漂移；依赖阶数有限 |
| PCTree | 复用 DSpark backbone/Markov head | 每个 concrete parent 单独 score child | tree | fixed verification budget | 严格 | tree verification cost；目前依赖 DSpark 条件结构 |
| DeLS-Spec | frozen DFlash + 独立 local NTP head | long-context expert + short-context causal expert | chain | 固定 | 严格 | logits fusion 的普适性与随机场景待验证 |
| xPress | 整块 parallel causal refinement | 无 token loop 的全块因果传播 | chain/block | 固定 | 严格 | parallel refiner 的真实 kernel 成本和扩展性 |
| CURE | parallel block + 不确定点 repair tree | 只在 fragility nodes 展开路径 | 动态局部 tree | confidence/budget aware | 严格 | error localization 与额外 tree 开销的权衡 |
| DBLAST | low-rank latent mixture over positions | 随机采样下的 joint dependence | block | 固定 | target 严格随机验证 | 目前模型/任务规模有限，速度结果仍需完整系统验证 |
| AngelSpec/DFly | hybrid conditioning + predecessor-conditioned head | intra-block causal | MTP 或 block | batch-level utility + profiled cost | target 严格验证 | 数据/结构/系统一体化，归因和跨硬件复现更难 |

这张表揭示了一个尚未解决的核心：要近似的并非 \(\prod_i p(x_{t+i}\mid x_{<t})\)，而是

\[
p(x_{t:t+K}\mid x_{<t})=\prod_{i=0}^{K-1}p(x_{t+i}\mid x_{<t},x_{t:t+i}).
\]

完全并行 position heads 容易学到前者的边缘预测；AR drafter 精确遵循后者的 factorization，却付出顺序 latency。当前所有 semi-AR/causal-parallel 方法，本质上都在选择一个低成本的结构来近似后一个 joint distribution。

## 7. DSpark 深入拆解

### 7.1 它具体解决什么

DFlash 已把 block drafting 压到一次并行 pass，但长 block 的后半段因缺少对已起草 token 的条件依赖而 acceptance decay。另一方面，在 continuous batching 中，即使长 block 中后部几乎必然被拒绝，统一把它们送入 target verification 仍占用 batch/token capacity。DSpark 同时处理：

- **模型侧：**补块内依赖，提高 long-prefix survival；
- **系统侧：**预测每个位置“此前所有 token 都能存活”的概率，只验证值得占用资源的前缀。

### 7.2 架构

1. **Parallel backbone**：DFlash 风格，一次产生整个 block 的 context-conditioned representations/distributions。
2. **低秩 Markov head**：默认把 transition/correction 矩阵写成 \(B=W_1W_2\)，论文默认 rank 256；在 block 内以非常小的 sequential sampling 开销让当前位置依赖前一 token。论文也讨论 RNN 变体。
3. **Confidence head**：预测每个位置的 prefix survival probability，而不只是该位置 token 的独立置信度；通过 post-hoc calibration 把 ECE 降到约 1%。
4. **Scheduler**：结合 confidence 与 engine profiling，给不同请求选择 truncation length \(K\)。生产实现使用约两步之前的 confidence，异步完成调度并维持 CUDA Graph 形状；它只裁剪候选验证长度，target verification 规则不变，所以不会改变最终 target 分布。

训练/模型已以 [DeepSpec](https://github.com/deepseek-ai/DeepSpec) 形式公开；vLLM Speculators 也提供了 [DSpark 算法文档](https://docs.vllm.ai/projects/speculators/en/latest/user_guide/algorithms/dspark/)。

### 7.3 论文报告的关键结果

- Qwen3 4B/8B/14B 离线宏平均 accepted length，相比 EAGLE-3 分别提高约 30.9%/26.7%/30.0%，相比 DFlash 提高 16.3%/18.4%/18.3%；
- block 上限增大时相对 DFlash 优势扩大：论文给出的 \(\gamma=7\) 下 math/code/chat 约 +16%/+15%/+18%，\(\gamma=15\) 下约 +30%/+26%/+22%；
- batch=128 时，proposal length 从 4 增到 16 的 full-round latency 增幅仅约 0.2–1.3%，说明 draft block 本身非常便宜；
- confidence pruning 将作者报告的 chat/math/code 接受率从 45.7/76.9/67.6% 提至 95.7/92.5/92.0%（这里是被选中验证 token 的条件接受率，不等同于每请求生成速度）；
- DeepSeek-V4 live traffic、matched throughput 下，相比 production MTP-1，V4-Flash per-user generation speed 提高 60–85%，V4-Pro 提高 57–78%，并改善严格交互约束下的 Pareto frontier。

### 7.4 为什么它重要

DSpark 把 SD 优化目标从“每个 request 猜更长”改成“**在共享 verifier 容量下，把 token-slot 给最可能形成可接受前缀的请求**”。这与只做 dynamic \(\gamma\) 的差别在于：调度器显式依赖硬件 throughput profile 和并发状态。因此它是算法到 production goodput 之间的重要桥梁。

### 7.5 尚不能从论文直接推出什么

- DeepSeek-V4 线上模型、流量和完整 serving stack 不完全可复现；60–85% 是相对其 MTP-1 production baseline、matched throughput 的结果，不能直接与 Qwen + Transformers 的 6×相乘或比较；
- Markov head 主要表达局部/一阶依赖。代码、数学中长程约束和高温采样下的多模态 joint distribution，可能需要更丰富的 latent state；DBLAST/xPress 正在覆盖这块；
- 原始 chain 在早期 mismatch 后仍丢掉后缀，PCTree 已证明同一 Markov 条件能力可以在不重训 backbone 的情况下转成多分支；
- confidence calibration 是在给定训练/验证分布上完成的。domain、language、temperature、model update 和 traffic mix 变化时，ECE 与 survival ranking 是否稳定尚未充分回答；
- 两步陈旧 confidence 对高速变化 batch 的最优性未知；profiled scheduler 跨 GPU、quantization、kernel/engine 版本需要重新测量；
- 论文优化的是系统 Pareto frontier，但尚缺少带 SLO、尾延迟、公平性和 online regret 的统一理论目标。

因此，DSpark 更像一个高质量研究平台：它把 drafter、calibration、scheduler 和 production engine 同时暴露出来，留下的可研究问题比“再提高一点 accepted length”更有价值。

## 8. Serving、硬件与实现生态

### 8.1 为什么论文速度经常无法复现

SD 主要利用低并发 decoding 的 memory-bound 特性：target 权重已经从 HBM 搬一次，多 score 几个 token 的增量算力可能比再搬一遍权重便宜。当 batch 增大，GEMM 利用率上升，verification 额外 tokens 变成真实 FLOPs；此时 accepted prefix 不够长就会负收益。

[Performance or Illusion?](https://arxiv.org/abs/2601.11580) 在 production-grade vLLM 上比较 n-gram、EAGLE/EAGLE-3、draft model 和 MTP，核心观察是 target verification 占主导、accepted length 会随输出位置/请求/数据显著变化，实测速度与理论上界之间仍有大间隙。[SPEED-Bench](https://arxiv.org/abs/2604.09557) 进一步显示：synthetic inputs 会高估真实 throughput；最佳 draft length 随 batch 改变；低多样性数据会产生偏置；vocabulary pruning 也有隐蔽代价。

[Lossless but Not Free](https://arxiv.org/abs/2607.17283) 在 Apple silicon/consumer backend 上给出一个有用反例：五种 draft/target 配置中三种减速，原因包括 drafter 没有真正比小 target 快，以及 Metal backend 把所谓 parallel verification 串行执行。**算法的并行性必须落实到 backend，才是 wall-clock 并行。**

### 8.2 截止检索日的主流框架能力

| 框架 | 已公开的主要 speculative 路线 | 适合的研究用途 | 注意点 |
|---|---|---|---|
| [vLLM](https://docs.vllm.ai/en/stable/features/speculative_decoding/) | draft model、EAGLE、MTP、PARD/MLP、n-gram/suffix、DFlash/dynamic 等；另有 [vLLM Speculators](https://docs.vllm.ai/projects/speculators/en/latest/) | continuous batching、真实吞吐、DSpark/P-EAGLE/DFlash 集成 | 支持矩阵随版本快速变化；必须记录 commit/engine config |
| [SGLang](https://github.com/sgl-project/sglang/blob/main/docs_new/docs/advanced_features/speculative_decoding.mdx) | EAGLE-2/3、MTP、DFlash、standalone、n-gram 与 overlap scheduling | tree kernel、MoE、serving 与高并发 | 不同 backend/attention kernel 的树与 batch 行为差异很大 |
| [TensorRT-LLM](https://nvidia.github.io/TensorRT-LLM/examples/llm_speculative_decoding.html) | draft-target、Medusa、lookahead、MTP、n-gram 等 NVIDIA 优化路径 | H100/B200、production kernel、SPEED-Bench | build profile、quantization 和固定 shape 会改变结论 |
| [Transformers assisted generation](https://huggingface.co/docs/transformers/assisted_decoding) | assistant model、prompt lookup、动态 speculation 等 | 算法原型与正确性 | 不能代表 production throughput；Python/高层开销可能主导 |

### 8.3 Production 评测的最小报告规范

任何声称“更快”的工作至少应同时报告：

- **正确性：**greedy exact match；随机采样的分布检验/理论证明；若有损则给 target-only 同采样设置的质量和分布偏差；
- **proposal：**每位置 acceptance curve、accepted length 分布而不只均值、首个 rejection 位置、tree coverage、draft latency；
- **verification：**实际 target-scored nodes/tokens、verification latency、padding/无效 token 比例、MoE activated-expert union；
- **端到端：**tokens/s/user、aggregate throughput/goodput、P50/P95/P99 inter-token latency/TPOT、TTFT 与 SLO attainment；
- **条件：**target/drafter 精确 checkpoint、dtype/quantization、temperature/top-p、ISL/OSL、batch/concurrency/request rate、GPU 数量和型号、engine commit、kernel/CUDA Graph、warm-up；
- **成本：**额外参数、显存、draft KV、训练 tokens/GPU-hours、adapter per-target 成本、必要时 energy/token；
- **基线：**同一 engine 上经过调优的 AR、相同 quality 和 sampling config、相同请求 trace；固定深度和自适应策略都要调参。

特别应避免：只报 batch=1；只用 Hugging Face baseline；只报 Math/Code 的 temperature=0；用总 tree nodes 不同的方法比较“同一 draft length”；忽略 target bonus token 的记账差异；用 synthetic repeated prompts 测吞吐；把 accepted length 提升直接写成 speedup。

## 9. 扩展场景与正在形成的独立问题

### 9.1 Reasoning 与 RL rollout

长 CoT 让 SD 的总收益更大，但 target policy 在 RL post-training 中不断更新，静态 drafter 会迅速 stale。已有方向包括 CAS-Spec/Lookahead Reasoning、EfficientRollout、WAR、FastGRPO 类 rollout 系统以及 [SpecRoll](https://arxiv.org/abs/2608.04962)。SpecRoll 用 future-token heads 并行 proposal，fast path 根据延迟 verifier feedback 做无反传的 trajectory-local hidden correction，slow path 只在持续退化时更新 head；target verification 仍严格，因此 GRPO objective 不变。这个方向很重要但已快速拥挤，新的工作必须同时比较 rollout generation 和完整 RL wall-clock，而不能只报 token generation。

### 9.2 MoE

MoE target 的 verification cost 不只由 token 数决定，还取决于候选节点激活专家的并集和 offload/cache residency。减少 tree nodes 未必同比减少 expert weight traffic。[AcceptMoE](https://arxiv.org/abs/2608.02989) 用 target router score、commitment probability 和 cache residency 动态限制 verifier expert eligibility；但这改变 target routing/distribution，属于近似 target computation。另一类安全方向是在 proposal 或 scheduler 侧减少会触发巨大 expert union 的候选，保持 full target 自然路由；这仍有明显空白。

### 9.3 异构 vocabulary/tokenizer

经典接受是 token 对 token，draft/target tokenizer 不同会导致一对多/多对一边界和概率映射。[Heterogeneous Vocabulary SD（ICML 2025）](https://proceedings.mlr.press/v267/timor25a.html)、UniSpec、SpecVocab 等分别从 universal drafter、映射与动态 speculative vocabulary 解决。最新 [SpecVocab](https://arxiv.org/abs/2602.13836) 每步选择 vocabulary subset，针对 output embedding 成为 drafter 时间瓶颈的问题。未解决点是：任意 tokenizer 的严格 stochastic coupling、动态词表 kernel，以及跨语言/代码/byte fallback 的尾部分布。

### 9.4 Multimodal、speech、image/video 与 VLA

这不是把 text SD 原样移植：

- VLM 的 vision tokens/prefix 很长，acceptance 同视觉内容和语言阶段变化；MMSpec 开始统一评测；
- Speculative Streaming 研究流式多模态/语音输出；SpecTTS、ParaASR 分别面对 acoustic/code tokens 与长上下文 ASR；
- autoregressive image/video token 的空间/时间冗余支持 spatial/speculative decoding，但验证结构不再只是文本最长前缀；
- VLA/autonomous driving 中 action token 的安全性和 real-time deadline 比平均 throughput 更重要。

因此多模态研究应明确“因果轴”是文本序列、时间、空间 raster order 还是 action chunk，并重新定义可接受前缀和质量不变性。

### 9.5 Edge–cloud 与端侧

异构网络下可以在 edge 起草、cloud target 验证，但 draft tokens/logits、KV 和网络 RTT/带宽决定是否有收益。WANSpec、AsymSpec、Speculation at a Distance、EdgeXpert 等已开始建模。真正有意义的基线必须包括本地小模型直接回答、cloud AR、pipeline overlap 和网络抖动；只减 GPU forward 次数不足以证明 edge-cloud latency 改善。

### 9.6 Tool calling、constrained decoding 与结构化输出

tool/JSON/grammar 场景通常有很强可预测模板，因此非常适合 retrieval/speculation；同时 request-specific values 会破坏 exact suffix match，Oilbird 已针对 addressing 修复。尚需处理：grammar mask 在每个 tree node 的状态不同、tokenizer 边界、tool execution 引入外部状态、以及 rejected branch 是否泄露或错误触发副作用。严格方案应保证只有 committed target token 能驱动 tool side effect。

## 10. 负面结果、安全与可靠性

### 10.1 Acceptance collapse 是独立攻击面

[Mistletoe](https://arxiv.org/abs/2605.14005) 通过优化 drafter–target mismatch、同时尽量保持 target 可见语义，令 accepted length/throughput 崩溃；[ADSD](https://arxiv.org/abs/2607.21804) 用 prompt suffix 和 verifier-aligned Soft-Collapse 直接压低接受率，在 GSM8K 上作者报告平均 sample time 增加 62.3% 而任务质量保持。lossless 只保证答案分布，不保证服务成本不受输入操控。

系统还可能泄露 per-token timing、是否接受/回滚、tree depth 或 architecture/optimization 信息。防御不能仅检测输出异常，应监控 acceptance residual、drafter-target disagreement、请求级 compute amplification，并有可预测成本的 AR fallback。

### 10.2 分布漂移与校准

不同 domain、语言、temperature、CoT 阶段和 prompt position 的 entropy 不同。平均置信度相同不代表 prefix survival 相同；对第 \(k\) 个 token，前缀存活是多个条件事件的乘积/联合事件。offline ECE 很低也不保证线上 ranking 和 tail-risk 稳定。DSpark/AngelSpec 把 confidence 用于资源分配后，校准错误会转化为 batch capacity 浪费甚至不同用户的服务不公平。

### 10.3 Lossy verification 的“质量看起来没掉”并不充分

任务准确率可能掩盖 calibration、diversity、rare mode、safety refusal、multilingual 和长尾事实性变化。relaxed 方法必须报告：与 target distribution 的 KL/TV 或可操作 proxy，多 seed 的任务质量，拒绝/安全集，temperature sweep，长期 repetition/degeneration，以及 regret budget 消耗位置。不能仅以 judge model 的平均分宣称“近似无损”。

### 10.4 训练与评测泄漏

大量 feature drafter 用 target 自生成 trajectories 训练；在 HumanEval/MT-Bench/GSM8K 上的高接受率可能来自 domain/style overlap。应公开 trajectory 来源、去重和 target sampling policy，并用 held-out model family、语言、prompt style 与真实 trace 检查是否只是 imitation of benchmark continuations。

## 11. 基准与建议的统一实验矩阵

### 11.1 现有基准互补关系

- **Spec-Bench**：六类典型应用，用于 method-level 可比性；样本和系统负载覆盖仍有限；
- **SPEED-Bench**：Qualitative split 强调语义多样性，Throughput split 覆盖 1K–32K ISL 和大 batch/并发，并对接 vLLM/TensorRT-LLM；更适合 production speed；
- **Performance or Illusion**：不是单一 dataset，而是 production vLLM 上的 variants × workloads × batch 系统剖析；
- **MMSpec**：面向 VLM 的 acceptance/速度测量；
- 领域 benchmark：GSM8K/MATH/AIME、HumanEval/MBPP/LiveCodeBench、MT-Bench、长文总结/RAG、tool-calling、multilingual、creative writing。它们应作为 entropy/structure 不同的 strata，而不是事后挑最好看的结果。

### 11.2 建议最小矩阵

若目标是发表一个新的通用 SD 方法，建议至少覆盖：

| 轴 | 最小设置 |
|---|---|
| target | dense 7–14B；MoE active-parameter 相近；至少一个 native-MTP 或 hybrid-attention 模型 |
| workload | open chat、math reasoning、code、summarization/RAG、tool/structured、至少 3 种语言 |
| sampling | greedy；temperature 0.7/top-p；temperature 1.0 或 creative high-entropy |
| ISL/OSL | 1K/4K/16K；reasoning 长输出；若声称 long context，再加 64K+ |
| load | batch/request concurrency 1/4/16/64，或以 arrival rate 做 open-loop trace |
| hardware | 至少一种 datacenter GPU；若声称 portable，再加另一代 GPU/consumer device |
| baselines | optimized AR、EAGLE-3、native MTP/P-EAGLE、DFlash、DSpark；按子问题加入 retrieval/tree/relaxed baseline |
| metrics | AL curve、draft/verify latency、E2E TPS、goodput/SLO、tail latency、memory、正确性/质量 |

跨方法公平比较时，至少同时固定两种预算：相同最大 verifier nodes/tokens，以及各方法经开发集调优后的最佳 wall-clock。前者看算法效率，后者看实际可用性。

## 12. 尚未充分解决的问题地图

评分含义：**新颖空间**是从本次检索判断的相对空间，不是 novelty 保证；**拥挤度**反映 2025–2026 新论文密度；**风险**包括理论不可行、系统实现量或快速被同期工作覆盖。

| 编号 | 问题 | 最接近工作 | 真正空白 | 新颖空间 | 拥挤度/风险 |
|---|---|---|---|---|---|
| G1 | 分布漂移下的 prefix-survival calibration | DSpark、AngelSpec、D-cut | domain/language/temp/model update 后有风险控制的在线校准与 SLO regret | 高 | 低–中；需真实/合成 shift trace |
| G2 | 随机采样下的 causal-parallel joint drafter | DSpark、Domino、xPress、DBLAST、JetSpec | 高熵、多模态 continuation 下兼具联合依赖、并行 scan 和 acceptance-oriented training | 中 | 极高拥挤；迭代速度必须快 |
| G3 | 严格无损地利用首个 rejection 之后的 verifier 计算 | tree verification、CURE、ASD | 不接受近似 mismatch 的前提下，把已 score suffix/hidden/KV 转成后续可提交工作 | 很高 | 高理论风险：prefix 改变使旧 logits 通常失效 |
| G4 | 多租户 goodput/SLO 的验证预算分配 | TETRIS、DSpark、D-cut、AngelSpec | arrival-rate、tail latency、公平性、stale confidence 与 CUDA shape 联合优化，带 online regret | 中–高 | 中；系统工程较重 |
| G5 | Acceptance-collapse 鲁棒防御 | Mistletoe、ADSD | 保持 target 输出不变的检测、robust proposal ensemble、compute amplification bound 和 fallback | 高 | 低；需要自适应攻击评测 |
| G6 | Hybrid/linear attention 与 draft KV 的解耦 | MagicDec、SpecExtend、Windowed-MTP、Dustin、Bole | target/draft/verify 三套 context policy 的自动联合选择 | 中–高 | 中；长上下文实验昂贵 |
| G7 | 可移植的 SD cost model 与自动方法选择 | Performance or Illusion、SPEED-Bench、Not-a-Bandit | 跨 GPU/engine/quant/batch 预测 break-even，自动选择 AR/ngram/EAGLE/block/tree | 中 | 中；容易被视作工程，需强泛化证据 |
| G8 | Hardware-aware goodput training objective | DistillSpec、HASS、EAGLE-3、acceptance-oriented losses、DSpark | 把 prefix survival、draft latency、verifier token/expert cost 直接纳入可优化且可迁移的目标 | 中 | 高；需避免过拟合某硬件 |
| G9 | MoE verification 的 expert-union 控制且不改 target | MoA、AcceptMoE、DraftExpert | 只改变 proposal/topology/schedule，保持自然 target routing，同时最小化 expert union/transfer | 高 | 中；需要 MoE kernel/路由观测 |
| G10 | 任意 tokenizer 的严格 stochastic SD | hetero-vocab SD、UniSpec、SpecVocab | byte/string 对齐下高效 residual sampling、动态词表 kernel、multilingual tail | 中–高 | 中；理论+kernel 双难 |
| G11 | Grammar/tool-state-aware speculation | n-gram/suffix、Oilbird、constrained decoding | 每 branch grammar state、外部 side effects、semantic key retrieval 和 exact commit protocol | 高 | 低–中；应用价值清楚 |
| G12 | 持续变化 target 的 rollout speculation | Online SD、EfficientRollout、SpecRoll | policy drift 可测量的 exact adaptation、训练稳定性与 end-to-end RL goodput | 中 | 极高拥挤；2026 增长很快 |
| G13 | 多模态/VLA 的安全可验证 speculative chunks | Speculative Streaming、MMSpec、VLA/image/video SD | 非文本因果拓扑、deadline、action safety 和跨模态 acceptance calibration | 高 | 中；任务定义尚未统一 |
| G14 | 能源/成本/碳而不只是 tokens/s | SPEED-Bench、端侧 SD | verifier waste、额外 drafter memory/training 与 energy/token 的标准测量 | 中 | 低；需证明科学而非测量报告 |

## 13. 推荐的五个可执行研究课题

### P1. Distribution-shift-aware confidence scheduling for lossless block SD（首选）

**假设。** DSpark 类 prefix-survival confidence 在 i.i.d. 验证集上可校准，但真实 domain/language/temperature/load shift 下会过度自信或排序失真；使用在线、风险控制的 survival lower bound，可以在严格 target verification 不变的情况下减少 verification waste，并降低 SLO miss。

**方法空间。** 把每个 request/depth 的 prefix survival 当作 time-to-event/survival prediction；用分组或在线 conformal calibration、change-point detection、temperature/domain conditional calibrator；scheduler 以 survival lower confidence bound 而非 point estimate 分配 token slots。输出 token 永远由 target 的原验证规则决定，所以算法层仍 lossless。

**最小实验。** Qwen3 8B/14B + 公开 DSpark/DeepSpec；train on chat/math/code，测试 unseen languages、tool calling、creative temperature、模型量化和流量 mix shift；batch 1–64。基线为 fixed \(\gamma\)、DSpark 原 scheduler、仅 temperature scaling、D-cut/AngelSpec 可复现策略。指标为 ECE/Brier、prefix coverage violation、wasted verifier tokens、goodput、P95 TPOT/SLO、相对 oracle regret。

**成功判据。** 相同输出与相同 aggregate throughput 下，跨 shift 的 SLO goodput 稳定提高；最坏组 calibration violation 有统计置信区间；收益不依赖单一 GPU profile。

**新颖性检查重点。** 需要重点再查 2026 年 7–8 月 confidence scheduling/conformal LLM serving 的同期稿；只做 temperature scaling 不足以构成研究贡献。

### P2. Exact rejection-aware verifier computation reuse（高风险高收益）

**问题。** 标准 chain 在位置 \(j\) 拒绝后，target 已经对原 draft suffix 做了计算，但新提交 token 改变了后续 prefix，旧 suffix logits 通常失效。ASD 用允许少量 mismatch 的方式复用，CURE 用 repair tree；严格无损版本仍不清楚。

**可能路径。** 在首次 verification 时加入少量 alternative anchors/repair nodes，使拒绝时至少有一条新 prefix 已被 target 严格 score；或对可证明不受局部 prefix 改动影响的结构化状态做 cache reuse。研究首先应给出“不可能直接复用”的条件，再设计最小额外 tree budget 的 exact re-anchoring，而非宣称任意旧 logits 可继续用。

**最小实验。** greedy 与 stochastic 分开；测每次 rejection 后真正可复用的 target layers/KV/nodes 比例、额外 anchor cost、分布正确性和 wall-clock。基线为 strict chain/tree、CURE、ASD-zero/nonzero budget。

**风险。** Transformer 全局依赖可能使通用复用理论上收益很小；但一个清楚的 impossibility/result boundary 本身也有研究价值。

### P3. Robust lossless SD against acceptance-collapse attacks

**假设。** acceptance residual 的跨位置统计、drafter ensemble disagreement 和 target entropy 能在答案退化前识别 Mistletoe/ADSD 类 compute amplification；自适应切换到 AR 或训练免费 drafter可以限制最坏成本。

**方法空间。** 请求级 sequential test、domain-conditioned baseline、robust head ensemble、随机化 proposal topology、per-client compute budget。防御只能改变是否 speculative/使用哪个 drafter，不可改变 target logits/接受规则，从而保持严格输出。

**实验。** 白盒/迁移/自适应攻击；正常流量 false positive；攻击下 slowdown bound、正常 goodput 损失、P99、公平性；必须让攻击者知道检测器并重新优化。

### P4. Lossless MoE-aware tree budgeting

**假设。** 可以用 draft probability、已知 target router history 和 tree path commitment 预测候选节点造成的 expert-union 增量，在不限制 target 自然路由的情况下构造/裁剪 tree，从而减少 verifier expert traffic。

**与 AcceptMoE 的差别。** AcceptMoE 限制 verifier 可选 experts，因而近似改变 target；本课题只改变送给 target 的候选树和调度，所有被验证节点仍执行完整 target routing，最终分布严格。

**实验。** GPU-resident 与 CPU/NVMe offload 两种 regime；相同 tree node budget和相同 accuracy；测 expert union、HBM/PCIe traffic、accepted path coverage、E2E。需要 EAGLE-3/JetSpec/DSpark-tree 基线。

### P5. Grammar- and tool-state-aware semantic speculation

**假设。** Oilbird 的 verifier hidden-state semantic keys 能解决 exact suffix 的 addressing failure；若把 grammar automaton state 和 tool schema/value slots 一起编码为 retrieval key，可在 JSON/API/tool traffic 中显著提高覆盖，同时严格禁止未 commit branch 触发副作用。

**方法。** lexical suffix + semantic verifier key + grammar-state key 的多源 tree；candidate expansion 时执行 branch-local grammar transition；只有 target-committed path 进入 tool executor。

**实验。** API-Bank、BFCL/真实 JSON traces、不同 tokenizer；结构合法率必须 100%，比较 n-gram/suffix/Oilbird/EAGLE-3；报告 retrieval/search latency、AL、端到端以及错误 tool side-effect 数（应为 0）。

## 14. 选题决策建议

若目标是 **3–6 个月内形成扎实论文**，建议顺序是：

1. **P1 校准鲁棒调度**：基线和评价闭环最清楚，能延续 DSpark，但不与几十个新 block heads 正面拼模型规模；
2. **P3 acceptance-collapse 防御**：新问题、严格 lossless 边界清楚，算力需求相对较低；
3. **P4 MoE-aware lossless budgeting**：系统价值大，但需要可控的 MoE serving stack；
4. **P5 tool/grammar semantic speculation**：应用导向强，容易得到实际 traces 时优先级可上升；
5. **P2 exact suffix reuse**：潜在影响最大但理论风险最高，适合先做两周 feasibility study。

不建议以“把 DFlash/DSpark head 再改一个小结构并在 GSM8K/HumanEval 上提高 AL”作为起点。Domino、TreeFlash、JetSpec、DeLS、xPress、CURE、DBLAST、AngelSpec 在三个月内已经密集覆盖了 causal correction、tree、local expert、parallel refinement、repair、stochastic dependence 和 batch allocation；除非有新的理论 factorization、硬件机制或在真实 serving 上非常显著的结果，否则 novelty 很容易被稀释。

## 15. 人工确认的核心文献索引

下面按研究问题给出“进入子方向必须读”的核心集合。它不是候选目录的重复；长尾和最新论文请在 CSV 中按 `track_tags`、日期和摘要检索。

### 基础、理论与综述

- [Blockwise Parallel Decoding, 2018](https://arxiv.org/abs/1811.03115)
- [Speculative Decoding for Seq2seq, 2022](https://arxiv.org/abs/2203.16487)
- [Fast Inference from Transformers via Speculative Decoding, ICML 2023](https://proceedings.mlr.press/v202/leviathan23a.html)
- [Accelerating LLM Decoding with Speculative Sampling, 2023](https://arxiv.org/abs/2302.01318)
- [SpecTr: Optimal-Transport Verification, 2023](https://arxiv.org/abs/2310.15141)
- [Speculative Decoding Survey and Spec-Bench, ACL Findings 2024](https://aclanthology.org/2024.findings-acl.456/)
- [Decoding Speculative Decoding, NAACL 2025](https://aclanthology.org/2025.naacl-long.328/)
- [Global Resolution, ICLR 2026 oral](https://openreview.net/forum?id=gpsczXOsHn)
- [When Is a Draft Accepted?, 2026](https://arxiv.org/abs/2606.30265)

### 独立 drafter、对齐与在线选择

- [Big Little Decoder](https://arxiv.org/abs/2302.07863)
- [Staged Speculative Decoding](https://arxiv.org/abs/2308.04623)
- [Online Speculative Decoding, ICML 2024](https://proceedings.mlr.press/v235/liu24y.html)
- [DistillSpec](https://arxiv.org/abs/2310.08461)
- [HASS, ICLR 2025](https://openreview.net/forum?id=T9u56s7mbk)
- [Not-a-Bandit, ICLR 2026](https://arxiv.org/abs/2510.20064)
- [Curse of Multilinguality](https://arxiv.org/abs/2605.30580)

### Feature head、MTP、parallel/block drafting

- [Medusa](https://arxiv.org/abs/2401.10774)
- [Hydra](https://arxiv.org/abs/2402.05109)
- [EAGLE, ICML 2024](https://proceedings.mlr.press/v235/li24bt.html)
- [EAGLE-2, EMNLP 2024](https://aclanthology.org/2024.emnlp-main.422/)
- [ReDrafter](https://arxiv.org/abs/2403.09919)
- [EAGLE-3, NeurIPS 2025](https://proceedings.neurips.cc/paper_files/paper/2025/hash/c7b5a35ea98b62512a869c19ea7b03cb-Abstract-Conference.html)
- [PARD](https://arxiv.org/abs/2504.18583)
- [P-EAGLE](https://arxiv.org/abs/2602.01469)
- [DFlash, ICML 2026](https://arxiv.org/abs/2602.06036)
- [Domino](https://arxiv.org/abs/2605.29707)
- [DFlare](https://arxiv.org/abs/2606.02091)
- [TreeFlash](https://arxiv.org/abs/2606.03819)
- [JetSpec](https://arxiv.org/abs/2606.18394)
- [DSpark](https://arxiv.org/abs/2607.05147)
- [DeLS-Spec](https://arxiv.org/abs/2607.07409)
- [AngelSpec](https://arxiv.org/abs/2607.25852)
- [CURE](https://arxiv.org/abs/2608.00531)
- [PCTree](https://arxiv.org/abs/2608.02123)
- [xPress](https://arxiv.org/abs/2608.02438)
- [DBLAST](https://arxiv.org/abs/2608.05448)

### Tree、multi-draft 与 verification

- [SpecInfer](https://arxiv.org/abs/2305.09781)
- [Multi-Candidate Speculative Decoding](https://arxiv.org/abs/2401.06706)
- [Sequoia](https://arxiv.org/abs/2402.12374)
- [SpecExec](https://arxiv.org/abs/2406.02532)
- [Block Verification, ICLR 2025](https://openreview.net/forum?id=frsg32u0rO)
- [HeteroSpec](https://arxiv.org/abs/2505.13254)
- [MARS margin-aware verification](https://arxiv.org/abs/2601.15498)
- [Revisiting Lossy Verification](https://arxiv.org/abs/2607.26627)
- [Approximate Speculative Decoding](https://arxiv.org/abs/2608.03447)

### Training-free、自推测与 long context

- [Draft & Verify / Self-Speculative Decoding, ACL 2024](https://aclanthology.org/2024.acl-long.607/)
- [REST, NAACL 2024](https://aclanthology.org/2024.naacl-long.88/)
- [Lookahead Decoding, ICML 2024](https://proceedings.mlr.press/v235/fu24a.html)
- [TriForce](https://arxiv.org/abs/2404.11912)
- [MagicDec](https://arxiv.org/abs/2408.11049)
- [SuffixDecoding](https://arxiv.org/abs/2411.04975)
- [LongSpec](https://arxiv.org/abs/2502.17421)
- [SpecExtend](https://arxiv.org/abs/2505.20776)
- [Windowed-MTP](https://arxiv.org/abs/2607.21535)
- [Oilbird](https://arxiv.org/abs/2608.03839)

### Serving、基准、安全与应用

- [Synergy of SD and Batching](https://arxiv.org/abs/2310.18813)
- [Speculative Streaming, EMNLP 2025](https://aclanthology.org/2025.emnlp-main.986/)
- [Performance or Illusion?, MLSys 2026](https://proceedings.mlsys.org/paper_files/paper/2026/hash/554e056fe2b6d9fd27ffcd3367ae1267-Abstract-Conference.html)
- [PRISM, MLSys 2026](https://proceedings.mlsys.org/paper_files/paper/2026/hash/414fd191b3246a19a55741b938380136-Abstract-Conference.html)
- [SpecGen, MLSys 2026](https://proceedings.mlsys.org/paper_files/paper/2026/hash/66a026c0d17040889b50f0dfa650e5e0-Abstract-Conference.html)
- [SPEED-Bench, ICML 2026](https://arxiv.org/abs/2604.09557)
- [Mistletoe](https://arxiv.org/abs/2605.14005)
- [ADSD](https://arxiv.org/abs/2607.21804)
- [Lossless but Not Free](https://arxiv.org/abs/2607.17283)
- [SpecRoll](https://arxiv.org/abs/2608.04962)
- [AcceptMoE](https://arxiv.org/abs/2608.02989)

## 16. 最终判断

这个方向尚未“做完”，但研究重心已经变化。2023–2024 年，提出一个新的 draft source 或 tree 往往足以构成贡献；到 2026 年，单纯的平均 accepted length 改进很难说明价值。真正前沿的工作必须回答至少两个层面：

1. proposal/verification 在条件分布或理论上为什么更有效；
2. 在优化过的 engine、变化的 batch/context/hardware 上，为什么这些额外候选确实提高 goodput 或降低尾延迟。

DSpark 的价值正是同时回答了模型和系统两层；它的未解问题也恰恰位于两层交界处。基于本次调研，下一步最稳妥的深入研究不是重新发明一个 generic drafter，而是从 **calibration under shift、lossless resource allocation、robustness、以及 verifier computation reuse** 中选择一个可证伪问题，再以 DSpark/DFlash/EAGLE-3 和 production engine 做强基线。
