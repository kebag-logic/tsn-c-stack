# ACMP publish port handoff

## Round 3

Status: REVIEW READY; Round 3 implementation and validation complete.
Branch: `acmp-publish-port`. Head: `bc68ad8f3577e8f3dc24c4336e9b80a933df6c79`.
Parent: `f3dc2ae5bad02aa05a504b43c207e8b304d2bed5`.
Original base: `1a9f651cdf7846b8e10ac246a6ef6916960fbb92`.
Reference: milan-fpga dev `09c7231eca343607c97c0d66abebb2553688712c`.
F-INT commits: `5a50b2045427313527197eb22cd0f8276ef4b015` and `7c583daace3a459bcf462deaf58acefee21cd41b`.
All revisions were resolved with `git rev-parse`.

The [Round 3 assignment](https://github.com/kebag-logic/tsn-c-stack/issues/21#issuecomment-6115822525)
and [R622-2 review](https://github.com/kebag-logic/tsn-c-stack/pull/22#issuecomment-6115818580)
were read in full, alongside the issue body, original assignment and acceptance amendments.
R622-2-F1 and S-4 are addressed together: each publication-cache field has an independent hosted assertion and restore-only plant, and a gate derives the required field set from the header.
The ACMP core and header are byte-unchanged from Round 2. No other core file changes from the assigned base.

One new commit, `Require per-field ACMP publication cache coverage`, was made after all 26 Linux gates and both RV32 configurations passed.
The configured identity was retained, with a one-line subject and no body or trailers; no amend or rebase occurred.
The review scripts then ran against that exact committed head. Current receipts are under [round3](round3/); root and round2 build receipts are historical.

### Round 3 change map

| File:line | Change and defect caught |
|---|---|
| `tests/test_acmp.cpp:2232` | Bind with STREAMING_WAIT, restore an empty record, then require a withdrawal at open. With only bound nonzero, losing `published_bound` cannot hide behind a started or stream change. |
| `tests/test_acmp.cpp:2249` | Bind started, restore a stopped record for the same talker, then require a stop publication at open. Dropping only `published_started` loses that publication and fails its named assertion. |
| `tests/mutations.json:5249`, `:5264` | Add bound-only and started-only restore-loss plants, each graded by its own hosted assertion. |
| `tests/mutations.json:5234` | Express the existing stream plant as only the restore statement, without unchanged following context; its defect and named assertion are retained. |
| `scripts/check_acmp_cache.py:24`, `:32` | Discover every `published_*` member in `acmp_sink` from compiler tokens, require exactly one restore in `sink_reset`, one restore-only loss plant, and one distinct hosted assertion message. |
| `scripts/check_acmp_cache.py:65` | Thirty negative metadata controls and a covered-future-field positive control. Missing tests, assertions, plants or restores, duplicate plants, unchanged or multi-field substitutions, wrong paths and shared assertions are refused. A changed needle cannot disguise a shared assertion literal. |
| `scripts/validate.py:61` | Run the cache completeness selftest as a mandatory source gate. |
| `docs/TESTS.md:67`, `docs/TRACEABILITY.md:24` | Regenerate both inventories, tracing the new cases to ACMP-10 and their individual plants. |
| `docs/VERIFICATION.md:23`, `:33`, `:162` | Record 342 plants and document the cache gate, controls and hosted-only kill requirement. |

The checker has no fixed three-field allowlist: adding a `published_*` member without its own assertion and plant fails. Metadata validation is separate from execution: the mandatory mutation campaign proves the selected assertion actually fails. The checker also passes under optimized Python.

### Individual cache evidence

| Field | Hosted case suffix under `AcmpCore` | Plant | Result |
|---|---|---|---|
| `published_bound` | `A31StoreResetOfABoundStoppedSinkPublishesItsWithdrawal` | `acmp-publish-reset-bound-cache` | CAUGHT by its only required assertion |
| `published_started` | `A31StoreRestoreOfAStoppedRecordPublishesTheStop` | `acmp-publish-reset-started-cache` | CAUGHT by its only required assertion |
| `published_stream` | `A31StoreResetOfASettledSinkPublishesAMovedStream` | `acmp-publish-reset-stream-cache` | CAUGHT by its only required assertion |

[cache-plants.json](round3/cache-plants.json) preserves the three hosted failure diagnostics, and [mutation-summary.json](round3/mutation-summary.json) records every campaign outcome. All 342 plants are CAUGHT, with 0 ESCAPED and 0 ERROR. No RV32 result contributes to these kills.

## Retained Round 2 changes

| File:line | Finding and resulting check |
|---|---|
| `tests/test_acmp.cpp:2206` | F-1: settle through PROBE_TX_RESPONSE, require a publication and timer callback, then assert publication precedes the timer port. |
| `tests/test_acmp.cpp:2218` | F-1: reset a settled sink through restore, require silent restore, then assert the next open publishes withdrawal with `stream_moved=true`. |
| `tests/mutations.json:5219` | Plant publication after timers, killed by `A31 settlement publication precedes the timer port in finish`. |
| `tests/mutations.json:5234` | Drop only the restored stream cache, killed by `A31 withdrawal after a store reset reports the settled stream moved`. |
| `docs/TESTS.md:66`, `docs/TRACEABILITY.md:24` | Regenerate both new test/defect links and the ACMP-10 origin. |
| `docs/requirements.json:177`, `docs/REQUIREMENTS.md:38` | F-2: explicit F-INT / issue #21 provenance, separate from the import-baseline table; pinned source and both commits linked, with each standard separately linked at the recorded clauses. |
| `scripts/requirement_records.py:15`, `:194`, `:309` | Validate the additional origin without allowing a verification exemption; missing, false and broken origin controls must fail. The original source inventory stays pinned. |
| `scripts/traceability.py:116` | Generate the additional origin link instead of the import-baseline fallback. |
| `src/acmp.c:29`, `:188`, `:198`, `:216`, `:488` | F-3: add or move only blank lines to align every code token with the reference. |
| `include/acmp.h:146`, `:330` | F-3: retain blank lines for the introductory publication contract and callback comments. |
| `docs/VERIFICATION.md:23` | Record the 340-plant campaign. |
| `CHANGELOG.md:5` | Describe the required publish callback and its integration effect. |

## Full port change map

The following Round 1 changes remain; line references are for the delivered head.

| File:line | Change |
|---|---|
| `src/acmp.c:188`, `:198` | Guard `p_publish`; publish only a changed bound/started/settled-stream triple. |
| `src/acmp.c:288`, `:489` | Publish before a new send or queue insertion and first in `finish`. |
| `src/acmp.c:518` | Preserve all publication-cache fields across sink reset. |
| `include/acmp.h:330`, `:385` | Required publish callback and its three cache fields, in upstream field order. |
| `tests/acmp_fake.hpp:107`, `:228` | Record publication values and ordering; provide callback re-entry stimulus. |
| `tests/test_acmp.cpp:2045` | Port the ordering helpers and six F-INT A31 cases. |
| `examples/rv32/smoke.c:141`, `:174` | Implement the publication port and test restore/open, rollback, response ordering, settlement, START/STOP and withdrawal. |
| `docs/PORTING.md:170`, `:178`, `:266` | Callback signature, synchronous application, order, startup and cache ownership. |
| `docs/ARCHITECTURE.md:55` | Explain publication before responses and completion callbacks. |
| `tests/mutations.json:5009` | Original fourteen publication plants. |
| `tests/coverage.ratchet:5` | ACMP ratchet: 767/767 lines and 362/362 branches; no new exclusion. |
| `scripts/check_port_contracts.py:115`, `:264` | Require the callback, fields and ordering phrases, including meaning-removal controls. |

## Source bytes, tokens and line positions

[ported-reference.diff](round3/ported-reference.diff) is the complete byte-preserving diff of both delivered ACMP files against the reference at `09c7231e`.
[baseline-layout.diff](baseline-layout.diff) compares the original base against the pre-F-INT copies at `0a62616e08dd58928e73183ecdf16dbee330becd`.
[file-identity.json](round3/file-identity.json) records sizes, SHA-256 and line counts.
The delivered source has 1294 lines and the header 494, exactly matching the reference.
Round 3 changes neither core file. Round 2 added only blank lines; no other core file changes from the original base.

The unchanged R622-2 token comparison uses Clang 18 raw tokens and returns 0 for both files:
7849 source tokens and 1175 header tokens, equal in kind, spelling, line and column.
[token-lines.log](round3/token-lines.log) records the result.
The complete residual proof independently uses the repository's pinned raw lexer.

[residuals.json](round3/residuals.json) enumerates every differing byte interval between equal code tokens, with exact byte strings, offsets and line positions.
Its [summary](round3/token-proof.json) identifies 197 intervals whose reference and delivered bytes are exactly the corresponding pre-F-INT and `1a9f651c` bytes (95 source, 102 header).
Those are all pre-existing licence/comment/layout differences.
Eight remaining intervals are the explicitly authorized F-INT comment rewrites or adjacent blank-line preservation:

| File and interval | Classification |
|---|---|
| `src/acmp.c` introductory comment | F-INT expanded ordering prose; retain the existing MIT/tracing preamble and preserve the reference's line count. |
| `src/acmp.c` before `publish` | Two upstream prose lines become a blank line and `REQ: ACMP-10`. |
| `src/acmp.c` before `decode` | Preserve the inherited removed wire-section prose as blank lines after the inserted publish function. |
| `src/acmp.c` before `finish` | Expanded ordering prose becomes blank lines; meaning remains in PORTING and ARCHITECTURE. |
| `src/acmp.c` before `sink_reset` | Expanded cache prose retains the existing Milan reference and blank lines. |
| `include/acmp.h` introductory comment | New published-before-promised prose becomes blank lines; API documentation retains the contract. |
| `include/acmp.h` before the callback | Six upstream prose lines become five blank lines and the requirement annotation. |
| `include/acmp.h` before the cache | Upstream cache prose becomes the requirement annotation. |

Every byte in these eight intervals is a comment or whitespace, verified by the lexer.
They are the amendment's authorized comment treatment, not claimed to predate F-INT.
There are zero residual code-token differences and no new code-line shift.
The raw-byte identity wording is interpreted under [acceptance amendment 6115181911](https://github.com/kebag-logic/tsn-c-stack/issues/21#issuecomment-6115181911), as retained by the Round 2 and Round 3 assignments.

## RV32 raw object identity

The unchanged review `object_compare.sh` builds both copies in the same scratch directory, with the same `wire.h`, minimal port headers, compiler and flags.
All six raw object pairs are byte-equal before stripping; no section differs.
[object-compare.log](round3/object-compare.log) and [objects.json](round3/objects.json) give flags, full SHA-256 and sizes.
The compiler is RV32 GCC 16.2.0. Include path variables below name the minimal port and compiler intrinsic headers.

Common flags, followed by each row's flags and `-c src/acmp.c -o "$OUTPUT"`:

```sh
-Isrc -I"$PORT_INCLUDE" -march=rv32i -mabi=ilp32 -ffreestanding -fno-builtin -nostdinc -isystem "$(riscv64-elf-gcc -print-file-name=include)" -std=c11 -Wall -Wextra -Werror
```

| Configuration | Exact additional flags | Raw result | Bytes per object |
|---|---|---|---:|
| Debug without debug sections | `-DCTRL_REENTRY_ASSERT -g0` | EQUAL | 36176 |
| Debug | `-DCTRL_REENTRY_ASSERT -g` | EQUAL | 156816 |
| Release | `-DCTRL_REENTRY_ASSERT -O3 -DNDEBUG` | EQUAL | 30684 |
| Size optimization | `-DCTRL_REENTRY_ASSERT -Os` | EQUAL | 21092 |
| O2 without the re-entry hook | `-O2` | EQUAL | 25776 |
| Size optimization with macro debug data | `-Os -g3` | EQUAL | 336736 |

The first two use the compiler's default O0. The Debug and Release rows cover the repository's RV32 configurations.
Debug object hashes depend on the comparison directory; both sides use the identical directory.
No object file is placed in the output packet. The oversized `-Os -g3` objects remain in scratch with size/hash evidence.

## Tests and defects

[test-port-identity.json](round3/test-port-identity.json) proves all six imported A31 bodies and the entire fake remain token-identical to the pinned reference.

| Test suffix, all under `AcmpCore` | Source | Defect caught |
|---|---|---|
| `A31TheBindingIsPublishedBeforeTheResponseThatPromisesIt` | `tests/test_acmp.cpp:2052` | Response before publication, missing/wrong stream or binding, stale cached fields, redundant GET/unbind publication. |
| `A31LeavingSettlementTakesTheStreamOffTheDatapath` | `tests/test_acmp.cpp:2085` | Old settled stream retained after rebind, timeout or unregister; wrong sink/interface. |
| `A31OnlyAMovedTripleIsPublished` | `tests/test_acmp.cpp:2107` | Redundant unchanged publication. |
| `A31TheStartedLevelIsPublishedBeforeItIsPromised` | `tests/test_acmp.cpp:2122` | Lost started state, late publication, wrong moved flag or redundant stop. |
| `A31RestoredBindingsArePublishedWhenTheTransportOpens` | `tests/test_acmp.cpp:2157` | Premature or omitted restore publication, wrong restored started state, duplicate open, lost bound cache. |
| `A31ACallBackFromThePublishPortIsRefused` | `tests/test_acmp.cpp:2194` | Unguarded synchronous re-entry from the publication callback. |
| `A31SettlementIsPublishedBeforeTheTimerPort` | `tests/test_acmp.cpp:2206` | Publication after timer rearm in `finish`. |
| `A31StoreResetOfASettledSinkPublishesAMovedStream` | `tests/test_acmp.cpp:2218` | Lost stream-cache history across reset, falsely reporting no stream movement on withdrawal. |
| `A31StoreResetOfABoundStoppedSinkPublishesItsWithdrawal` | `tests/test_acmp.cpp:2232` | Lost bound-cache history suppresses withdrawal of a stopped, unsettled binding. |
| `A31StoreRestoreOfAStoppedRecordPublishesTheStop` | `tests/test_acmp.cpp:2249` | Lost started-cache history suppresses the restored stop of an unchanged binding. |

The full campaign reports 342 CAUGHT, 0 ESCAPED, 0 ERROR. All three individual cache defects compile and are caught by their exact named assertion messages.
The executable inventory has 121 declarations and 382 instances across seven binaries.
RV32 runs its documented focused smoke subset in Debug and Release; the full mutation, sanitizer and coverage denominators belong to Linux.
The reviewed clauses remain Milan v1.2 5.3.8.7, 5.5.3.5.18 step 4 and 5.5.3.5.36 step 1, and IEEE 1722.1-2021 7.4.35 and 7.4.36.
Publication order is the assigned local integration contract supporting those clauses. No standards text is reproduced.

## Round 3 reviewer reproduction

The seven original review scripts were fetched from `tsn21-review-evidence` at `a6071dc0dc770113228c7e8406f07959bbe20572`, under `review-evidence/tsn21-r1/reviews/R622-2/scripts/`. Their original bytes and hashes are preserved in [source-integrity.json](round3/source-integrity.json).

- The unmodified `probes.sh` runs the head control and six faults. Both previously escaped cache faults now fail only their corresponding new repository test. Its seventh substitution, `settled-ignores-rsv-ok`, refuses to run because the search string occurs twice in the unchanged core. This is a script replacement failure, not a test catch.
- [probes-scoped.diff](round3/probes-scoped.diff) records the only correction in a scratch copy: constrain that old/new string with the precise context already used by `witness2.sh`. All seven faults then compile and fail named repository assertions; the head control passes all 79 ACMP tests. The original script is retained unchanged.
- The unmodified `witness2.sh` passes all 81 cases on head. W2 and W3 and their new repository counterparts each fail on the matching bound-only or started-only fault. Its RSV_OK control is also caught.
- The unmodified `rv32_probe.sh` is rerun on head, bound-only and started-only trees. Head passes Debug and Release. The bound-only tree builds and links in both configurations, then QEMU exits 34 in both; these are expected smoke failures. The started-only tree still passes both smoke configurations, matching the prior review. The hosted campaign now catches it independently.

[review-audit.json](round3/review-audit.json) checks build success, complete test counts, return codes, failed-test names and assertion messages. Its audit returns 0. Fault-injected nonzero results are expected controls, not failures of the delivered-head gates. The original probe replacement error is retained explicitly and superseded only by the disclosed scoped replay.

## Gate table on both targets

[linux-gates.json](round3/linux-gates.json) records all 26 commands at rc 0. [rv32-results.json](round3/rv32-results.json) records both delivered-head configurations at rc 0. The runners were invoked directly, without output pipes. Commands, logs and return codes remain in scratch; receipt manifests record sizes and SHA-256 values.

| Gate | Linux | Bare-metal RV32 |
|---|---|---|
| Boundary and dependency controls | 0 / 0 | Debug/Release dependency and import checks: 0 |
| Assertion needles and templates | 0 / 0 | Shared source contract |
| Comments and assertion contract | 0 | Includes assembly and linker controls |
| Conditional matrix | 0 | Both configurations additionally build |
| Port contracts | 0 | Same API contract |
| ACMP cache completeness | 0; 30 negative controls, future-field positive control | Shared contract; kills established on Linux |
| Registration controls | 0 | Hosted registration |
| Licence | 0 | Same sources |
| Traceability | 0; 43 requirements | Both target obligations retained |
| Test inventory | 0; 121 declarations, 382 instances, 7 binaries | Focused smoke subset |
| Coverage controls | 0 | Hosted controls |
| Privacy and privacy selftest | 0 / 0; also rerun after commit | Same source/history |
| GCC configure, build and tests | 0 / 0 / 0 | Cross-build below |
| Coverage | 0; adjusted 100% lines and branches | No RV32 coverage claim |
| Clang 18 sanitizer configure, build and tests | 0 / 0 / 0; ASan, UBSan and leak detection | Not applicable |
| Static analysis | 0; clang-tidy 18 | Same production files |
| Mutation and report controls | 0 / 0; 342 CAUGHT, 0 ESCAPED, 0 ERROR | Hosted campaign |
| Graphs | 0 | Shared documentation |
| Configure, build, whole-archive link and smoke | Hosted checks above | 0 in Debug and Release |
| ELF architecture, ABI and symbols | Not applicable | RV32I/ILP32; zero unresolved symbols |
| Token, line and column comparison | 0 | Same source bytes |
| Reference object comparison | Cross-build evidence | All 6 raw pairs byte-equal |
| Exact-head review audit | 0 | Head and planted controls verified |

## Environment and limits

Round 1's local sanitizer build failed because Clang 18 encountered incompatible host libstdc++ 16 headers and lacked sanitizer runtime archives. Round 2 resolved both entirely in scratch. Round 3 reuses that unchanged setup: pinned Clang 18.1.3, compatible Ubuntu libstdc++ 13.3 headers and matching compiler-rt 18.1.3 archives, with the host libstdc++ shared library and pinned GoogleTest/GMock 1.14.0. Static analysis uses clang-tidy 18.1.3. No package installation, shared-prefix change, analyzer suppression or core field reorder was needed. Package hashes remain in the Round 2 receipt manifest.

Scratch: `$VALIDATION_STORAGE/tsn21-a602/round3/`; shared environment: `$VALIDATION_STORAGE/tsn21-a602/round2/env.sh`; full runners: `run-gates.sh`, `run-review.sh`, `run-rv32-controls.sh`, `run-probes-scoped.sh`. Builds use `--jobs 16` and `-j16`; unchanged reviewer scripts retain their internal concurrency. The reference clone remains clean at `$VALIDATION_STORAGE/tsn21-a602/milan-fpga/`.

Observed gate MemoryCurrent peak: 3,844,722,688 bytes. Concurrent review peak: 4,557,553,664 bytes. Service cgroup peak including the scoped replay: 5,386,645,504 bytes, below 9 GB. Memory receipts are included. Full build trees, dependencies, binaries and files over 200 KB stay in scratch; their sizes and hashes are recorded, never copied into this packet.

Reproduce from the branch with the pinned dependencies and a compatible Clang 18 sanitizer environment:

```sh
python3 scripts/validate.py --work build-validation --jobs 16 --graphs
python3 scripts/baremetal.py --work build-rv32 --jobs 16
python3 scripts/check_acmp_cache.py --selftest
```

Standards clauses were checked against the local IEEE 1722.1-2021 and Milan v1.2 PDFs. Only clause references are reproduced. The local publication contract supports Milan 5.3.8.7, 5.5.3.5.18 step 4 and 5.5.3.5.36 step 1, and IEEE 7.4.35 and 7.4.36; it is not itself a standards-defined callback.

## Remaining integration duties

Acceptance item 6 remains pending. The manager owns the push, hosted acceptance, fresh independent reviews, current-main merge candidate, merge commit, current-dev consumer checks and pin update. The assigned-base validation above does not claim execution of unrelated newer-main entity-generator gates or a future merged tree. No hardware, physical timing, builder bank or consumer firmware result is claimed.

The amended source-identity acceptance is met. The byte diff and full residual ledger distinguish inherited differences from explicitly authorized F-INT comment treatment; they do not claim literal raw-byte identity across rewritten comments. PR-BODY.md uses `Relates to #21` because the integration and review acceptance is unfinished.

## Delivery

Post-commit privacy selftests and history/content scan return 0. All 77 tracked files match the committed tree, and the working tree is clean. TAKEN was not repeated. No push, PR creation, existing comment edit, parent-repository change or hardware access occurred. Posted [REVIEW READY](https://github.com/kebag-logic/tsn-c-stack/issues/21#issuecomment-6115938213) on issue #21 with the exact branch head. All background runs have completed.
