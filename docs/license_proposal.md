# License proposal (not yet approved)

**Decision pending. No active LICENSE is granted by this document.**

Recommendation for founder/legal review: **Apache License 2.0** for company-owned original source code, after source-file rights are confirmed. Apache-2.0 permits redistribution and commercial use, requires preservation of license and notices, and includes an express contributor patent grant with specified termination. Compared with the shorter MIT license, it supplies a more explicit patent framework and notice mechanism, at the cost of additional obligations. Neither license provides a warranty or grants rights to third-party private data, unpublished model outputs, or trademarks.

Official text: https://www.apache.org/licenses/LICENSE-2.0.txt

Decision before activation:

- Verify authorship and assignment for every reusable upstream-derived component, including `targets.py`, `replay.py`, and `transport.py`.
- Verify execution of any relevant separate contractor IP assignment; an unsigned draft is insufficient evidence.
- Confirm there are no prohibited third-party code excerpts or licenses.
- Decide whether Utilyze intends to grant the Apache-2.0 contributor patent license.
- Obtain founder authorization for applying the license to the exact release tree.

If approved: add the **unmodified** full Apache-2.0 text as `LICENSE`, set `license = "Apache-2.0"` in project metadata, and add any required copyright/NOTICE entries. Until then, this repository remains private and unlicensed for public redistribution.

References: https://www.apache.org/licenses/LICENSE-2.0.html ; https://opensource.org/license/mit
