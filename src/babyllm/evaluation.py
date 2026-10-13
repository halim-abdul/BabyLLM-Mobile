"""Reproducible held-out evaluation for the n-gram baseline."""

from __future__ import annotations

import math
from collections.abc import Iterable

from .memory import END, START, NGramMemory, tokenize


def evaluate_next_token(memory: NGramMemory, texts: Iterable[str]) -> dict[str, float | int]:
    """Top-1 accuracy and coverage; test texts must not appear in training data."""
    correct = covered = total = 0
    for text in texts:
        sequence = [START] * (memory.order - 1) + tokenize(text) + [END]
        for position in range(memory.order - 1, len(sequence)):
            context = sequence[max(0, position - memory.order + 1):position]
            choices = memory.candidates(context, limit=1)
            total += 1
            if choices:
                covered += 1
                correct += int(choices[0][0] == sequence[position])
    return {
        "tokens": total,
        "coverage": covered / total if total else math.nan,
        "top1_accuracy": correct / total if total else math.nan,
    }
