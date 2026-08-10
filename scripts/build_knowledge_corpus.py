#!/usr/bin/env python3
"""Build an auditable full-text corpus from the survey's curated core index."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path

from pypdf import PdfReader


ARXIV_RE = re.compile(r"arxiv\.org/abs/([^/?#]+)")
LINK_RE = re.compile(r"^- \[([^]]+)\]\((https?://[^)]+)\)$")
HEADING_RE = re.compile(r"^### (.+)$")
OPENREVIEW_PDF_FALLBACKS = {
    "gpsczXOsHn": "https://arxiv.org/pdf/2511.15898",
    "T9u56s7mbk": (
        "https://proceedings.iclr.cc/paper_files/paper/2025/file/"
        "575286a73f238b6516ce0467d67eadb2-Paper-Conference.pdf"
    ),
    "frsg32u0rO": (
        "https://proceedings.iclr.cc/paper_files/paper/2025/file/"
        "3e710b42b1a9ed898f607ec0f4fcc971-Paper-Conference.pdf"
    ),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--survey", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--request-delay", type=float, default=1.0)
    return parser.parse_args()


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii").lower()
    words = re.findall(r"[a-z0-9]+", ascii_value)
    return "-".join(words[:12]) or "paper"


def infer_year(title: str, url: str) -> int | None:
    match = re.search(r"\b(20\d{2})\b", title)
    if match:
        return int(match.group(1))
    arxiv = ARXIV_RE.search(url)
    if arxiv:
        prefix = int(arxiv.group(1).split(".", 1)[0][:2])
        return 2000 + prefix
    match = re.search(r"/(20\d{2})[./]", url)
    return int(match.group(1)) if match else None


def parse_core_index(survey: Path) -> list[dict]:
    text = survey.read_text(encoding="utf-8")
    section = text.split("## 15. 人工确认的核心文献索引", 1)[1]
    section = section.split("## 16.", 1)[0]
    category = None
    records = []
    used_ids: set[str] = set()
    for line in section.splitlines():
        heading = HEADING_RE.match(line)
        if heading:
            category = heading.group(1).strip()
            continue
        link = LINK_RE.match(line)
        if not link:
            continue
        if category is None:
            raise ValueError(f"Paper appears before a category: {line}")
        title, landing_url = link.groups()
        year = infer_year(title, landing_url)
        identifier = f"{year or 'unknown'}--{slugify(title)}"
        base_identifier = identifier
        suffix = 2
        while identifier in used_ids:
            identifier = f"{base_identifier}-{suffix}"
            suffix += 1
        used_ids.add(identifier)
        records.append(
            {
                "id": identifier,
                "title": title,
                "year": year,
                "category": category,
                "landing_url": landing_url,
                "pdf_url": initial_pdf_url(landing_url),
                "reading_status": "pending_full_text",
            }
        )
    if len(records) != 66:
        raise ValueError(f"Expected 66 curated core papers, found {len(records)}")
    return records


def initial_pdf_url(landing_url: str) -> str | None:
    arxiv = ARXIV_RE.search(landing_url)
    if arxiv:
        return f"https://arxiv.org/pdf/{arxiv.group(1)}"
    parsed = urllib.parse.urlparse(landing_url)
    if parsed.netloc == "aclanthology.org":
        identifier = parsed.path.strip("/")
        return f"https://aclanthology.org/{identifier}.pdf"
    if parsed.netloc == "openreview.net" and parsed.path == "/forum":
        paper_id = urllib.parse.parse_qs(parsed.query).get("id", [None])[0]
        if paper_id:
            return OPENREVIEW_PDF_FALLBACKS.get(
                paper_id,
                f"https://openreview.net/pdf?id={paper_id}",
            )
    return None


def fetch(url: str) -> tuple[bytes, str]:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "speculative-decoding-knowledge-base/1.0"},
    )
    with urllib.request.urlopen(request, timeout=90) as response:
        return response.read(), response.geturl()


def resolve_pdf_url(landing_url: str) -> str:
    known = initial_pdf_url(landing_url)
    if known:
        return known
    html_bytes, final_url = fetch(landing_url)
    html = html_bytes.decode("utf-8", errors="replace")
    candidates = re.findall(r'href=["\']([^"\']+)["\']', html, flags=re.I)
    pdf_candidates = [
        urllib.parse.urljoin(final_url, candidate)
        for candidate in candidates
        if ".pdf" in candidate.lower()
        or "paper" in candidate.lower() and "download" in candidate.lower()
    ]
    if not pdf_candidates:
        raise RuntimeError(f"Could not resolve PDF from {landing_url}")
    preferred = sorted(
        pdf_candidates,
        key=lambda value: (
            "supp" in value.lower(),
            "paper" not in value.lower(),
            len(value),
        ),
    )
    return preferred[0]


def extract_pdf(pdf_path: Path, text_path: Path) -> tuple[int, int]:
    reader = PdfReader(str(pdf_path))
    chunks = []
    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        chunks.append(f"\n\n===== PAGE {page_number} =====\n\n{text}")
    full_text = "".join(chunks).strip() + "\n"
    text_path.parent.mkdir(parents=True, exist_ok=True)
    text_path.write_text(full_text, encoding="utf-8", errors="replace")
    return len(reader.pages), len(full_text)


def download_record(record: dict, repo_root: Path) -> dict:
    source_root = repo_root / ".sources"
    pdf_path = source_root / "pdfs" / f"{record['id']}.pdf"
    text_path = source_root / "text" / f"{record['id']}.txt"
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    pdf_url = record.get("pdf_url") or resolve_pdf_url(record["landing_url"])
    if not pdf_path.exists():
        payload, final_url = fetch(pdf_url)
        if not payload.startswith(b"%PDF"):
            raise RuntimeError(
                f"Expected PDF for {record['id']}, got {len(payload)} bytes from {final_url}"
            )
        pdf_path.write_bytes(payload)
    else:
        final_url = pdf_url
        payload = pdf_path.read_bytes()
    page_count, text_chars = extract_pdf(pdf_path, text_path)
    return {
        **record,
        "pdf_url": final_url,
        "pdf_sha256": hashlib.sha256(payload).hexdigest(),
        "pdf_bytes": len(payload),
        "page_count": page_count,
        "extracted_text_chars": text_chars,
        "source_pdf_path": str(pdf_path.relative_to(repo_root)),
        "source_text_path": str(text_path.relative_to(repo_root)),
        "reading_status": "full_text_available",
    }


def write_manifest(repo_root: Path, records: list[dict]) -> None:
    metadata_dir = repo_root / "metadata"
    metadata_dir.mkdir(parents=True, exist_ok=True)
    path = metadata_dir / "core_papers.json"
    path.write_text(
        json.dumps(records, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    repo_root.mkdir(parents=True, exist_ok=True)
    records = parse_core_index(args.survey.resolve())
    write_manifest(repo_root, records)
    if not args.download:
        return
    completed = []
    for index, record in enumerate(records, start=1):
        try:
            completed_record = download_record(record, repo_root)
            print(
                f"OK {index}/{len(records)} {record['id']} "
                f"pages={completed_record['page_count']}",
                flush=True,
            )
        except Exception as error:
            completed_record = {
                **record,
                "reading_status": "download_failed",
                "download_error": str(error),
            }
            print(
                f"FAIL {index}/{len(records)} {record['id']}: {error}",
                flush=True,
            )
        completed.append(completed_record)
        write_manifest(repo_root, completed + records[index:])
        if index < len(records):
            time.sleep(max(float(args.request_delay), 0.0))


if __name__ == "__main__":
    main()
