---
id: 2026--treeflash
title: "TreeFlash: Parallel AR-Approximation for Faster Speculative Decoding"
authors: [Peer Rheinboldt, Frédéric Berdoz, Roger Wattenhofer]
year: 2026
venue: arXiv preprint
status: deep_read_complete
primary_source: https://arxiv.org/abs/2606.03819
version_read: arXiv:2606.03819
pages_read: 1-13
pdf_sha256: 0f41751b6ae4bf33c276ac0c646ea7c7f0620046718c25782975f7a0b78bfb39
---

# TreeFlash 精读

## 核心思想

TreeFlash 在 DFlash hidden 与具体父 token embedding 上加一个 SwiGLU residual：`h'_i=h_i+SwiGLU([norm(h_i);norm(e_parent)])`，再复用 target output embedding。它使同一深度的不同分支有不同 child distribution，近似 AR 条件性；但不逐路径串行运行，而是先用原 DFlash 建 top-M 规则树，再对所有 `M×γ` 父/深组合并行修正，之后用 OPT-Tree 在预算 B 内选节点，所以 draft 深度的 wall-clock 仍近 O(1)。

训练从 DFlash 初始化、approximator 零初始化，真 predecessor teacher forcing；forward KL 到 target distribution 优于只用 hard CE，早位置继续加权。100k synthetic Nemotron/CodeAlpaca、1 epoch、batch128、128 anchors、lr `1e-4`、长度3072。推理默认 block16、M=16、GH200。

## 结果与诊断

深度 15 时 DFlash 对 verifier 的 TVD 从首位 .19 升到 .81，TreeFlash 约 .62；top-2 coverage 在第 3 位 `.79` 对 `.69`，深度15的 TreeFlash top-1 `.45` 甚至略高于 DFlash top-5 `.44`。预算 B=16 相对 DFlash 平均 `τ +1.35 (+24.8%)`、speed `+0.69× (+17.1%)`；其中单纯 DFlash→DDTree 已贡献大部分，TreeFlash 相对 DDTree仍约 `τ +7.5%`、speed +3.9%。B=64 时 AR approximation 的增益扩大，摘要报告约 +12% block efficiency、+9% speedup。

greedy 中用 equality verification 保持序列。论文随机温度实验的严格性要看树上 proposal/acceptance 实现；树构造分数近似不会损害正确性，但若多候选采样没有相应校正会改变分布。

## 局限和复现

两阶段只使用单一 parent token，尚非完整 prefix state；M×γ evaluation 在 M 大时仍有成本，动态树/OPT-Tree 与 cache 重排可能主导。EAGLE-3 使用不同数据，不能据其表做纯架构结论。复现需用同一 DFlash checkpoint和 finetune data，分别比较 chain、DDTree、零初始化 approximator；报告 B/M、实际树节点、TVD、τ 与构树/校验耗时。可进一步研究多阶 parent 表示、严格 stochastic tree sampling 和 serving-aware B。

原文第 3–5 页为算法，第 5–8 页为实验/消融，第 9–13 页为构树伪码与补充。
