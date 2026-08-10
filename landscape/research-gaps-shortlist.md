# 下一阶段选题短名单

**基于调研截止：2026-08-10**

## 推荐顺序

| 优先级 | 课题 | 核心基线 | 新颖空间 | 主要风险 |
|---|---|---|---|---|
| 1 | 分布漂移鲁棒、带风险控制的 DSpark prefix-survival 调度 | DSpark、D-cut、AngelSpec | 高 | 需要构造可信的 online shift/traffic traces |
| 2 | Acceptance-collapse 攻击的 lossless 防御 | Mistletoe、ADSD、DSpark/EAGLE-3 | 高 | 防御须经自适应攻击检验 |
| 3 | 不改变 target routing 的 MoE-aware tree/verification budgeting | AcceptMoE、EAGLE-3、JetSpec/PCTree | 高 | 需要可观测 expert routing/traffic 的 serving stack |
| 4 | Grammar/tool-state-aware semantic speculation | Oilbird、suffix/n-gram、EAGLE-3 | 高 | 需要真实 tool traces 与严格副作用隔离 |
| 5 | 首次 rejection 后 verifier 计算的严格无损复用 | strict tree、CURE、ASD | 很高 | 可能存在很强的不可能性边界 |

## 首选课题：两周 feasibility study

### 研究问题

DSpark 的 confidence head 在训练/校准分布上预测 prefix survival，并据此裁剪每个请求的 verification length。若 domain、language、temperature、quantization 或 traffic mix 改变，offline ECE 和排序可能失效。问题是：

> 能否在不改变 target verification 和输出分布的前提下，用在线、风险控制的 survival calibration 提高分布漂移下的 goodput 与 SLO 稳定性？

### 第一周：复现和诊断

1. 在公开 DeepSpec/DSpark checkpoint 上复现 Qwen3-8B 的 chat/math/code accepted-length 与 fixed-threshold 曲线；
2. 加入四类 shift：未见语言、tool/JSON、temperature 0→0.7/1.0、输入/输出长度与 concurrency shift；
3. 按 depth 报告 reliability diagram、ECE/Brier、prefix coverage、ranking AUC；
4. 记录 verification waste、draft/verify latency、TPS/user、P95 TPOT；
5. 判断性能损失究竟来自 calibration、ranking、还是硬件 profile 不匹配。

### 第二周：最小方法验证

1. baseline：全局 temperature scaling、per-depth scaling、滑动窗口 isotonic；
2. 方法原型：domain/depth-conditional online conformal lower bound，配 change detector；
3. scheduler 用 survival LCB 选择 \(K\)，并加入最大风险/最小服务公平约束；
4. 在 unseen shift 和回到原分布两种情况下测恢复速度和 oracle regret；
5. 若校准改进不能转化为至少一个 production metric 的稳定提升，则及时停止，不把它包装成只改善 ECE 的论文。

### Go / no-go

Go：原 DSpark scheduler 在至少两种自然 shift 下出现显著过验证或欠验证；简单 offline scaling 不能解决；online risk control 在相同输出、相同硬件下改善 SLO goodput，且开销小于收益的 10%。

No-go：confidence ranking 在所有自然 shift 下都稳定；瓶颈完全来自 verifier kernel/profile；或 online calibration 的 sample complexity 大到无法在 traffic phase 内收敛。此时转向“跨硬件 cost-model/profile adaptation”，而不是继续堆 calibration 方法。

## 选题前必须再做的查重

- 检索 2026-08-10 之后的 `confidence scheduled speculative decoding`、`calibrated speculative decoding`、`conformal LLM serving`；
- 对 DSpark、AngelSpec、D-cut、TETRIS、SPEED-Bench 做向前引用追踪；
- 检查 DeepSpec/vLLM Speculators/SGLang issue 和 pending PR，确认系统功能未先行实现；
- 明确工作是 strict lossless scheduler，而不是 relaxed verification；
- 在摘要中把贡献写成“shift-risk/goodput guarantee”，不要写成泛化的“dynamic draft length”。

