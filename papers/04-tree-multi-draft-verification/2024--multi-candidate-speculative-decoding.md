---
id: 2024--multi-candidate-speculative-decoding
title: "Multi-Candidate Speculative Decoding"
authors: [Sen Yang, Shujian Huang, Xinyu Dai, Jiajun Chen]
year: 2024
venue: arXiv preprint
status: deep_read_complete
primary_source: https://arxiv.org/abs/2401.06706
version_read: arXiv:2401.06706
pages_read: 1-15
pdf_sha256: d1875a3186dba1804766c87ce79e2c03abbe9fb3a170edf539752bf6a196474d
---

# Multi-Candidate Speculative Decoding 精读

## 核心思想

标准 SD 每位置只有一条候选，首个错误令后缀失效。本工作从同一 draft model采 K 条 candidate segments，批量/树形交给 target验证；重点贡献是多候选 sampling算法，而非一个新 drafter。

对同一 prefix依次尝试候选 token：每次按当前 target residual与当前 proposal计算接受概率，失败后从 residual中扣除 draft可解释的质量并归一，再尝试下一候选；全部失败才从最终 residual采样。论文给出两个组织版本以及 tree attention去重共享前缀，并证明边缘输出等于 target。候选不能独立用 `min(1,p/q)` 后任取一个成功项，否则重复概率质量会被多算。

实验在多个 LLaMA draft/target与数据集显示 K增大显著提高 acceptance，尤其单候选 α低时；但生成 K条 draft、target节点数和显存也增加，收益很快饱和。论文主要强调 acceptance/理论，端到端速度对硬件批处理效率敏感。

复现应保存每次候选对应条件 q、严格按 residual更新；用 trie减少重复，报告 unique nodes而非 K×γ；做大量采样频率与 target baseline的 TV/χ²测试。局限是多序列草稿成本、分支间高度相关、动态树不易服务批处理。它与 SpecInfer接近，区别是更集中推导多候选分布保持规则；Sequoia再改善 without-replacement鲁棒性和树结构。

原文第 2 页背景，第 3–6 页两个 verifier与证明，第 6–8 页 tree attention，第 8–12 页实验，第 13–15 页补充推导。

## 残差验证的实现细节

设同一位置候选按顺序为 `x₁…xK`。第一个候选失败后，后一个候选面对的已不是原始 `p`，而是从当前目标质量中扣除前一个 proposal 可匹配部分后归一化得到的 residual；proposal 侧也要对应条件化。因而实现应保存每轮剩余质量并在全词表逐元素 clamp 非负，最后所有候选都失败才从归一化 residual 采样。浮点误差可能令总质量略小于零，正确做法是记录误差并用稳定归一化处理，而不是悄悄退化为 target top-1。

树化只是计算去重，不会自动赋予合法采样语义：相同 token 的共享前缀只算一次，而不同父节点下同名 token 仍是不同事件。单元测试可用三词小分布穷举 K=1/2/3 的输出概率，验证经验频率回到 target；随后测试重复候选、零概率候选和全部拒绝。系统评估要同时画 K 对 unique tree nodes、accepted length、draft latency、verify latency及显存的曲线，才能找到真正的甜点，而不是把更高 acceptance 误当成必然加速。
