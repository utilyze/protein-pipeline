# Acceptance 05 release-candidate status

**PRIVATE DRAFT. DO NOT MERGE OR MAKE PUBLIC WITHOUT APPROVAL.**

Release target: v0.1.0, after rights clearance and final testing.

Focused engineering changes:
- Reject self-certified `source_hash_verified` profile metadata. A self-authored JSON profile cannot attest original source authenticity.
- Require complete N/CA/C/O atom records for each selected modeled target and binder residue before reporting target-chain integrity passed.
- Reject duplicate archive names, symlink/device entries, and encrypted ZIP entries in deterministic historical replay.
- Add negative tests covering these cases.

Scientific limitations remain: fingerprints certify source-chain sequences, not exact target-coordinate conservation or energy-minimized structures; geometric distance cutoffs are heuristics; no experimentally verified binder is claimed.

Rights gating remains open: founder must verify code ownership and separate contractor IP assignments, select an outbound license, and approve a complete disclosure manifest. The current draft contains a license recommendation, not an active open-source grant.

No private H1 source, binder sequences, provider JSON, private evidence archives, or raw 7OW6 coordinates are part of this repository.
