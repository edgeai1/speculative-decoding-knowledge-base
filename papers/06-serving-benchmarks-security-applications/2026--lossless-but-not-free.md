---
id: 2026--lossless-but-not-free
title: "Lossless but Not Free: An Empirical Anatomy of Speculative Decoding on Consumer Hardware"
authors: [Param Chordiya]
year: 2026
venue: arXiv preprint
status: deep_read_complete
primary_source: https://arxiv.org/abs/2607.17283
version_read: arXiv:2607.17283v1
pages_read: 1-15
pdf_sha256: 2f98f68776f01fd83197141adbaaaaa06e8406b2b81052061b807722c8d97831
---

# Lossless but Not Free 精读

## 论文价值

这是从零实现和失败案例报告，而非新算法。Apple Silicon laptop上五种CUDA/MPS/CPU/llama.cpp draft-target/backend组合，完整实现proposal概率、`min(1,p/q)`、positive residual、bonus和KV truncate；用单步代数、小toy分布、真实模型约9200 token两样本χ²三层correctness gate，最终 `χ²=162.5,dof=200,p=.976`且greedy完全一致。

最佳配置K=6约 `1.61×`；position/pooled acceptance随K从约69.7%降到最优点37.8%。五种中三种减速：draft相对小target不够快，或量化Metal backend把看似batch target verification内部串行化。理论yield `(1-α^(K+1))/(1-α)`用常α会高估，因为真实accept随位置下降。

## 实践启示

必须先单测target的1-token与K-token forward是否真正并行，再选draft；扫K并计TTFT、峰值RSS、cache copy和backend dispatch。量化减少权重读也可能削弱SD“多token几乎同成本”的前提。研究限制是单作者、单消费设备、小模型和样本量；χ²不证明所有prefix/实现无bug，但透明artifact比只报速度可靠。

原文第 3 页算法/证明，第 4–5 页实现，第 6–10 页正确性/速度，第 11–15 页K sweep与artifact。

## 可迁移的实现检查表

proposal 阶段必须保存每一位置完整 q 分布；target 一次为 γ 个候选位置及 bonus 位置给出 p。按顺序以 `min(1,p(x)/q(x))` 接受，第一次拒绝从归一化的 positive residual `max(p-q,0)` 采样并终止；全接受才从 bonus 分布取额外 token。拒绝后 draft/target KV 都截到实际提交 prefix，不能保留候选后缀。零概率、半精度负残差、EOS 与随机数复用都应有独立单测。

正确性验证建议分三层：小词表精确枚举每个输出概率；固定 seed 比较 greedy 序列；大量随机采样对首 token 和短序列联合分布做统计检验。性能层先 microbenchmark target 的 1、2、4、8-token forward，确认后端是否真正批处理，再扫描 K。报告 draft-to-target cost ratio、各位置 conditional acceptance、每轮提交数、cache copy、内存峰值和能耗。论文的核心价值不是 1.61× 这个设备特定数字，而是说明“算法 lossless”与“实现值得运行”是两个必须分别验证的命题。
