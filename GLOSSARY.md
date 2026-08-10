# 术语、公式与正确性边界

## 基本符号

- `p(x|c)`：target model在真实前缀 `c` 上的条件分布。
- `q(x|c)`：drafter/proposal分布。
- `γ` 或 `K`：每轮最大草稿深度；树方法还需节点预算 `B`。
- `α`：单位置接受概率；不少简化分析假设各位置同α，真实情况通常随深度下降。
- `τ` / acceptance length：每次target verification实际推进token数。论文有的含bonus token、有的不含，比较前必须检查。
- `T_draft,T_verify`：一轮草稿和验证wall time；每token延迟常写作 `(T_draft+T_verify)/τ`。

## 标准单候选 speculative sampling

drafter采 `x~q`，以

`a(x)=min(1,p(x)/q(x))`

接受。拒绝时从

`r(x) ∝ max(p(x)-q(x),0)`

采校正token。接受部分贡献 `min(p,q)`，残差补齐其余target质量，因此最终边缘为p。多步按真实prefix重复；首拒绝后不能继续使用基于错误prefix的普通链后缀。

## Greedy-exact 与 sampling-exact

Greedy-exact只要求最终序列与target逐步argmax相同，不能推出非零温度分布保持。Sampling-exact要求任意prefix下最终token分布等于p，单个随机种子下不必与AR baseline逐样本相同；应做统计检验而非逐样本比较。

## Bonus / correction token

target tree/block forward通常还算出 accepted prefix后的下一个分布。全草稿接受时从该p采一个bonus；拒绝时从residual采correction。很多论文的τ把它计入，因此最大值是 `γ+1`。

## Tree attention

把候选trie节点线性打包；节点只可attend根到自身的祖先，position id使用真实深度。兄弟互看、使用打包下标当position、accepted后保留错误branch KV都会破坏target条件分布。

## Proposal probability 与 confidence

`q`是生成候选的正规化概率，进入拒绝校正。confidence只是“可能被接受”的proxy，可用于排序/预算，但通常不能代替q。EAGLE-2的path value或DSpark的confidence错误会影响效率；若仍用标准verifier，不应影响分布。

## TV 与预计接受率

单候选标准校验的无条件接受概率为

`Σ_x min(p_x,q_x)=1-TV(p,q)=1-1/2||p-q||_1`。

这解释DistillSpec、DSpark、xPress为何用TV/L1对齐。多步预计接受是prefix survival之和，而非各位置top-1准确率简单平均。

## Marginal、conditional 与 joint draft

- marginal block：第k位只估 `q_k(x_k|prefix)`；各位置组合不一定形成target风格的联合。
- conditional/AR：`q(x_1:K|prefix)=∏q_k(x_k|prefix,x_<k)`。
- latent joint：引入共享z，`q(x_1:K)=Σ_z q(z)∏q_k(x_k|z,...)`。

随机校验需要知道实际proposal事件的概率。将parallel marginals直接相乘并称作AR q，必须有额外推导。

## Lossless、lossy 与“质量保持”

- **Lossless**：数学上保持指定target greedy行为或采样分布。
- **Approximate/lossy**：主动改变接受、target logits/router或trajectory。
- **任务质量近似不变**：有限benchmark经验结论，不能替代lossless。

典型反例：Medusa typical acceptance、MARS top-2 margin、ASD regret预算、AcceptMoE限制target experts均是lossy；Shared Speculative Streaming微调base后只相对新模型谈验证正确性。

## Non-anticipating scheduler

验证长度/候选准入不得利用在该决定之后才生成的随机candidate，否则selection bias会改变输出分布。DSpark对confidence全局排序时专门讨论这一点：理论early-stop或生产的历史capacity信号形成因果边界。

## 速度指标

- latency/TPOT：单请求或每输出token时间。
- throughput：系统每秒输出token；可能牺牲单请求延迟。
- goodput：满足SLA的有效吞吐。
- block efficiency：忽略/弱化实际kernel成本的每轮token推进。
- speedup：必须写清相对哪个baseline；“相对AR 4×”与“比EAGLE快1.4×”不可混写。

## 最低正确性测试

1. Greedy：多prompt、长输出逐token与无SD一致。
2. Sampling：小词表toy模型穷举；真实模型大量token做频率/TV/χ²，并覆盖拒绝、全接受、q=0、top-p边界。
3. Tree/cache：对每节点逐条AR重算logits对照tree logits；接受后cache与从头prefill对照。
4. 调度：固定同一proposal random stream，改变batch/load不应改变目标分布统计。
5. Lossy方法：显式报告trajectory divergence和真正改变后的decoding-policy baseline。
