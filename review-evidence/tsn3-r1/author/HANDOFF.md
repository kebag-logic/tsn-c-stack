# ADP malformed discovery handoff

Status: REVIEW READY. Acceptance items 1–3 are met.
Branch: `adp-malformed-discard`.
Confirmed base and `origin/main`: [1a9f651c](https://github.com/kebag-logic/tsn-c-stack/commit/1a9f651cdf7846b8e10ac246a6ef6916960fbb92).
The local `main` reference is older. It was not changed.

Scope follows the [assignment](https://github.com/kebag-logic/tsn-c-stack/issues/3#issuecomment-6085285119) and [acceptance items 1–3](https://github.com/kebag-logic/tsn-c-stack/issues/3).
The consumer update remains a later lane.
The [start marker](https://github.com/kebag-logic/tsn-c-stack/issues/3#issuecomment-6085300053) is posted.

## Refused inputs

| Refused input | Clause |
|---|---|
| AVTP versions 1 through 7 | [IEEE 1722.1-2021 6.2.2.3](https://standards.ieee.org/ieee/1722.1/6670/); [IEEE 1722-2016 4.4.3.4](https://standards.ieee.org/ieee/1722/5979/) |
| Fewer than 82 bytes including the untagged Ethernet header | [IEEE 1722.1-2021 Figure 6-1 and 6.2.2.6](https://standards.ieee.org/ieee/1722.1/6670/) |
| Any 11-bit control_data_length other than 56 | [IEEE 1722.1-2021 6.2.2.6](https://standards.ieee.org/ieee/1722.1/6670/); [IEEE 1722-2016 4.4.5.4](https://standards.ieee.org/ieee/1722/5979/) |

The receiver checks length before reading fields. Each refusal increments discarded once.
All other core bytes stay unchanged. Strict callback expectations check that no port is called.
Valid global and own-entity discovery follow [Milan v1.2 5.6.3.1 and Table 5.51](https://avnu.org/resource/milan-specification/).
The PDFs were checked locally. No standards text is reproduced.

## Tests and planted defects

| Test | Defect caught |
|---|---|
| [RejectsUnsupportedVersion](https://github.com/kebag-logic/tsn-c-stack/blob/66b3a75746fbbca3cffdfc7d89f013ab14aa1cc0/tests/test_adp.cpp#L736) | Removing the version guard accepts versions 1 through 7. |
| [RejectsShortFrame](https://github.com/kebag-logic/tsn-c-stack/blob/66b3a75746fbbca3cffdfc7d89f013ab14aa1cc0/tests/test_adp.cpp#L753) | Restoring the 26-byte prefix guard accepts truncated ADPDUs. Exact-sized buffers also expose premature reads under sanitizers. |
| [RejectsWrongControlDataLength](https://github.com/kebag-logic/tsn-c-stack/blob/66b3a75746fbbca3cffdfc7d89f013ab14aa1cc0/tests/test_adp.cpp#L770) | Removing the control length guard accepts zero and every other incorrect 11-bit value. |
| [ValidDiscovery](https://github.com/kebag-logic/tsn-c-stack/blob/66b3a75746fbbca3cffdfc7d89f013ab14aa1cc0/tests/test_adp.cpp#L788) | Rejecting the local entity target prevents the expected WAITING-to-DELAY transition. Global and local targets, exact length and trailing bytes remain accepted. |

All four declarations carry requirement tags. They run in disabled, DOWN, DELAY, blocked-output DELAY and WAITING conditions.
The [hosted tests](https://github.com/kebag-logic/tsn-c-stack/blob/66b3a75746fbbca3cffdfc7d89f013ab14aa1cc0/tests/test_adp.cpp) also check both target forms.
The [RV32 smoke test](https://github.com/kebag-logic/tsn-c-stack/blob/66b3a75746fbbca3cffdfc7d89f013ab14aa1cc0/examples/rv32/smoke.c) checks the three reported malformed controls and the valid control in those five conditions.
The fresh campaign caught all 327 plants through 356 required killer entries.
Each added defect was caught in all five receive conditions.
The [mutation summary](MUTATION-SUMMARY.json) records the names and failed tests.
The complete failed-assertion reports remain in [scratch]($VALIDATION_STORAGE/tsn3-a579/validation/mutations/).
Documentation and generated inventories are updated.
Initial hosted tests and RV32 Debug/Release passed.
Coverage remains 100% after the unchanged exclusions. The ADP ratchet increased from 203 to 205 lines and from 93 to 97 branches.
The first full attempt refused three clause comments with unsupported punctuation. Those references are now split into permitted short comments.
That attempt is retained in scratch.
The second attempt passed runtime, coverage, all 327 mutations, mutation controls and graph rendering.
Static analysis refused the moved location of an existing RV32 callback false positive. Its suppression and linked explanation now point to line 136 instead of 137. No exception was added or widened.
The pinned directory supplied the versioned lexer but no unversioned compiler driver. The second attempt therefore used the ambient compiler for its sanitizer build.
Scratch-only driver shims now select the pinned compiler. Compatible C++ headers, matching sanitizer runtimes and the matching analyzer are also in scratch.
The pinned sanitizer build and corrected analysis both passed their focused reruns.
The final complete run passed with that corrected setup. Shared installations are unchanged.

## Reproduction and evidence

Use the [scratch environment]($VALIDATION_STORAGE/tsn3-a579/env.sh) before running the commands in the [verification guide](https://github.com/kebag-logic/tsn-c-stack/blob/66b3a75746fbbca3cffdfc7d89f013ab14aa1cc0/docs/VERIFICATION.md).
The [driver shims]($VALIDATION_STORAGE/tsn3-a579/bin/) select the pinned compiler and analyzer.
The C++ shim uses compatible standard-library headers. It retains the existing runtime library.
The matching sanitizer runtime is selected through the compiler resource directory.
The [version record](VERSIONS.json) and [package manifest](PACKAGES.json) contain versions, sizes and hashes.
The [evidence manifest](EVIDENCE.json) records the head, changed file hashes and complete log locations.
The full mutation report exceeds the packet size limit. Its size and hash are recorded instead.
Peak service memory was 5,206,818,816 bytes, below the 9 GB limit.
Build trees, binaries, extracted packages and full campaign reports stay in [scratch]($VALIDATION_STORAGE/tsn3-a579/).

```sh
python3 scripts/validate.py --work build-validation --jobs 16 --graphs
python3 scripts/baremetal.py --work build-rv32 --jobs 16
```

## Gates

The [hosted gate receipt](HOSTED-GATES.json) contains all 25 zero return codes.
The [RV32 receipt](RV32-GATES.json) contains Debug and Release results, ELF sizes and hashes, import audits and no unresolved final symbols.
Hosted campaigns run on the shared core source. RV32 executes the minimal port smoke suite.
No RV32 sanitizer or coverage denominator is claimed. This follows the [target split](https://github.com/kebag-logic/tsn-c-stack/blob/66b3a75746fbbca3cffdfc7d89f013ab14aa1cc0/docs/VERIFICATION.md#bare-metal-rv32).

| Gate | Linux | RV32 |
|---|---|---|
| [boundary]($VALIDATION_STORAGE/tsn3-a579/validation/boundary.log) | rc 0 | Dependency and import audit also passed in both target builds |
| [needles]($VALIDATION_STORAGE/tsn3-a579/validation/needles.log) | rc 0 | Shared source policy passed |
| [assertion-templates]($VALIDATION_STORAGE/tsn3-a579/validation/assertion-templates.log) | rc 0 | Shared source policy passed |
| [dependencies]($VALIDATION_STORAGE/tsn3-a579/validation/dependencies.log) | rc 0 | Shared source policy passed |
| [comments]($VALIDATION_STORAGE/tsn3-a579/validation/comments.log) | rc 0 | Shared source policy passed |
| [conditionals]($VALIDATION_STORAGE/tsn3-a579/validation/conditionals.log) | rc 0 | Freestanding file combinations included |
| [port-contracts]($VALIDATION_STORAGE/tsn3-a579/validation/port-contracts.log) | rc 0 | Shared source policy passed |
| [registration-controls]($VALIDATION_STORAGE/tsn3-a579/validation/registration-controls.log) | rc 0 | Shared source policy passed |
| [license]($VALIDATION_STORAGE/tsn3-a579/validation/license.log) | rc 0 | Shared source policy passed |
| [traceability]($VALIDATION_STORAGE/tsn3-a579/validation/traceability.log) | rc 0 | Shared source policy passed |
| [test-inventory]($VALIDATION_STORAGE/tsn3-a579/validation/test-inventory.log) | rc 0 | Shared source policy passed |
| [coverage-controls]($VALIDATION_STORAGE/tsn3-a579/validation/coverage-controls.log) | rc 0 | Shared source policy passed |
| [privacy-selftest]($VALIDATION_STORAGE/tsn3-a579/validation/privacy-selftest.log) | rc 0 | Shared source policy passed |
| [privacy]($VALIDATION_STORAGE/tsn3-a579/validation/privacy.log) | rc 0 | Shared source policy passed |
| [gcc-configure]($VALIDATION_STORAGE/tsn3-a579/validation/gcc-configure.log) | rc 0 | Hosted campaign on shared source |
| [gcc-build]($VALIDATION_STORAGE/tsn3-a579/validation/gcc-build.log) | rc 0 | Hosted campaign on shared source |
| [gcc-test]($VALIDATION_STORAGE/tsn3-a579/validation/gcc-test.log) | rc 0 | Hosted campaign on shared source |
| [coverage]($VALIDATION_STORAGE/tsn3-a579/validation/coverage.log) | rc 0 | Hosted campaign on shared source |
| [clang-sanitizers-configure]($VALIDATION_STORAGE/tsn3-a579/validation/clang-sanitizers-configure.log) | rc 0 | Hosted campaign on shared source |
| [clang-sanitizers-build]($VALIDATION_STORAGE/tsn3-a579/validation/clang-sanitizers-build.log) | rc 0 | Hosted campaign on shared source |
| [clang-sanitizers-test]($VALIDATION_STORAGE/tsn3-a579/validation/clang-sanitizers-test.log) | rc 0 | Hosted campaign on shared source |
| [mutation]($VALIDATION_STORAGE/tsn3-a579/validation/mutation.log) | rc 0 | Hosted campaign on shared source |
| [static-analysis]($VALIDATION_STORAGE/tsn3-a579/validation/static-analysis.log) | rc 0 | Hosted campaign on shared source |
| [mutation-controls]($VALIDATION_STORAGE/tsn3-a579/validation/mutation-controls.log) | rc 0 | Hosted campaign on shared source |
| [graphs]($VALIDATION_STORAGE/tsn3-a579/validation/graphs.log) | rc 0 | Shared source policy passed |
| [Freestanding Debug]($VALIDATION_STORAGE/tsn3-a579/rv32/debug/smoke.log) | Not applicable | rc 0 |
| [Freestanding Release]($VALIDATION_STORAGE/tsn3-a579/rv32/release/smoke.log) | Not applicable | rc 0 |
| [Post-commit privacy]($VALIDATION_STORAGE/tsn3-a579/postcommit-privacy.log) | rc 0 | Shared history and source policy passed |

Each hosted compiler ran 388 instances across seven binaries.
Adjusted coverage is 1,166/1,166 lines and 587/587 branches. The existing exclusions are unchanged.
All three Mermaid diagrams rendered. No graph source changed.
The final commands, including both target runners, returned zero without shell pipelines.

## Delivery

Head: [66b3a75746fbbca3cffdfc7d89f013ab14aa1cc0](https://github.com/kebag-logic/tsn-c-stack/commit/66b3a75746fbbca3cffdfc7d89f013ab14aa1cc0).
The commit is local. Remote links to this head become available after publication.
Subject: `Discard malformed ADP discovery frames`.
The worktree is clean. The configured holder identity was used.
The commit has one subject line, no body and no trailers.
The [proposed PR body](PR-BODY.md) uses `Closes #3` because the assigned acceptance items are met.
The [consumer update](https://github.com/kebag-logic/milan-fpga/issues/697) remains separate.
The production diff changes only the ADP receive guard. Public headers are unchanged.
No push or pull request was created. No other repository was changed. No hardware was accessed.
The manager publishes the branch and opens the pull request.
