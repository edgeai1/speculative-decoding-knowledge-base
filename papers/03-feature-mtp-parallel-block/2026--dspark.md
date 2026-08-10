---
id: 2026--dspark
title: "DSpark: Confidence-Scheduled Speculative Decoding with Semi-Autoregressive Generation"
authors: [Xin Cheng, Xingkai Yu, Chenze Shao, Jiashi Li, Yunfan Xiong, Yi Qian, Jiaqi Zhu, Shirong Ma, Xiaokang Zhang, Jiasheng Ye, Qinyu Chen, Chengqi Deng, Jiping Yu, Damai Dai, Zhengyan Zhang, Yixuan Wei, Yixuan Tan, Wenkai Yang, Runxin Xu, Yu Wu, Zhean Xu, Xuanyu Wang, Muyang Chen, Rui Tian, Xiao Bi, Zhewen Hao, Shaoyuan Chen, Huanqi Cao, Wentao Zhang, Anyi Xu, Huishuai Zhang, Dongyan Zhao, Wenfeng Liang]
year: 2026
venue: arXiv preprint
status: deep_read_complete
primary_source: https://arxiv.org/abs/2607.05147
version_read: arXiv:2607.05147v1 (2026-07-06)
pages_read: 1-33
pdf_sha256: 522036b0cc16ad4678bd7c278dd0a0ab4da31170af7b97c2041067cc09a8289a
---

# DSpark 精读

## 一句话定位

DSpark 是“算法 + serving policy”的完整 speculative-decoding 方案：用 DFlash 式深并行 backbone 获得首位置容量，再以极小 Markov/RNN head 恢复 block 内条件依赖；另训练校准的接受置信度，在全 batch 内按真实 engine throughput 曲线分配每请求验证长度。离线它比 EAGLE-3/DFlash 有更长接受前缀，线上已用于 DeepSeek‑V4 preview serving，相对原 MTP‑1 基线在匹配吞吐时将每用户生成速度提高 `60%–85%`（Flash）和 `57%–78%`（Pro）。

## 1. 论文真正解决三个不同瓶颈

每 token 平均延迟写作 `L=(T_draft+T_verify)/τ`。AR drafter 的 `T_draft∝γ`，但 suffix 条件一致；parallel drafter 一次生成长 block，却因每位置估计 marginal 而产生 multi-modal collision，条件接受率随深度下降；即使长 block 草稿不错，在高并发中校验低存活 suffix 也会挤占别的请求 batch capacity。DSpark 分别优化 draft cost、τ 和有效 verify cost，不能只把它理解为一个新 MTP head。

## 2. 半自回归 proposal：重计算放并行，条件性放小 head

并行 backbone 基于 DFlash：从 target 多层 hidden 融合 `H_ctx` 并注入 5 层 draft 的每层 KV；输入改为 anchor + `γ-1` masks，anchor 本身也作为第一个预测位置，单次得到 hidden `h_k` 和 base logits `U_k`。

最终因果 proposal 为

`p_k(v|x_0,x_<k)=softmax(U_k(v)+B_k(x_0,x_<k,v))`，

故整块 `P(X|x_0)=∏_k p_k`，可为标准拒绝采样提供明确的逐条件概率。两种 B：

- **Markov head（默认）**：全词表 transition `V×V` 以 `W1[V,r]W2[r,V]` 低秩化，`r=256`；给定上一 token 做 embedding lookup + 小投影，对 base logits 加一阶 transition bias。
- **RNN head**：将 recurrent state、上一 token embedding 和本位置 backbone hidden 拼接，用一个 gated update累积完整块 prefix，再投影 bias。长 block略强但部署更复杂，论文最终默认 Markov。

小 head 仍左到右采样，但没有 transformer/KV 的重前向。batch128、总 round latency约 190ms 时，block 4→16 相对 DFlash只增加 `0.2%–1.3%`；这依赖 target verify 占主导，低 batch 或小 target未必同样微小。

## 3. 接受率诊断揭示了为什么“深 parallel”能赢浅 AR

论文定义 position-wise conditional acceptance：只在前 `k-1` 位已接受的轮次统计第 k 位，隔离 prefix survival。Qwen3-4B math 首位 DFlash约 .88、EAGLE-3 .81，chat .72 对 .53，说明 5 层 parallel backbone 的容量优势首先守住最重要的第一位；但 DFlash code 从约 .87 降到 .78、chat .72→.63，EAGLE则随 prefix确定性保持/上升。DSpark同时保留高首位和稳定 suffix。2 层 DSpark 已胜 5 层 DFlash；block越长相对提升越大，γ=15 时 math/code/chat 接受长约 +30%/+26%/+22%。

## 4. Confidence head、校准与全 batch scheduler

线性 sigmoid head 输入 `[h_k; W1[x_{k-1}]]`，预测“此前已接受条件下本 token 被接受”的 `c_k`。软监督不是一次采样的 0/1，而是精确 proposal/target 分布的重叠：

`c*_k = 1 - 1/2 ||p^d_k-p^t_k||_1`。

