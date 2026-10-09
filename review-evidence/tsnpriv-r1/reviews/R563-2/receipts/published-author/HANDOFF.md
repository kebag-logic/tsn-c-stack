# Privacy gate: accept the GitHub squash identity (tsn-c-stack PR #17)

- Problem: `main` at `18d73783` fails `scripts/check_privacy.py` ("unexpected identity"). The gate exempts only the exact squash `ae982af`. Later GitHub squash merges carry the account's noreply author with GitHub as committer.
- Change (commit `61fb7c9`): `identity_ok()` accepts the holder identity pair or the GitHub web-flow pair. The one-line message rule applies to both. The `ae982af` exception and the content scan are unchanged. `--selftest` holds six identity controls. `validate.py` gains a `privacy-selftest` gate. IMPORT.md and VERIFICATION.md describe the rule.
- Validation: `validate.py --jobs 16` with GoogleTest 1.14.0 (scratch prefix via PKG_CONFIG_PATH and CMAKE_PREFIX_PATH) and Clang 18.1.3 on PATH; 24 of 24 gates rc 0 (`receipts/validate-gates.json`, `receipts/validate.log`).

## Round 2 (head `b7c6b7b`)

- `738b131`: docs/IMPORT.md paragraph states both accepted identity pairs and keeps "It still scans that commit's content" next to the `ae982af` exception (R563-1-F1, R562-1-F2).
- `b7c6b7b`: `commit_errors()` holds the per-commit check (identity plus one-line message, with the exact `ae982af` exception). `--selftest` drives it with 11 controls: holder, web-flow and owner squash pass; mixed, holder-with-GitHub-committer, other noreply account, reversed pair, case variant, and multi-line messages on both pairs fail. Unknown arguments are refused (R562-1-F1, S1). VERIFICATION.md row and CHANGELOG updated (S4).
- R562-1's `mutant_probes.py`, run unchanged on a disposable copy: all 9 planted faults give `--selftest` rc 1; the control gives rc 0.
- `validate.py`: 24 of 24 gates rc 0 with GoogleTest 1.14.0 and Clang 18.1.3 (`receipts/validate-gates-r2.json`).
- Repository settings (manager, R562-1-S3): squash merge only, PR-title subject and blank body; merge commits and rebase merges disabled.
- Not done: R562-1-S2 (raw commit-object scan) goes to the residue checklist.
