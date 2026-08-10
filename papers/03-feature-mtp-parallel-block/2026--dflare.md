---
id: 2026--dflare
title: "DFLARE: Scaling Up Draft Capacity for Block Diffusion Speculative Decoding"
authors: [Jiebin Zhang, Zhenghan Yu, Song Liu, Eugene J. Yu, Zheng Li, Dawei Zhu, Jiangshan Duo, Weimin Xiong, Yifan Song, Guanghua Yu, Jianchen Zhu, Sujian Li]
year: 2026
venue: arXiv preprint
status: deep_read_complete
primary_source: https://arxiv.org/abs/2606.02091
version_read: arXiv:2606.02091
pages_read: 1-12
pdf_sha256: f6b301797ca5496de7bdedb15fd5ae47a04248b62074adfe283ab168a972161f
---

# DFLARE 精读

## 核心贡献

DFlash 把少数 target layers 先融合成同一个 context，再喂给每个 draft layer；DFLARE 认为这形成“窄瓶颈”：不同 draft layer 看相同信号，增加深度后难以专门化。它让每个 draft layer 对更广的 target layer 集合学习自己的加权组合，以很小 fusion 参数获得 layer-wise target view，再把数据从 800k 扩到 2.4M。

每个 draft 层不是存一整套巨大 target projection，而是对候选 target hidden 做可学习标量/轻量投影组合并注入本层 KV；因此额外 runtime 很小，但训练时需抽取、保存/传输更多中间特征。结构不改 DFlash 的一次 block-parallel generation，也沿用 target embedding/LM head 和严格 verification。

## 证据

六个 math/code/chat 基准的平均 wall-clock speedup：Qwen3-4B `5.52×`、Qwen3-8B `5.46×`、GPT-OSS-20B `3.91×`，相对 DFlash 约 +11%/+8%/+5%。增加 draft depth 在 DFlash 中快速饱和，layer-wise fusion 后更持续；数据 270k→2.4M 时接受长和速度继续提高。该结果同时改变 architecture capacity 和数据规模，故主结论应拆成“融合改善同规模效率”和“扩大数据释放容量”，不能全部归于某一个因素。

## 实现与局限

复现应锁定 target layer pool、每层 fusion 权重归一化、draft depth/block、同数据 DFlash baseline，并记录 target feature storage、tensor-parallel 通信和 draft latency。随机采样仍需标准 residual correction。

它没有修复 block 内 token 的条件独立，扩大容量只能更准确估计 marginals；高熵 suffix 仍会组合失配。更广特征还增加 target-specific 绑定和训练 I/O。后续可研究稀疏/请求自适应 layer routing、跨 checkpoint feature alignment，以及在 causal refiner 与 layer-wise fusion 之间分配参数预算。

原文第 3–6 页为 layer-wise fusion，第 6–10 页为主结果/数据和深度 scaling，第 11–12 页为细节与局限。
