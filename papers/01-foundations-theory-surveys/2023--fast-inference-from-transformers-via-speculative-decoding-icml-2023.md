---
id: 2023--fast-inference-from-transformers-via-speculative-decoding-icml-2023
title: "Fast Inference from Transformers via Speculative Decoding"
authors: [Yaniv Leviathan, Matan Kalman, Yossi Matias]
year: 2023
venue: ICML 2023
status: deep_read_complete
primary_source: https://proceedings.mlr.press/v202/leviathan23a.html
version_read: ICML 2023 proceedings
pages_read: 1-13
pdf_sha256: b287adca11d8126e86dfd6facf162f74f2f6dcfefdef9130af7dde35b08e1d1d
---

# Fast Inference from Transformers via Speculative Decoding（ICML 2023）精读

## 一句话定位

这是现代 **严格 speculative sampling** 的奠基论文之一：小模型 `q` 自回归提出 `γ` 个 token，大模型 `p` 一次并行打分；每个草稿以 `min(1,p/q)` 接受，首个拒绝处从归一化残差 `(p-q)_+` 重采样，从而对任意 `q` 保持目标分布 `p`。论文还给出了 accepted tokens、分布差异、成本系数和最优 draft length 的统一分析。

## 1. 算法完整流程

对当前 prefix：

1. drafter `M_q` 逐步采样 `x₁…x_γ`，并保存每步完整分布 `q_i`；
2. target `M_p` 对 prefix、prefix+x₁、…、prefix+x₁…x_γ 一次 teacher-forced 并行前向，得到 `p₁…p_{γ+1}`；
3. 从左至右独立取 `r_i~U(0,1)`，若 `r_i ≤ p_i(x_i)/q_i(x_i)` 就接受，否则在该处停止；
4. 若第 `n+1` 个草稿被拒绝，从 `norm(max(0,p_{n+1}-q_{n+1}))` 采一个修正 token；
5. 若全部 `γ` 个草稿被接受，直接从已算出的 `p_{γ+1}` 再采一个免费 bonus token。

因此每轮至少生成 1 个，最多 `γ+1` 个 token。target 的串行调用轮数不会比普通 AR 更多，但总计算量可能更多。

### 1.1 为什么残差修正不可省

直接拒绝 `q` 样本后改从 `p` 重采会重复计算已经由“接受分支”覆盖的概率质量，最终分布不是 `p`。正确分解是：接受分支给 token `x` 的质量为 `min(p(x),q(x))`；所有拒绝事件的总质量正好等于 `Σ_x (p(x)-q(x))_+`，所以拒绝后从其归一化残差采样，两部分相加才精确等于 `p(x)`。附录 A.1 给出完整证明。

argmax、top-k、nucleus、temperature 都先变成“调整后并归一化的概率分布”，再统一运行算法；严格性针对该调整后的 target policy，而不是原始 logits。

## 2. 理论：接受率、分布距离与速度

定义给定 prefix 的接受率 `β=E_{x~q}[min(1,p(x)/q(x))]`。论文定义对称距离 `D_LK(p,q)=1-Σ_x min(p(x),q(x))`，因此：

`β = 1-D_LK(p,q) = Σ_x min(p(x),q(x))`。

若各步接受事件简化为 i.i.d.、均值 `α=Eβ`，一轮期望生成：

`E[N] = (1-α^(γ+1))/(1-α)`。

令 drafter 单步时间与 target 单步时间比为 `c`，墙钟加速近似：

`S = (1-α^(γ+1))/((1-α)(1+γc))`。

这条公式清楚表达两个矛盾：增大 `γ` 提高一次 target 调用可能提交的 token，却线性增加 draft 时间；提高 drafter 大小可能增大 `α`，也会增大 `c`。最优 `γ` 应由二者和硬件共同决定，而不是固定的模型超参。

若 `α>c`，至少存在能取得收益的 `γ`；`γ=1` 时加速为 `(1+α)/(1+c)`。论文还分析算术操作量：并行 target scoring 会增加 FLOPs，拒绝越多浪费越大，但权重/KV 的串行内存读取次数可减少。SD 本质是以额外并行计算换低延迟。

## 3. Drafter 选择结论

分布正确性对 `q` 没有限制：它可以是小 Transformer、并行模型、n-gram、context-copy heuristic，甚至随机模型；性能才要求高 `α`、低 `c`。实验中 target 的约百分之一规模常取得较好平衡。一个几乎零成本的 bigram 在 T5-XXL En-De 上仍有 `α≈0.2`，理论上可给约 1.25×，预示了后来 prompt lookup/retrieval drafting。

