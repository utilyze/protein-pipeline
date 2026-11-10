# Synthetic fixture

Use `python -m protein_pipeline.fixtures` only through local tests or write a fixture with
`make_synthetic_cif()`. The structure is deliberately artificial and does not reflect a
real protein or a generated NVIDIA binder. Tests verify that source profiles, chain identity,
mutation-position atom categories, and deterministic distances behave consistently.
