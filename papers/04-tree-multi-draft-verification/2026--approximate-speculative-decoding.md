---
id: 2026--approximate-speculative-decoding
title: "Approximate Speculative Decoding"
authors: [Yuannuo Feng, Zegang Peng, Yuxin Xie, Yubing Ye, Yizhe Chen, Wenshuai Yao, Wenyong Zhou, Wang Kang]
year: 2026
venue: arXiv preprint
status: deep_read_complete
primary_source: https://arxiv.org/abs/2608.03447
version_read: arXiv:2608.03447
pages_read: 1-8
pdf_sha256: 76813e2e94d7be83d964df710729897e728cf7f25e9c330a3cf5aa502ff91724
---

# Approximate Speculative Decoding（ASD）精读

## 核心思想

strict greedy verifier首 mismatch即停，但 target前向已经给后续位置 logits。ASD允许少数 mismatch通过：其 target-logit regret低于门限、单 block例外数不超过 M、且请求级累计 regret预算未耗尽；随后只复用在这条已实现prefix下仍 target-greedy的 **连续 suffix**，不再对 suffix作新的近似决定。预算0精确退化 strict greedy。

算法在所有可选 prefix中做 budgeted longest-prefix selection，状态包含本请求持久 regret；一旦接受异常 token，会改变真实prefix，因此原树上更远 logits是否有效必须按论文的连续性/对齐条件检查。它是有界近似策略，不是分布保持SD，论文也明确说结果非 output-preserving。

Qwen3-14B+DSpark-14B、B=8、regret gate .25、M=2，七任务相对 matched strict fixed-work throughput提高 `3.05%–15.26%`，平均 `7.78%`。DeepSeek-V4-Flash+DSpark在 FP4 draft/FP8 target compatibility设置，GSM8K/MATH verifier-side acceptance约 +10–16%，未报告完整线上速度/质量。固定workload与natural EOS会因输出长度变化得不同结论，论文两种都测是优点。

复现必须锁定 regret定义/归一、M、持久budget、EOS协议，报告 deviation次数/位置、累积regret、任务正确率和 strict-relative throughput；不能只看 acceptance。量化差异可能制造虚假低regret mismatch。研究价值在于把 lossy greedy从无界“top2也行”变为请求级风险预算；仍需建立 regret与语义质量的可证明关系以及自动按任务分配预算。

原文第 2–4 页算法，第 4–7 页跨模型结果/控制消融，第 8 页结论。

## 近似预算的状态机

实现可将每个请求维护为 `(remaining_budget, exceptions_in_block)`：顺序扫描草稿位置，完全匹配不花预算；不匹配时计算论文定义的 target regret，只有同时满足单点阈值、block 例外上限和请求剩余预算才提交该 draft token。接受近似 token 后，后续 logits 必须确实对应以它为祖先的已计算分支；若原 verification 是单链并在错误 prefix 上计算，不能跨过 mismatch 继续复用。达到任一限制时提交 target greedy token并结束本轮，随后从真实 prefix 重启。

质量评估不能只报告 pass@1 均值。应记录每条输出偏离 strict greedy 的首次位置、例外总数、累计 regret、编辑距离，以及按任务/长度分位的准确率最坏下降；同时用相同门限在量化和非量化 target 上比较。门限选择最好通过独立校准集限定质量风险，测试集不得回调。该方法真正打开的问题是“局部 logit regret 能否作为序列级语义损失的可靠货币”；在循环生成、结构化代码和早期推理分叉中，很小的局部差异仍可能造成巨大轨迹变化。
