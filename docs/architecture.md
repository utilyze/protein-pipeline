# Architecture and lineage

- `molecules.py`: read-only Gemmi parser and authoritative atom/sequence normalization.
- `targets.py`: explicit source profile and strict output reference checking.
- `geometry.py`: chunked heavy-atom screening and mutation positional analysis.
- `provenance.py`: offline third-party response-envelope consistency checks; never model-origin attestation.
- `transport.py`: optional fixed-host one-request adapter requiring three explicit operator confirmations.
- `replay.py`: source-derived historical replay, requires operator-supplied original evidence ZIP.
- `cli.py`: ordinary read-only commands; never calls a remote model.

Lineage: standalone Utilyze-owned implementation maintained as its own Git repository.
No private parent-repository commit history, provider data or unpublished protein designs are included.
