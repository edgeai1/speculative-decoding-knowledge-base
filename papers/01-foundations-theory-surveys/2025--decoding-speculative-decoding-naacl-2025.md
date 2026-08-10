---
id: 2025--decoding-speculative-decoding-naacl-2025
title: "Decoding Speculative Decoding"
authors: [Minghao Yan, Saurabh Agarwal, Shivaram Venkataraman]
year: 2025
venue: NAACL 2025
status: deep_read_complete
primary_source: https://aclanthology.org/2025.naacl-long.328/
version_read: NAACL 2025 proceedings
pages_read: 1-14
pdf_sha256: f417b9f915fec9eb3957d832f88a8c3d943d2a74dc635f5c30295910a6b26262
---

# Decoding Speculative Decoding（NAACL 2025）精读

## 核心定位

这是一篇以 352+ 次实验反驳“draft LM 越强就越适合 SD”的系统研究。作者发现 draft latency 主要随 **深度** 而非参数量增长，语言任务 accuracy 又与 TAR（tokens accepted per iteration）弱相关；因此从 LLaMA-7B 结构化剪枝出仅 5 层、很宽的 796M drafter，在 LLaMA-65B 上比 Sheared-LLaMA-1.3B 提高约 98–112% throughput。

## 1. 两个诊断结论

### 1.1 Target verify 不一定是瓶颈

target 对 candidate block 做一次 prefill-like forward；drafter 却要做多次 serial decode。微剖析显示即使 lookahead 增大到较多 token，target verify 的增加相对有限，反而 draft loop 主导延迟。OPT-350M 与 1.3B 的 draft latency 接近，引出“参数量不是延迟代理”。

### 1.2 深度比宽度更贵

保持约 350M 参数改变 depth/width，AR latency 随层数近似线性；OPT-350M 从 24 层减少时 latency 线性下降，而 heads 从 16 增到 36、宽度翻倍，latency 几乎不变。原因是每层都引入顺序 kernel launch、权重/KV 和同步，宽矩阵在低 batch 下还有并行余量。

任务 accuracy 与 TAR 相关很弱：许多易接受 token 是功能词、标点和固定片段，不决定 MMLU/HellaSwag 正确率。选择 drafter 应直接优化 target agreement 与成本，而非下游 leaderboard。

## 2. Wide–shallow drafter 怎样得到

作者用 Sheared-LLaMA 的可学习 mask 从 LLaMA-7B 结构化剪枝，使用 RedPajama 0.4B tokens，跳过原方案额外 50B-token fine-tuning（故名 NoFT）。

- deep 1.3B：24 layers / 16 heads / FFN 5504 / d_model 2048；
- wide 1.3B：12 / 20 / 9280 / 2560；
- wide 796M/543M/290M：保持 LLaMA-7B 的 32 heads、FFN 11008、d_model 4096，只留 5/3/1 层。

1.3B wide 的 TAR 3.70，略低于 deep 的 3.81；单步 latency 却由 13.13ms 降至 6.69ms，throughput 从 23.10 升至 32.59 token/s。证明小幅牺牲 TAR 换大幅降低 `c` 更划算。

5 层 796M 最优；降到 3/1 层后对齐能力急降，而且 target 已占 cycle 80% 以上，继续压 draft 的收益上限很小。

## 3. 主结果与泛化

LLaMA-65B target、MMLU/HellaSwag/Chatbot Arena：temperature 1.0 下 796M wide 为 24.32/24.32/24.18 token/s，Sheared-1.3B 为 12.06/12.30/11.45，即 +101.6/+97.7/+111.8%；T=.5 仍约 +100–103.5%。

浅层也减少每序列 KV：context 1024 时 1.3B wide 120MB vs deep 192MB，降 37.5%，可支持更大 batch。LLaMA-3.1-8B target 上，由 LLaMA-3.2 剪枝的 Wide-829M 仅用 1M tokens、约 10 分钟蒸馏恢复 TAR，三任务 throughput 比 LLaMA-3.2-1B 高 42.6%，比 self-spec 高 51.8%。

796M drafter 从 LLaMA-1 family 得到，却在 LLaMA-2-70B 的 TAR 与 LLaMA-65B 接近；对 Vicuna-33B SFT target 也比 TinyLLaMA-1.1B throughput 高最多 45%，尽管后者 TAR 更高。对 CNNDM/XSum，作者方法相对 AR 131%/145% speedup，自推测为 99%/60%。

## 4. 复现与设计准则

1. 先 profile target prefill-like verify 和 draft serial loop；不要按参数比推断瓶颈。
2. 在等参数预算做 depth/width sweep，直接测 per-step latency、TAR 和最终 throughput。
3. 结构化剪枝需要与 target tokenizer/模型族对齐；用少量 target-like data 做 recovery distillation。
4. 选择 lookahead 时让 target cycle 占比和接受后缀浪费共同最小。
5. 同时测 KV footprint；浅层 drafter 的收益会通过更大可用 batch 二次放大。
6. accuracy、perplexity 可作 sanity check，但 model selection objective 应是 target agreement × hardware cost。

## 5. 结论边界

- 结果依赖当时 GPU/kernel 和低 batch regime；更宽层在 compute-bound GPU 上未必近似免费。
- 剪枝数据/target model family 仍相近，跨 tokenizer、语言和 domain 的移植性未充分验证。
- TAR 与“任务 accuracy 弱相关”不表示任何低质量模型都能起草；3/1 层退化正说明存在容量下限。
- paper 研究经典 independent AR drafter，不能直接推出 feature/block drafter 的最优宽深比。
- 111% 是相对现有 drafter 的 throughput 增幅，不是对 AR 的 2.11× speedup。

这篇论文把 drafter 设计从“小模型排行榜选择”变成了硬件—对齐共同优化，并直接连接到 Chen 2023 的宽浅 4B、后来的 DSpark hardware-aware scheduler 和 cost-aware training。

## 审读导航

| 内容 | 页码 |
|---|---:|
| 352+ 实验与问题定义 | 1–2 |
| latency/TAR 微剖析 | 3–6 |
| 剪枝结构、主结果 | 6–8 |
| 跨模型、SFT、自推测消融 | 8–9 |
| 限制与结论 | 9 |
| latency 模型、配置和补充实验 | 11–14 |

## 原始来源

- https://aclanthology.org/2025.naacl-long.328/

