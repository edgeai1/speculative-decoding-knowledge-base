---
id: 2026--speed-bench-icml-2026
title: "SPEED-Bench: A Unified and Diverse Benchmark for Speculative Decoding"
authors: [Talor Abramovich, Maor Ashkenazi, Izzy Putterman, Benjamin Chislett, Tiyasa Mitra, Bita Darvish Rouhani, Ran Zilberstein, Yonatan Geifman]
year: 2026
venue: ICML 2026
status: deep_read_complete
primary_source: https://arxiv.org/abs/2604.09557
version_read: ICML 2026 proceedings / arXiv:2604.09557v2
pages_read: 1-28
pdf_sha256: fedc5b8d375295148d3deb678ecd63d6e1bc144888593f58c785da5a1e5e5c12
---

# SPEED-Bench 精读

## 基准设计

SPEED-Bench针对SD强数据依赖和旧SpecBench小/低多样性问题提供两套split：Qualitative按语义embedding在math/code/chat等类别内最大化覆盖；Throughput按domain difficulty与ISL 1K–32K构造固定桶，每ISL/difficulty可支持batch至512。统一适配vLLM、TensorRT-LLM、SGLang及HF/SpecBench，报告acceptance、user TPS、aggregate throughput和不同并发。

论文用它揭示：合成/重复输入会显著高估throughput/接受；最佳draft length随batch；低多样性小集合使方法排名偏置；频率词表pruning虽省LM head，却可能在不同domain漏掉关键token。数据curation本身不保证生产代表性，但比只报MT-Bench 80问更可审计。

使用时必须锁定engine commit、kernel、GPU、quantization、ISL/OSL/EOS协议、temperature和arrival；Qualitative比较draft质量，Throughput比较系统，不能把两者混成单平均。建议同时发布per-domain/per-position trace与bootstrap置信区间。

局限是到2026-05的数据/模型快照、非真实arrival tail/SLA、target-generated序列可能偏向特定模型；公开基准也可能被过拟合。它应作为共同测量层，而非证明某方法“所有场景最好”。原文第 2–5 页构造，第 5–10 页framework，第 10–17 页case studies，第 18–28 页数据/补充。

## 运行与报告协议

Qualitative split 应按既定 prompt 原样生成，保存任务类别、输出及逐位置接受 trace；Throughput split 则固定 ISL/difficulty 桶、OSL 或 EOS 规则和并发，不能让不同方法处理不同 token 数。每次运行记录 engine commit、模型与 drafter revision、GPU/驱动、精度、attention backend、scheduler 参数和 warmup。跨 engine 比较时先用各自 no-SD baseline 归一化，再给绝对 TPS/TPOT，避免某引擎基础优化被误算为 speculative 优势。

聚合结果至少提供 domain × ISL × batch 的表或可下载原始 trace，并用 request-level bootstrap 给置信区间。若一个方法只在重复/代码桶领先、在开放对话落后，单个总平均会掩盖其适用域。基准维护还需版本化数据、去重并检测 benchmark 与 drafter 训练语料的泄漏。SPEED-Bench 最适合作为共同测量协议；研究者仍应另加真实 arrival、ragged output、P99/SLO 和故障回退实验，才足以支持生产部署结论。
