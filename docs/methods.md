# Methods and scope

The pipeline first parses PDB or mmCIF with Gemmi. Protein chain identity is determined by
standard recognized polymer residues with coordinates. The reference target profile pins source SHA-256,
chain sequence SHA-256, and chain lengths. Output validation requires precisely the same selected
target-chain identities plus one separately identified candidate binder chain. A source-file check
prevents silently reusing a mismatched profile.

Geometry screening excludes hydrogen isotopes and computes heavy-atom Euclidean distances in angstroms.
Every pair with distance <2.5 A is a **close-distance warning** and each pair <=5 A is a geometric
contact. This is not a formal nonbonded clash energy or physical bond assay. The mutation-position
parameter refers to the **1-based ordinal in the selected peptide chain**, not arbitrary author
residue numbering. This avoids the common Asp6 indexing trap.

RCSB 7OW6 is an x-ray structure of a T-cell receptor complex with HLA-A*11:01 and KRAS G12D peptide.
It is a public source structure, not evidence that a generated candidate binds. Its original TCR
chains must be removed in a controlled conditioning workflow and cannot be mistaken for a generated
binder chain.

The source validation of 7OW6 and a private H1 input must use different digests and profiles.
Profile creation is self-asserted, not a certificate that the reference itself is biologically correct.

The separate MolProbity demo involved a different 40-residue protein and cannot certify these candidates.
