---
id: 2023--big-little-decoder
title: "Speculative Decoding with Big Little Decoder"
authors: [Sehoon Kim, Karttikeya Mangalam, Suhong Moon, Jitendra Malik, Michael W. Mahoney, Amir Gholami, Kurt Keutzer]
year: 2023
venue: NeurIPS 2023
status: deep_read_complete
primary_source: https://arxiv.org/abs/2302.07863
version_read: arXiv:2302.07863v4
pages_read: 1-21
pdf_sha256: 4a2dcdbfd818e49b20f04d0b8b52b857fe1df4504aa60fe9976919c06d018a42
---

# Big Little Decoder（BiLD）精读

## 核心定位

BiLD 让小模型持续 AR 生成，只有当小模型置信度低时才调用大模型一次并行复查整个尚未确认窗口；大模型可回滚最早的不可信 token。它是动态窗口、plug-and-play 的“有损协作解码”，在 T4/batch=1 上以约 0–1 BLEU/ROUGE 损失换 1.34–2.12×。它不使用严格 rejection correction，不能宣称保持大模型分布。

## 1. 两个策略

**Fallback**：小模型在每步生成分布 `p_S`。若 `max_y p_S(y|prefix) < α_FB`，才把当前 prefix/window 交给大模型；否则继续生成。窗口长度由置信度自然决定，而非固定 `γ`。

**Rollback**：大模型 teacher-force 整个小模型窗口，同时得到窗口内所有位置 `p_L`。从左到右找首个 `d(p_S,p_L)>α_RB` 的位置 m，删除 m 及之后 token，并以大模型在 m 的输出替换；若无越阈值位置，只用大模型生成当前 token。实验采用“小模型 hard label 对大模型 soft distribution 的 cross-entropy”作为 d。

大模型复查是非自回归并行 forward，增加 FLOPs 但提高 arithmetic intensity。过少 fallback 会让错误积累，过多则退化为大模型 AR；rollback 又形成质量—重复计算权衡。

## 2. 对齐

两模型只需同 vocabulary。可直接用独立 checkpoints；也可用大模型 greedy 输出组成 calibration set，再微调小模型，使其词面选择接近大模型，减少“语义相同但用词不同”引发的无益 rollback。这是 sequence-level black-box alignment，不需要大模型内部 hidden/logits。

## 3. 实验

IWSLT17/WMT14 De-En 用 mT5-large/small，XSum/CNN-DM 用 T5-large/small，大小约差 20×；单 NVIDIA T4、batch=1。无质量损失附近，unaligned BiLD 为 1.43/1.34/1.48/1.71×，aligned 为 1.62/1.47/1.50/1.85×。允许约 1 指标点下降，aligned 达 1.78/1.70/1.80/2.12×。阈值 sweep 形成整条 latency-quality Pareto curve。

论文附录与严格 speculative sampling 比较：BiLD 的 deterministic rollback 和动态 window 可取得更好的任务级 latency-quality 点，但代价是改变采样分布。采样扩展（nucleus p=.8）仍可运行，却同样不提供 target-distribution 保证。

## 4. 实现与边界

- 缓存每个小模型位置的概率/选中 token；fallback 时大模型对 window causal score。
- rollback 必须同步截断两模型 KV，并重建替换 token 后的 cache；这常是论文伪代码外的主要工程成本。
- `α_FB/α_RB` 应在 held-out set 联合调参并报告整条质量曲线，不能只报一个“minimal degradation”点。
- small-model confidence 未校准且可过度自信；distribution shift 会导致过长错误窗口。
- 主结果是 seq2seq、老一代模型/硬件，不等价于现代 continuous-batching LLM serving。

BiLD 的持久启示是：draft length 可以是事件触发的动态量；但若最终目标是 lossless sampling，必须把 deterministic rollback 改成合法 coupling/correction。

## 审读导航

| 内容 | 页码 |
|---|---:|
| 方法动机与形式化 | 4–5 |
| fallback/rollback/伪代码 | 5–7 |
| 实验与主表 | 7–9 |
| 与严格 SD、sampling、cache/FLOP 补充 | 15–21 |

## 原始来源

- https://arxiv.org/abs/2302.07863
- https://github.com/kssteven418/BigLittleDecoder

