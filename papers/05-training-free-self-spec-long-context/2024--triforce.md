---
id: 2024--triforce
title: "TriForce: Lossless Acceleration of Long Sequence Generation with Hierarchical Speculative Decoding"
authors: [Hanshi Sun, Zhuoming Chen, Xinyu Yang, Yuandong Tian, Beidi Chen]
year: 2024
venue: COLM 2024
status: deep_read_complete
primary_source: https://arxiv.org/abs/2404.11912
version_read: COLM 2024 paper
pages_read: 1-16
pdf_sha256: 30b4071aceff2b7925e74b979ed0f41fb227afd97862b60bb2f20700d206af3a
---

# TriForce 精读

## 核心思想

长上下文下 target KV读取成为主瓶颈。TriForce构造三级链：最小独立 draft先 speculative加速一个“中间模型”；中间模型其实是 **同一 target权重 + retrieval选出的稀疏KV cache**，再向完整 target提案。稀疏 self-draft参数完全一致且保留关键历史，接受率高；小模型又摊薄它每个token仍要运行target权重的成本。

retrieval以最近 query/attention选约1K–4K相关KV，并利用上下文locality不每轮更新；rolling acceptance跌破阈值或固定stride才重检。每层 verifier都用标准拒绝校正，因此最终分布等于完整target；中间近似只影响proposal。

Llama2-7B-128K、A100最高 `2.31×`；batch6/19K仍约1.9×。两RTX4090 offload约 .108s/token；相对其优化offload系统可达 `7.78×`，相对单4090 DeepSpeed-Zero-Inference `4.86×`。不同 baseline/hardware的倍数不能混用。分析称120K context、1K KV top-k理论/实测 acceptance约97.6%/90.5%，高度依任务attention稀疏。

实现难点是target KV格式复用、层级两套 residual概率、retrieval更新、三套cache回滚和offload overlap。局限是attention不稀疏任务、retrieval开销、双层控制复杂；后来的MagicDec给更系统的batch/context成本选择。原文第 3–4 页观察，第 4–7 页层级算法，第 7–11 页结果，第 12–16 页细节。

## 三级流水线的正确性与计时

把完整 target 分布记为 `p`、稀疏 KV 自草稿为 `q₂`、小模型为 `q₁`：内层先用 `q₁` 加速产生严格服从 `q₂` 的样本/前缀，外层再把 `q₂` 当 proposal 由 `p` 校正。两层 residual 的概率和随机数状态必须独立，不能把内层“已被接受”误认为外层也被接受。cache 同样有三种进度：小模型、稀疏自草稿和完整 target；每次拒绝后只推进实际提交长度，并截断所有 tentative 部分。

端到端分解应包含小模型草稿、稀疏 target forward、KV 检索/gather、完整验证、cache rollback 与设备间传输。检索更新频率既影响 q₂ 质量也影响关键路径，需画 stride 的 Pareto 曲线。正确性测试先分别关闭一层，使系统退化为普通 SD，再组合并对小词表做采样频率检验。若完整 attention 不够稀疏或 target 已常驻高带宽 GPU，第二级节省会消失，此时复杂的嵌套 speculative 可能比单层方案更慢。
