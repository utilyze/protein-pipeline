# Architecture and lineage

- `molecules.py`: read-only Gemmi parser and authoritative atom/sequence normalization.
- `targets.py`: explicit source profile and strict output reference checking.
- `geometry.py`: chunked heavy-atom screening and mutation positional analysis.
- `provenance.py`: offline third-party response-envelope consistency checks; never model-origin attestation.
- `transport.py`: optional fixed-host one-request adapter requiring three explicit operator confirmations.
- `replay.py`: source-derived historical replay, requires operator-supplied original evidence ZIP.
- `cli.py`: ordinary read-only commands; never calls a remote model.

Lineage: reimplementation and extraction informed by `protein_studio/core.py`,
`rfd4_direct_api.py`, `rfd4_preflight.py`, `kras_grinder.py`, `public_kras_7ow6.py`
at `utilyze/research-platform` PR #183 and PR #182, and the user's prior local private replay utility.
This is not a branch or copy of the private repository's Git history.
