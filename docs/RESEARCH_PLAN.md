# Research and release plan

## Questions

1. Does n-gram backoff improve immediate adaptation at a fixed memory budget?
2. Does causal attention improve a compact GRU over a parameter-matched GRU?
3. Can a hybrid improve quality without exceeding Android latency and energy targets?
4. How much quality is lost under quantization and on-device constraints?

## Experimental design

| Axis | Required comparisons |
| --- | --- |
| Models | unigram, 2/3/5-gram, GRU, GRU-attention, proposed hybrid |
| Adaptation | no update, 10/100/1000 user-approved examples |
| Languages | each language separately plus code-mixed sets |
| Splits | document-level and user-level holdout; report both |
| Seeds | at least three neural seeds with confidence intervals or dispersion |
| Resources | model and database bytes, peak RAM, cold and warm latency, energy |

Publish dataset provenance, preprocessing code, split identifiers, hyperparameters, exact checkpoints, hardware, and commands. Do not log private user content. A reported win must include the same evaluation set and resource budget for all baselines.

## Gates before an Android release

- A working Android project with repeatable build instructions and a tested device/OS matrix.
- A measured on-device inference path, including cold start, RAM, storage, latency, and battery impact.
- Explicit consent for every ingestion source, local storage protection, and a verified delete/unlearn flow.
- Multilingual evaluation and failure analysis with data and model cards.
- Safety review for fabricated answers, private-data leakage, and adversarial documents.

These gates are open. The Python prototype is an experiment platform, not a release candidate.
