# Release gate

Mandatory checks before public visibility:

1. Verify all selected source files and code ownership; resolve contributor rights.
2. Select a code license and verify dependencies, NVIDIA service terms, RCSB attribution.
3. Run a clean Python 3.11 and 3.12 CI install, offline tests and public-source inspection.
4. Run threat modeling, static code checks, dependency audit and entire-history secret scan.
5. Confirm source-specific public 7OW6 and private H1 profiles cannot be cross-applied.
6. Ensure documentation says user-supplied private archives are required for historical replay.
7. Review figure/blog wording; no unvalidated binding/novelty assertions.
8. Create new PRIVATE `utilyze/protein-pipeline` with a fresh Git history, no source-repository remote.
9. Inspect the exact future public commit and CI checks, then switch visibility.
10. Verify unauthenticated clone and read-only public accessibility.

The standalone repository already exists privately and the current `main` CI passed on Python 3.11 and 3.12. A private release-candidate branch is being prepared. Public visibility, merge, licensing, and external publication remain blocked until the founder authorizes the exact reviewed tree and all mandatory rights gates pass.
