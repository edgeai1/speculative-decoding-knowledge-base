---
id: 2026--specgen-mlsys-2026
title: "Accelerating Large-Scale Reasoning Model Inference: Self-Speculative Decoding with Sparse Attention (SparseSpec)"
authors: [Yilong Zhao, Jiaming Tang, Kan Zhu, Zihao Ye, Chi-Chih Chang, Chaofan Lin, Jongseok Park, Guangxuan Xiao, Mohamed S. Abdelfattah, Mingyu Gao, Baris Kasikci, Song Han, Ion Stoica]
year: 2026
venue: MLSys 2026
status: deep_read_complete
primary_source: https://proceedings.mlsys.org/paper_files/paper/2026/hash/66a026c0d17040889b50f0dfa650e5e0-Abstract-Conference.html
version_read: MLSys 2026 proceedings
pages_read: 1-15
pdf_sha256: 296653f5c27d2822672e32b324b7f2e3c1ee22865091bbd4c99a44a89793b612
---

# SparseSpec 精读

> 元数据早期简称写作 SpecGen；论文正式系统名为 SparseSpec。

## 问题和算法

reasoning输出数千token后，batched推理KV attention占时可超77%。SparseSpec用同target权重、只让draft attention读约5%关键KV；完整attention target校验保持lossless。PillarAttn不使用静态window：每k次sparse draft后的 full verify本来就算attention logits，定制kernel顺手dump并按draft tokens/query heads聚合top-k，供下一周期使用，零额外target forward且适应CoT语义漂移。

成本模型：`T_base=T_GEMM(B)+T_Attn(M)`；k、接受α、稀疏s时attention项约乘 `(ks+1)/(kα+1)`，例如k16/α.75/s.05理论降6.78×，但GEMM多算且B超过饱和点会抵消。

## 系统协同

统一scheduler把不同请求错开在draft/verify buckets，使每step GEMM大小近均匀，避免k次小GEMM+一次超大verify；新请求进最低负载bucket并调整draft剩余数。Delayed verification允许CPU处理上一verify的accept/cache metadata时，其他请求GPU继续；dynamic KV manager把低活跃cache offload主存、近满GPU利用而不靠错误输出长度预测/retraction重算。

多reasoning模型/数据最高 throughput `2.13×`，明显接近oracle sparse bound且胜MagicDec；收益由PillarAttn acceptance和三项系统优化共同形成。训练免费但需要attention kernel、scheduler和offload大改。

正确性来自full target verifier；sparse draft只改q。风险是上一周期top-k对突变context滞后、attention score dump带宽、offload PCIe和跨请求公平。复现需报告s/k/α、attention/GEMM breakdown、bucket分布、CPU stall、KV H2D及逐组件消融。原文第 3–4 页模型，第 4–8 页设计，第 8–12 页实验，第 13–15 页补充。
