---
id: 2024--redrafter
title: "Recurrent Drafter for Fast Speculative Decoding in Large Language Models"
authors: [Yunfei Cheng, Aonan Zhang, Xuanyu Zhang, Chong Wang, Yi Wang]
year: 2024
venue: arXiv preprint
status: deep_read_complete
primary_source: https://arxiv.org/abs/2403.09919
version_read: arXiv:2403.09919v5
pages_read: 1-14
pdf_sha256: 27b266ccb64e8b0aeb25ad310e1a54fdf9709e323ecb1bc4670ffd665ee3a63a
---

# ReDrafter 精读

## 一句话定位

ReDrafter 用一个以目标 LLM 隐藏状态为条件的轻量 RNN 自回归地产生 beam，再把 beam 中重复前缀合并成动态树交给目标模型一次校验。它证明了“顺序相关的小 drafter + 多候选树”在服务器 GPU 和 Apple Silicon 端侧都能落地，PyTorch/H100 最多约 `2.8×`，MLX/M2 Ultra 最多约 `2.3×`。

## 1. 设计动机

Medusa 的位置专属 heads 参数不共享、未来预测相互独立，候选笛卡尔积中有大量不协调组合。普通独立小 LM 虽然有因果结构，却没有直接利用目标 LLM 已算出的语义 feature。ReDrafter 折中：每轮目标模型产生当前保证正确的起始 token 与 hidden state，RNN 以它们为条件，使用共享 recurrent parameters 逐步扩展 beam；这样远期 token 看到了前序草稿，又无需重新用小 Transformer 编码整个前缀。

## 2. 一轮解码

1. 目标 LLM 对已确认前缀给出下一 token 和最后 hidden state；该 token 是本轮至少能提交的保底。
2. RNN 从此状态出发做固定深度、固定 beam 宽的搜索，生成若干候选序列及分数。
3. **Dynamic Tree Attention (DTA)** 将 beam 的共享 prefix 合并为 trie。线性打包节点，用 parent/ancestor mask 阻止兄弟分支互看，并设置正确 position ids。
4. LLM 一次评分整棵 trie；在 greedy 场景选择与目标逐位置匹配的最长候选前缀，写回对应 KV，丢弃其他节点。

树节点数常远少于 `beam_width × depth`，DTA 因而同时降低目标 attention 和 KV 搬运。它不是新的接受规则；正确性取决于外层 verifier。论文主流程面向 greedy，因此与目标 greedy 解码一致。

## 3. 训练

RNN 输入融合目标 hidden state 和 token embedding，递归状态负责携带候选历史。作者使用目标 LLM 做 knowledge distillation：软分布比单一 hard label 更能告诉小 RNN 哪些备选可用于 beam。训练/推理必须匹配 rollout 条件；只用 teacher-forced 真 token 会高估真实 beam 质量。

与 Medusa 每个 horizon 一套 head 不同，参数跨步共享，推理长度可调；但 RNN 步数形成串行小 kernel 链，beam top-k、索引和 gather 也可能成为端侧瓶颈。

## 4. 实验证据

论文在 Vicuna/MT-Bench 上比较 AR、Medusa、EAGLE 和不同实现。PyTorch/NVIDIA H100 最高约 `2.8×`，MLX/Apple M2 Ultra 最高约 `2.3×`。端侧结果是重要贡献：统一内存和 Metal kernel 下仍获益，说明方法不只依赖数据中心 GPU 的高算力/带宽比。

消融围绕 beam 宽/深、DTA 合并、蒸馏和 RNN 规模：更大 beam 提高找到匹配路径的概率，但树节点和 draft 搜索成本上升；DTA 在候选共享前缀多时最有效；蒸馏提高候选命中。最高速度数字对应特定配置，不能把 H100 与 M2 的实现差异解释成算法差异。

## 5. 实现检查表

官方代码是 `apple/ml-recurrent-drafter`。实现需取得与 LM head 对齐的目标 hidden state；RNN beam 状态和 token 序列同步重排；用 trie 去重并生成 parent map；目标 tree forward 后把 trie node 索引映射回各 beam；接受后仅保留路径 KV。端侧还要避免小 tensor 在 CPU/GPU 间同步。

基准至少拆出 RNN rollout、beam top-k、trie 构建、LLM tree verify、KV compact 五部分，并同时报告平均 accepted length 和实际树节点数。batch 增大后应测试 beam 状态 ragged batching，而非将 batch-1 结果外推。

## 6. 局限与可研究方向

- 主正确性叙述和实验偏 greedy；若做随机采样，必须另接标准拒绝校正并保存 proposal probability。
- RNN 串行 rollout 限制极长草稿，且目标 hidden state 与 checkpoint 强绑定。
- beam score 优化的是 draft likelihood，不一定等价于单位树成本的目标接受收益。
- DTA 的 trie 构建和动态形状可能妨碍 CUDA graph/静态编译；适合研究固定模板近似、GPU 原生构树和 serving-aware beam allocation。

原文第 2–6 页给算法、RNN 和 DTA，第 6–10 页为服务器/端侧实验与消融，第 11–14 页包含训练与实现补充。
