---
id: 2024--rest-naacl-2024
title: "REST: Retrieval-Based Speculative Decoding"
authors: [Zhenyu He, Zexuan Zhong, Tianle Cai, Jason D. Lee, Di He]
year: 2024
venue: NAACL 2024
status: deep_read_complete
primary_source: https://aclanthology.org/2024.naacl-long.88/
version_read: NAACL 2024 proceedings
pages_read: 1-14
pdf_sha256: cd810cf3d88826443cdee053329c299997fc47f4a1cdf8af895c629993230fec
---

# REST 精读

## 核心思想

REST 用 datastore中的文本 continuation代替神经 drafter。索引将 token n-gram prefix映射到历史后缀；当前已确认序列取最长/多长度 exact match，检索多个延伸并合并为 trie，一次 target tree attention验证。代码/模板化文本重复高时，CPU检索远便宜于小模型 forward。

## 数据结构、选择与校验

datastore可来自训练语料或领域文本，记录 prefix→后继序列及频率。exact-match算法从最长 suffix回退，Trie选择在固定节点预算下保留高频共享路径。草稿不是完整概率LM；论文主结果多用 greedy exact verification，输出与 target greedy一致。若非零温度使用其较宽松/多候选策略，必须核对是否执行严格 tree residual；检索频率不能未经校正充当 q后直接宣称分布保持。

7B/13B、batch1，在 HumanEval代码和MT-Bench文本约 `1.62–2.36×`；代码重复更高、domain datastore更好。datastore增大先提升coverage再让检索变慢；tree selection优于只取单个最长结果。数字包括特定 tree kernel，且不适用于隐私禁止历史复用的服务。

## 成本和局限

“无需训练”仍需语料、tokenizer一致的离线索引、CPU内存和在线查询；模型升级若 tokenizer改变要重建。exact lexical match对变量名/数值/改写脆弱，这一 identifiability gap后来由 Oilbird语义hidden key处理。复现报告索引token数/来源、query latency、hit rate、unique tree nodes、greedy/采样规则和数据泄漏检查。官方 `FasterDecoding/REST`。原文第 3–7 页方法，第 7–11 页实验，第 12–14 页附录。

## 索引与验证的最小实现

离线把语料按与 target 完全相同的 tokenizer 编码，为长度范围内的 n-gram 建倒排表，value 保存后继 token、频次和文档边界；必须禁止 continuation 跨文档拼接。在线从当前 prefix 的最长 suffix 开始回退，汇集命中 continuation 后插入 trie，共享前缀只占一个 verification 节点，再按频次/路径分数和节点预算裁剪。索引版本、语料许可、去重规则与 target 训练/评测集重叠都应写进实验清单。

单元测试可构造含重复片段的小语料，手工核对最长回退、文档边界、trie 节点数和 target greedy 提交路径；零命中必须无缝回退普通解码。性能应分解 CPU 查询、序列化/传输、tree mask、target verify，并按 domain 报 hit 后接受率。若用线上历史更新 datastore，还要做租户隔离、TTL、删除传播及 prompt injection 污染测试；这些不是外围工程，而是检索式 drafter 能否安全部署的必要条件。
