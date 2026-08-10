#!/usr/bin/env python3
"""Build a page-aware evidence packet for a locally extracted paper.

The packet is an aid for close reading, not an automatic summary.  It keeps the
highest-signal passages for each review dimension and always preserves PDF page
numbers so that claims in a paper note can be checked against the source.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


DIMENSIONS = {
    "method_and_algorithm": (
        "method", "algorithm", "framework", "architecture", "inference",
        "verification", "accept", "draft", "proposal", "sampling",
    ),
    "training_and_objective": (
        "train", "loss", "objective", "distill", "dataset", "optimization",
        "learning rate", "epoch", "batch size",
    ),
    "theory_and_guarantee": (
        "theorem", "proof", "proposition", "lemma", "guarantee", "lossless",
        "distribution", "complexity", "bound",
    ),
    "experiments_and_system": (
        "experiment", "evaluation", "benchmark", "latency", "throughput",
        "speedup", "hardware", "gpu", "baseline", "implementation",
    ),
    "ablation_and_sensitivity": (
        "ablation", "sensitivity", "analysis", "effect of", "impact of",
        "varying", "comparison",
    ),
    "limitations_and_failure_modes": (
        "limitation", "future work", "fail", "drawback", "however", "risk",
        "degrade", "overhead",
    ),
}


def split_pages(text: str) -> list[tuple[int, str]]:
    chunks = re.split(r"===== PAGE (\d+) =====\n", text)
    return [(int(chunks[i]), chunks[i + 1].strip()) for i in range(1, len(chunks), 2)]


def paragraphs(page: str) -> list[str]:
    raw = re.split(r"\n\s*\n", page)
    cleaned = [re.sub(r"[ \t]+", " ", p.replace("\n", " ")).strip() for p in raw]
    return [p for p in cleaned if len(p) >= 100]


def score(p: str, words: tuple[str, ...]) -> int:
    lower = p.lower()
    return sum(1 + min(lower.count(w), 3) for w in words if w in lower)


def make_packet(source: Path, per_dimension: int) -> str:
    pages = split_pages(source.read_text(encoding="utf-8", errors="replace"))
    all_paras = [(n, p) for n, page in pages for p in paragraphs(page)]
    lines = [f"# Reading packet: {source.stem}", "", f"Pages traversed: {len(pages)}", ""]

    # The beginning and end are included for bibliographic context and author conclusions.
    for label, selected in (("opening", pages[:2]), ("closing", pages[-2:])):
        lines.extend([f"## {label}", ""])
        for n, page in selected:
            lines.extend([f"### PDF page {n}", "", page[:6000], ""])

    for dimension, words in DIMENSIONS.items():
        ranked = sorted(
            ((score(p, words), n, p) for n, p in all_paras),
            key=lambda item: (-item[0], item[1]),
        )
        chosen = []
        seen = set()
        for value, n, p in ranked:
            if value <= 0:
                break
            fingerprint = re.sub(r"\W+", "", p.lower())[:180]
            if fingerprint in seen:
                continue
            seen.add(fingerprint)
            chosen.append((value, n, p))
            if len(chosen) == per_dimension:
                break
        lines.extend([f"## {dimension}", ""])
        for value, n, p in chosen:
            lines.extend([f"### PDF page {n} · evidence score {value}", "", p[:3500], ""])

    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("paper_id", help="Stable paper id used under .sources/text")
    parser.add_argument("--per-dimension", type=int, default=8)
    parser.add_argument("--output-dir", type=Path, default=Path(".cache/reading_packets"))
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    source = root / ".sources" / "text" / f"{args.paper_id}.txt"
    if not source.exists():
        raise SystemExit(f"Missing extracted text: {source}")
    output_dir = root / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"{args.paper_id}.md"
    output.write_text(make_packet(source, args.per_dimension), encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
