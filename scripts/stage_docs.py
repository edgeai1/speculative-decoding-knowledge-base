#!/usr/bin/env python3
"""Create an ignored MkDocs source tree without duplicating tracked research files."""

from __future__ import annotations

import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / ".cache" / "docs-src"

TOP_LEVEL_DOCS = (
    "TAXONOMY.md",
    "COMPARISON.md",
    "METHODOLOGY.md",
    "GLOSSARY.md",
    "SOURCES.md",
    "AUDIT_REPORT.md",
)

CONTENT_DIRS = (
    "assets",
    "collections",
    "landscape",
    "papers",
    "metadata",
)


def main() -> None:
    if STAGE.exists():
        shutil.rmtree(STAGE)
    STAGE.mkdir(parents=True)

    for name in TOP_LEVEL_DOCS:
        shutil.copy2(ROOT / name, STAGE / name)
    shutil.copy2(ROOT / "HOME.md", STAGE / "index.md")
    shutil.copy2(ROOT / "README.md", STAGE / "catalog.md")
    catalog = STAGE / "catalog.md"
    catalog.write_text(
        catalog.read_text(encoding="utf-8").replace('src="assets/', 'src="../assets/'),
        encoding="utf-8",
    )
    for name in CONTENT_DIRS:
        shutil.copytree(ROOT / name, STAGE / name)

    # README is the GitHub landing page, while HOME is the documentation landing
    # page. Rename both only in the ignored staging tree and repair local links.
    for path in STAGE.rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        text = text.replace("(README.md", "(catalog.md")
        text = text.replace("(../README.md", "(../catalog.md")
        path.write_text(text, encoding="utf-8")

    files = sum(path.is_file() for path in STAGE.rglob("*"))
    print(f"staged {files} documentation source files in {STAGE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
