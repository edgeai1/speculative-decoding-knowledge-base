#!/usr/bin/env python3
"""Generate the public README, source manifest, and normalized paper status metadata."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
META_PATH = ROOT / "metadata" / "core_papers.json"

CATEGORIES = [
    ("01-foundations-theory-surveys", "01 基础、理论与综述"),
    ("02-independent-drafters-alignment-selection", "02 独立 drafter、对齐与在线选择"),
    ("03-feature-mtp-parallel-block", "03 Feature head、MTP 与并行块草稿"),
    ("04-tree-multi-draft-verification", "04 Tree、多候选与 verification"),
    ("05-training-free-self-spec-long-context", "05 Training-free、自推测与长上下文"),
    ("06-serving-benchmarks-security-applications", "06 Serving、基准、安全与应用"),
]

CATEGORY_PAGES = {
    "01-foundations-theory-surveys": {
        "path": "collections/01-foundations.md",
        "description": "从 blockwise parallel decoding 到严格 speculative sampling、最优传输、多 draft 凸优化与接受率理论，建立整个方向的数学底座。",
        "questions": [
            "为什么一次 target forward 可以无损提交多个 token？",
            "greedy-exact 与 distribution-preserving 分别需要什么条件？",
            "接受率、期望提交长度与真实 wall-clock speedup 如何区分？",
        ],
        "route": [
            "2018--blockwise-parallel-decoding-2018",
            "2023--fast-inference-from-transformers-via-speculative-decoding-icml-2023",
            "2023--spectr-optimal-transport-verification-2023",
            "2026--global-resolution-iclr-2026-oral",
        ],
    },
    "02-independent-drafters-alignment-selection": {
        "path": "collections/02-independent-drafters.md",
        "description": "研究独立小模型如何与 target 对齐、蒸馏、在线更新和动态选择，并揭示跨语言、跨领域与模型族迁移的边界。",
        "questions": [
            "什么训练目标真正优化接受率，而不只是 next-token accuracy？",
            "什么时候在线适应的收益能覆盖更新成本？",
            "一个 drafter 能否跨 checkpoint、语言和 tokenizer 迁移？",
        ],
        "route": [
            "2023--big-little-decoder",
            "2023--distillspec",
            "2025--hass-iclr-2025",
            "2026--curse-of-multilinguality",
        ],
    },
    "03-feature-mtp-parallel-block": {
        "path": "collections/03-feature-mtp.md",
        "description": "方向最密集的主线：从 Medusa / EAGLE feature heads 到 DFlash 并行块，再到 Domino、DSpark、PCTree 对候选内因果性与生产调度的修复。",
        "questions": [
            "parallel marginals 为什么不是一个合法的 joint proposal？",
            "怎样用低成本 Markov / RNN / tree conditioning 修复 block 内依赖？",
            "proposal 质量、draft latency 与 verification capacity 应如何联合优化？",
        ],
        "route": [
            "2024--medusa",
            "2024--eagle-icml-2024",
            "2026--dflash-icml-2026",
            "2026--domino",
            "2026--dspark",
            "2026--pctree",
        ],
    },
    "04-tree-multi-draft-verification": {
        "path": "collections/04-tree-verification.md",
        "description": "用树和多候选扩大 target support 覆盖，同时维护严格 residual 账本；也系统审视 block verification 与 lossy verifier 的收益边界。",
        "questions": [
            "多候选为何不能各自独立接受后任取一个成功项？",
            "固定 verification 节点预算下，怎样选择最有价值的前缀闭包树？",
            "近似接受应如何量化 regret、轨迹偏离和序列级质量风险？",
        ],
        "route": [
            "2023--specinfer",
            "2024--sequoia",
            "2025--block-verification-iclr-2025",
            "2026--revisiting-lossy-verification",
        ],
    },
    "05-training-free-self-spec-long-context": {
        "path": "collections/05-self-spec-long-context.md",
        "description": "无需独立神经 drafter 或专门训练，利用跳层、自身稀疏 KV、历史检索与窗口化 MTP，应对长上下文中的 KV 读取税。",
        "questions": [
            "如何让 self-draft 变快而不破坏完整 target cache？",
            "长上下文中应该使用 window、retrieval、sparse KV 还是层级 proposal？",
            "历史复用带来的内存、隐私、污染与租户隔离成本是什么？",
        ],
        "route": [
            "2024--draft-verify-self-speculative-decoding-acl-2024",
            "2024--triforce",
            "2024--magicdec",
            "2025--longspec",
            "2026--windowed-mtp",
        ],
    },
    "06-serving-benchmarks-security-applications": {
        "path": "collections/06-serving-security.md",
        "description": "把 speculative decoding 放进真实系统：dynamic batching、goodput、SLA、MoE、RL rollout、统一基准，以及输出不变但计算成本崩溃的攻击。",
        "questions": [
            "为什么 batch=1 的最高 speedup 不能代表生产 serving？",
            "怎样用 non-anticipating scheduler 给全 batch 分配 draft / verify 预算？",
            "如何隔离 acceptance-collapse 攻击并给出最坏额外成本上界？",
        ],
        "route": [
            "2023--synergy-of-sd-and-batching",
            "2026--performance-or-illusion-mlsys-2026",
            "2026--speed-bench-icml-2026",
            "2026--adsd",
        ],
    },
}


def front_matter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not match:
        raise ValueError(f"missing front matter: {path}")
    result: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        result[key.strip()] = value.strip().strip('"')
    return result


def collect_notes() -> tuple[list[dict], dict[str, Path]]:
    notes: list[dict] = []
    paths: dict[str, Path] = {}
    for path in sorted((ROOT / "papers").glob("*/*.md")):
        fm = front_matter(path)
        fm["path"] = path.relative_to(ROOT).as_posix()
        fm["category_dir"] = path.parent.name
        notes.append(fm)
        paths[fm["id"]] = path
    return notes, paths


def write_readme(notes: list[dict]) -> None:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for note in notes:
        grouped[note["category_dir"]].append(note)

    out = [
        '<div align="center">',
        '  <img src="assets/images/repo-banner.svg" width="100%" alt="Speculative Decoding Research Knowledge Base banner">',
        "  <h1>Speculative Decoding 研究知识库</h1>",
        "  <p>把论文森林变成一张可比较、可复现、可以直接选题的研究地图。</p>",
        "  <p>",
        '    <a href="https://edgeai1.github.io/speculative-decoding-knowledge-base/"><img alt="Documentation" src="https://img.shields.io/badge/Documentation-在线阅读-4f46e5?style=for-the-badge&logo=materialformkdocs&logoColor=white"></a>',
        '    <a href="https://edgeai1.github.io/speculative-decoding-knowledge-base/AUDIT_REPORT/"><img alt="Audit" src="https://img.shields.io/badge/Audit-0_errors-0891b2?style=for-the-badge&logo=checkmarx&logoColor=white"></a>',
        '    <a href="https://edgeai1.github.io/speculative-decoding-knowledge-base/papers/03-feature-mtp-parallel-block/2026--dspark/"><img alt="DSpark" src="https://img.shields.io/badge/Includes-DSpark-312e81?style=for-the-badge"></a>',
        "  </p>",
        "  <p><b>66 篇核心精读</b> · <b>1,188 页全文核读</b> · <b>6 条研究主线</b> · <b>截至 2026-08-10</b></p>",
        "</div>",
        "",
        "---",
        "",
        "> [!NOTE]",
        "> 本库覆盖 2018–2026 年 8 月的 66 篇核心论文。每个条目均记录已读版本、页码范围与 PDF SHA-256；原始 PDF 因版权不进入仓库。",
        "",
        "这个知识库面向准备进入 speculative decoding 研究的读者。目标不是复述摘要，而是把每篇论文的问题、假设、算法、公式、训练与推理流程、正确性边界、实验、实现路径、复现风险、局限和可继续研究的问题压缩进一个可独立阅读的中文文件。",
        "",
        "<p align=\"center\"><a href=\"https://edgeai1.github.io/speculative-decoding-knowledge-base/\"><b>打开可搜索文档站 →</b></a></p>",
        "",
        "## 从哪里开始",
        "",
        "- 第一次进入方向：先看 [方法谱系与分类](TAXONOMY.md)，再读基础类别中的两篇 2023 年 speculative sampling 奠基论文。",
        "- 准备做算法：看 [跨论文比较与研究问题](COMPARISON.md) 和 [研究空白 shortlist](landscape/research-gaps-shortlist.md)。",
        "- 准备做系统：重点读第 05/06 类、DSpark、DFlash、SPEED-Bench 和 *Performance or Illusion?*。",
        "- 核对 lossless/lossy：先看 [术语与正确性边界](GLOSSARY.md)，再看 Block Verification、MARS、Revisiting Lossy Verification 与 ASD。",
        "- 查更宽文献：看 [截至 2026-08-10 的完整方向综述](landscape/complete-survey-2026-08-10.md)；[1260 条高召回候选表](metadata/literature_candidates.csv) 仅是检索候选，不等于 1260 篇核心论文或已完成精读。",
        "",
        "## 阅读状态与证据边界",
        "",
        "本 README 只列出 `deep_read_complete` 条目。原始 PDF 与抽取文本用于本地核读，因版权不进入仓库；公开文件保留官方入口、版本、页码和哈希。速度数字均按原论文硬件、batch、temperature、backend和baseline解释，不把最高 endpoint 当作普遍结论。详见 [调研与精读方法](METHODOLOGY.md) 和 [来源清单](SOURCES.md)。",
        "",
        "## 核心论文目录",
        "",
    ]

    for category_dir, label in CATEGORIES:
        items = sorted(grouped[category_dir], key=lambda n: (int(n["year"]), n["title"].lower()))
        collection_path = CATEGORY_PAGES[category_dir]["path"]
        out.extend([
            f"### {label}（{len(items)} 篇）",
            "",
            f"[查看本类导读与推荐阅读路线]({collection_path})",
            "",
            "| 年份 | 论文 | Venue |",
            "|---:|---|---|",
        ])
        for item in items:
            out.append(f"| {item['year']} | [{item['title']}]({item['path']}) | {item.get('venue', '—')} |")
        out.append("")

    out.extend([
        "## 仓库结构",
        "",
        "```text",
        "papers/       66 篇逐篇精读，按研究问题分为 6 类",
        "collections/  6 个专题入口与推荐阅读路线",
        "landscape/    全方向综述、研究空白与候选问题",
        "metadata/     核心语料元数据与高召回候选表",
        "assets/       文档站视觉样式、图标与横幅",
        "scripts/      语料构建、阅读证据包与质量审计脚本",
        "```",
        "",
        "## 维护原则",
        "",
        "- 论文是否“无损”以输出序列/分布的数学保证为准，不以任务分数近似不变代替。",
        "- acceptance length、wall-clock speedup、throughput 与 goodput 分开记录。",
        "- 跨论文比较先统一硬件、engine、batch、上下文、输出长度、temperature、tree/block budget 与 baseline。",
        "- 新论文先进入候选表，经人工相关性筛选和全文精读后才进入核心目录。",
        "- 当前快照日期之后出现的论文不被暗示为已覆盖。",
        "",
    ])
    (ROOT / "README.md").write_text("\n".join(out), encoding="utf-8")


def write_collections(notes: list[dict]) -> None:
    grouped: dict[str, list[dict]] = defaultdict(list)
    by_id = {note["id"]: note for note in notes}
    for note in notes:
        grouped[note["category_dir"]].append(note)

    for category_dir, label in CATEGORIES:
        details = CATEGORY_PAGES[category_dir]
        items = sorted(grouped[category_dir], key=lambda n: (int(n["year"]), n["title"].lower()))
        total_pages = sum(int(str(item["pages_read"]).split("-")[-1]) for item in items)
        latest = max(int(item["year"]) for item in items)
        output_path = ROOT / details["path"]
        output_path.parent.mkdir(parents=True, exist_ok=True)

        out = [
            "---",
            f'title: "{label}"',
            f'description: "{details["description"]}"',
            "---",
            "",
            f"# {label}",
            "",
            '<div class="kb-section-lead" markdown>',
            "",
            details["description"],
            "",
            "</div>",
            "",
            '<div class="kb-inline-stats">',
            f"  <span><strong>{len(items)}</strong> 篇核心论文</span>",
            f"  <span><strong>{total_pages}</strong> 页核读</span>",
            f"  <span>更新至 <strong>{latest}</strong></span>",
            "</div>",
            "",
            "## 读完这一类，应能回答",
            "",
        ]
        out.extend(f"- {question}" for question in details["questions"])
        out.extend(["", "## 推荐阅读路线", ""])
        for index, paper_id in enumerate(details["route"], start=1):
            paper = by_id[paper_id]
            relative = "../" + paper["path"]
            out.append(f"{index}. **[{paper['title']}]({relative})** — {paper.get('venue', '—')}，{paper['year']}。")

        out.extend([
            "",
            "## 全部精读",
            "",
            "| 年份 | 论文 | Venue | 核读页码 |",
            "|---:|---|---|---:|",
        ])
        for item in items:
            relative = "../" + item["path"]
            out.append(
                f"| {item['year']} | [{item['title']}]({relative}) | {item.get('venue', '—')} | {item.get('pages_read', '—')} |"
            )
        out.extend([
            "",
            '<div class="kb-footer-cta" markdown>',
            "",
            "### 继续横向比较",
            "",
            "读完单篇后回到方法矩阵，检查正确性保证、proposal 结构和系统工作区间是否可直接比较。",
            "",
            "[打开跨论文比较](../COMPARISON.md){ .md-button .md-button--primary }",
            "[返回全部目录](../README.md){ .md-button }",
            "",
            "</div>",
            "",
        ])
        output_path.write_text("\n".join(out), encoding="utf-8")


def update_metadata(notes: list[dict], paths: dict[str, Path]) -> None:
    meta = json.loads(META_PATH.read_text(encoding="utf-8"))
    note_by_id = {n["id"]: n for n in notes}
    for row in meta:
        note = note_by_id[row["id"]]
        row["reading_status"] = note["status"]
        row["interpretation_path"] = paths[row["id"]].relative_to(ROOT).as_posix()
        row["version_read"] = note.get("version_read", "")
        row["pages_read"] = note.get("pages_read", "")
    META_PATH.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_sources(notes: list[dict]) -> None:
    out = [
        "# 核心论文来源与核读版本",
        "",
        "以下 66 项与逐篇解读一一对应。`pages_read` 表示本知识库核读的 PDF 页范围；SHA-256 用来确定本地核读版本。PDF 不随仓库发布。",
        "",
        "| 年份 | 论文 | 已读版本 | 页码 | 官方入口 | PDF SHA-256 |",
        "|---:|---|---|---:|---|---|",
    ]
    for item in sorted(notes, key=lambda n: (int(n["year"]), n["title"].lower())):
        sha = item.get("pdf_sha256", "")
        source = item.get("primary_source", "")
        out.append(
            f"| {item['year']} | [{item['title']}]({item['path']}) | {item.get('version_read', '—')} | "
            f"{item.get('pages_read', '—')} | [source]({source}) | `{sha}` |"
        )
    out.append("")
    (ROOT / "SOURCES.md").write_text("\n".join(out), encoding="utf-8")


def main() -> None:
    notes, paths = collect_notes()
    if len(notes) != 66 or any(n.get("status") != "deep_read_complete" for n in notes):
        raise SystemExit("refusing to publish: expected 66 deep_read_complete notes")
    write_readme(notes)
    write_collections(notes)
    update_metadata(notes, paths)
    write_sources(notes)
    print(f"generated README/SOURCES and normalized {len(notes)} metadata records")


if __name__ == "__main__":
    main()
