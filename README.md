# BabyLLM-Mobile

**A small, inspectable starting point for research on incremental language memory.** The repository provides a Python n-gram baseline, local document ingestion, a reproducible evaluation helper, an offline Android n-gram prototype, and an optional PyTorch GRU with causal attention. **It is not a pretrained assistant or a demonstrated research result.**

The original project vision is an on-device assistant that adapts to user-approved chats and documents, combines symbolic memory with a compact neural model, and works across languages. This repository now separates that vision from what can be run and measured today.

## What works today

| Component | Status | Evidence |
| --- | --- | --- |
| Incremental n-gram memory | Implemented | SQLite counts, context backoff, deterministic generation, tests |
| Local text ingestion | Implemented | UTF-8 `.txt`, `.md`, `.html`, `.htm`; content-hash deduplication |
| Next-token evaluation | Implemented | Held-out top-1 accuracy and coverage helper |
| GRU with causal attention | Experimental | Optional PyTorch model and one-step training test |
| Adaptive embeddings | Planned | No adaptation algorithm or benchmark yet |
| Cross-language assistance | Planned | Unicode tokenization works, but multilingual quality is unmeasured |
| Android, offline n-gram prototype | Implemented; build/device validation pending | Local text entry, document picker, memory deletion; no network permission |
| Android neural deployment | Planned | No model export, neural runtime, latency, or battery measurements yet |
| Automatic web learning | Planned | No crawler or background browsing; only explicitly supplied local HTML |

## Quick start

Requires Python 3.10 or later. Use a virtual environment and install the baseline:

```bash
python -m venv .venv
# Activate the environment for your shell, then:
python -m pip install -e '.[test]'
python -m pytest -q
```

The neural experiment requires `python -m pip install -e '.[neural,test]'` and a supported PyTorch installation. The normal baseline has no runtime dependencies beyond Python.

```bash
babyllm --db memory.sqlite3 learn "Hello world. Hello researcher."
babyllm --db memory.sqlite3 complete "Hello" --max-tokens 12
babyllm --db memory.sqlite3 ingest notes.md
babyllm --db memory.sqlite3 stats
```

`learn` and `ingest` modify only the selected local SQLite file. Files are read only when named on the command line. Re-ingesting identical file content adds no duplicate counts. Generation is greedy and deterministic; it is a baseline continuation, not reliable question answering.

## Architecture

```text
explicit text or local file
          │
          ▼
  Unicode tokenizer ──► SQLite n-gram counts ──► backoff continuation
          │
          └────────────► optional GRU-attention experiment
                                │
                                └── next-token logits (no deployment path yet)
```

The n-gram system stores counts for context lengths from zero through `order - 1`. At inference it uses the longest observed context and backs off to shorter contexts. The neural model uses a GRU and masked self-attention so a position cannot read later tokens. These components are currently separate baselines; there is no validated hybrid selection or fusion mechanism.

## Research protocol

To make performance claims, freeze a dataset and license, deduplicate documents **before** splitting, hold out entire documents or users, and report the tokenization and vocabulary rules. Compare at least a unigram baseline, the n-gram model, GRU without attention, and GRU with attention. Record three or more random seeds for neural runs and report mean and dispersion. Measure next-token loss or perplexity, top-1 accuracy, memory footprint, latency, energy, and adaptation after new data. Evaluate English and other languages separately, including code-mixed text. Never present training-set scores as held-out results.

The current `evaluate_next_token` helper reports top-1 accuracy and coverage. It does **not** create a split or prevent leakage; callers must supply genuinely held-out texts. No benchmark scores are claimed in this repository.

See the [research plan](docs/RESEARCH_PLAN.md) for the experiment matrix and release criteria. The first public benchmark uses [WikiText-2 raw](docs/DATASETS.md); the 200/100-row default run is a pipeline check, not a research result.

## Privacy and limitations

The SQLite file contains text-derived token counts and may reveal sensitive content. Keep it private, delete it when no longer needed, and do not ingest material without permission. Content-hash deduplication is not a privacy guarantee. The Android prototype has a clear-all control but lacks per-document unlearning, encryption, safety filtering, retrieval citations, and neural inference. Do not use its generated text for consequential decisions.

## Repository layout

```text
src/babyllm/       local baseline, ingestion, evaluation, neural experiment
tests/             functional and causal-attention tests
docs/              research protocol and implementation roadmap
notebooks/         small reproducible examples
android/           offline Android n-gram prototype and reference target
scripts/           pinned public-data benchmark
.github/workflows/ CI for the dependency-light baseline
```

## Roadmap

1. Define licensed multilingual corpora and leakage-resistant splits.
2. Add a reproducible neural training pipeline, checkpoints, tokenizer, and ablations.
3. Design consent, source provenance, and deletion for learned content.
4. Benchmark quantization and model export on named Android devices.
5. Build an Android client only after the on-device runtime and resource budgets are measured.

Contributions should include a test or reproducible experiment, a clear license for added data, and a measured claim where performance is discussed. This project is licensed under Apache-2.0; see [LICENSE](LICENSE).
