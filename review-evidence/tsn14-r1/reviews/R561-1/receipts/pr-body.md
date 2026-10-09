[A571]

Relates to #14.

Port the applicable [source requirements](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/docs/reference/FR_NFR.md) into the portable library contract. Add 24 requirements with origins, linked clauses and verification methods. Account for all 114 numbered source rows and the two Mark II decisions. State each exclusion and each change to the proposed mapping.

Separate tested protocol behavior from port duties for identity, persistence, reservation, service timing and recovery accounting. Both Linux and bare-metal RV32 remain required. The 10 ms service bound and wire timing require measurements by each integration.

Add an independent ADP advertisement vector and eleven field defects. Extend the traceability gate to check the pinned source inventory, both targets, citations and justified inspection or port obligations. Regenerate the requirements, traceability and test-defect tables.

Validate with:

```sh
python3 scripts/validate.py --work build-validation --jobs 16 --graphs
python3 scripts/baremetal.py --work build-rv32 --jobs 16
```

Validation: both hosted compiler builds and all seven test binaries pass. Sanitizers and static analysis pass. Coverage is 100% after unchanged exclusions. All 322 mutation plants and the report controls pass. All three graphs render. RV32 Debug and Release link and smoke checks pass.

The branch merges `main` at `74445d28`, which includes the privacy gate fix ([PR 17](https://github.com/kebag-logic/tsn-c-stack/pull/17)). With GoogleTest 1.14.0 and Clang 18, all 24 `validate.py` gates pass at the head.

