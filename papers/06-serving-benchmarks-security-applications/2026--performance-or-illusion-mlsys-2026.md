---
id: 2026--performance-or-illusion-mlsys-2026
title: "Speculative Decoding: Performance or Illusion?"
authors: [Xiaoxuan Liu, Jiaxiang Yu, Jongseok Park, Ion Stoica, Alvin Cheung]
year: 2026
venue: MLSys 2026
status: deep_read_complete
primary_source: https://proceedings.mlsys.org/paper_files/paper/2026/hash/554e056fe2b6d9fd27ffcd3367ae1267-Abstract-Conference.html
version_read: MLSys 2026 proceedings
pages_read: 1-23
pdf_sha256: ca94c05c3112e46c652a17682ffe13008cb5550785f5e0fe04b743ebb67df8ca
---

# Speculative Decoding: Performance or Illusion? 精读

## 研究问题与方法

在production-grade vLLM统一测 n-gram、draft model、EAGLE/EAGLE-3、MTP，跨模型、数据、batch；把每轮分成draft、target verify、采样/调度/cache，并用真实position/request/dataset acceptance trace驱动simulator和理论upper bound。核心发现是 target verification通常主导，B=1论文数字不能代表serving。

acceptance有三维异质性：同一请求随位置递减/变化；请求间difficulty差异；数据领域差异。单一平均α会错误预测预计长度和最优γ。随着batch增加，baseline利用率提高而verify处理更多tokens的边际成本上升，多种SD收益收缩或负收益；n-gram在重复输出可与训练drafter相当。

理论上限用oracle组合每位置最合适proposal/预算并消除部分开销；实测与上限有大gap。论文模拟利用不同方法position-specific优势，潜在相对no-SD可到 `4.9×`，这不是已实现系统结果，而是研究机会。

## 如何用结论

任何新SD至少报告 vLLM/SGLang版本、arrival/concurrency、ISL/OSL、固定工作量、P50/P99、throughput/goodput、每阶段时间、位置接受曲线；与相同engine no-SD而非HuggingFace比较。局限是engine版本快速演化、所测GPU/model不覆盖全部kernel，理论oracle未计实现约束。原文第 3–5 页E2E，第 5–8 页breakdown/acceptance，第 8–11 页bound/simulator，第 12–23 页补充。

## 怎样复用论文的方法论

trace 至少要逐轮保存请求 ID、当前位置、batch、context、proposal 类型/长度、验证节点、接受位置、draft/verify/sample/schedule 时间和提交 token。用同一 trace 回放不同策略时，只能改变控制决策，不能让某方案看到未来接受结果；oracle 则应明确标注为不可实现上界。验证 simulator 的方法是留出一组真实运行，比较预测的每请求完成时间、GPU busy time 和 batch 演化，而非只拟合平均 throughput。

一个可靠新算法结果应同时给三层指标：proposal 层的 overlap/接受曲线，kernel 层的各阶段成本，服务层的 SLO goodput/tail latency。这样能定位“接受更高却更慢”“B=1 快但并发慢”等反直觉现象。还要保持 no-SD baseline 使用完全相同的量化、attention backend、prefix cache 和调度功能。论文给出的 4.9× oracle 是尚未兑现的组合空间；任何实现若接近它，必须证明没有通过预知未来、减少输出工作量或选择性排除困难请求获得优势。
