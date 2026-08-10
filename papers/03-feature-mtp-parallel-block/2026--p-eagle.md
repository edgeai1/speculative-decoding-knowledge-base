---
id: 2026--p-eagle
title: "P-EAGLE: Parallel-Drafting EAGLE with Scalable Training"
authors: [Mude Hui, Xin Huang, Jaime Campos Salas, Yue Sun, Nathan Pemberton, Xiang Song, Ashish Khetan, George Karypis]
year: 2026
venue: arXiv preprint
status: deep_read_complete
primary_source: https://arxiv.org/abs/2602.01469
version_read: arXiv:2602.01469
pages_read: 1-13
pdf_sha256: 35310a5280cd01e9c4d85be65aef9506728a69b17f09560ade26716a86dfbcd7
---

# P-EAGLE 精读

## 核心定位

P-EAGLE 将 EAGLE 的 `K` 次自回归 draft forward 改成一次并行多位置预测，并重点解决 reasoning 长序列训练中 `n×K` 展开造成的 attention OOM。其贡献一半是 drafter、一半是训练系统；vLLM 上相对 AR EAGLE-3 报告 `1.10–1.36×`，不是相对 vanilla AR 的数字。

## 方法

目标模型冻结并抽取第 2、中间、倒数第 2 层表示，拼接 `3d→d`。首个 NTP 位置使用真实 token embedding 与 target context；后续 MTP 位置缺少上一预测 token/hidden，于是统一用可学习 mask embedding 和一个共享 `h_shared`。所有位置经 4 层 LLaMA/RoPE draft decoder 和目标 LM head，一次输出 K 个候选。作者证明 RoPE attention score 可恢复位置信息，故 shared state 不必显式按 horizon 区分；四种 position-aware 变体反而低 `7–15%`。

训练沿用 PARD/COD：深度 `k` 仅保留约 `nr^k` 个位置，降低总 token。但动态构造 `(nK)^2` mask 本身极慢。P-EAGLE 预计算最大长度 mask，短序列取左上视图；2048/K=8 下将 PARD 约 718.5s/128 样本 loading 降至 17.5s，epoch 12h+ 降至 1.8h。单个长序列仍可能 OOM，故在序列内部切段并做 gradient accumulation：深度 0/1 按位置分段，深度≥2继承其依赖位置所在段，并累计包含先前 NTP prefix，保持跨深度因果边。

经验配方是 4 层（相对 1 层 HumanEval 接受长 +45.7%）、解冻 embedding（约 +5%）、`K_train=8,K_infer=5` 优于 5/5、延长训练。正式设置为 8×H200、最大 8192、COD r=.8、batch 8、peak lr `1e-4`；数据 UltraChat/GSM8K/OpenCodeInstruct。

## 结果、保证与边界

GPT-OSS 120B/20B、Qwen3-Coder 30B 的 vLLM 结果相对强 AR EAGLE-3 为 `1.10–1.36×`。收益来自把多次小 forward 合成一次，代价是更深 draft。论文训练表显示 20K reasoning context 可行，而复现的 ParallelSpec/PARD OOM或极慢；这反映特定实现与硬件，不是那些方法理论上不能长训。

P-EAGLE 只是 proposal；严格 greedy 比对或标准 residual rejection 才保持目标输出。并行各位置缺乏候选内条件依赖，高熵任务的 suffix 仍可能衰减。shared hidden 的理论只说明位置可辨识，不证明最优统计估计。

## 复现与研究接口

锁定 target 抽层、RoPE/position ids、mask token ID；实现 COD 采样、预计算 mask 和依赖保持的分段；解冻 embedding 后不要误称 target 完全不变（推理目标 embedding 应与 draft/target 权重管理明确隔离）。分别测 draft latency、接受长、mask 数据管线与训练峰值显存。最值得延伸的是并行位置间轻量因果修复、长序列无偏分段，以及训练目标直接优化单位 serving 成本。

原文第 2–3 页为架构，第 3–5 页为 mask/sequence partition，第 5–8 页为配方和主实验，第 9–13 页为证明及补充。
