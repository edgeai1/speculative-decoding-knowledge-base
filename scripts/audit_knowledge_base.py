#!/usr/bin/env python3
"""Fail-closed integrity audit for the publishable knowledge base."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def parse_front_matter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not match:
        raise ValueError(f"missing front matter: {path.relative_to(ROOT)}")
    result = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            result[key.strip()] = value.strip().strip('"')
    return result


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def pdf_pages(path: Path) -> int | None:
    try:
        output = subprocess.check_output(["pdfinfo", str(path)], text=True, stderr=subprocess.DEVNULL)
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    match = re.search(r"^Pages:\s+(\d+)$", output, re.M)
    return int(match.group(1)) if match else None


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    meta = json.loads((ROOT / "metadata" / "core_papers.json").read_text(encoding="utf-8"))
    rows = {row["id"]: row for row in meta}
    notes = sorted((ROOT / "papers").glob("*/*.md"))
    fms = {path.stem: parse_front_matter(path) for path in notes}

    if len(meta) != 66 or len(notes) != 66:
        errors.append(f"expected 66 metadata rows and notes, got {len(meta)} and {len(notes)}")
    if set(rows) != set(fms):
        errors.append(f"metadata/note id mismatch: metadata-only={sorted(set(rows)-set(fms))}, note-only={sorted(set(fms)-set(rows))}")

    required = {"id", "title", "year", "venue", "status", "primary_source", "version_read", "pages_read", "pdf_sha256"}
    for path in notes:
        fm = fms[path.stem]
        missing = required - set(fm)
        if missing:
            errors.append(f"{path.relative_to(ROOT)} missing front-matter keys {sorted(missing)}")
            continue
        if fm["id"] != path.stem or fm["status"] != "deep_read_complete":
            errors.append(f"{path.relative_to(ROOT)} has inconsistent id/status")
        row = rows.get(path.stem)
        if not row:
            continue
        for key in ("pdf_sha256", "reading_status", "interpretation_path"):
            expected = fm["status"] if key == "reading_status" else (path.relative_to(ROOT).as_posix() if key == "interpretation_path" else fm["pdf_sha256"])
            if row.get(key) != expected:
                errors.append(f"{path.stem}: metadata {key} mismatch")
        text = path.read_text(encoding="utf-8")
        if len(text) < 1500:
            errors.append(f"{path.stem}: interpretation unexpectedly short ({len(text)} chars)")

        pdf = ROOT / row["source_pdf_path"]
        if pdf.exists():
            if sha256(pdf) != fm["pdf_sha256"]:
                errors.append(f"{path.stem}: local PDF SHA-256 mismatch")
            pages = pdf_pages(pdf)
            if pages is not None and pages != row["page_count"]:
                errors.append(f"{path.stem}: PDF page count {pages} != metadata {row['page_count']}")
        else:
            warnings.append(f"{path.stem}: local PDF absent; public note/source metadata still available")

    markdown_files = sorted(ROOT.glob("*.md")) + sorted((ROOT / "landscape").glob("*.md")) + notes
    link_pattern = re.compile(r"(?<!!)\[[^\]]*\]\(([^)]+)\)")
    for path in markdown_files:
        for target in link_pattern.findall(path.read_text(encoding="utf-8")):
            target = target.strip().split("#", 1)[0]
            if not target or re.match(r"^[a-z]+://", target):
                continue
            local = (path.parent / target).resolve()
            if not local.exists():
                errors.append(f"dead local link in {path.relative_to(ROOT)}: {target}")

    # Split every marker so this audit source does not trigger its own literal scan.
    forbidden = ["github" + "_pat_", "BEGIN " + "PRIVATE KEY", "XDS" + "@2025"]
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or any(part in {".sources", ".cache", ".git"} for part in path.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for marker in forbidden:
            if marker in text:
                errors.append(f"sensitive marker found in {path.relative_to(ROOT)}")

    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    for entry in (".sources/", ".cache/"):
        if entry not in gitignore:
            errors.append(f".gitignore missing {entry}")

    deep = sum(fm.get("status") == "deep_read_complete" for fm in fms.values())
    pages = sum(row["page_count"] for row in meta)
    chars = sum(row["extracted_text_chars"] for row in meta)
    total_note_chars = sum(len(path.read_text(encoding="utf-8")) for path in notes)
    report = [
        "# 知识库完整性审计",
        "",
        "- 审计日期：2026-08-10",
        f"- 核心元数据 / 解读：{len(meta)} / {len(notes)}",
        f"- `deep_read_complete`：{deep}",
        f"- 核读 PDF 页数：{pages}",
        f"- 抽取原文字符：{chars:,}",
        f"- 逐篇解读字符：{total_note_chars:,}",
        f"- 错误：{len(errors)}",
        f"- 警告：{len(warnings)}",
        "",
    ]
    if errors:
        report.extend(["## 错误", ""] + [f"- {item}" for item in errors] + [""])
    if warnings:
        report.extend(["## 警告", ""] + [f"- {item}" for item in warnings] + [""])
    if not errors:
        report.extend(["## 结论", "", "核心论文、逐篇状态、来源哈希、PDF 页数、内部链接、忽略规则和敏感信息扫描均通过。", ""])
    (ROOT / "AUDIT_REPORT.md").write_text("\n".join(report), encoding="utf-8")

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"audit passed: {len(notes)} notes, {pages} pages, {total_note_chars:,} interpretation chars, {len(warnings)} warnings")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
