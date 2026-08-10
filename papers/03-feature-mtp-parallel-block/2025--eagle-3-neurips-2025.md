---
id: 2025--eagle-3-neurips-2025
title: "EAGLE-3: Scaling up Inference Acceleration of Large Language Models via Training-Time Test"
authors: [Yuhui Li, Fangyun Wei, Chao Zhang, Hongyang Zhang]
year: 2025
venue: NeurIPS 2025
status: deep_read_complete
primary_source: https://arxiv.org/abs/2503.01840
version_read: NeurIPS 2025 paper
pages_read: 1-20
pdf_sha256: a9b7fabd038de1862791d8b73766d4a2e4caa451502f7c816215cc8e660c9277
---

# EAGLE-3 精读

## 核心变化

EAGLE-3 不是“更大的 EAGLE”。它放弃下一 feature 回归约束，改为直接训练未来 token；同时融合目标模型低/中/高三层 features，并在训练中显式模拟 5 步 draft rollout（training-time test），让模型看到推理时自己的预测轨迹。配合 EAGLE-2 动态树，最高报告约 `6.5×`，相对 EAGLE-2 约 `1.4×`，SGLang batch 64 吞吐提高 `1.38×`。

## 1. 为什么推翻 feature regression

EAGLE 的 feature L1 loss 要求小模型逼近目标内部表示，但“最适合还原 feature”的方向未必是“最适合命中目标 token”的方向。作者发现扩大训练数据时 EAGLE 很快平台，而解除 feature constraint 后 token 接受率继续提升。EAGLE-3 只保留最终 token CE，让 draft 表示自由服务于提案。

单一顶层 feature 也可能丢掉词法/局部模式或过度贴近输出。作者取目标网络低、中、高三个位置的 features，拼成 `3d`，经线性投影得到 `d` 维融合表示 `g`。draft decoder 将 `g`、自身状态和 token embedding 结合；冻结目标模型和其 LM head，训练轻量 decoder。

## 2. Training-Time Test

普通 teacher forcing 总把真 token/真 feature 喂回，推理却喂自己的输出，误差会沿 draft 链累积。EAGLE-3 在一次训练样本中用特殊 attention mask 模拟约 5 个自回归测试步：模型预测、将自己的 token 路径反馈，再在这些 rollout 位置计算 CE。它不是运行完整目标模型做在线强化学习，而是把“测试时草稿状态分布”构造成可并行训练图。

这一思想与 HASS 的 harmonized context 有亲缘关系，区别是 EAGLE-3 无 feature regression，且将多层 target features 作为初始/锚定信息。推理沿用 EAGLE-2 的 confidence-value 动态树和严格 target verification。

## 3. 训练成本和数据

论文从 ShareGPT 68k 扩到 UltraChat 约 464k；推理/数学模型再使用 target-generated 数据和 OpenThoughts 约 114k。典型 AdamW 学习率 `5e-5`、`β=(0.9,0.95)`、梯度裁剪 `0.5`。70B 适配报告约 16 张 A100 两周，说明“小 draft”不等于低训练成本；其模型专用性仍是部署负担。

## 4. 结果与消融

温度 0 的六任务均值中：Vicuna-13B EAGLE-3 约 `5.51×/接受长6.62`，EAGLE-2 `4.22×/4.83`；LLaMA3.1-8B 约 `4.44×/6.23` 对 `3.23×/4.11`；LLaMA3.3-70B `4.12×/5.88` 对 `2.85×/3.78`；DeepSeek-R1-Distill-Llama-8B `4.16×/5.84` 对 `3.26×/3.92`。HumanEval 单项最高约 `6.47×/7.54`。温度 1 均值通常下降，但仍显著超过 EAGLE-2。

LLaMA3.1-8B 消融很有解释力：EAGLE-2 在 MT-Bench 约 `3.16×/4.05`；移除 feature constraint 后 `3.82×/5.37`；再加多层融合为 `4.40×/6.13`，GSM8K 趋势类似。数据 scaling 曲线显示 EAGLE-3 随数据持续改善而 EAGLE-2 平台。

在 SGLang/H100 的 serving 试验中为便于部署使用长度 3 的链而非完整动态树；EAGLE 在 batch 增大时收益衰退，EAGLE-3 到 batch 64 仍报告 `38%` 吞吐增益。这里的配置与单请求树实验不同，不应交叉引用接受长度。

## 5. 正确性、复现与风险

直接 token 训练不会自动改变输出：只要把它视为 proposal，并用 target 的标准 speculative verifier，greedy/采样仍分别保持原序列/分布。若服务实现为吞吐省略 residual correction，结论另当别论。

复现需锁定三个抽取层、target revision、chat template 和 teacher-generated 数据；实现 training-time-test mask，确认 rollout 节点不能偷看未来真值；随后接 EAGLE-2 动态树。报告训练 PFLOPs、数据生成成本、draft 参数/显存、target feature 读取代价和端到端 serving 指标。

## 6. 局限与研究接口

- 每个 target 仍要长时间训练；数据生成和版权/隐私也可能成为成本。
- 多层 feature 读取可能影响 tensor parallel 通信和框架侵入性。
- 训练 5 步与推理树深不完全匹配，长链 exposure bias 仍在。
- 高接受长度依赖领域数据；需要研究跨 checkpoint 的可迁移 adapter、按硬件成本训练的 objective，以及 tree 与 continuous batching 的联合优化。

原文第 2–6 页为方法，第 6–11 页为主实验和消融，第 12–20 页给数据、训练、serving 与补充结果。
