# Third-party license and attribution audit

This is a dependency and external-service inventory, not an authorization to redistribute provider outputs.

| Component | Usage | Upstream licensing evidence | Release action |
| --- | --- | --- | --- |
| Gemmi | Installed molecular-coordinate parser | MPL-2.0 **or** LGPL-3.0 at distributor's option | Depend on installed package, do not vendor source; maintain notices and verify selected distribution obligations |
| NumPy | Installed numerical library | BSD-3-Clause core; binary wheels may bundle separately licensed libraries | Depend on package, do not redistribute its wheels; record full installed-license notices if shipping bundled binaries |
| NVIDIA RFD4-Proteina | External model; opt-in HTTPS adapter only | The Institute for Protein Design model is described as BSD-3-Clause on the model API page; NVIDIA NIM/container and hosted trial are governed by separate terms | Credit the model authors and host; do not redistribute model weights, containers, tokens, private API inputs or response archives; confirm independent API entitlement |
| RCSB PDB 7OW6 | Linked external reference only | wwPDB public structural data reuse policy, subject to data-use verification | Reference and cite; do not include unreviewed coordinates in repo |
| Python / setuptools / pytest | Runtime/build/test tooling | Independent upstream terms | No vendored binaries in the repository |

This repo contains no copied NVIDIA RFD4 model weights, no private modeled designs, and no bundled third-party structural-data binary.

Primary sources:
- https://github.com/project-gemmi/gemmi
- https://numpy.org/doc/stable/license.html
- https://build.nvidia.com/ipd/rfd4-proteina/modelcard
- https://www.wwpdb.org/about/wwpdb-policies

License audit date: November 10, 2026. Model, hosted trial service and container licensing are different and may change. Recheck applicable terms against the actual distribution and use case. Contributor and distribution rights are documented privately by Utilyze; no confidential rights records are published.
