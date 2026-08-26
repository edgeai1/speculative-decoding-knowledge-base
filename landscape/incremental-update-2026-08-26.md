---
title: 最新增量检索：现有知识库之外的方法
description: 截至 2026-08-26，对原 2026-08-10 快照之后的新论文与正式出版源遗漏进行去重、全文方法核验和研究机会重估。
---

# 最新增量检索：现有知识库之外的方法

> 检索截止：**2026-08-26 23:59（Asia/Shanghai）**。本页回答一个窄而重要的问题：哪些 speculative decoding 工作还不在当前 66 篇核心精读中，它们究竟新增了什么？

## 先看结论

本次以现有 `66` 篇核心论文和 `1,260` 条高召回候选为去重基线，重新检查 arXiv 最新提交、标题/摘要同义词、ACL Anthology 和出版商页面：

- 找到 **20 条不在原快照中的 arXiv 记录**：19 条发表于原截止窗口之后，另 1 条 *Matryoshka Language Model Suites* 在 8 月 10 日当晚上传，因摄取时序未进入旧快照。
- 20 条中，**14 条建议进入核心精读队列**，4 条是应用或系统扩展，1 条是诊断/综述，1 条属于相邻的直接生成方法而非 draft–verify speculative decoding。
- 从正式出版源另补出 **4 个方法**：AHSD、SPIDE、LinguaSpec、HCSpec；它们不应继续只靠 arXiv 标题检索发现。
- 对 20 份 arXiv PDF 共 **354 页**完成了方法、算法、实验表、消融、结论与局限核验。此状态记为 `method_results_verified`，**不冒充**现有 66 篇逐页精读的 `deep_read_complete`。

最值得优先读的第一梯队是：**ResiSpec、DARTree、LiLiCorr、TreeWY、AgentSpec、S2-MoE、FOVEA、MemSpec、AnchorDraft**。它们分别封住了多候选严格采样、半自回归树、并行候选相关性、混合状态模型、agent serving、MoE、视觉条件、边缘内存和 ASR 对齐中的具体缺口。

## 纳入边界

本页把“新方法”分为三层：

1. **核心机制**：直接改变 proposal、verification、residual correction、target state、drafter selection 或系统调度，建议进入核心精读。
2. **应用/系统扩展**：把已有 SD 嵌入 VLA、自动驾驶、RL rollout、边云部署等工作流，但主要创新不全在解码算法。
3. **诊断或相邻方向**：能改变研究判断，但不是新的 draft–verify 方法。

正确性标签严格区分：`distribution-exact`、`greedy-exact`、`target-preserving with finite-precision caveat`、`lossy/approximate`。任务分数接近不等于无损。

### 检索与去重路径

- arXiv：按 `submittedDate` 倒序检查精确短语 `"speculative decoding"`，再用 speculative sampling/inference/verification、draft model/token/tree/block、parallel drafting、verifier skipping、Jacobi、MoE、VLM/VLA/ASR 等组合扩展；人工排除只在 related work 提及 SD 的误召回。
- 正式论文源：逐项检查 ACL Anthology 2026 ACL/Findings/EACL 的 speculative 条目，并检查 DOI/出版商页，补偿论文没有 arXiv 版本或 arXiv 元数据未命中的情况。
- 双重去重：先按 arXiv/DOI/Anthology ID，再对标准化标题与方法别名去重；与 `metadata/core_papers.json` 和 `metadata/literature_candidates.csv` 分别比较，从而区分“核心库没有”和“连旧候选表也没有”。
- 时间边界：搜索结果覆盖到 arXiv `2608.248xx` 段；8 月 26 日可见的更高编号中未发现新的直接 SD 方法。论文之后修订版本仍可能改变结论或数字。

## 新增方法总表

