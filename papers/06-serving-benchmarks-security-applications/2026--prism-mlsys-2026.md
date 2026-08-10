---
id: 2026--prism-mlsys-2026
title: "PRISM: Parametrically Refactor Inference for Speculative Decoding Draft Models"
authors: [Xuliang Wang, Yuetao Chen, Maochan Zhen, Fang Liu, Xinzhou Zheng, Xingwu Liu, Hong Xu, Ming Li]
year: 2026
venue: MLSys 2026
status: deep_read_complete
primary_source: https://proceedings.mlsys.org/paper_files/paper/2026/hash/414fd191b3246a19a55741b938380136-Abstract-Conference.html
version_read: MLSys 2026 proceedings
pages_read: 1-14
pdf_sha256: c98885564d422a097dcc5b7f2c414a1209f3677d04f1ac072beb47f37d7534b2
---

# PRISM 精读

## 核心架构

普通深drafter每个draft step激活全部层，容量与成本一起涨。PRISM把K个draft steps经满射映射到M个独立 processing modules（fusion FC +一层Transformer）：第k步只激活 `f_map(k)`模块，下一步主动换参数，但 KV在模块间传递。于是整个horizon拥有M层参数容量，每步仍只跑一层；同模块可服务多个step。

首轮把 accepted token embedding与target last hidden融合，经模块1 prefill；第一个draft由最后hidden LM head直接预测；之后每步融合上一token/hidden，切换指定模块、沿共享KV递归。与树和stochastic兼容，但不同层参数读写同一KV的语义不是标准Transformer深度，完全由训练学习。

训练先单模块CE+target hidden MSE warmup，复制成M份后去MSE、按step切模块；HASS式3步context alignment使训练输入/KV接近rollout。只反传当前subnetwork，所以相同总参数比monolithic训练/推理低成本。SGLang集成CUDA graph/continuous batching。

实验相对EAGLE-2/HASS等 acceptance平均约+14.09%，A800/H800已优化engine吞吐相对vanilla最高/平均口径超过 `2.6×`；数据scaling比feature-constrained结构持续。应按表区分“相对AR倍数”和“相对baseline增幅”。

局限是每step参数切换增加HBM读，KV跨模块distribution shift、K/M映射固定、每target专训；batch大时小层kernel效率。复现锁定map、module数、复制初始化、alignment steps和SGLang graph。原文第 3–6 页架构，第 6–10 页结果/scaling，第 11–14 页消融。

## 模块切换的实现语义

映射 `f_map(k)` 必须由 draft step 而非生成序列绝对位置决定；新一轮验证后又从第一个模块开始。每个 module 有独立参数，但递归 KV 的 slot/长度跨 step 连续，因此训练和推理必须用完全相同的模块序列。首 token 直接由 target hidden 经 LM head 得到，后续 token 才经过 fusion 与 module；这处 off-by-one 最容易使复现 acceptance 异常。拒绝后所有 module 看到的 tentative cache 都要截到提交点。

训练消融应分开单模块 warmup、复制初始化、去掉 hidden MSE、context alignment 和不同 K/M 映射，同时报告参数总量、每步激活参数、训练 token/GPU-hours。系统侧测每步权重读取、kernel launch、CUDA graph 数量、batch 利用率和 tree verify，避免把 SGLang 集成收益归给模型结构。与单个更宽/更深 module 比较时既要匹配总参数，也要匹配每步 FLOPs；PRISM 的主张是用“时间维度参数专门化”打破这两种预算的绑定。
