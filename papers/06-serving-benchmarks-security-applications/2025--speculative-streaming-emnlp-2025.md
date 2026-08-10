---
id: 2025--speculative-streaming-emnlp-2025
title: "Speculative Streaming: Efficient and Scalable Speculative Decoding with Multi-Stream Attention"
authors: [Nikhil Bhendawade, Irina Belousova, Qichen Fu, Henry Mason, Antonie Lin, Mohammad Rastegari, Mahyar Najibi]
year: 2025
venue: EMNLP 2025
status: deep_read_complete
primary_source: https://aclanthology.org/2025.emnlp-main.986/
version_read: EMNLP 2025 proceedings
pages_read: 1-24
pdf_sha256: 521e62b5510c1d362d705e0b91f764c2f80f02824647d66cca5e84edf6769f12
---

# Speculative Streaming 精读

## 核心思想

在target顶部 `N_s`层插入多条 speculative residual streams。第j stream看 base prefix和同一时刻前j条streams，因而未来token有依赖但一次MSA并行产生；下一forward同时验证上一棵树并发出下一棵，重叠speculation/verification。streams不保存独立KV，只读base KV；用rank-η投影从 `N-N_s`层base hidden初始化，加stream ID embedding。

**Lossless mode** 冻结base，base stream保持原MHA，仅训练stream adapters/embeddings，严格tree verifier保持原分布。**Shared mode** 允许base反向attend未来streams并训练共享adapter/n-gram loss，得到的是能力/质量可能变化的新模型，不与原checkpoint lossless。二者速度与质量表必须分开。

top-k streams形成指数树，故在stream插入前用target中间层early-exit logits估 parent-child transition并行prune；越早prune越省算、误裁风险越大。训练loss是base next-token与γ future CE加权；segment attention降训练峰值。

多模型/SpecBench约 `2–3.5×`；lossless随model scale约2–3×，shared约3.05–3.35×并评下游score。额外参数声称比Medusa少1000×，但MSA激活/FLOPs和树batch不是参数量能代表。

复现需实现base/spec stream隔离mask、上一树verify+下一树draft同forward、early-exit pruning和cache；逐模式报告模型质量。局限是修改target层/专属训练、stream组合计算、shared不保持原分布、大batch转compute-bound。原文第 2–5 页方法，第 6–10 页结果，第 11–24 页训练/附录。