| 论文 | 新增问题/机制 | 正确性边界 | 作者报告的代表性结果 | 建议 |
|---|---|---|---|---|
| [ResiSpec](https://arxiv.org/abs/2608.24411) | 识别 multi-candidate rejection 后继续从原 proposal 采样造成的 residual drift；构造局部对齐 proxy 与 coupled residual update | 多候选采样分布严格保持；论文报告 KL 约 `1e-10` | 相对 SpecInfer/Sequoia/EAGLE 类多候选基线，接受长度最高约 `1.86×`，吞吐最高约 `1.68×`；摘要口径最高 `1.92×` | **立即精读** |
| [AgentSpec](https://arxiv.org/abs/2608.24004) | agent/query/语义块隔离的检索草稿，加上按冗余和算术强度分配的 batch token budget | 标准 target verification；依赖上层提供可靠语义边界 | 四类 agent workload；部分表格最高约 `2.28×`，拒绝率显著低于通用 n-gram/cache 草稿 | **立即精读** |
| [FOVEA](https://arxiv.org/abs/2608.22883) | 为每张图像建立 visual memory；每个树节点按深度和 hidden state 动态取视觉证据，不向历史 KV 塞视觉 token | 严格 target 验证保持 greedy 输出 | 三个 VLM、九个 benchmark，平均约 `1.60–1.68×`，最高 `2.13×` | **立即精读** |
| [TailSieve](https://arxiv.org/abs/2608.22788) | 在 RL rollout 中根据部分轨迹识别 tail request，隔离到低并发副本，并按路由类别配置 MTP/DFlash | rollout 重新生成但整体训练链路非严格等价证明 | 路由最高 `1.67×`，结合 speculative backend 最高 `2.59×` | 应用扩展 |
| [TreeWY](https://arxiv.org/abs/2608.20961) | 用树形 WY/UT 变换一次处理 Gated DeltaNet 树验证，只重建接受路径的 recurrent state | greedy 语义保持；有限精度不承诺 bit-exact | recurrent-state 存储量从每节点矩阵降至向量级；高并发吞吐示例约 `1.4×` | **立即精读** |
| [Multimodal SD diagnosis](https://arxiv.org/abs/2608.20743) | 统一比较 VLM 的 tokenwise、MTP、block-parallel 方法，定位视觉 conditioning 成本 | 诊断研究，不是新解码器 | DFlash/DSpark 在纯文本与 VLM 上行为明显不同；高分辨率可能抹掉收益 | 作为证据纳入 |
| [LiLiCorr](https://arxiv.org/abs/2608.20530) | 将 block-parallel 各位置 top-k 构成 lattice，用轻量 Transformer 学相邻候选兼容性，再走局部归一化路径 | 最终由标准 verifier 保持目标输出/分布；top-k 覆盖构成上限 | DFlash 接受率提高约 `9–19%`；70/72 个主设置速度最快 | **立即精读** |
| [Precompiled Pipeline Shards](https://arxiv.org/abs/2608.19147) | OpenVINO stateful KV 无法便宜物理回退时，用 mask 和逻辑 position 跳过拒绝状态 | greedy bit-exact 实测；目前仅验证 greedy | 8B 单节点 SD 平均约 `1.33×`；两节点双流总系统约 `1.79×` | 系统精读 |
| [HB-SJD](https://arxiv.org/abs/2608.18183) | 视觉 on-policy distillation rollout 中，各图像独立 Jacobi cursor、统一 batch verify，并按活跃数切换 full/compact kernel | greedy 可对当前 student 精确；概率版用 rejection sampling | rollout 约 `1.46–1.65×` | 应用精读 |
| [SpecVLA](https://arxiv.org/abs/2608.15636) | 用小 VLA 串行验证大 VLA 的动作，inactive 状态跳过验证，失败时回滚 | 语义阈值与跳过验证使其为近似 closed-loop 推测执行 | 平均接受动作长 `7.1/8`；A100 约 `2.9×` | 相邻应用 |
| [Dynamic Multi-Byte Prediction](https://arxiv.org/abs/2608.15454) | 可变 byte window/mask 的分层 MTP 直接生成 | 无 target draft–verify，不属于本库核心定义 | — | 排除到相邻方向 |
| [S2-MoE](https://arxiv.org/abs/2608.15018) | 共享 context KV、按 expert activation latency 扩树，并软偏置候选复用已激活 experts | routing-aware gating 改变 target 路由，属于可控近似 | Jetson `1.3–5.3×`、RTX 4090 `1.2–2.9×`；论文报告很小质量变化 | **立即精读，标注 lossy** |
| [Skipping Verifier Calls](https://arxiv.org/abs/2608.14787) | 用 token confidence 或 learned prefix survival 判断何时直接提交 draft prefix | 明确 lossy；相同观察 pass@1 不构成分布保证 | 在作者匹配的 pass@1 点减少约 `9.6–13.5%` verifier calls；调用少不必然更快 | **立即精读，研究价值高** |
| [DARTree](https://arxiv.org/abs/2608.13524) | 将 causal correction head 从链扩成树；层内批量展开、延迟全局 top-B 剪枝 | 标准 tree verification；随机采样实现仍需独立审计 | Qwen3-4B/8B 中最高接受 `12.97`、相对本地 AR 最高 `9.73×` | **立即精读** |
| [SPADE](https://arxiv.org/abs/2608.13076) | 小 draft 放 edge、大 target 放 cloud 的标准 speculative sampling 部署 | 形式算法可严格；论文的任务表与“zero accuracy loss”文字不完全一致 | 云调用减少 `76%`；报告吞吐从 `1.21` 到 `1.95` | 系统补充，谨慎引用 |
| [FlashDrive](https://arxiv.org/abs/2608.12932) | 自动驾驶 VLA 的 2-layer DFlash reasoning，再与 streaming KV、flow cache、量化和 kernel 融合 | 文本验证可严格，整个 VLA pipeline 为近似优化 | reasoning decode `271.7→58.2 ms`；总链路 `717→151 ms` | 应用扩展 |
| [Decoupled Contrastive Decoding](https://arxiv.org/abs/2608.12913) | proposal 不再绑定 amateur model；EAGLE3/n-gram 起草，expert 与 amateur 只在 verify 时并行算 contrastive target | 对 contrastive target 分布严格 rejection correction | 8B 平均约 `1.65–1.95×`；70B 扩展示例约 `2×` | **立即精读** |
| [Alignment Drift in ASR SD](https://arxiv.org/abs/2608.12703) | 发现浅层 ASR draft 在 verify 间隔中丢失音频锚点；运行时重定位窗口，训练时用 forced alignment 约束 attention | 理想算术下 greedy 保持；BF16 下报告 token/utterance exactness | AnchorDraft 对匹配控制额外提速约 `4.5–6.8%` | **立即精读** |
| [MemSpec](https://arxiv.org/abs/2608.10362) | 在显存装不下全部 drafter 时，离线预测 top-k resident drafts，异步 prefetch/evict，只在驻留集合中在线选 | 标准 verification 保持目标分布 | Jetson 上 steady-state 吞吐比 static 高 `58.8%`，端到端延迟低 `32.3%` | **立即精读** |
| [Matryoshka Language Model Suites](https://arxiv.org/abs/2608.09703) | 从头训练宽度/深度嵌套模型；小 draft 是大 verifier 的参数与层前缀，KV/权重天然共享 | 标准 SD；结果以所训练 target 为基准 | suite 训练算力低 `36%`；500M/3B 配对吞吐比普通 suite 高约 `26%` | **立即精读** |

所有数字均是**作者在各自硬件、模型、batch 和后端上的报告**，不能横向排序。结构化记录见 [`metadata/incremental_candidates_2026-08-26.csv`](../metadata/incremental_candidates_2026-08-26.csv)。

## 第一梯队方法拆解

### 1. ResiSpec：多候选严格采样里被忽略的“残差漂移”

多候选 SD 常在一个候选被拒绝后，从残差分布

\[
r(x) \propto [p(x)-q(x)]_+
\]

采样修正 token。问题在于：如果同一位置还要尝试第二、第三个候选，却继续独立从原始 `q` 取样，那么 proposal 已经不知道前面拒绝事件暴露出的 blind spot，候选质量会随尝试次数下降。ResiSpec 将它形式化为 **Residual Drift**。

它不要求完整重算一个新 proposal，而是在已经采出的 token 位置上构造局部对齐 proxy `k`，使 `k(x_i)=q(x_i)`，再以 clipping/water-filling 方式重塑剩余质量，并同步更新 residual。关键点不是 heuristic reweighting，而是 proposal 与 residual **耦合更新**；论文给出对任意候选数保持 target distribution 的证明。

研究含义：泛泛地做“更多候选 + 同一 residual”已被堵住。真正还开放的是如何把这套严格 residual ledger 与并行树、不同来源 proposal、硬件预算共同优化，并证明不会重复计算概率质量。

### 2. DARTree 与 LiLiCorr：半自回归 block 的两个正交缺陷

DFlash/DSpark/Domino 一类方法把多个未来位置并行预测，但独立 argmax 会产生彼此不相容的 token。两篇新工作从不同方向修补：

- **DARTree**保留 parent-conditioned causal correction，把链变成有宽度的树。每个深度批量展开候选，保留 path-specific correction state，最后按累计 log probability 加深度偏置做 deferred top-B pruning。论文证明在特定偏置和 tie-breaking 条件下，该剪枝与顺序 best-first heap 等价且保持 prefix closure。
- **LiLiCorr**不显式自回归展开，而把每个位置的 top-k 组成 lattice。候选节点含 token embedding、draft hidden、confidence、slot/rank 编码；一个小 Transformer 一次输出入/出向量，相邻位置用兼容分数连接，最后走局部归一化路径。它学的是“哪个 token 能和下一个位置接起来”，不是再预测一遍 token。

二者揭示同一核心瓶颈：并行 marginal 很便宜，但 target 接受的是 **joint prefix**。后续研究应直接比较 tree expansion 与 lattice compatibility 的单位延迟收益，并检查在高并发时小 head、top-k 展开和大树是否反而吃掉 verifier 节省。

### 3. TreeWY：混合状态模型的树验证不是普通 KV tree attention

Qwen3.5 一类 Gated DeltaNet/attention hybrid 的 recurrent state 是矩阵。朴素树验证若为每个树节点 snapshot 整个状态，内存随节点数乘上矩阵大小，很快失去树验证优势。

TreeWY 用树结构的 WY/UT 变换把所有节点更新合并成一次下三角求解；验证时只保存向量级中间量，接受后才重建最终路径状态。其意义类似“把 tree attention mask 推进 recurrent algebra”，使状态开销从每节点 `d_v × d_k` 级降到 `d_v` 级。它保留接受长度，只改变 state execution；通用树需要非因果 mask 和分段 CUDA capture，因此小并发仍可能被额外 kernel 开销抵消。

这是一个强信号：下一代 SD runtime 不能只抽象 KV cache，还需统一描述 attention KV、SSM/recurrent state、MoE expert cache 和 rejection rollback。

### 4. AgentSpec 与 MemSpec：drafter selection 已经变成资源驻留问题

AgentSpec 利用 agent 系统天然存在的结构：agent id、query id、tool/code/math block。它让检索草稿只在同一 scope 中复用，并用 pushdown automaton 限制语义块边界；随后按候选长度、冗余度和 batch 的算术强度分配全局 draft token budget。收益来自减少污染匹配和把 verifier 工作投到更值钱的位置。

MemSpec 处理另一种现实：边缘设备装不下所有 specialized drafters，切换一次模型甚至比一次 SD iteration 贵。它先用轻量预测器从 prompt 与最近 token 预测 top-k drafter 驻留集，异步 prefetch/evict；在线选择器只能从 resident set 中挑选，避免理论最优但实际要换入模型的决策。

二者共同表明，“选哪个 drafter”不能只比较 acceptance。真正的状态包含语义隔离、内存驻留、换入成本、batch 负载和未来请求。尚未解决的是不依赖人工 block metadata、又能防止跨租户/跨工具内容污染的自动 scope inference。

### 5. S2-MoE：速度来自 expert union，但它不是严格无损

S2-MoE 的核心不是简单地给 MoE 配一个小 draft，而是让 draft/target 共享 context KV，并把树节点的边际收益与新增 expert activation latency 比较；同时用 reuse-aware gating 软偏置候选走已激活 expert，从而缩小一个 verification batch 的 expert union。

成本模型拟合很好，边缘设备上的倍数也很醒目，但 reuse-aware gating 改了 target routing。论文报告 perplexity ratio 约 `1.012–1.013`、top-1 一致率超过 `89%` 和很小 KL；这些是良好的经验近似指标，**不是 target-preserving 证明**。

因此更有价值的开放题不是再做一个 routing bias，而是：在完全不修改 target router/logits 的前提下，能否用 non-anticipating tree selection、expert prefetch 与 verification packing 获得接近的 expert reuse？这比泛化的“MoE-aware SD”题目更清晰、更可证伪。

### 6. Verifier skipping：少调用 target 不等于更快，也不等于无损

该工作显式研究 lossy speculative diffusion decoding：若 draft 的局部置信度、prefix survival score 和最小长度门限都满足，就直接提交一段 prefix，不调用 verifier。论文还给出反例说明，逐 token calibration 不能唯一决定 prefix-level schedule。

最重要的实验不是“少了约 10% target call”，而是 `K_min=0` 虽然调用最少，却因产生更多 draft block 而更慢；峰值吞吐出现在更大的最小跳过长度。也就是说优化目标必须包含 proposal latency、verify latency、失败重算和序列级风险，而不是 verifier-call count。

该论文只有一个主要 model pair、HumanEval 164 个样本且未缓存 verifier KV。适合作为研究问题生成器，不适合作为普遍结论。一个真正尚未完成的方向是：给定显式质量风险预算，学习 sequence-level、cost-aware 的跳过策略，并把严格模式作为可证明 fallback。

### 7. FOVEA 与 AnchorDraft：多模态接受率由“条件何时进入”决定

FOVEA 观察到不同树节点对视觉证据的需求并不单调。它一次构建图像专属 visual memory，每个节点根据 hidden state 与 depth 选 cumulative-mass top-k 视觉条目，再通过 gated correction 融入当前 scoring hidden；视觉证据不作为新 context token 插入，因此历史 KV 不被污染。

ASR 工作发现类似但更动态的问题：浅层 self-draft 虽看过全部音频，却会在连续 draft 步间丢失当前音频位置。运行时版本从 target verification attention 读回锚点并重置下一窗口；AnchorDraft 则用 forced alignment 帧构造高斯 attention target，训练浅层 draft 保持时间定位。

共同开放问题是：能否为图像、音频、视频统一学习一个**最小充分条件接口**，在不扩大 target historical state 的情况下只给当前 proposal 需要的证据，并把读取成本纳入 block/tree budget？

## 其他应纳入核心队列的工作

### Decoupled Contrastive Decoding

普通 contrastive decoding 同时运行 expert 与 amateur，并把二者都绑进 proposal。DCD 的诊断是：contrastive signal 往往弱于普通 drafter error，专门模仿 contrastive target 的小模型不稳定。它让 EAGLE3 或 n-gram 独立起草，expert 与 amateur 只在一次并行验证中构成

\[
\pi_{CD}(x) \propto \pi_p(x)^{1+\alpha}\pi_q(x)^{-\alpha},
\]

再按该目标分布做标准 rejection correction。这是一个清楚的原则：proposal 不必在架构上等同于 target distribution，只需可算 proposal 概率并正确校正。

### Matryoshka Language Model Suites

它不是训练一个额外 draft，而是从头训练宽度和深度嵌套的模型套件：小模型是大模型参数/层的真子集，一次 forward 可得到多个层级 logits，并可在线蒸馏。作为 SD 配对时，小模型天然共享权重和一部分 KV，解决“为了部署 SD 再维护一套模型”的工程摩擦。限制是它要求训练阶段共同设计，不能直接改造任意已发布 target。

### Mask-based KV rewind for OpenVINO

Intel pipeline 工作中最有独立价值的 SD 技术是逻辑回退：stateful OpenVINO 物理裁剪拒绝 KV 约需几十毫秒，系统保留这些物理状态，却用 attention mask 和 logical position id 让后续 token 永远看不见它们。论文实测 greedy bit-exact、墙钟成本低于 1%。长期生成仍需要周期性 compaction，否则物理 cache 会不断膨胀。

### HB-SJD

同步 batching 会被最慢图像拖住，缓存 AR 又可能在小 batch 更快。HB-SJD 为每张图像维护独立 Jacobi cursor/window，让已收敛图像立即前进；同时依据在线活跃图像数，在高吞吐 full execution 和小 batch compact execution 间切换。这是 SD/SJD 与动态 batch 控制共同设计的好例子，但结论目前主要针对 LlamaGen on-policy distillation rollout。

## 正式出版源补漏：arXiv 检索不够

下列方法没有进入现有核心，也没有被原候选表完整覆盖；它们说明维护流程必须加入 proceedings/publisher audit：

| 方法 | 正式来源 | 已确认贡献 | 当前证据状态 |
|---|---|---|---|
| AHSD | [Neurocomputing 689 (2026), 133760](https://www.sciencedirect.com/science/article/pii/S0925231226011574) | 置信度/熵反馈阈值、高置信 token 绕过验证、动态 block length 分桶；作者报告 `1.48–2.43×`，perplexity 增量小于 `0.3%` | publisher HTML/摘要核验；**近似而非严格无损** |
| SPIDE | [Findings of ACL 2026](https://aclanthology.org/2026.findings-acl.1040/) | training-free confidence-to-acceptance 映射；串行动态起草、并行验证 draft；作者报告相对 AR 平均 `3.25×`、最高 `4.56×` | 正式摘要核验；待全文精读 |
| LinguaSpec | [Findings of ACL 2026](https://aclanthology.org/2026.findings-acl.1065/) | POS/语言学 probe、syntactic normalized surprisal、POS-adaptive deferred verification | 正式摘要核验；deferred verification 的正确性需全文审计 |
| HCSpec | [ACL 2026](https://aclanthology.org/2026.acl-long.353/) | 水平两级 cascade：前部位置用双层双路径，后部位置改用轻层；作者报告比 EAGLE-3 高 `15–30%`、相对 AR 最高 `3.72×` | 正式摘要核验；待全文精读 |

另外，[EACL 2026 的小模型实证研究](https://aclanthology.org/2026.eacl-long.255/)不是新方法，但给出重要反证：小 target 上 neural drafter 的固定开销更容易吞掉接受收益，retrieval 方法反而更稳，应进入 benchmark/边界证据层。

原候选表中还有一些已获得 2026 ACL 正式版本、但尚未升为 66 篇核心精读的工作：

- [RACER](https://aclanthology.org/2026.findings-acl.998/)：retrieval proposal 加 target-logit future cue；
- [LogitSpec](https://aclanthology.org/2026.findings-acl.1655/)：利用 target logits 构造 training-free proposal；
- [SpecBound](https://aclanthology.org/2026.findings-acl.802/)：研究可接受 speculative token 的边界；
- [DiffuSpec](https://aclanthology.org/2026.findings-acl.1048/)：diffusion drafter 路线。

它们不是“新发表后才出现”的条目，而是**旧候选尚未完成正式版本升格**，应与本次新论文分开管理。

## 原候选表中仍未升格的高优先级 backlog

本次去重也发现，不能把“已在 1,260 条候选表”理解为“知识库已经解释过”。下列较早工作尚无逐篇核心解读，且与本次前沿直接相连：

- **Bole** (`2608.01651`)：hybrid attention 的 tree-state transform；应与 TreeWY 合读。
- **SparseSpec-L** (`2607.27735`)：长上下文 sparse/recallable KV 与 entropy controller。
- **EcoSpec** (`2607.12696`)：按 MoE expert activation cost 选树；应与 S2-MoE、AcceptMoE 比较严格性。
- **TIGER** (`2607.11131`)：多模态 visual routing 与 acceptance-aligned training；应与 FOVEA 合读。
- **DominoTree** (`2607.08642`) 与 **Dustin** (`2606.24957`)：并行块到树/结构化相关性的同类路线。
- **Test-Time Speculation** (`2605.09329`) 与 **Learning to Draft** (`2603.01639`)：在线/测试时优化 proposal。
- **PARSE** (`2605.04263`)：语义并行 prefix verification；因接受规则近似，应和 verifier skipping 一起做质量边界审计。
- **Speculative Verification** (`2509.24328`)、**Saguaro** (`2603.03251`)、**DART** (`2601.19278`)、**MoE-Spec** (`2602.16052`)：分别补 verification、层级 speculation、动态调度和 MoE 路线。

## 这些新工作如何改变选题判断

### 已明显拥挤的题目

- **只增加并行候选数**：ResiSpec 已把 residual correctness 推到中心，DARTree/LiLiCorr 又分别解决 tree 与 lattice correlation；没有严格概率账本或真实 latency 结果，很难形成新贡献。
- **只用 token confidence 调 block length**：DSpark、SPIDE、verifier skipping、AHSD 已从严格调度到直接跳过验证覆盖多个层次。新工作必须给出 sequence-level calibration、成本函数或保证。
- **泛泛做 multimodal SD**：FOVEA、TIGER、AnchorDraft 和 VLM 诊断已经说明真正瓶颈是 conditioning interface 与对齐，而非简单把 EAGLE/DFlash 移植到视觉模型。

### 仍然清晰开放的题目

1. **严格、non-anticipating、硬件成本感知的统一 scheduler**：同时把 residual risk、target verification shape、MoE expert union、KV/recurrent state、batch concurrency 和 SLA 纳入决策；不能偷看尚未计算的 target logits。
2. **不改 target routing 的 exact MoE speculative decoding**：用 proposal/tree packing、expert prefetch 和共享验证降低 expert union，直接对比 EcoSpec/S2-MoE/AcceptMoE；核心指标是 exactness 下的 expert loads 与 goodput，而非只有 acceptance。
3. **sequence-level risk-controlled verifier skipping**：显式给质量风险预算，联合学习 prefix survival 与真实成本，并提供自动回退严格 verification 的保证。
4. **统一 hybrid-state rollback runtime**：把 attention KV、DeltaNet/SSM recurrent state、position、expert cache 和 rejected branch 生命周期纳入一个可编译状态接口。
5. **多模态最小充分条件读取**：每个 proposal node 只读取需要的视觉/音频/视频证据，不污染历史 target state，并对读取量、接受率和端到端延迟联合优化。

## 当前最推荐的下一步

若目标是做一项算法与系统都站得住、又没有被最新论文直接覆盖的研究，我当前首推：

> **Exact MoE Speculative Scheduling：在不修改 target router/logits 的条件下，联合优化 tree proposal、expert-union-aware verification packing 和 non-anticipating 动态预算。**

它比“再做一个更准的 drafter”更有辨识度，也能直接回应 S2-MoE 的正确性代价、EcoSpec 的成本建模与现有 serving scheduler 的 batch 问题。最低可发表闭环应包括：

1. 形式化 exactness 与 non-anticipation；
2. 可测的 expert-load/latency cost model，而非只用 token confidence；
3. dynamic batch 下的算法与 fallback；
4. correctness gate（toy vocabulary/分布检验）和 routing bit-for-bit 审计；
5. 至少两种 MoE 架构、多个并发/上下文分布上的 goodput 与尾延迟。

第二选择是 **sequence-level risk-controlled verifier skipping**，创新空间更大但质量评测与理论保证更难；第三选择是 **hybrid-state rollback runtime**，系统价值强但需要深入 kernel/runtime 工程。

## 证据状态与复核说明

- arXiv 20 项：本地保存 PDF 与逐页文本证据包，核验 method/algorithm、主要结果、消融、局限和结论；公开仓库不分发 PDF。
- 正式出版源补漏：本页只按可访问的正式 HTML/摘要陈述；未通读全文者不写成 `deep_read_complete`。
- 本页所有倍数都是论文自己的 endpoint/表格口径，不意味着跨论文可比，也不意味着生产环境一定加速。
- 下一轮应按优先级为第一梯队建立与现有 66 篇相同标准的逐篇解读，之后才更新核心论文计数与总页数。
