---
id: 2024--draft-verify-self-speculative-decoding-acl-2024
title: "Draft & Verify: Lossless Large Language Model Acceleration via Self-Speculative Decoding"
authors: [Jun Zhang, Jue Wang, Huan Li, Lidan Shou, Ke Chen, Gang Chen, Sharad Mehrotra]
year: 2024
venue: ACL 2024
status: deep_read_complete
primary_source: https://aclanthology.org/2024.acl-long.607/
version_read: ACL 2024 proceedings
pages_read: 1-20
pdf_sha256: 66cfd86ab84c8a453131806c27969aad1bc63c89376cf798bee7e3650ae7fd25
---

# Draft & Verify / Self-Speculative Decoding 精读

## 核心思想

同一 LLM在 draft阶段跳过一组中间 transformer layers，快速自回归 γ个 token；verify阶段恢复完整网络一次评分，严格 greedy匹配或标准采样校正。无需另存小模型/训练，跳层 draft与 target共享权重、embedding和大部分 KV。

## 层选择和自适应退出

跳太少 draft不够快，跳太多接受率低。论文先用校准数据搜索候选 skip集合，目标是端到端时间而非单纯 acceptance；采用分段/贪心而非指数枚举。运行时维护最近接受统计，根据目标 α自适应调 draft exiting/长度：容易样本多草稿，困难样本早验证。分析指出低于约80%接受时最佳 K可能只有1，说明固定长 draft会倒退。

验证使用原完整模型，greedy输出逐 token相同；非零温度只有实现 residual rejection才分布相同。跳层产生的 draft KV不能简单当完整层 KV使用：被跳层在 verify中补算/更新，cache索引需与 accepted prefix一致。

## 结果和边界

LLaMA-2及变体、多个任务最高 `1.99×`，常见约1.4–1.9×；无需额外权重是优势，但 verify仍运行完整模型，draft每 token也运行多数层，理论上限低于极小独立 drafter。最佳 skip集合模型/任务相关，校准开销与跨领域漂移存在；tensor/pipeline parallel时不连续跳层可能破坏均衡。

复现需固定 layer IDs、γ、温度；测 skipped forward、verify、补cache与接受长；逐 token比较 greedy；以采样频率测试 stochastic。它是 LayerSkip/early-exit self-speculation的重要基线。原文第 3–6 页算法/层搜索，第 6–11 页结果，第 12–20 页附录。

## 缓存与层选择的实现要点

一轮 draft 中，未跳过层可以递增自己的 KV，但被跳过层没有与草稿 token 对应的完整表示；verify 接受前缀后，必须用完整网络产生并提交所有层的正式 KV，再丢弃被拒绝位置。最稳妥的实现是把 tentative 与 committed cache 分开，用接受长度统一推进指针。测试应覆盖全接受、首 token 拒绝、中途拒绝和 EOS，并逐层比较 self-spec 路径与原始自回归路径的 cache shape、position id 和最终 logits。

层集合的选择应在独立校准集上最小化 `draft_time + verify_time` 除以期望提交 token，而不是最大化 top-1 agreement。还要加入连续层段等硬件约束，因为理论上相同的跳层数可能产生完全不同的 pipeline bubble 和 kernel 启动成本。报告至少包含每个候选 skip set 的 draft 延迟、接受位置曲线和端到端 TPOT；若跨域后接受率下降，控制器要能退回较浅跳层或普通 AR，避免自适应本身成为振荡源。
