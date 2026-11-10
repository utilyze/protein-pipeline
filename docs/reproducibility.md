# Reproducibility certificate scope

A clean environment can install the `utilyze-protein-pipeline` package, run the offline tests, and execute a synthetic in-memory molecular validation. The optional model API is never needed for this path.

```bash
python -m pip install -e . pytest
python -m pytest -q
python -m protein_pipeline --help
python examples/synthetic/run_demo.py
```

A user may inspect an independently downloaded RCSB 7OW6 reference:

```bash
protein-pipeline inspect /path/to/7OW6.cif
```

The 7OW6 reference is a pMHC complex that includes original TCR chains, **not** a generated binder. To validate a generated design, use its exact conditioned source and a source-specific fingerprint profile. User-generated profiles are self-asserted and a local SHA-256 is not an independent provider attestation.

Private model-design campaign results, provider response archives and confidential screening evidence are
excluded from the public package. The public checkout independently reproduces only the offline tests,
synthetic workflow and public-source structural inspection; it cannot reproduce private campaign results.

No experimental binding, specificity, stability, or therapeutic performance has been established by the code or the historical geometry screen. A pairwise distance threshold is not an official MolProbity clashscore.

The optional NVIDIA request path requires independent account access, rights and entitlement confirmations. It is deliberately not a clean-install demonstration and cannot promise identical sampled outputs.
