---
id: 2026--oilbird
title: "Oilbird: Training-Free Speculative Decoding with Keys the Verifier Already Computes"
authors: [Tao Jin, Phuong Minh Nguyen, Zhenzhu Yan, Teeradaj Racharak, Naoya Inoue]
year: 2026
venue: arXiv preprint
status: deep_read_complete
primary_source: https://arxiv.org/abs/2608.03839
version_read: arXiv:2608.03839
pages_read: 1-18
pdf_sha256: ffca1d97b95cd1db334023fd1b33dc4ca6336176ae651d6e8247beebc7183159
---

# Oilbird 精读

## 发现：coverage有了，key找不到

exact suffix retrieval在tool-call中会被一个新姓名/数值打断，但正确后续其实已在历史pool。十基准position诊断把这叫 identifiability gap；最密集tool benchmark中 strongest lexical drafter漏掉的约一半位置在池内却不可达。用静态token embedding做语义key只恢复约23%，用 verifier已经计算的上下文hidden可在oracle 8候选下恢复81%，证明关键信息来自上下文状态。

## 算法

每个历史已提交位置存 `(token x_i, normalized fp16 hidden h_i)`，默认target约0.85L层，约8KB/token@8B；prompt不存、当前请求不检索自身。当前anchor hidden与pool做cosine top8，最大相似≥.8才触发；相似≥.90复制后续48 token，≥.82复制8，否则0。因query state滞后一位，复制从邻居后两位起。自校准在近期命中差时mute语义源。

它不替代lexical suffix automaton/Token Recycling，而在60节点树中预留16节点。语义chain从root沿已有lexical path重走，只为首次分歧买新节点，避免重复；还收集被拒树节点的hidden与target argmax rollout进短ring。target ancestor-mask greedy verify不变，同一forward又产下一轮hidden，故无额外target pass。

## 结果与成本

在三种published training-free drafter、匹配pool和节点预算下 τ提高24–29%。API-Bank速度 `4.4×`，strongest training-free baseline `3.9×`，EAGLE-3 `2.0×`。语义检索约占 verification cycle 4.8–5.8%，主要是keep/search；hidden store远大于token suffix index，长期多租户可能不可承受。

greedy输出严格不变；sampling需另有概率化检索 verifier。隐私、历史分布漂移、ANN近似、层选择和hidden跨checkpoint失效是主要限制。复现应匹配总pool/60节点、排除self leakage，报告recoverable coverage、semantic独有位置、store GB、query latency与tree merge消融。原文第 3 页诊断，第 4–6 页算法，第 6–11 页结果，第 12–18 页附录。
