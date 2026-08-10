---
id: 2026--mistletoe
title: "Mistletoe: Stealthy Acceleration-Collapse Attacks on Speculative Decoding"
authors: [Shuoyang Sun, Chang Dai, Hao Fang, Kuofeng Gao, Xinhao Zhong, Yi Sun, Fan Mo, Shu-Tao Xia, Bin Chen]
year: 2026
venue: arXiv preprint
status: deep_read_complete
primary_source: https://arxiv.org/abs/2605.14005
version_read: arXiv:2605.14005v2
pages_read: 1-14
pdf_sha256: fc506897f47b4f67d072b0eeda4a17af392b06dfdeb94c41202eb273d175412e
---

# Mistletoe 精读

## 威胁模型与攻击

Lossless保证用户输出，不保证计算成本。Mistletoe优化小prompt扰动，使target输出分布/语义近似不变，却让draft proposed tokens在target下surprisal上升，τ和throughput塌缩。攻击目标为draft-target disagreement/接受下降，semantic-preservation目标约束target；两梯度冲突时，将degradation gradient投影到局部semantic gradient的null space，减少可见输出漂移。

它需要white/gray-box访问draft、target概率/梯度来离线造输入，不是任意API即刻攻击；论文跨多种model-based SD、领域测τ、speed、throughput、perplexity/任务质量，显示明显collapse而质量近似保持。exact数值随系统表变化，核心证据是matched clean/attack和随机/普通adversarial suffix对照。

## 意义与防御

共享batch中单一低accept请求不仅自己慢，还可占verify节点拖累他人，形成cost DoS。防御包括在线τ异常检测、请求级verify/draft预算、低收益自动退回AR、drafter ensemble/randomization、训练时worst-case alignment；仅content safety filter可能看不见。

局限是null-space仅局部一阶近似、“语义保持”由有限指标，优化suffix可被过滤；攻击生成成本和迁移未知。复现要计入攻击成本、不同temperature/seed、tail latency与跨请求影响，且检查prompt长度本身不是原因。原文第 3–5 页threat/objective，第 5–9 页实验，第 10–14 页附录。

## 梯度投影与防御验证

设加速退化目标的梯度为 `g_c`、语义保持目标梯度为 `g_s`，核心操作是去除 `g_c` 在 `g_s` 方向上的分量，再由离散 token 搜索近似该更新。实现必须处理 `||g_s||` 很小时的稳定项，并在每次投影后重新测真实 target 语义约束；局部一阶正交并不保证多步优化后仍保持语义。对照应包括未投影攻击、随机同长 suffix、普通 loss-increase 攻击，以及只在 draft 或 target 上优化的版本。

防御不应只看输入表面。运行时可为每请求维护 `accepted / verified nodes`、预测节省时间和连续低收益轮数，跌破阈值后切回 AR，并限制单请求在共享 batch 中占用的 speculative 节点。评估防御时既要测攻击检出/恢复时间，也要测干净的困难请求被误降级的比例和切换开销。若采用 drafter 随机化或 ensemble，还要重新验证 sampling correctness 与额外内存；防御带来的成本不能从安全结果中省略。
