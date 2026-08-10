---
id: 2024--online-speculative-decoding-icml-2024
title: "Online Speculative Decoding"
authors: [Xiaoxuan Liu, Lanxiang Hu, Peter Bailis, Alvin Cheung, Zhijie Deng, Ion Stoica, Hao Zhang]
year: 2024
venue: ICML 2024
status: deep_read_complete
primary_source: https://proceedings.mlr.press/v235/liu24y.html
version_read: ICML 2024 proceedings
pages_read: 1-16
pdf_sha256: 76ab5471033a7534f24a8fbb7873d336bf61262873b19dc916c3bf2bc09ba1f4
---

# Online Speculative Decoding（OSD）精读

## 核心定位

OSD 把 target verification 产生的 logits 当作免费 teacher data，周期性在线更新小 drafter，使其适应真实 query distribution；还可按语言/主题路由到多个专门 drafter。接受率提高 0.1–0.65，A100 上四任务端到端 1.42–2.17×，但训练并发、灾难遗忘和隐私是生产化关键缺口。

## 1. 在线环路

每次 SD 得到 draft/target 在实际 trajectory 上的分布，把样本存入 buffer；当 buffer 达 size threshold 或超时，执行若干 KD update。论文比较 teacher-token、student-token 和 mix trajectory，以及 forward/reverse KL、JSD。最终推荐 teacher sampling + forward KL，但明确最优组合随任务/模型变化。

在线训练不改变 verification/correction，因此输出仍由 target distribution 决定；更新只改变未来 proposal。update interval 主实验为 8，lookahead=5。训练可用服务空闲 FLOPs；论文估算 160M vs 7B、80M vs 3B 的算力比为 18.75/12.6，Arena trace 中 cluster utilization 很低，但这是假设性 capacity 论证而非完整生产 scheduler。

## 2. 离线/在线结果

target/draft：Vicuna-7B/LLaMA-160M、FLAN-T5-XL 3B/T5-small 80M；Spider、GSM8K、CodeSearch-Python、Alpaca-Finance。

两 epoch 离线 KD 中 Vicuna 原始 α=.28/.58/.38/.57，teacher-forward-KL 后 .76/.75/.65/.67；FLAN-T5 原始 .13/.29/.28/.39，提升到 .78/.62/.81/.63。student trajectories 通常稍差，但更便宜/更贴近 exposure。

streaming 时，OSD 起初落后于用前 10% 数据预蒸馏的 static model，但经过少量请求迅速追上。将四数据集每 2k 请求拼接模拟 shift，边界 α 立即下降，随后恢复；说明能适应 abrupt shift，也说明短期尾延迟会恶化。

## 3. 多 drafter customization

LMSYS 4 个月 trace 按 top-5 非英语语言 metadata 或 BERT topic classifier 路由。专门 drafter 的 α 比通用 model 高 .1–.2；topic 多数 >.6，social/computer 接近 .9。5×160M 权重+KV 从 target 的约 2% 内存增至约 10%。论文没有解出最优 expert 数/路由，也没有处理错误路由和专家冷启动。

## 4. 墙钟

llama.cpp、A100-80G、batch=1。33B/1.1B 在 α=.5→.9 时加速从 1.28×→2.63×；7B/160M 从 .95×（实际减速）→2.55×。真实蒸馏后，33B pair 的 Spider/GSM/Finance/Code 为 2.17/1.89/1.92/1.69×；7B pair 为 1.63/1.60/1.47/1.42×，Arena 1.36×。OSD fine-tuned Medusa heads 在 Spider 从 Medusa 1.34× 提至 2.01×。

## 5. 实现与局限

- buffer 必须只保存必要 logits/top-k，并明确用户数据 retention/privacy；在线 teacher distributions 可能含敏感内容。
- training stream 与 inference stream 要隔离 CUDA/内存，按 SLO 决定更新；论文未实测训练抢占下 P99。
- 需 replay/正则化避免 domain shift 后遗忘旧域，并按 model version invalidation buffer。
- 多 expert routing 是 query-level，不能捕获同一 response 内 code/math phase 变化。
- adaptation 改变接受率但不改 target correctness；不要把 α 提升直接当任务质量提升。

## 审读导航

| 内容 | 页码 |
|---|---:|
| buffer/KD 算法和 sampling choices | 1–4 |
| 系统开销与路由 | 4–5 |
| offline/online/shift 实验 | 5–7 |
| real trace、latency、Medusa | 7–9 |
| 训练/系统细节 | 12–16 |

## 原始来源

- https://proceedings.mlr.press/v235/liu24y.html
- https://github.com/LiuXiaoxuanPKU/OSD

