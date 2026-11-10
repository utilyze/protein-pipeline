# Third-party license and attribution audit

This is a dependency and external-service inventory, not an authorization to redistribute provider outputs.

| Component | Usage | Upstream licensing evidence | Release action |
| --- | --- | --- | --- |
| Gemmi | Installed molecular-coordinate parser | MPL-2.0 **or** LGPL-3.0 at distributor's option | Depend on installed package, do not vendor source; maintain notices and verify selected distribution obligations |
| NumPy | Installed numerical library | BSD-3-Clause core; binary wheels may bundle separately licensed libraries | Depend on package, do not redistribute its wheels; record full installed-license notices if shipping bundled binaries |
| NVIDIA RFD4-Proteina | External model; opt-in HTTPS adapter only | Model reported BSD-3-Clause; separate NVIDIA API Trial Service Terms | Attribute third-party model and host; exclude model weights, tokens, private API responses and requests |
| RCSB PDB 7OW6 | Linked external reference only | wwPDB public structural data reuse policy, subject to data-use verification | Reference and cite; do not include unreviewed coordinates in repo |
| Anthropic x Adaptyv / Proteinbase | Historical competition context | Competition terms include publication, licensing and confidentiality provisions | No organizer endorsement, no unpublished competition artifacts |
| Python / setuptools / pytest | Runtime/build/test tooling | Independent upstream terms | No vendored binaries in the repository |

This repo contains no copied NVIDIA RFD4 model weights, no private modeled designs, and no bundled third-party structural-data binary.

Primary sources:
- https://github.com/project-gemmi/gemmi
- https://numpy.org/doc/stable/license.html
- https://build.nvidia.com/ipd/rfd4-proteina/modelcard
- https://proteinbase.com/competitions/anthropic-adaptyv-2026/terms
- https://www.wwpdb.org/about/wwpdb-policies

Recheck source terms against the exact release date and document contributor rights before public distribution.
