# Utilyze Protein Pipeline

**PRIVATE RELEASE CANDIDATE. NOT YET LICENSED OR APPROVED FOR PUBLIC DISTRIBUTION.**

CPU-first, source-aware structural identity and geometric screening for computational protein research.
Extracted and adapted from the private Utilyze research-platform prototype into a separate package.

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
conditioning target, not the raw reference with TCR D/E. The public and private H1 source profiles
must never be interchanged.

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
protein-pipeline replay /PRIVATE/YOUR_OWN_KRAS_RFD4_EVIDENCE.zip
```

Only works with the matching **privately held** original evidence archive layout. The archive is not shipped.
It was previously replayed against seven provider responses with 24 outputs, 22 target-preserving outputs,
20 shortlisted structures and specific distance checks. This private historical result is not publicly
reproducible without the original inputs.

## Critical scientific boundaries

- A SHA-256 digest verifies byte integrity, not remote provider provenance.
- Pair distances are simple geometry, not an official MolProbity clashscore.
- NVIDIA RFD4-Proteina is the third-party generator. Utilyze does not claim authorship of its model.
- Historical challenge results are computational and were not experimentally validated.

See `docs/methods.md`, `docs/reproducibility.md`, and `docs/third_party_notices.md`.

## License

**Proposed license: Apache-2.0.** Outbound licensing is not active until Utilyze's ownership and patent-grant authorization is confirmed and the standard `LICENSE` file is committed. Until then this private release candidate is not open source.