同一 `q` 不一定适合所有 sampling policy：更尖锐的分布往往有更高接受率，greedy 常比温度 1 更快。论文也指出若可预测局部 `β` 并动态调 `γ`，理论上还能比固定 `γ` 高约 60%，这成为后续 adaptive-length/scheduling 工作的起点。

## 4. 实验与数字

主墙钟实验用 T5-XXL 11B 作为 target，在单 TPU-v4、batch=1 上测试 WMT En-De 与 CNN/DM；drafter 为现成 T5-small 77M、base 250M、large 800M（第 6 页）。

| 任务 / policy | 最佳 drafter | `γ` | `α` | 加速 |
|---|---|---:|---:|---:|
| En-De argmax | T5-small | 7 | 0.75 | 3.4× |
| En-De temp=1 | T5-small | 7 | 0.62 | 2.6× |
| CNN/DM argmax | T5-small | 5 | 0.65 | 3.1× |
| CNN/DM temp=1 | T5-small | 5 | 0.53 | 2.3× |

更大的 T5-base/large 虽提高 `α`，实际速度变差：如 En-De argmax 的 `α` 从 .75 升至 .80/.82，速度却由 3.4× 降到 2.8×/1.7×。这直接证伪“选最接近 target 的 drafter 就最好”。

论文还测 97M GPT-like、137B LaMDA 和不同 n-gram。小模型相对大模型的 `α` 多在 0.5–0.9；任务、温度和模型族都会改变它。LaMDA 137B 用 100M/2B/8B 时 greedy `α` 为 .61/.71/.75，但这些只是接受率测量，不是完整墙钟实现。

## 5. 复现与工程关键点

1. draft 和 target 必须在完全相同的 token 空间与已标准化 sampling policy 上给出概率；保存每个已采 token 的 `q_i(x_i)`。
2. target forward 对 `γ+1` 个位置使用 causal mask；利用 KV prefix，避免重复计算 prompt。
3. 接受比较最好在足够精度中做，残差要 clamp nonnegative 后归一化；处理浮点误差和残差质量接近 0 的情况。
4. 只提交 accepted prefix + correction/bonus token；未提交候选对应 KV 必须丢弃或安全覆盖。
5. 对相同 seed，不应强求 token-by-token 相同：算法消费随机数的次序和浮点图不同；应验证分布/统计一致性。greedy 情况才可检查序列一致。
6. benchmark 需 profile `c`、target scoring 随 `γ` 的非恒定成本、KV 长度、batch 和尾延迟；论文公式假设短块并行 scoring 与单 token target pass 等时，现代高并发下可能不成立。

## 6. 保证、假设与限制

- **保证**：在精确概率算术和正确残差采样下，每一步条件分布为 target，故联合序列分布不变；`q` 可以任意差。
- **非保证**：不保证省 FLOPs、能耗或吞吐；只在可用并行算力且 target memory-bound 时倾向降低 latency。
- i.i.d. `α` 仅用于简化成本分析；真实 prefix/depth 接受事件强相关。
- 论文实验集中 batch=1、encoder–decoder T5；高并发时额外 verifier tokens 会使计算成为瓶颈。
- beam search 兼容性未解决；严格采样证明不能直接搬到全局 beam pruning。
- drafter 与 target 默认同 tokenizer；异构词表要解决字符串对齐与残差分布。

## 7. 与后续工作的关系

Chen et al. 同期独立给出几乎相同 rejection scheme，并在 Chinchilla 70B 分布式系统验证。DistillSpec/HASS 优化的是 `α`；EAGLE/Medusa/DSpark 改造的是 `q` 的来源和执行结构；Sequoia/SpecTr/Global Resolution 扩展多候选 coupling；DSpark/AngelSpec 等将动态 `γ` 提升为共享 verifier budget 的在线决策。后续所有宣称“lossless SD”的方法，核心都必须最终落回这里的 target correction 或一个等价 coupling。

## 8. 审读导航

| 内容 | PDF 页码 |
|---|---:|
| 算法与统一 sampling policy | 2–3 |
| 接受率、距离、速度/FLOPs 定理 | 3–5 |
| drafter 类型与零成本 heuristic | 5–6 |
| T5-XXL 与多模型实验 | 6–8 |
| 局限和未来方向 | 8 |
| 分布保持证明、实现偏差 | 11–13 |

## 原始来源

- 会议主页：https://proceedings.mlr.press/v202/leviathan23a.html
- arXiv：https://arxiv.org/abs/2211.17192
