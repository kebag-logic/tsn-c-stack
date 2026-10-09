[A571]

Closes #14.

Port the applicable [source requirements](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/docs/reference/FR_NFR.md) into the portable library contract. Add 25 requirements with origins, linked clauses and verification methods. Account for all 114 numbered source rows and both Mark II decisions. State every exclusion and each change to the proposed mapping.

Separate tested protocol behavior from port duties for identity, authentication configuration, persistence, reservation, service timing and recovery accounting. Each requirement addresses Linux and bare-metal RV32. The 10 ms service bound and wire timing require integration measurements.

Add an independent ADP advertisement vector with eleven field defects. Extend traceability checks for source inventory, exact pinned anchors, both targets and justified verification methods. Regenerate the requirements, traceability and test-defect tables.

## Round 2

Tag the enforcing startup draw test with MFDISC-01. Add separate departure and timeout tests tagged MFCONN-03 and MFRECOVERY-01. Each checks binding retention and a fresh probe after rediscovery. Two new plants must fail both tests. The three review probes now fail tests carrying the affected requirement tags.

Record NFR-SEC-01 as an entity configuration port obligation. Reject moved source anchors with a planted control. Add the Unreleased change-log entry.

Validate with:

```sh
python3 scripts/validate.py --work build-validation --jobs 16 --graphs
python3 scripts/baremetal.py --work build-rv32 --jobs 16
```

All 25 `validate.py --graphs` gates pass. Both compiler builds, all seven test binaries, sanitizers and static analysis pass. Coverage is 100% after unchanged exclusions. All 324 mutation plants are caught. All three graphs render. RV32 Debug and Release link and smoke checks pass.

Validation uses GoogleTest 1.14.0 and Clang 18. The branch includes the main privacy fix from [PR #17](https://github.com/kebag-logic/tsn-c-stack/pull/17). Production behavior is unchanged.
