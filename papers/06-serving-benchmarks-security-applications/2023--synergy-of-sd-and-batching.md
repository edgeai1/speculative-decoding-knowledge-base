---
id: 2023--synergy-of-sd-and-batching
title: "The Synergy of Speculative Decoding and Batching in Serving Large Language Models"
authors: [Qidong Su, Christina Giannoula, Gennady Pekhimenko]
year: 2023
venue: arXiv preprint
status: deep_read_complete
primary_source: https://arxiv.org/abs/2310.18813
version_read: arXiv:2310.18813
pages_read: 1-9
pdf_sha256: 323b330427ed0f7b6c58ea9a5fe07b82fdbf6a8051efa8a0aa9fe80223d166a7
---

# The Synergy of Speculative Decoding and Batching 精读

## 核心结论

最佳 speculation length不是算法常数，而随 batch改变。小batch target decode memory-bound，一次verify多token几乎免费，可用长γ；batch增大后矩阵乘饱和、verify额外token成为真实算力成本，最佳γ收缩，固定配置甚至比AR差。

论文用多个LLM/GPU profile draft/target latency，以实测接受率和batch建立定量时间模型，然后在线/查表选择γ。某小batch点可约 `2.73×`，大batch可能仅 `1.31×`；跨设置平均SD约1.94×，adaptive相对两种固定γ中较优者仍约1.07×。这些早期prototype绝对数已过时，但结构性结论被 MagicDec、Performance or Illusion、DSpark反复验证。

复现应保持总并发/continuous batching、相同输出工作量，分别测draft γ次、target verify `(γ+1)B`、采样/cache；扫B而非只B=1。模型假设position-independent acceptance且batch整齐，现实ragged请求、KV长度、MoE和scheduler会偏离。研究接口是按实时load/请求difficulty联合选γ，而非只按batch静态表。

原文第 2–4 页characterization/model，第 5–7 页adaptive策略与结果，第 8–9 页讨论。

## 从离线剖析到在线控制

可先建立二维 profile 表：横轴为活跃 batch，纵轴为 γ；每格记录 γ 次 draft、一次 `(γ+1)`-token target verify、采样/调度开销和实际位置接受曲线。在线控制器在每轮开始时读取当前 batch、context 长度与近期接受率，选择预计 `time / committed_tokens` 最小的 γ；当收益预测不超过普通 AR 时直接关闭 speculation。控制决策只能使用历史和当前可见状态，不能用本轮 target 结果回看选择。

服务实验要采用相同 arrival trace、请求集合、最大 token 和调度器比较，报告 goodput、P50/P99、每请求 TPOT 以及 aggregate TPS。只固定 batch size 的离线 microbenchmark 会漏掉 ragged completion 导致的 batch 变化；只报告 throughput 又会掩盖个别低接受请求拖累同批请求。对于 MoE、量化或长上下文模型，还需把 expert/KV 读取加入状态，因为相同 B 下 verify 成本并不恒定。论文最持久的结论是“配置属于系统状态”，而非某个具体最优 γ。
