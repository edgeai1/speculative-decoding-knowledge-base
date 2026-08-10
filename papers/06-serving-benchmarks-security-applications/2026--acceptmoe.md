---
id: 2026--acceptmoe
title: "AcceptMoE: Commitment-Weighted Self-Sizing Verifier Expert Sets for Efficient MoE Speculative Decoding"
authors: [Shuang Liang, Hao Chen, Zhiwen Mo, Qianzhou Wang, Guoyu Li, Lingxiao Ma, Wayne Luk]
year: 2026
venue: arXiv preprint
status: deep_read_complete
primary_source: https://arxiv.org/abs/2608.02989
version_read: arXiv:2608.02989
pages_read: 1-10
pdf_sha256: 771ac623b4f135ad8c191d7234881fd691c2d2c430d7443ff9c2fc6d76041c08
---

# AcceptMoE 精读

## 核心问题与方法

MoE tree verification的成本不只节点数：各分支router选出的 **expert union** 可能很大，即使最终只提交一条路径；offload时还取决于专家是否已驻GPU。AcceptMoE用target router score乘离线估计的节点commitment probability，评价某expert对最终输出的预计贡献；根据整block score分布自动选择eligible expert set大小，而非用户给固定budget。offload模式优先cache-resident eligible专家，避免预测自然route再prefetch。

这会约束 **target verifier自身路由**，因此改变模型分布，严格说不是lossless SD。12个model-task、Qwen3-Instruct/Coder/GPT-OSS120B，平均准确率比natural-routing EAGLE-3低0.27百分点；全专家驻留SGLang B=1 throughput为baseline `1.290×`（范围1.217–1.339），offload `2.06×`，H2D traffic降73.6–77.1%。准确率均值可能掩盖任务最坏下降，且speed仅B=1。

复现需区分token count、union experts、实际route/load balance、cache hit和H2D bytes；以相同模型直接 constrained routing baseline判断收益是否真来自speculative commitment。还要评KL/perplexity、稀有领域、router collapse和batch。研究价值是把“节点被接受概率”纳入MoE计算预算，但可进一步做可恢复fallback、误差预算与lossless cache/prefetch而非改路由。

原文第 3–5 页commitment selector，第 5–8 页resident/offload实验，第 9–10 页消融与结论。

## 路由预算如何实现与审计

对树中每个节点先由 target router 得到 expert score，再乘该节点最终落在提交路径上的 commitment 估计；跨节点聚合后排序 expert，并依据本 block 分数分布确定集合大小。执行 MoE 层时仅允许集合内专家，offload 场景再在近似等价项中优先 resident expert。这里必须保存 natural-routing 结果作为旁路基线，因为集合裁剪发生在 verifier 内部，最终 token 已不再来自原 target 模型。

性能统计应区分逻辑 top-k routes、整树 union size、真正执行的 expert-token pairs、H2D bytes、cache hit 与负载不均；仅报节点数无法解释收益。质量审计则应按任务和 token 位置报告 natural/constrained router 分歧、输出 KL、最坏准确率变化及罕见 expert 的覆盖，不能只看十二项平均。一个更严格的研究方向是保持 natural route 不变，只用 commitment 预测做预取/驻留和验证节点选择；这样可把 AcceptMoE 的系统洞察与模型近似风险拆开。
