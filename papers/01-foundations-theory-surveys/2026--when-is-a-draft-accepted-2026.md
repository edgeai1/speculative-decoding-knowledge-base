---
id: 2026--when-is-a-draft-accepted-2026
title: "When Is a Draft Accepted? A Theory of Acceptance in Speculative Decoding"
authors: [Aaryam Sharma]
year: 2026
venue: arXiv preprint
status: deep_read_complete
primary_source: https://arxiv.org/abs/2606.30265
version_read: arXiv:2606.30265v1
pages_read: 1-29
pdf_sha256: bbe6f221c16e34bde65aab394ce166ccc96a702561fbeec0cf70664be89fa31e
---

# When Is a Draft Accepted?（2026）精读

## 核心定位

多数 SD 理论研究 stochastic distribution preservation；本文转而回答 greedy/relaxed/tree verification 的局部确定性问题：给定 target distribution `p` 和 drafter `q`，`KL(p||q)` 小到什么程度，才能保证 drafter 的选择仍被接受？作者把拒绝事件写成 target probability 的 lower-level set，求“触发拒绝所需的最小 KL”，形成精确 certificate 和 margin bounds。

## 1. Certificate 的含义

固定 target `p` 及其 greedy token `x₀`，对某接受规则定义 rejection region `R_p`（所有会拒绝的 drafter distributions q）。精确 certificate：

`C_p = inf_{q∈R_p} KL(p||q)`。

若实际 `KL(p||q)<C_p`，拒绝不可能发生，因而该 token 被保证接受。它是充分条件，不是实际 acceptance probability；certificate 小也不代表必拒绝，只表示 KL 上界不足以保证。

统一 lower-level-set 形式覆盖 strict greedy、additive `q(x_d)≥q(x₀)-t`、multiplicative threshold、top-m gate 和 entropy-based Medusa rule。优化本质上把 q 投影到“刚好发生排序/阈值翻转”的边界。

## 2. Strict greedy 与 relaxed 结论

strict greedy 拒绝当 drafter argmax 不是 target argmax。精确 threshold 依赖 `p(x₀)` 与最有威胁竞争 token 的质量；只知道 target top-margin `γ=p(x₀)-max_{x≠x₀}p(x)` 时可给 tight bounds。单候选 certificate 有通用 `log 2` 上界：target 几乎把质量全放在 x₀ 时，要让 q 的另一 token 至少追平，最小 reverse KL 趋于 log2。

additive/multiplicative relaxation扩大 rejection boundary 距离，因此 certificate 提高；放宽越强，越能容忍较大 drafter KL。top-m 将“drafter 是否把 x₀ 排进前 m”与阈值规则结合。entropy rule 的阈值随 target uncertainty 变化，在低 margin 步骤比固定 strict greedy 更宽容。

这些 certificate 只描述规则下的接受稳定性，不证明 relaxed 输出保持 target greedy/分布或任务质量；放宽本身仍可能有损。

## 3. Tree-based greedy

若每个节点保留 drafter top-m 候选，只要 target greedy token `x₀` 在集合中就能沿 tree 继续。作者推导精确 tree certificate 和 margin-only bounds。其通用上界从单 token 的 `log2` 提升为 `log(m+1)`；小 margin 下 lower bound 主项约 `(m+1)γ²/4`。等价地，相同 margin 时，m-way branching 能容忍的 KL 约是 strict greedy 的 `(m+1)/2` 倍。

这给 tree width 的统计收益一个局部解释，但没有扣除 m 倍 target nodes、tree attention 与内存成本。

## 4. 实证

Qwen3-1.7B/4B，UltraChat 200k 中随机 500 prompts（≥64 prompt tokens），各 greedy 生成 128 steps，共约 63k steps。target top-1 mean .845/.871，median .969/.988；第 5 百分位仅 .343/.391，说明大多数位置极尖锐但有长的低置信 tail。top-10 在 p5 仍覆盖 .901/.927。

精确 KL certificate：strict greedy 的 mean .438/.468、median .559/.619，但 p5 仅 .006/.007。additive t=.3 的 p5 升至 .102/.107，multiplicative α=.1 为 .279/.296，Medusa 设置为 .375/.378。tree m=2/4/8 的 median 在 1.7B 为 .962/1.456/2.038，p5 为 .071/.249/.531；4B 类似。

按假设每一步都有统一 KL≤ε 计算连续 certified run：极小 ε 下 relaxed rule 可得到很长 run；更现实较大 ε 下单候选保证长度约 2–5。若放宽过强、ε 达 .3，几乎全部接受并不意味着有益，反而可能严重改变质量。

## 5. 如何用于研究/训练

- 用 held-out prefix 估计 target margin/certificate 分布，定位 acceptance collapse 的低 margin positions。
- 训练 drafter 时不仅最小化平均 KL，还优化 certificate violation 或最坏组 `KL-C_p`。
- adaptive tree 可只在 certificate 小的节点扩宽；调度目标应加入额外 verifier node cost。
- 校验理论方向：KL 是 `KL(p||q)`，与常见 distillation 的方向不可随意互换；tie-breaking 采用论文 worst-case convention。

## 6. 限制

- 局部 certificate 不直接给整段 expected accepted length，后者还需跨位置 KL 和依赖假设。
- 实验只测两个较小 Qwen3 target distribution，没有实际 drafter、wall-clock 或质量评估。
- 只分析 greedy/tree/local relaxed 规则，不替代 stochastic rejection sampling 的分布正确性理论。
- KL 上界在实际大词表上难保证；估计误差和 support mismatch 会破坏 certificate。
- tree 结论只衡量覆盖，不衡量重复候选、branch correlations 和 verifier saturation。

这篇论文的价值是把“为什么某一步容易接受”从平均经验指标变为可证的局部 margin/KL 条件，为 acceptance-oriented training、风险控制 tree 和分布漂移检测提供理论接口。

## 审读导航

| 内容 | 页码 |
|---|---:|
| 问题与统一框架 | 1–4 |
| 单 token 精确 certificate / bounds | 5–10 |
| additive/multiplicative/top-m/entropy | 10–14 |
| tree certificate 与 `log(m+1)` | 15–19 |
| Qwen3 分布和 certificate 实证 | 19–24 |
| 结论、证明补充 | 24–29 |

## 原始来源

- https://arxiv.org/abs/2606.30265
