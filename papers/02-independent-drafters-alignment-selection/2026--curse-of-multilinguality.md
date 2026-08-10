---
id: 2026--curse-of-multilinguality
title: "Speculative Decoding and the Curse of Multilinguality"
authors: [Nirajan Paudel, Michael Ginn, Luc De Nardi, Alexis Palmer]
year: 2026
venue: arXiv preprint
status: deep_read_complete
primary_source: https://arxiv.org/abs/2605.30580
version_read: arXiv:2605.30580v2
pages_read: 1-15
pdf_sha256: df424a7f6e2a746f8e36eebcc6f62ec6df17b2065274079fc9fd7d920d6b4303
---

# Speculative Decoding and the Curse of Multilinguality 精读

## 核心定位

这篇负面研究表明：小 multilingual drafter 在低资源语言上的容量缺口使 draft-target divergence 系统性升高，经典 SD 常不加速甚至减速；task-specific distillation 只改善同任务并伤害另一任务，有限 monolingual 数据也无法提供代表性覆盖。极便宜 bigram 虽接受率低，却因 cost ratio 小而更稳健。

## 1. 假设与设置

11 种低资源语言：ber、grn、chr、zgh、que、oci、npi、yor、haw、ibo、amh；两个任务为 English→target translation 与 target-language story generation。模型族为 Qwen3.5 与 Llama3.2 的大小 pair。作者用 FineWeb2 bytes 代理 resourcedness，以每字符 total variation/LK divergence 和 token acceptance、理论 speedup 联结表示差异与成本。

语言资源量与大小模型 divergence 呈负相关（Qwen/Llama r≈-.47/-.41，未收录的 ber/grn 排除）。tokenizer 每字符 token 数也会改变端到端速度，因而 paper 用 per-character divergence 避免只看 token 单位造成偏差。

## 2. 结果

低资源语言 acceptance 显著低；Qwen 仍有部分 >1 speedup，Llama 3B/1B 规模太接近，cost ratio 不利，多数约≤1。增大 Qwen draft 0.8B→2B→4B 虽单调提高 acceptance，speedup 可能不升反降，再次说明 α 与 c 必须同时优化。

**Task-specific distillation**：teacher greedy translation outputs、top-20 soft logits。所有语言 translation acceptance 都提高，npi/oci 尤明显；但 story generation 几乎全面下降，表明在窄 trajectory 上对齐产生任务过拟合。

**General-domain distillation**：用 monolingual corpus existing text 做 off-policy teacher logits；两个任务效果混杂，常同时变差。低资源 corpus 常只含 Bible/儿童故事等少数 genre，无法覆盖服务分布。

**n-gram**：在 monolingual corpus、Qwen tokenizer 上训练，bigram 在各语言最好。接受率远低于 neural drafts，但 CPU dict lookup 成本极小，两个任务的理论 speedup 全面优于最佳 distilled Qwen，并且跨任务更稳。

## 3. 实践结论

- 语言应成为 drafter/router/cost model 的显式条件；English 平均值会掩盖低资源组 slowdown。
- 不能用同语言一个任务的 KD 证明语言级泛化；至少做 translation、open generation、instruction/reasoning 的 cross-task matrix。
- 按字符/语义单位同时报告 latency，避免 tokenizer fertility 使 token/s 看起来虚高/虚低。
- 低成本 n-gram 可作为 fallback；最终 target verification 仍保持输出分布。

## 4. 限制

只测两个模型族、11 语言、两个任务，且作者承认 generation 本身质量很差；速度结论未在完整优化 engine 墙钟上普遍验证。FineWeb bytes 只是 resourcedness proxy，script/tokenizer/typology是混杂因素。n-gram Python dict 还有优化空间，也会有 corpus/domain 泄漏风险。

这篇论文揭示 acceptance fairness：lossless 只保证各语言输出与 target 一致，不保证服务成本公平。未来需要 group-aware calibration、language-conditioned expert selection 和 worst-language SLO。

## 审读导航

| 内容 | 页码 |
|---|---:|
| 多语言假设/指标 | 1–4 |
| divergence/acceptance/speed | 4–6 |
| 两类 distillation | 7–8 |
| n-gram 与结论 | 8–9 |
| 数据、超参、全结果 | 11–15 |

## 原始来源

- https://arxiv.org/abs/2605.30580
