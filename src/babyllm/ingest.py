"""Explicit local document ingestion. No background browsing or uploads."""

from __future__ import annotations

import hashlib
from html.parser import HTMLParser
from pathlib import Path

from .memory import NGramMemory


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.suppressed = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style"}:
            self.suppressed += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"} and self.suppressed:
            self.suppressed -= 1

    def handle_data(self, data: str) -> None:
        if not self.suppressed:
            self.parts.append(data)


def read_text(path: str | Path) -> str:
    path = Path(path)
    if path.suffix.lower() not in {".txt", ".md", ".html", ".htm"}:
        raise ValueError("supported formats: .txt, .md, .html, .htm")
    data = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".html", ".htm"}:
        parser = _TextExtractor()
        parser.feed(data)
        return " ".join(parser.parts)
    return data


def ingest_file(memory: NGramMemory, path: str | Path) -> int:
    path = Path(path)
    content = read_text(path)
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
    return memory.learn(content, document_id=digest, source=str(path))
