"""Command line interface for the reproducible local baseline."""

from __future__ import annotations

import argparse
import json

from .ingest import ingest_file
from .memory import NGramMemory


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="babyllm")
    parser.add_argument("--db", default="babyllm.sqlite3", help="local SQLite memory path")
    parser.add_argument("--order", type=int, default=3)
    commands = parser.add_subparsers(dest="command", required=True)
    learn = commands.add_parser("learn", help="learn from explicitly supplied text")
    learn.add_argument("text")
    ingest = commands.add_parser("ingest", help="learn from a local text, Markdown, or HTML file")
    ingest.add_argument("path")
    complete = commands.add_parser("complete", help="generate a deterministic continuation")
    complete.add_argument("prompt")
    complete.add_argument("--max-tokens", type=int, default=30)
    commands.add_parser("stats", help="show local memory size")
    args = parser.parse_args(argv)
    with NGramMemory(args.db, order=args.order) as memory:
        if args.command == "learn":
            print(memory.learn(args.text))
        elif args.command == "ingest":
            print(ingest_file(memory, args.path))
        elif args.command == "complete":
            print(memory.complete(args.prompt, args.max_tokens))
        else:
            print(json.dumps(memory.statistics(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
