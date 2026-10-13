"""Incremental, auditable token memory with interpolated n-gram prediction."""

from __future__ import annotations

import json
import re
import sqlite3
from collections import Counter
from pathlib import Path

TOKEN_RE = re.compile(r"\w+|[^\w\s]", re.UNICODE)
START = "<s>"
END = "</s>"


def tokenize(text: str) -> list[str]:
    """Unicode-aware word and punctuation tokenization; preserve original case."""
    return TOKEN_RE.findall(text)


class NGramMemory:
    """SQLite-backed token counts. Training is incremental and deterministic."""

    def __init__(self, path: str | Path = ":memory:", order: int = 3):
        if order < 1:
            raise ValueError("order must be at least 1")
        self.order = order
        self.db = sqlite3.connect(str(path))
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS grams (context TEXT NOT NULL, token TEXT NOT NULL, "
            "count INTEGER NOT NULL CHECK(count > 0), PRIMARY KEY(context, token))"
        )
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS documents (id TEXT PRIMARY KEY, source TEXT NOT NULL, "
            "token_count INTEGER NOT NULL, added_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)"
        )
        self.db.commit()

    def close(self) -> None:
        self.db.close()

    def __enter__(self) -> "NGramMemory":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def learn(self, text: str, *, document_id: str | None = None, source: str = "chat") -> int:
        tokens = tokenize(text)
        if not tokens:
            return 0
        if document_id is not None and not document_id:
            raise ValueError("document_id cannot be empty")
        with self.db:
            if document_id is not None:
                existing = self.db.execute("SELECT 1 FROM documents WHERE id=?", (document_id,)).fetchone()
                if existing:
                    return 0
                self.db.execute(
                    "INSERT INTO documents(id, source, token_count) VALUES (?, ?, ?)",
                    (document_id, source, len(tokens)),
                )
            sequence = [START] * (self.order - 1) + tokens + [END]
            counts: Counter[tuple[str, str]] = Counter()
            for position in range(self.order - 1, len(sequence)):
                for width in range(self.order):
                    context = sequence[position - width:position] if width else []
                    counts[(json.dumps(context, ensure_ascii=False), sequence[position])] += 1
            self.db.executemany(
                "INSERT INTO grams(context, token, count) VALUES (?, ?, ?) "
                "ON CONFLICT(context, token) DO UPDATE SET count=count+excluded.count",
                [(context, token, count) for (context, token), count in counts.items()],
            )
        return len(tokens)

    def candidates(self, context: list[str], limit: int = 10) -> list[tuple[str, float]]:
        """Return candidates ranked by highest available context, with unigram fallback."""
        if limit < 1:
            raise ValueError("limit must be at least 1")
        for width in range(min(len(context), self.order - 1), -1, -1):
            key = json.dumps(context[-width:] if width else [], ensure_ascii=False)
            rows = self.db.execute(
                "SELECT token, count FROM grams WHERE context=? ORDER BY count DESC, token LIMIT ?",
                (key, limit),
            ).fetchall()
            if rows:
                total = self.db.execute("SELECT SUM(count) FROM grams WHERE context=?", (key,)).fetchone()[0]
                return [(token, count / total) for token, count in rows]
        return []

    def complete(self, prompt: str, max_tokens: int = 30) -> str:
        if max_tokens < 0:
            raise ValueError("max_tokens cannot be negative")
        context = ([START] * (self.order - 1) + tokenize(prompt))[-(self.order - 1):] if self.order > 1 else []
        output: list[str] = []
        for _ in range(max_tokens):
            choices = self.candidates(context, limit=1)
            if not choices or choices[0][0] == END:
                break
            token = choices[0][0]
            output.append(token)
            if self.order > 1:
                context = (context + [token])[-(self.order - 1):]
        return detokenize(output)

    def statistics(self) -> dict[str, int]:
        documents = self.db.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        grams = self.db.execute("SELECT COUNT(*) FROM grams").fetchone()[0]
        tokens = self.db.execute("SELECT COALESCE(SUM(count), 0) FROM grams WHERE context='[]'").fetchone()[0]
        return {"documents": documents, "distinct_ngrams": grams, "observed_tokens": tokens}


def detokenize(tokens: list[str]) -> str:
    text = " ".join(tokens)
    return re.sub(r"\s+([.,!?;:%)\]}])", r"\1", text)
