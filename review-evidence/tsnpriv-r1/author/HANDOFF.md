# Privacy gate: accept the GitHub squash identity (tsn-c-stack PR #17)

- Problem: `main` at `18d73783` fails `scripts/check_privacy.py` ("unexpected identity"). The gate exempts only the exact squash `ae982af`. Later GitHub squash merges carry the account's noreply author with GitHub as committer.
- Change (commit `61fb7c9`): `identity_ok()` accepts the holder identity pair or the GitHub web-flow pair. The one-line message rule applies to both. The `ae982af` exception and the content scan are unchanged. `--selftest` holds six identity controls. `validate.py` gains a `privacy-selftest` gate. IMPORT.md and VERIFICATION.md describe the rule.
- Validation: `validate.py --jobs 16` with GoogleTest 1.14.0 (scratch prefix via PKG_CONFIG_PATH and CMAKE_PREFIX_PATH) and Clang 18.1.3 on PATH; 24 of 24 gates rc 0 (`receipts/validate-gates.json`, `receipts/validate.log`).
