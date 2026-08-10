---
id: 2026--windowed-mtp
title: "Windowed-MTP: Removing the Full-Context Draft-KV Tax at Million-Token Context"
authors: [Alagappan Valliappan]
year: 2026
venue: arXiv preprint
status: deep_read_complete
primary_source: https://arxiv.org/abs/2607.21535
version_read: arXiv:2607.21535
pages_read: 1-25
pdf_sha256: c63f01ea5839cd33710325498ec6371a5606937dab1088937d230cd73460e586
---

# Windowed-MTP 精读

## 关键观察与方法

内置MTP常被视为免费，但其每个draft step若 full-attend 1M KV，γ次读取会主导；hybrid/linear target verify更便宜时这一税更暴露，低acceptance甚至比无SD慢。Windowed-MTP只把 **draft attention** 改成 StreamingLLM式 sink + 最近W window，target verification仍 full context。未读KV可用ring buffer不存，1M处回收总KV约7.7–11%。

正确性边界很干净：window改变q而不改p/verifier；greedy严格比对在精确算术下同序列，sampling用标准拒绝校正同分布。论文还做 in-run decision-invariance：window proposal top1与native相同约86–94%，按位置conditional acceptance多数在置信区间内；少数任务acceptance可能升或降，系统读节省通常覆盖。

Qwen GDN-MoE 35/122B与Mamba2-hybrid NoPE120B，SGLang、单B200、1M、深度d=7(γ=6)：相对shipping native MTP每 decode-step降 `28–44%`，margin随context增大。该比值是 **每轮成本**；只有matched acceptance时才等于每token延迟改善。摘要的“+28%”符号按论文语义是cost reduction/ratio优势，应在报告中写清方向。

## 复现和局限

需要把window应用到每个MTP层且不误裁target cache；sink、W、NoPE/RoPE position、ring wrap与CUDA graph需测试。扫context/γ/workload并报native/window AL、step cost、TPOT。单作者preprint、模型/硬件覆盖有限；1M实验不代表中短context最佳；事实检索若依远KV可能显著损害q。研究接口是按请求/position动态W、draft-only learned retrieval与线性target的联合cost model。原文第 3 页税模型，第 4–5 页方法/正确性，第 6–12 页实验，第 13–25 页分解与附录。

## 内存路径与退化测试

每个 MTP step 的 attention 都应读取相同定义的 sink 加最近 W 个已提交/暂存位置；环形缓冲必须在 wrap 后保持逻辑 position 与物理 slot 的映射。target verifier 仍读取完整 KV，因此实现最好把 target cache 与 draft 的轻量视图分离，避免“节省 draft 内存”的裁剪误伤 target。对 RoPE 模型，窗口化不意味着位置从零重排；对 NoPE/混合层，也需逐层确认哪些模块真正应用窗口。

评估应先在短 context 上确认 native 与 windowed MTP 的 logits/接受差异来自远程信息裁剪而非 cache bug，再扩展到 1M。报告每个 draft step 的 HBM bytes、attention kernel 时间、实际 window 命中、接受位置曲线与每输出 token 时间；同时加入 W 从 full 到极小的扫描。最重要的反例集是答案依赖开头稀有事实且 sink 不含该事实的请求。若该集 proposal 明显退化，在线策略就应根据检索需求或接受反馈扩大 W，而不能把固定窗口当作普适配置。
