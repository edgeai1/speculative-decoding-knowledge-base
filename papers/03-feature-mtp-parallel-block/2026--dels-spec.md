---
id: 2026--dels-spec
title: "DeLS-Spec: Decoupled Long-Short Contexts for Parallel Speculative Drafting"
authors: [Hong-Kai Zheng, Piji Li]
year: 2026
venue: arXiv preprint
status: deep_read_complete
primary_source: https://arxiv.org/abs/2607.07409
version_read: arXiv:2607.07409
pages_read: 1-17
pdf_sha256: 06c14c37c330f9f6f0728c2646d14258bc197f3f7ccb034707aaebca0fe9e588
---

# DeLS-Spec 精读

## 核心思想

DeLS-Spec 不重训已有 DFlash，而把它视为长上下文专家 `p_L(x|y)`，另用纯文本、标准 next-token loss 独立训练很小 RNN/Markov 短上下文专家 `p_S(x|z)`。推理按

`log p≈log p_L + α log p_S - β log p_unigram`

融合后左到右采样。除 unigram 是为避免两个专家重复计算词频 prior；严格 Bayes 分解还含 long/local interaction residual，方法有意忽略它换取模块化，这正是它与 Domino/DSpark 端到端残差学习的差别。

默认 `α=β=.3`，理论值1因专家 calibration 不一致并不最好。Qwen3-4/8B、DFlash block16、单 L20；math/code增益较清楚，如 T=0 MATH500 `6.09×→6.35×`、AIME25 τ最多 +.44，T=1 HumanEval `4.61×/5.84→4.85×/6.21`。同 local head还能挂 DSpark发布的 DFlash block7，支持“与具体 DFlash checkpoint解耦”，但仍必须共享 tokenizer/语言分布。

训练成本是主价值：Qwen3-4B Domino-FT 13.4h/42.6GB，DeLS RNN 1.1h/9GB，Markov .4h/6.5GB；8B前者 L20 OOM，后两者1.1h/10.1GB与.5h/5.9GB。固定 .3比额外10k steps学 α/β 的 τ更好，说明 CE calibration不等同 acceptance优化。

最终 proposal 有局部因果 softmax，可接标准 residual verifier；忽略 residual只影响效率而非 target正确性。限制是顺序 local loop、手调 fusion、unigram语料漂移和缺失 long-short interaction。复现要锁定 tokenizer/prior平滑、logit temperature、αβ、fused kernel，并与“不减 prior/只 local”消融。原文第 3–5 页推导，第 5–10 页实验/成本，第 11–17 页证明和补充。

## 从公式到代码

工程上应在同一词表空间取得三个向量：长专家 log-prob、短专家 log-prob 与带平滑的 unigram log-prob，再做逐元素线性组合并归一化。这里不能把概率直接相乘后再取对数，否则低精度下极易下溢；也不能漏掉各专家自己的 temperature/calibration。短专家每接受一个 token 都要更新状态，发生拒绝时只能保留到已提交位置的状态，因此实现需要 checkpoint/rollback 或按已接受前缀重放。若用 Markov 版本，则状态只是上一 token；RNN 版本还要特别测试 hidden-state 的分支复制和截断。

最有辨识力的消融不是单报最终 speedup，而是同时给 `long only`、`short only`、简单相加、减 unigram、学习/固定 αβ，并报告每个位置的 target–proposal TV 与接受概率。训练成本比较还需统一样本数、序列长度、精度、GPU 和是否缓存长专家特征。论文支持的是“一个低成本局部专家可补足既有长专家”，并没有证明朴素条件独立假设普遍成立；在跨语言、代码缩进或远距离复制任务上，interaction residual 可能正是决定性项。
