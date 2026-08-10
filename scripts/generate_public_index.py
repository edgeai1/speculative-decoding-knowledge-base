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
        "# Speculative Decoding 研究知识库",
        "",
        "> 截止日期：**2026-08-10（Asia/Shanghai）**。本库收录 **66 篇核心论文的逐篇全文精读**，覆盖 2018–2026 年 8 月；每个条目均记录已读版本、页码范围与 PDF SHA-256，便于复核。",
        "",
        "这个知识库面向准备进入 speculative decoding 研究的读者。目标不是复述摘要，而是把每篇论文的问题、假设、算法、公式、训练与推理流程、正确性边界、实验、实现路径、复现风险、局限和可继续研究的问题压缩进一个可独立阅读的中文文件。",
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
        out.extend([f"### {label}（{len(items)} 篇）", "", "| 年份 | 论文 | Venue |", "|---:|---|---|"])
        for item in items:
            out.append(f"| {item['year']} | [{item['title']}]({item['path']}) | {item.get('venue', '—')} |")
        out.append("")

    out.extend([
        "## 仓库结构",
        "",
        "```text",
        "papers/       66 篇逐篇精读，按研究问题分为 6 类",
        "landscape/    全方向综述、研究空白与候选问题",
        "metadata/     核心语料元数据与高召回候选表",
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
    update_metadata(notes, paths)
    write_sources(notes)
    print(f"generated README/SOURCES and normalized {len(notes)} metadata records")


if __name__ == "__main__":
    main()
