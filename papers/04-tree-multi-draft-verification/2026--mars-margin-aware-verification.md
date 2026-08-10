---
id: 2026--mars-margin-aware-verification
title: "MARS: Unleashing the Power of Speculative Decoding via Margin-Aware Verification"
authors: [Jingwei Song, Xinyu Wang, Hanbin Wang, Xiaoxuan Lei, Bill Shi, Shixin Han, Eric Yang, Xiao-Wen Chang, Lynn Ai]
year: 2026
venue: arXiv preprint
status: deep_read_complete
primary_source: https://arxiv.org/abs/2601.15498
version_read: arXiv:2601.15498
pages_read: 1-12
pdf_sha256: a7308c5226d08bffeab845d8e59d288b977a508404c820a9d832bef1a2d6e8f9
---

# MARS 精读

## 方法与保证边界

MARS 是明确的 **lossy greedy verifier**：draft等于 target top-1就接受；若等于top-2且 raw-logit ratio `r=z_(2)/z_(1)>θ`（默认 .9）也接受；否则写入 top-1并停止。它认为 r接近1表示 target不决断，此时为一个 runner-up回滚不值得。可挂 chain/tree或 target-coupled drafter，不需训练。

该规则改变后续 prefix，既不保持原 greedy文本，也不保持 target sampling分布。“质量保持”只是下游任务/LLM judge经验结果，不能标 lossless。raw logit ratio还有数学脆弱性：softmax对所有 logits加常数不变，ratio却会改变；论文观察其模型top logits多为正只能保证所测设置定义良好，不能给跨量化/模型的 shift invariance。所谓 scale适应也不等于 calibration invariant。

## 结果与复现

8B–235B、多任务，MARS在 EAGLE-3等上提高 τ与速度；正文示例某平均约 `3.12×→更高`、τ可至7.20，完整数值须按模型表读取。阈值越低接受越多、质量风险越大；.9是作者经验折中，不是通用最优。

公平评估应同时跑：原 target greedy、真正 top-2/温度采样质量基线、strict SD、MARS；固定输出长度/EOS协议并报告任务准确、文本多样性、KL/trajectory divergence、速度。还应测试 logit affine shift、temperature scaling、quantization和 adversarial低margin。MARS适合研究“近似解码愿意花多少 regret换速度”，不应与严格SD放在同一无损排行榜。

原文第 3–5 页规则，第 5–9 页结果/阈值消融，第 10–12 页补充。

## 数值语义与压力测试

实现时先从 target logits 取 top-1/top-2 的 token 与数值，只有 draft token 恰为 runner-up 才进入 margin 判断；不能把“落在 top-2 集合”误写成任意第二候选接受。由于 raw-logit ratio 对加性平移不变性缺失，一个简单压力测试是在完全相同 softmax 分布上给所有 logits 加常数，观察决策是否改变；若改变，说明阈值刻画的是特定实现的数值坐标而非模型概率不确定性。可比较 logit gap、概率比或归一化 margin，区分论文规则本身与更稳健替代项。

端到端实验必须持久保存 strict target 输出和 MARS 输出成对比较，并按“发生过近似接受”的样本单独统计质量，而不能让大量零偏离样本稀释风险。代码任务应重跑测试，数学任务核对最终答案与推理链，对话任务同时看 judge 与事实一致性；再报告阈值—接受长—速度—质量的完整 Pareto 曲线。生产保护可设置请求级近似次数/累计概率损失上限，但那属于对 MARS 的扩展，不能把扩展后的安全性回填为原论文保证。
