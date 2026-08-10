---
id: 2023--distillspec
title: "DistillSpec: Improving Speculative Decoding via Knowledge Distillation"
authors: [Yongchao Zhou, Kaifeng Lyu, Ankit Singh Rawat, Aditya Krishna Menon, Afshin Rostamizadeh, Sanjiv Kumar, Jean-François Kagy, Rishabh Agarwal]
year: 2024
venue: ICLR 2024
status: deep_read_complete
primary_source: https://arxiv.org/abs/2310.08461
version_read: arXiv:2310.08461v2 / ICLR 2024
pages_read: 1-40
pdf_sha256: c9a399bf8bf5bc0658bb7212990bb589227931e85c1b80cc28e7c89924d9566e
---

# DistillSpec（ICLR 2024）精读

## 核心定位

DistillSpec 系统研究“为 speculative acceptance 而蒸馏”，而不是把 standalone student accuracy 当目标。关键结论：model-generated、尤其 draft on-policy trajectories 远优于固定 ground truth；最优 FKL/RKL/JSD/TV loss 随任务和 sampling policy 变化；蒸馏后相对标准 SD 再快 10–45%，GSM8K drafter 跨 23 个 BBH tasks 仍平均改善约 26%。

## 1. 目标为何不是普通 KD

单 token 接受率 `β=Σ min(p,q)=1-TV(p,q)`，但真实 block efficiency 还依赖 target trajectory 上各位置误差与 prefix survival。训练目标为白盒 target/draft distribution 间 divergence 的 token 平均；候选数据可来自固定数据、teacher、student 或二者混合。

直接最小 TV 理论最贴近 acceptance，却实验中很少最好；优化性、mode behavior 和 rollout distribution 同样重要。固定 ground-truth prefix 有 exposure mismatch；student on-policy 会暴露自己的错误 prefix，成本又低于 teacher generation。因此论文推荐从 student-generated data 起步，把 divergence 当需验证集搜索的超参。

## 2. Recipe sweep

XSum greedy 上 student+teacher / JSD 的 block-efficiency improvement 约 .53；GSM8K greedy 最佳是 student-only/FKL 约 .61；GSM8K T=1 最佳 teacher/RKL 约 .49。固定数据各 loss 普遍最差。蒸馏后的 task accuracy 增益与 SD compatibility 仅弱相关，再次说明不能按 student leaderboard 选 drafter。

T5-small→T5-XL 的 XSum/GSM8K/CNN-DM/WMT/BBH，论文图 1 报 greedy/non-greedy 相对标准 SD 增益约 10–46%。GSM8K distilled small 用于 23 个 unseen BBH，SD speed 从 1.93/1.78× 提至 2.21/2.02×（greedy/non-greedy）；给 T5-XXL target 也比未蒸馏 draft 高 7–37%。

## 3. Lossy 与 model garden

论文把 leniency `ε` 加进 acceptance，比较线性/平方/指数变换，形成 quality-latency curve；它明确是 lossy，不应与标准 DistillSpec 的严格 correction 混淆。GSM8K 很多 token 不影响最终准确率，所以可明显提速，但该结论不自动覆盖 calibration/safety/diversity。

五档 T5（77M/250M/800M/3B/11B）的结论是：先把大 teacher 蒸馏成满足质量的较小 target，再用 DistillSpec 为该 target 训练更小 draft。XSum latency 17.3→2.7（6.4×），ROUGE2 23.1→23.0；GSM8K 15.0→1.4（10.7×），accuracy 33.1→34.8。此“6–10×”包含换 target/KD 的复合收益，不是同一 target 上纯 SD 的速度。

## 4. 复现/局限

- 采集 target 与 draft on-policy trajectories，按目标 sampling temperature/top-p 生成；混用 greedy data 会损害 stochastic setting。
- sweep FKL/RKL/JSD/TVD，选择指标应是 block efficiency + wall-clock，而不只 loss。
- target 版本变更后 draft alignment 失效；披露生成数据与蒸馏成本。
- 主体是 T5 family/有限任务；同 tokenizer、encoder-decoder 结果不保证跨架构。
- acceptance rate 的 i.i.d. 公式仅作 proxy，完整实验必须测 finite γ。

DistillSpec 奠定了 acceptance-oriented training 的实验方法学：data distribution、divergence 和 decoding policy 必须联合选择。

## 审读导航

| 内容 | 页码 |
|---|---:|
| 接受率与训练目标 | 3–6 |
| 主结果与 transfer | 6–7 |
| recipe 16 组合 | 7–8 |
| lossy/model-garden | 8–9 |
| 算法、超参和全面补充 | 13–40 |

## 原始来源

- https://arxiv.org/abs/2310.08461

