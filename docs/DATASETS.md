# Dataset policy and first benchmark

The initial public benchmark is [Salesforce WikiText-2 raw](https://huggingface.co/datasets/Salesforce/wikitext), configuration `wikitext-2-raw-v1`, pinned to revision `00aa25585682d4957f9e86edc73f59be7419af99`. The dataset card lists CC BY-SA 3.0 and GFDL. This repository does not redistribute the corpus. Review the dataset's terms before using or redistributing it.

The benchmark reads only the official `train` and `validation` files. It never trains on validation. The default 200/100-row run is a pipeline smoke benchmark, not a competitive language-model result. Increase the limits and document the hardware and run time for a full experiment.

```bash
python -m pip install -e '.[benchmark]'
python scripts/benchmark_wikitext.py --train-limit 200 --validation-limit 100
```

The output includes the exact dataset revision and SHA-256 hashes of downloaded files, row counts, model order, timing, observed token count, held-out next-token coverage, and held-out top-1 accuracy. Local downloaded data is ignored by Git.

One local smoke run using the default 200 training rows and 100 validation rows produced 9,576 validation tokens and 15.17% top-1 accuracy. This is a single, small-subset result from the Python n-gram baseline; it says nothing about Android speed or energy and is not a comparable published benchmark. The downloaded train and validation SHA-256 values were `49280f3dd993cbdfd322186194133d5d1935f81e1c91064c239f2a70ebb02701` and `a10eb5a42c4264c45dd38bfef4da6a74ddef5fc22cb419e1a89d54c4cc6d748f`.

WikiText-2 is English only. It does not validate the project's multilingual vision. A future multilingual dataset must have documented language coverage, licensing, source provenance, and train/test separation before any cross-language claim is made.
