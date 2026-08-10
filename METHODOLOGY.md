# 调研、全文精读与质量控制方法

## 截止范围

本快照截止 **2026-08-10（Asia/Shanghai）**。核心集不是按标题关键词自动得到，而是从高召回检索结果中人工筛出对 speculative decoding 的 proposal、verification、training、serving、benchmark、安全或应用有直接技术贡献的论文。

## 语料规模

- 高召回候选：1260 条，保留在 `metadata/literature_candidates.csv`，其中包含综述引用、相邻方向和误召回，不能解释为1260篇核心论文。
- 核心全文：66篇、1188 PDF页、约4,201,415字符抽取文本、PDF约95.33MiB。
- 深读产物：66个一一对应的中文解读文件；所有条目状态均为 `deep_read_complete`。
- 原始PDF/text：仅本地研究证据，`.gitignore`排除，不随知识库发布。

## 核心纳入标准

满足至少一项：提出/严格分析draft–verify算法；改变drafter结构/训练/选择；提出多候选/树/校正规则；解决长上下文/continuous batching/MoE/offload等系统瓶颈；提供有代表性的统一benchmark、正确性审计或安全攻击；将SD用于RL等新工作负载。

排除或降到候选表：只在背景提到SD；纯量化/剪枝且无SD机制；重复版本只保留最新或正式版；不可定位原文；营销文章；没有足够技术细节的衍生实现。

## 每篇精读流程

1. 从官方 proceedings、OpenReview或arXiv下载PDF，记录入口、版本、页数和SHA-256。
2. 按页抽取文本并生成带page marker的reading packet；从首页读到附录结束，而非只读abstract。
3. 定位问题、假设、符号、algorithm、proof、architecture、training、inference、experiment tables、ablation、limitations和appendix implementation。
4. 把论文事实与本库判断分开：用“作者报告/论文证明”表述原结论，用“边界/风险/不能推出”标注审计。
5. 每个解读至少覆盖：一句话定位；方法与实现；正确性/复杂度；实验数字和baseline；消融；复现清单；局限和后续问题；原文页码定位。
6. 仅完成上述步骤后将状态从 `full_text_available` 改为 `deep_read_complete`，并进入顶层README。

## 速度数字的规范化阅读

不跨论文直接排序最高speedup。每个数字至少绑定：target/draft、GPU、precision、engine/kernel、batch/concurrency、ISL/OSL、task、temperature/top-p、chain/tree/block budget、acceptance rule、baseline和是否含prefill/外部action。

特别警惕：相对慢HF baseline；offload对常驻GPU的巨大倍数；batch1对serving的外推；论文间不同训练数据；包含lossy acceptance；acceptance length含bonus与否；模拟上限被写成实测；固定输出长度与natural EOS混用。

## 正确性审计

逐篇区分四层保证：greedy序列等价、采样分布等价、只相对微调后模型等价、经验质量近似。重点检查proposal `q`是否可定义、拒绝residual是否更新、多候选是否重复计质量、树mask是否保持真实prefix、动态调度是否non-anticipating、target本身的router/logits是否被改。

## 自动质量检查

`scripts/audit_knowledge_base.py` 检查：核心metadata与notes一一对应；66项状态/页码/哈希；README链接；本地PDF哈希与页数（若语料存在）；敏感字符串；`.sources/.cache`不进入Git。`scripts/generate_public_index.py`只从完成状态生成公开目录，防止把未读候选误标成精读。

## 已知局限

- 2026年论文多数仍是快速迭代preprint；快照后版本可能改变数字或论证。
- 66篇是高相关核心集而非数学意义“全世界所有相关文本”；候选表用于后续增量审计。
- 中文解读不能替代在投稿/证明复用时查原文；哈希和页码用于回溯。
- 部分闭源模型/生产系统（尤其线上traffic/kernel）只能评公开证据，无法独立复现实验。
- 未把PDF上传，读者需从 `SOURCES.md` 官方入口获取。

## 更新协议

新论文先进入候选表；确认正式标题/版本和核心相关性；下载核读全文；新增解读和source hash；运行审计；更新截止日期和方向综述。旧论文出现新版时保留原hash并更新 `version_read`，在解读中标明结果变化。