prefix 第 j 位存活概率 `a_{r,j}=∏_{i≤j}c_{r,i}`。raw confidence AUC约 .81–.90，却过置信（ECE 3%–8%）；Sequential Temperature Scaling 按位置从左到右校准累计 product，把平均 ECE降到约 1%。

对 R 个请求选择各自长度 `ℓ_r`。target verification token batch `B=Σ_r(1+ℓ_r)`，预计提交量 `τ=Σ_r(1+Σ_{j≤ℓ_r}a_{r,j})`。engine 启动时 profile `SPS(B)`（每秒 step），目标最大化 `Θ=τ·SPS(B)`。把所有 `(request,depth)` 按 `a` 排序，单调 product 自动保持 prefix闭包；沿加入路径查 profile 即可分配预算。

一个容易漏掉的正确性细节：当前候选 token 会影响下一 confidence，若事后全局搜索再决定是否让前一步进入校验，会泄露未来提案并产生 selection bias。理论算法在 throughput 首次不增时 early-stop，以满足 non-anticipating；这只在平滑/单峰 SPS 下全局最优。生产 SPS有 CUDA graph 台阶，DSpark用 **两步之前** 的 confidence仅预测总 capacity K，而当前真实 confidence只做 top-K排序；历史信号形成 causal barrier，允许去掉 early-stop搜索 jagged profile，且不把当前 token结果泄露进预算。

## 5. 训练目标和数据

target、embedding、LM head冻结；随机 anchors构 block。三个按 `w_k=exp(-(k-1)/γ)` 加权的损失：hard CE；`L1` target/draft distribution matching（TV 的两倍，直接对应接受率）；confidence 对 soft `c*` 的 BCE。默认 `L=0.1 L_CE+0.9 L_TV+1.0 L_conf`。强 TV 权重解释其 sampling proposal alignment，而非只追 top-1。

公开离线比较在同一 DeepSpec pipeline、同 1.3M Open-PerfectBlend prompts、各 target重生成 response、10 epochs；EAGLE-3 1层/TTT7，DFlash/DSpark 5层/block7，抽取层一致，T=1，chain-only。这一 same-data 设计比跨论文表格可信。

## 6. 离线结果

Qwen3-4/8/14B 九任务 macro acceptance 相对 EAGLE-3 提高 `30.9%/26.7%/30.0%`，相对 DFlash `16.3%/18.4%/18.3%`，Gemma4-12B也一致。例 Qwen3-8B：GSM8K EAGLE/DFlash/DSpark `5.30/5.33/6.17`，HumanEval `4.33/4.64/5.52`，MT-Bench `2.66/3.11/3.72`。它报告的是含 target bonus token 的 τ，不是端到端 speedup；offline 特意关闭 scheduler以隔离 drafter质量。

static confidence threshold将 chat 总接受率 `.457→.957`，但也缩短每轮实际提交，不能把接受“比例”提升当作吞吐提升。math/code从 `.769/.676` 到 `.925/.920`，说明 domain difficulty确有明显差异。

## 7. DeepSeek‑V4 生产部署该怎样解读

V4‑Flash/Pro 的 draft 是 3 个 MoE+mHC 层、sliding-window 128、最大 γ=5、Markov head；训练用 hidden-before-LM-head 通信把跨 worker 数据从 O(V) 降 O(d)，并以固定 anchors + token-level indices 做 dense packing。推理将 ragged verify tokens展平，依赖由 sparse-attention marker表达，只需改 index-attention/compress kernels。

对线上 raw telemetry拟合 throughput–TPS frontier。相对旧 MTP‑1：匹配实用吞吐时 Flash 每用户 +60%–85%，Pro +57%–78%；中等 SLA 下 aggregate throughput约 +51%/+52%。严格 120 TPS Flash 与 50 TPS Pro处出现名义 +661%/+406%，原因是 baseline已跌到极低 concurrency；作者明确把它解释为“扩展可行 frontier”，不应引用成通常吞吐倍数。负载低时 scheduler给每请求约 4–6 verify positions，负载高时收缩接近 MTP‑1，避免 static MTP-3/5 的 capacity cliff。

## 8. 正确性、复现与未证明部分

Markov/RNN给出局部归一条件 q，标准 `min(1,p/q)` 与 residual sampling 能精确保持 target distribution。调度还需 non-anticipating，上述异步 barrier 是证明关键。生产模型、HAI-LLM kernel、traffic分布和完整 profiler未完全公开，因此公开 checkpoint/DeepSpec能复现 drafter，却不能独立复现 V4线上 Pareto曲线；V4-preview与最终模型也需区分。

固定 draft前向成本在极难请求上不可回收；SPS仅以 token batch近似，极长 context、MoE routing和异构请求可能破坏；两步延迟的 capacity预测在突发负载下会滞后；confidence分布漂移需重校准。新的研究机会包括 draft early exit、鲁棒/在线校准、context-aware SPS、多租户SLA效用以及严格可证明的异步调度。

## 9. 原文定位

第 3–4 页背景；第 4–6 页并行 backbone与 Markov/RNN；第 6–9 页 confidence、STS、scheduler与 non-anticipation；第 9–10 页训练；第 10–15 页离线结果和诊断；第 16–20 页 V4训练/系统/线上部署；第 22–33 页证明、反例、实现和补充。
