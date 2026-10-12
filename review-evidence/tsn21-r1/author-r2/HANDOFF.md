# ACMP publish port handoff

## Round 2

Status: REVIEW READY; all assigned fixes and validation complete. The new status comment is linked under Delivery.
Branch: `acmp-publish-port`. Head: `f3dc2ae5bad02aa05a504b43c207e8b304d2bed5`.
Round 2 parent: `2dcbe91ead981591d5bfb652f6616f6edb325875`.
Original base: `1a9f651cdf7846b8e10ac246a6ef6916960fbb92`.
Reference: milan-fpga dev `09c7231eca343607c97c0d66abebb2553688712c`.
F-INT commits: `5a50b2045427313527197eb22cd0f8276ef4b015` and `7c583daace3a459bcf462deaf58acefee21cd41b`.
All revisions were resolved with `git rev-parse`.

The [Round 2 assignment](https://github.com/kebag-logic/tsn-c-stack/issues/21#issuecomment-6115533235),
[negative review](https://github.com/kebag-logic/tsn-c-stack/pull/22#issuecomment-6115528348)
and [positive review](https://github.com/kebag-logic/tsn-c-stack/pull/22#issuecomment-6115496993)
were read in full, along with the issue body, original assignment and acceptance amendment.
Round 2 chooses F-3 option (a): preserve F-INT line positions. The core remains token-identical.

One new commit, `Close ACMP publication review gaps`, follows the existing head without amendment or rebase.
It was committed only after all 25 Linux gates and both RV32 configurations passed.
The configured identity was retained, with a one-line subject and no body or trailers.
All current receipts are under [round2](round2/); root-level Round 1 build receipts are historical.

## Round 2 change map

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

[ported-reference.diff](round2/ported-reference.diff) is the complete byte-preserving diff of both delivered ACMP files against the reference at `09c7231e`.
[baseline-layout.diff](baseline-layout.diff) compares the original base against the pre-F-INT copies at `0a62616e08dd58928e73183ecdf16dbee330becd`.
[file-identity.json](round2/file-identity.json) records sizes, SHA-256 and line counts.
The delivered source has 1294 lines and the header 494, exactly matching the reference.
Round 2 changes only whitespace in these two core files; no other core file changes from the original base.

The original #697 token comparison runs unchanged, now with line checking enabled, and returns 0 for both files:
7849 source tokens and 1175 header tokens, equal in kind, spelling and line position.
[token-lines.log](round2/token-lines.log) records the result.
The repository's pinned Clang 18 raw lexer independently establishes token equality.

[residuals.json](round2/residuals.json) enumerates every differing byte interval between equal code tokens, with exact byte strings, offsets and line positions.
Its [summary](round2/token-proof.json) identifies 197 intervals whose reference and delivered bytes are exactly the corresponding pre-F-INT and `1a9f651c` bytes (95 source, 102 header).
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
The raw-byte identity wording is interpreted under [acceptance amendment 6115181911](https://github.com/kebag-logic/tsn-c-stack/issues/21#issuecomment-6115181911), as directed by Round 2.

## RV32 raw object identity

The unchanged review `object_compare.sh` builds both copies in the same scratch directory, with the same `wire.h`, minimal port headers, compiler and flags.
All six raw object pairs are byte-equal before stripping; no section differs.
[object-compare.log](round2/object-compare.log) and [objects.json](round2/objects.json) give flags, full SHA-256 and sizes.
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

[test-port-identity.json](round2/test-port-identity.json) proves all six imported A31 bodies and the entire fake remain token-identical to the pinned reference.

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

The full campaign reports 340 CAUGHT, 0 ESCAPED, 0 ERROR. Both new defects compile and are caught by their exact named assertion messages.
The executable inventory has 119 declarations and 380 instances across seven binaries.
RV32 runs its documented focused smoke subset in Debug and Release; the full mutation, sanitizer and coverage denominators belong to Linux.
The reviewed clauses remain Milan v1.2 5.3.8.7, 5.5.3.5.18 step 4 and 5.5.3.5.36 step 1, and IEEE 1722.1-2021 7.4.35 and 7.4.36.
Publication order is the assigned local integration contract supporting those clauses. No standards text is reproduced.

## Reviewer reproduction

The three scripts were read from `tsn21-review-evidence`, `review-evidence/tsn21-r1/reviews/R622-1/scripts/`, and their bytes were preserved.
The six object comparisons pass. [review-audit.json](round2/review-audit.json) audits the unchanged scripts against the committed head. All 11 probe builds succeed. Both required faults are CAUGHT by the new repository tests and their exact named messages. The unmodified witness suite passes all 10 selected tests; each fault fails both its original reviewer witness and the corresponding new repository assertion.
The review script's `failed_tests` list is empty because its parser selects the status word; the audit extracts the actual names from the preserved logs. No build failure is counted as a catch.
The harmless blank-line control remains an expected pass. The guard-clearing suggestion remains outside this round's required fixes. The bound-cache-only fault still escapes hosted tests and is caught by RV32 smoke check 34 in both Debug and Release; both faulty binaries configure, build and link successfully. [probe-rv32-audit.json](round2/probe-rv32-audit.json) records the expected simulator failures. The guard-clearing suggestion and harmless control also retain their prior passing RV32 outcomes. These probes are outside the 340-plant repository campaign; that campaign has no escape or error.

## Gate table on both targets

[linux-gates.json](round2/linux-gates.json) reports all 25 commands at rc 0; [rv32-results.json](round2/rv32-results.json) reports Debug and Release rc 0.
The full runner commands were unpiped. Each command has its own log and rc under scratch; [receipt-manifest.json](round2/receipt-manifest.json) records hashes and sizes.

| Gate | Linux | Bare-metal RV32 |
|---|---|---|
| Boundary and forbidden-dependency controls | 0 | Debug/Release dependency and symbol checks: 0 |
| Assertion needles and diagnostic templates | 0 / 0 | Shared source contract |
| Dependency pin controls | 0 | No hosted test library |
| Comment and assertion contract | 0 | Includes assembly/linker controls |
| Conditional matrix | 0 | Shared source matrix plus both builds |
| Port contracts | 0 | Same API contract |
| Registration controls | 0 | Hosted inventory |
| Licence | 0 | Same sources |
| Traceability | 0; 43 requirements, 28 metadata controls | Both target obligations retained |
| Test inventory | 0; 119 declarations, 380 instances | Focused smoke subset |
| Coverage controls | 0 | Hosted controls |
| Privacy / privacy selftest | 0 / 0 | Same source/history |
| GCC configure / build / tests | 0 / 0 / 0; seven binaries | Cross-build below |
| Coverage | 0; adjusted 100% lines and branches in every measured file | No RV32 coverage claim |
| Clang 18 sanitizer configure / build / tests | 0 / 0 / 0; seven binaries, ASan/UBSan/leak checks | Not applicable |
| Static analysis | 0, clang-tidy 18 | Same production files |
| Mutation campaign / report controls | 0 / 0; 340 caught | Hosted campaign |
| Graphs | 0 | Shared documentation |
| Configure / compile / full-archive link / smoke | Hosted checks above | 0 in Debug and Release |
| ELF architecture, ABI and final symbols | Not applicable | RV32I/ILP32; zero unresolved symbols |
| Token comparison including lines | 0 | Same core bytes |
| Raw reference object comparison | Cross-build evidence | 0; all six pairs equal |

## Environment and limits

Round 1's local sanitizer build failed because the supplied Clang 18 installation met incompatible libstdc++ 16 headers and lacked sanitizer runtime archives.
Round 2 resolves both in scratch, without changing the repository, shared toolchain prefix or host packages.
The same pinned Clang 18.1.3 uses official Ubuntu libstdc++ 13.3 headers and matching compiler-rt 18.1.3 archives.
The runtime still links the host libstdc++ shared library and the pinned GoogleTest/GMock 1.14.0.
Compiler launchers add only the compatible C++ system include directories and a resource directory with the original Clang headers and matching runtimes.
The package SHA-256 and sizes are in the receipt manifest. Earlier exploratory failures are retained in scratch and are superseded by the complete fresh all-zero run.
Static analysis uses the previously extracted clang-tidy 18.1.3. No analyzer suppression or imported field order changed.

Scratch: `$VALIDATION_STORAGE/tsn21-a602/round2/`; environment: `env.sh`; launcher: `run-gates.sh`; full work trees: `linux/`, `rv32/`, `objects/`.
The read-only reference clone remains at `$VALIDATION_STORAGE/tsn21-a602/milan-fpga/` and was not changed.
Independent builds and campaigns ran concurrently with `--jobs 16` and build `-j16`.
Observed full-gate MemoryCurrent peaked at 3,831,742,464 bytes; reviewer reproduction peaked at 5,848,641,536 bytes. The service cgroup peak is 6,173,630,464 bytes, below 9 GB. Both runs retain memory receipts.
No unfinished background process is needed after delivery.

Reproduce from the source branch with the pinned dependencies available:

```sh
python3 scripts/validate.py --work build-validation --jobs 16 --graphs
python3 scripts/baremetal.py --work build-rv32 --jobs 16
```

## Round 1 and remaining integration duties

Round 1 was `2dcbe91ead981591d5bfb652f6616f6edb325875`, directly on the assigned base.
Its hosted run [38186240742](https://github.com/kebag-logic/tsn-c-stack/actions/runs/38186240742) supplied the previously missing sanitizer execution.
That run and the two Round 1 verdicts are historical; the current local receipts cover Round 2.
The current head still requires the manager's push, hosted acceptance, two independent positive reviews, main merge commit and consumer pin update.
The manager must validate the eventual current-main merge and the current-dev consumer candidate. No future merged tree or physical timing result is claimed here.
Acceptance item 6 remains pending, so PR-BODY.md uses `Relates to #21`.
No push, PR creation, existing comment edit, hardware access or parent-repository change was performed.

## Delivery

Exact-head reviewer scripts and audit pass. Post-commit privacy selftests and history/content scan both return 0 (7 commits, 160 historical blobs, 76 current files). Posted [REVIEW READY](https://github.com/kebag-logic/tsn-c-stack/issues/21#issuecomment-6115656360) on issue #21 with the exact branch head. TAKEN was not repeated. The branch remains unpushed.
