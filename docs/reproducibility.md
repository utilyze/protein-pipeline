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

The original private KRAS campaign involved 7 provider-response archives containing 24 outputs. A private evidence replay found 22 distinct target-preserving designs, two target-altered outputs, and a verified set of 20 shortlisted structures. **Those original model responses and candidates are not bundled here.** Therefore the public checkout alone cannot reproduce the historical campaign, its shortlisted coordinates, Proteinbase submission status, or its novelty-screening scores.

No experimental binding, specificity, stability, or therapeutic performance has been established by the code or the historical geometry screen. A pairwise distance threshold is not an official MolProbity clashscore.

The optional NVIDIA request path requires independent account access, rights and entitlement confirmations. It is deliberately not a clean-install demonstration and cannot promise identical sampled outputs.
