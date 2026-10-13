"""Run the n-gram baseline on pinned WikiText-2 raw train/validation splits."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import urllib.request
from pathlib import Path

from babyllm import NGramMemory
from babyllm.evaluation import evaluate_next_token

REVISION = "00aa25585682d4957f9e86edc73f59be7419af99"
BASE = f"https://huggingface.co/datasets/Salesforce/wikitext/resolve/{REVISION}/wikitext-2-raw-v1"


def get_file(cache_dir: Path, split: str) -> Path:
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = cache_dir / f"{split}-00000-of-00001.parquet"
    if not path.exists():
        url = f"{BASE}/{path.name}"
        temp = path.with_suffix(".partial")
        try:
            with urllib.request.urlopen(url, timeout=60) as response, temp.open("wb") as output:
                while chunk := response.read(1024 * 1024):
                    output.write(chunk)
            temp.replace(path)
        finally:
            temp.unlink(missing_ok=True)
    return path


def rows(path: Path, limit: int) -> list[str]:
    import pyarrow.parquet as parquet

    table = parquet.read_table(path, columns=["text"])
    return [value for value in table.column("text").to_pylist() if value.strip()][:limit]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-dir", type=Path, default=Path("data/wikitext-2-raw-v1"))
    parser.add_argument("--train-limit", type=int, default=200)
    parser.add_argument("--validation-limit", type=int, default=100)
    parser.add_argument("--order", type=int, default=3)
    args = parser.parse_args(argv)
    if args.train_limit < 1 or args.validation_limit < 1:
        parser.error("limits must be positive")
    train_path = get_file(args.cache_dir, "train")
    validation_path = get_file(args.cache_dir, "validation")
    train = rows(train_path, args.train_limit)
    validation = rows(validation_path, args.validation_limit)
    started = time.perf_counter()
    with NGramMemory(order=args.order) as memory:
        for index, text in enumerate(train):
            memory.learn(text, document_id=f"wikitext-train-{index}", source="wikitext-train")
        train_seconds = time.perf_counter() - started
        metrics = evaluate_next_token(memory, validation)
        result = {
            "dataset": "Salesforce/wikitext",
            "configuration": "wikitext-2-raw-v1",
            "revision": REVISION,
            "license": "CC BY-SA 3.0 / GFDL; see dataset card",
            "split": "validation",
            "train_rows": len(train),
            "validation_rows": len(validation),
            "order": args.order,
            "train_seconds": round(train_seconds, 3),
            "total_seconds": round(time.perf_counter() - started, 3),
            "files_sha256": {"train": sha256(train_path), "validation": sha256(validation_path)},
            **memory.statistics(),
            **metrics,
        }
    print(json.dumps(result, sort_keys=True, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
