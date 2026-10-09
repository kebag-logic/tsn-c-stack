# Prior public finding dispositions at b7c6b7ba0007aaa5791df68d30296423127b003e

The independent source verdict and five-lens ledger were written before reading
the prior public reports. The inventory contains two round-one findings comments,
zero submitted reviews and zero inline comments. The public issue and PR comments
contain no separate manager source-bank execution receipt.

| ID | Prior severity | All attributable lenses | Disposition | Current artifact and verification |
|---|---|---|---|---|
| R563-1-F1 | MINOR | Conformance, Docs | RESOLVED | IMPORT.md:133-138 requires one of both complete pairs and a one-line subject for every new commit. The content-scan sentence follows the exact exception. Real CLI and both accepted-pair controls pass. |
| R562-1-F1 | MINOR | Tests, Robustness | RESOLVED | check_privacy.py:28-58 and :71 share the full per-commit check. All requested rejection cases are shipped controls. Nine unchanged public substitutions give selftest rc 1; the control gives rc 0. Both hosted quality runs record 25 passing gates. |
| R562-1-F2 | MINOR | Docs, Conformance | RESOLVED | IMPORT.md:133-138 removes the holder-only instruction and restores the owner exception as the content-scan sentence's antecedent. VERIFICATION.md:40 describes the eleven-control rule accurately. |
| R562-1-S1 | SUGGESTION | Robustness | RESOLVED / adopted | check_privacy.py:93-95 refuses unknown and combined arguments. Five actual CLI rejection/acceptance cases supplement the normal scan. |
| R562-1-S2 | SUGGESTION | Robustness | RETAINED / deferred | check_privacy.py:69 still scans formatted author/committer/message data, not every raw commit header. Assignment defers raw commit-object scanning to the manager's residue checklist. No raw-object repair is claimed. |
| R562-1-S3 | SUGGESTION | Conformance (merge process), Robustness | RESOLVED / adopted | Repository API reports squash only, PR_TITLE subject, BLANK body, merge commits and rebase merges disabled. |
| R562-1-S4 | SUGGESTION | Docs | RESOLVED / adopted | CHANGELOG.md:5 records the hosted pair and preserved one-line rule. |

For the three resolved MINOR findings, the original impact was respectively a
contradictory privacy instruction, insufficient regression sensitivity, and the
same contradictory instruction with an ambiguous scanning antecedent. The required
outcomes are now present, with the code, prose and executable receipts above.
No prior finding is worsened.

The published mutation script is retained unchanged. The replay harness uses its
exact substitutions against this head and the actual selftest detector; it omits
the original old-head checkout and synthetic commits to honor this round's scope.
Normal and optimized Python produce identical expected return codes.

Prior authorities:

- [External round-one finding](https://github.com/kebag-logic/tsn-c-stack/pull/17#issuecomment-6081371868).
- [Internal round-one findings and suggestions](https://github.com/kebag-logic/tsn-c-stack/pull/17#issuecomment-6081398114).
- [Published round-one packet and round-two author receipts](https://github.com/kebag-logic/tsn-c-stack/tree/5f9b951b14fa8c22b03ea9b5cde49ed57033279b/review-evidence/tsnpriv-r1).
