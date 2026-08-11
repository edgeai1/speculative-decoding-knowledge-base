#!/usr/bin/env python3
"""Check that generated MkDocs pages contain no broken local href/src targets."""

from __future__ import annotations

import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


SITE_PREFIX = "/speculative-decoding-knowledge-base/"


class Links(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.targets: list[str] = []

    def handle_starttag(self, _tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for key, value in attrs:
            if key in {"href", "src"} and value:
                self.targets.append(value)


def resolve(site: Path, page: Path, raw: str) -> Path | None:
    parsed = urlsplit(raw)
    if parsed.scheme or parsed.netloc or raw.startswith(("#", "mailto:", "data:", "javascript:")):
        return None

    path = unquote(parsed.path)
    if path.startswith(SITE_PREFIX):
        target = site / path.removeprefix(SITE_PREFIX)
    elif path.startswith("/"):
        return None
    else:
        target = page.parent / path

    if not path or path.endswith("/"):
        target /= "index.html"
    return target.resolve()


def main() -> int:
    site = Path(sys.argv[1] if len(sys.argv) > 1 else "../.site/speculative-decoding-knowledge-base").resolve()
    errors: list[str] = []
    html_files = sorted(site.rglob("*.html"))

    for page in html_files:
        parser = Links()
        parser.feed(page.read_text(encoding="utf-8"))
        for raw in parser.targets:
            target = resolve(site, page, raw)
            if target is not None and not target.exists():
                errors.append(f"{page.relative_to(site)} -> {raw}")

    home = (site / "index.html").read_text(encoding="utf-8") if (site / "index.html").exists() else ""
    for marker in ("kb-hero", "66 篇精读", "研究空白"):
        if marker not in home:
            errors.append(f"home page missing expected marker: {marker}")
    if not (site / "search" / "search_index.json").is_file():
        errors.append("search index is missing")

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"site check passed: {len(html_files)} HTML pages, no broken local targets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
