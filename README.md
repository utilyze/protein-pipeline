# Utilyze Protein Pipeline

**Open-source scientific toolkit. Licensed under Apache-2.0.**

CPU-first, source-aware structural identity and geometric screening for computational protein research.
Standalone software for auditable molecular validation, not a distribution of any private research portfolio.

**Not a protein generator by default.** It can validate target identities, verify local model-response envelopes,
calculate simple heavy-atom distances, and replay privately supplied evidence archives. It does not demonstrate
binding affinity, fold stability, mutant specificity, experimentally confirmed binders, or an independently
attested NVIDIA response. The optional fixed-host NVIDIA adapter is explicitly gated and never called by tests.

## Install and verify

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e . pytest
python -m pytest -q
protein-pipeline --help
```

## Public-reference inspection, no API token

Download the RCSB 7OW6 coordinate file yourself, subject to the upstream data terms:

- https://www.rcsb.org/structure/7OW6
- https://files.rcsb.org/download/7OW6.cif

Then run:

```bash
protein-pipeline inspect /path/to/7OW6.cif
```

The output lists chain lengths and sequence fingerprints, not private candidate sequences.
The 7OW6 reference contains original TCR chains D/E and is **not a generated binder structure**.
To evaluate generated outputs, use a separately authorized modeled complex and a profile from its exact
conditioning target, not the raw reference with TCR D/E. Source profiles from different conditioning structures must never be interchanged.

## One-command synthetic example (offline)

```bash
python examples/synthetic/run_demo.py
```

The demo prints a source identity decision and heavy-atom distance counts. It uses
artificial coordinates and does not reproduce or predict a biological binder.

## Testable synthetic workflow

The unit tests build artificial mmCIF fixtures in memory to test molecular identity, source hashing,
mutation-atom categorization and distance thresholds. Fixtures are not measured structures, provider designs,
or new scientific findings. See `tests/` and `examples/synthetic/`.

## Historical evidence replay

```bash
protein-pipeline replay /path/to/authorized_evidence.zip
```

Only works with a matching **operator-supplied and legally authorized** evidence archive.
Original provider responses, candidate coordinates and confidential campaign results are not shipped;
the synthetic tests and public reference inspection demonstrate only the reproducible public functionality.

## Critical scientific boundaries

- A SHA-256 digest verifies byte integrity, not remote provider provenance.
- Pair distances are simple geometry, not an official MolProbity clashscore.
- NVIDIA RFD4-Proteina is the third-party generator. Utilyze does not claim authorship of its model.
- Historical challenge results are computational and were not experimentally validated.

See `docs/methods.md`, `docs/reproducibility.md`, and `docs/third_party_notices.md`.

## License

Copyright 2026 Utilyze, Inc. The standalone Utilyze-owned software is licensed under the
[Apache License 2.0](LICENSE), including the limited patent grant specified in Section 3.
This license does not grant rights to NVIDIA services, provider outputs, proprietary model weights,
third-party trademarks, confidential research assets, or unrelated Utilyze repositories.
See [third-party notices](docs/third_party_notices.md) for dependency and external-source attribution.
