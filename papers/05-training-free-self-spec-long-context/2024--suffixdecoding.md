---
id: 2024--suffixdecoding
title: "SuffixDecoding: Extreme Speculative Decoding for Emerging AI Applications"
authors: [Gabriele Oliaro, Zhihao Jia, Daniel Campos, Aurick Qiao]
year: 2024
venue: NeurIPS 2025
status: deep_read_complete
primary_source: https://arxiv.org/abs/2411.04975
version_read: arXiv:2411.04975v3 / NeurIPS 2025
pages_read: 1-22
pdf_sha256: c3cb7f16b044bbd6d2ac8849d460eba0846974b453734b2d177edae924af60f0
---

# SuffixDecoding 精读

## 核心思想

Agent/self-refine/SQL/coding请求会重复历史长片段。SuffixDecoding维护 global历史输出树与 per-request prompt/output树；以当前最后 p tokens做 exact suffix匹配，匹配节点的后代就是候选continuations。CPU draft约20µs/token，无神经模型逐步成本。

对候选节点 N，条件频率 `C(N)=count(N)/Σ_sibling count`，路径分数 `D(N)=D(parent)C(N)`。从匹配节点贪心加入 D最高叶子到验证树。匹配越长通常越可信，所以节点预算 `MAX_SPEC=αp`（经验α 1–4）；遍历两棵树和多个p，选择 `Σ_N D(N)`最高的树。也可按score在suffix与model drafter间路由。

greedy target tree equality验证保持输出。随机sampling需另接严格多候选校正；历史频率只是经验proposal。SWE-Bench/AgenticSQL最高 speculative `5.3×`，比 EAGLE-2/3最高约2.8×、Token Recycling约1.9×；含prefill与外部action的SWE端到端仍最高约4.5×。这些来自高重复agent workload，普通chat不是同分布。

## 成本、风险与复现

训练免费但global suffix tree可达O(历史token) CPU内存，历史日志涉及隐私/租户隔离和staleness；exact match会被新变量值打断。复现报告历史窗口、eviction、是否含当前prompt、α/P/节点预算、查询/构树/target耗时和污染检查。Oilbird正是修复“正确continuation在池中但lexical key不可达”。原文第 3–6 页算法，第 7–13 页agent实验，第 14–22 页内存和补充。

## 数据结构与在线生命周期

实现上可用反向 suffix trie 或 suffix-array 风格索引定位当前末尾 p tokens，再从每个命中状态向前展开 continuation。`count(node)/sum(count(siblings))` 的分母必须对应同一父节点，路径分数沿祖先相乘；合并 global 与 per-request 树时要去重同一 token prefix，之后再按总节点预算选择。每提交新 token 更新当前请求树，只有满足策略时才晋升全局历史，避免未验证草稿或失败输出污染索引。

复现实验需要给冷启动、预热后和跨会话三种状态，因为最高速度依赖已有重复历史。除平均 hit rate 外，还应报告匹配长度、候选在树中但未被预算选中的比例、被 target 接受的深度及内存随历史增长曲线。与 n-gram/REST 对比要统一可见语料和节点数。服务侧应默认禁止跨租户内容进入共享树；即使输出由 target 验证，命中行为、时延变化和候选内容仍可能形成隐私侧信道。
