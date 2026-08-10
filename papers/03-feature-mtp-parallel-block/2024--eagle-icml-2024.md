---
id: 2024--eagle-icml-2024
title: "EAGLE: Speculative Sampling Requires Rethinking Feature Uncertainty"
authors: [Yuhui Li, Fangyun Wei, Chao Zhang, Hongyang Zhang]
year: 2024
venue: ICML 2024
status: deep_read_complete
primary_source: https://proceedings.mlr.press/v235/li24bt.html
version_read: ICML 2024 proceedings
pages_read: 1-14
pdf_sha256: 260141e3e3942ac5797be5bd537aca30b9033d457e61e647fe119322ec9958f7
---

# EAGLE 精读

## 一句话定位

EAGLE 发现直接预测 token 太难、直接预测下一隐藏特征又会忽略采样不确定性，于是令小 draft model 自回归预测目标模型的次顶层 feature，同时把刚采样的 token embedding 作为条件输入。它以很小的目标相关模块获得高接受长度，再由原目标模型严格校验，成为 2024–2026 年最重要的 feature-level drafting 基线。

## 1. “feature uncertainty”到底是什么

若目标模型在同一前缀下可能采到不同 token，下一时刻隐藏特征也会随 token 分叉。只做 `f_{t+1}=g(f_t)` 的确定性回归会把多个可能未来平均起来，得到并不对应任何真实轨迹的 feature。EAGLE 的关键分解是：先由 feature 经冻结 LM head 得到 token 分布、采样 `x_{t+1}`，再预测

`q(f_{t+1} | f_≤t, x_≤t+1)`。

因此 token 承担随机分支，feature predictor 只拟合条件后的剩余变化。作者选择目标模型 **次顶层** feature，因为顶层经 LM head 前更贴近词表但也更目标专用；最终预测 feature 仍复用冻结的原 LM head 得到 token。

## 2. 架构、训练与递归生成

训练时将目标 feature `f_i` 与右移一位的真实 token embedding `e_{i+1}` 拼接，经 `2d→d` 线性层，再通过一个 decoder layer 预测下一 feature。递归推理时，第一次输入来自目标前向；此后输入 draft 自己预测的 feature 和自己采样的 token，而不是 ground truth。

损失为 Smooth-L1 feature regression 加 `0.1` 权重的 token-distribution CE；训练特征加入 `[-0.1,0.1]` 均匀噪声以缓解 rollout exposure bias。backbone embedding 与 LM head 冻结复用。论文以 ShareGPT 约 68k 对话训练，AdamW、学习率约 `3e-5`、`β=(0.9,0.95)`、梯度裁剪 `0.5`；7/13/33/70B 对应可训练模块约 0.24/0.37/0.56/0.99B，70B 适配约 4 张 A100 上 1–2 天。

## 3. 候选树与分布保持

draft module 自回归若干小步并保留多分支，例如三轮形成约 10 节点的固定树；节点按祖先 mask 打包，一次目标模型前向验证。严格 speculative sampling 对候选逐位做 `min(1,p/q)` 接受，拒绝时从正残差 `(p-q)_+` 采样；greedy 则比对目标 argmax。只要实现使用正确的 draft 概率、残差校正和目标 logits，EAGLE 改变的是提案效率而不改变目标文本分布。

这与 Medusa 常用 typical acceptance 不同，也是论文将比较限制在“不微调原 LLM、输出分布不变”的方法上的原因。

## 4. 实验读法

覆盖 Vicuna 7/13/33B、LLaMA2-Chat 7/13/70B、Mixtral-8×7B，任务含 MT-Bench、HumanEval、GSM8K、Alpaca 等，主要是 batch 1。温度 0 下不同模型/任务常见约 `3.17–3.76×`，平均每次目标前向产生约 `3.2–4.5` token；温度 1 下约 `2.39–2.92×`。70B 约 `2.7–3.5×`，Mixtral 只有约 `1.5×`，作者认为树中不同 token 激活更多专家，验证成本上升。优化实现 `gpt-fast` 在 RTX 3090 报告约 160.4 token/s。

消融支持 token embedding 条件、feature loss 与噪声训练均重要；直接 token draft、只预测 feature 或更传统小 LM 均较弱。但比较混合了不同公开实现，Medusa/Lookahead 部分数字取自原论文，系统公平性有限。

## 5. 复现路径与陷阱

需要对每个目标模型离线抽取训练序列的次顶层 features；对话模板、tokenizer、feature 层号和模型 revision 必须锁定。训练要模拟递归时的输入偏移，不能误把 `e_i` 与 `f_i` 同位拼接。推理要缓存 draft decoder 的 KV、复用目标 embedding/LM head、正确建立树 position ids，并在拒绝后裁剪两套 cache。

验证正确性的最低测试是：在固定随机种子下做分布统计，而非要求逐样本同序；greedy 模式则应逐 token 与原模型一致。基准应拆分 draft 三次小前向、树验证、cache 重排和采样 kernel。

## 6. 局限与后续脉络

- 每个 target checkpoint 都需抽 feature 并训练专属 draft；训练数据和算力并非零成本。
- draft 仍要自回归多轮，GPU 上小模型 kernel 利用率可能差；固定树忽略上下文难度，后由 EAGLE-2 修正。
- feature regression 在扩大数据后可能形成表示约束和上限，EAGLE-3 因而改用直接 token CE、多层融合与 training-time rollout。
- MoE、长上下文和大 batch 会改变验证成本，接受长度本身不足以预测速度。

原文第 2–5 页解释 feature uncertainty 和架构，第 5–9 页为实验/消融，第 10–14 页给训练、理论说明及补充表格。
