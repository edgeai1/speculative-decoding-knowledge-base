---
id: 2026--jetspec
title: "JetSpec: Breaking the Scaling Ceiling of Speculative Decoding with Parallel Tree Drafting"
authors: [Lanxiang Hu, Zhaoxiang Feng, Yulun Wu, Haoran Yuan, Yujie Zhao, Yu-Yang Qian, Bojun Wang, Peng Zhao, Daxin Jiang, Yibo Zhu, Tajana Rosing, Hao Zhang]
year: 2026
venue: arXiv preprint
status: deep_read_complete
primary_source: https://arxiv.org/abs/2606.18394
version_read: arXiv:2606.18394v3
pages_read: 1-21
pdf_sha256: 500750163f56a3a49939667611b63e9091a3ebdc60503bb1d626a95d0e03c142
---

# JetSpec 精读

## 核心定位

JetSpec 试图同时保留 DFlash 的“一次 head forward”与 EAGLE 树的 branch causality。它先融合冻结 target 多层 features 并注入 draft KV；训练时不是为每 horizon 输出无条件 marginal，而是在一棵预定义训练树上使用 ancestor-only tree-causal mask，使所有节点并行、每个节点却看到自己具体的祖先 token。候选预算可扩到 256 而接受收益不迅速饱和。

## 模型、训练与树搜索

对节点 v，mask 仅允许 `Anc(v)∪{v}`，于是 `q(path|x)=∏_u q(y_u|x,h_x,path_<u)`，与 target AR factorization 结构一致。训练从 target-aligned continuations 抽 anchors 和长度 N 的 future block，匹配相同 prefix 下 teacher logits。默认 forward KL `D_KL(p_T||q_T)`；reverse KL 太 mode-seeking，hard CE略差。损失按 active nodes/权重归一并乘蒸馏温度平方。

推理一次 draft head 得到各深候选；以累计 `Σ log q` 为默认 path score，从 priority queue 弹出最高可扩节点、加 top-W children，直到深度 N/节点预算 B。目标 tree attention 一次验证；标准 `min(1,p/q)` 与 residual distribution 可保持 sampling，greedy 则精确比对。

## 结果和边界

Qwen3 dense/MoE、math/code/chat，H100/B200。低预算16已具竞争力；高预算256在 MATH-500 报告 `τ≈10.76、9.64×`，MT-Bench 仍约 `τ5.94、4.58×`。这些是最有吸引力但也最需谨慎的 endpoint：目标模型很小/特定 H100 kernel、推理长且低 batch时大树摊薄权重读取最明显。vLLM 集成显示 concurrency 提升仍有 latency 收益，但节点预算越大越占批容量。

论文消融支持 forward KL、累计 log-prob 和 tree-causal mask；理论 speedup 图说明扩大 γ 只有在接受率 α 维持、draft单位成本 c 低时才有效。它不是证明 JetSpec 对所有任务单调 scaling。

## 复现与开放问题

官方代码 `hao-ai-lab/JetSpec`。需固定训练树拓扑、feature 层、N/W/B、蒸馏温度与 target-generated data；验证 mask 无 sibling leakage；测 priority-queue/节点重排、draft head、target tree kernel和 KV compact。多候选 stochastic verifier 需保存每节点条件 q，不能拿 marginal 代替。

限制是 target-specific 训练、大 B 显存与 serving 干扰、训练树到在线动态树的分布差、MoE 分支激活成本。值得研究硬件代价进入 tree score、ragged batch 全局节点调度，以及小 B/大 B 间在线切换。

原文第 2–6 页为方法，第 6–10 页为结果/系统，第 11–21 页为算法、消融和补充。
