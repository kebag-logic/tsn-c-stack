[R622] NEGATIVE - exact head f3dc2ae5bad02aa05a504b43c207e8b304d2bed5

# R622-2 independent delta review: tsn-c-stack issue #21 / PR #22

- Round: R622-2 (internal reviewer), delta over R622-1 at `2dcbe91e`.
- Exact head: `f3dc2ae5bad02aa05a504b43c207e8b304d2bed5`, tree `d4ec359c00b7b34070e2b01d297607327260550a`.
- Parent: `2dcbe91ead981591d5bfb652f6616f6edb325875`. Source base: `1a9f651cdf7846b8e10ac246a6ef6916960fbb92`.
- Reference: milan-fpga dev `09c7231eca343607c97c0d66abebb2553688712c` (`sw/firmware/ctrl/acmp/acmp.c`, `acmp.h`, `test/test_acmp.cpp`). Pre-F-INT control: milan-fpga `0a62616e` (parent of `5a50b2045`).

## Verdict summary

All three R622-1 findings are resolved at this head:

- **F-1:** two named assertions, each with a plant, catch publish-after-timers and the dropped stream cache.
- **F-2:** ACMP-10 now traces to #21 / F-INT `09c7231e`, and its clause references are linked.
- **F-3:** blank lines restore line alignment, and all six object comparisons are raw byte-equal.

The core stays token-identical. Every hosted quality and bare-metal job passed at this head.

My independent pass found one new MINOR finding (R622-2-F1). It is the same class as R622-1 F-1, on a cache field that round did not probe. `sink_reset` preserves three publication-cache fields. If it drops only `published_started`, the fault escapes every gate, and no plant covers it. The fault is observable: a store restore of a stopped record over a started binding loses its stop publication. Because an open MINOR leaves the Tests and Conformance lenses unclean, the verdict is NEGATIVE.

## Findings

### R622-2-F1 MINOR: Loss of the started publication cache across sink reset escapes every gate
- **Lenses:** Tests, Conformance.
- **Where:**
  - `src/acmp.c:519` and `src/acmp.c:525`: `sink_reset` saves and restores `published_started`.
  - The contract text claims preservation of the whole triple:
    - `docs/PORTING.md:203-205`: "Sink reset and rollback preserve the last published triple, so the next open or completed event can publish its withdrawal".
    - `docs/PORTING.md:266`: the public-field row for `published_bound`, `published_started`, `published_stream`.
    - `docs/requirements.json:178` and `docs/REQUIREMENTS.md:48`: ACMP-10, "preserve the publication cache across restore/reset", verification method test.
  - `tests/mutations.json` plants this only as all three fields together (`acmp-publish-reset-cache`, caught through the bound field) or as the stream field alone (`acmp-publish-reset-stream-cache`).
- **Authority:**
  - CONTRIBUTING.md: "A protocol change updates its requirement, tests and traceability. A regression needs a failing assertion and a runnable planted defect."
  - ACMP-10 is declared test-verified in the generated matrix (`docs/TRACEABILITY.md:24`).
  - R622-1 F-1 classified the stream-field analogue of this gap as MINOR, and the manager accepted that.
- **Evidence:** all runs used exported copies of the exact head tree with one replacement in `src/acmp.c`.
  - **The fault:** replace `\ts->published_started = published_started;\n` with `\t(void)published_started;\n`.
  - **Hosted suite:** `receipts/probes.txt` (`scripts/probes.sh`) shows all 77 `acmp_tests` pass. A full build and `ctest` pass all 7 binaries, which hold 380 instances (`receipts/rv32-probes.txt`).
  - **RV32 gate:** `scripts/baremetal.py`, Debug and Release smoke, rc 0 (`receipts/rv32-probes.txt`).
  - **Mutation table:** no plant covers it.
  - **It is not equivalent.** Witness `R622W3StoreRestoreOfAStoppedRecordPublishesTheStop` (`scripts/witness2.sh`, `receipts/witness2.txt`) passes on the unmodified head (79/79) and fails only on this fault. The witness sequence:
    1. Bind sink 0 started.
    2. Restore a valid, stopped record for the same talker with `acmp_restore_binding`.
    3. Call `acmp_open`. At head this publishes bound/stopped once. Under the fault it publishes nothing.
  - **Controls:**
    - Dropping only `published_bound` also escapes the hosted suite (witness `R622W2…` catches it). The mandatory RV32 smoke does catch it (Debug QEMU exits nonzero), so it is recorded only as S-4.
    - Five other independent probes are caught by repository tests: last sink skipped, `RSV_OK` not settled, `moved` meaning non-zero, bound ignored, publication after admission. An unmodified head control passes.
- **Impact:**
  - The documented "preserve the last published triple" contract and ACMP-10 claim more than the gates establish.
  - A regression that loses the started cache would make the datapath keep a started stream after a store restore of a stopped binding, and no gate would fail.
  - The shipped code is correct, since it is token-identical to F-INT. This is a verification gap, not a behaviour defect.
- **Required outcome:**
  - Add a hosted named assertion that fails when `published_started` is not restored in `sink_reset`; the W3 witness is a sufficient model.
  - Add its plant (for example `acmp-publish-reset-started-cache`) to `tests/mutations.json`.
  - Regenerate TESTS.md and TRACEABILITY.md, and update the plant count in VERIFICATION.md.
  - The core must stay token-identical.
  - The alternative is to narrow the PORTING text and the ACMP-10 record so they claim only what is tested.
- **Verification:**
  - Re-run `scripts/probes.sh` and `scripts/witness2.sh` against the new head: `reset-drops-started-cache-only` must fail a named repository assertion.
  - The mutation gate must report every plant CAUGHT, with zero ESCAPED and zero ERROR.

## Residue
None.

## Suggestions (no effect on the verdict)
- **S-1 (retained from R622-1 S-1), Tests/Robustness:**
  - Host clang-tidy 23.1.1 fails the static-analysis gate at head with `clang-analyzer-optin.performance.Padding` at `include/acmp.h:353` (32 padding bytes in `struct acmp_sink`). The base `1a9f651c` passes on the same host.
  - Hosted clang-tidy 18 passes, and suppresses non-user-code diagnostics ("Suppressed 337 warnings").
  - The field order is fixed by token identity with F-INT, so this PR cannot fix it.
  - Follow-up: reorder upstream, or pin the header filter or a suppression in `scripts/static_analysis.py` / `docs/STATIC_ANALYSIS.md:7` before CI moves past clang-tidy 18.
  - Receipts: `receipts/linux/static-analysis.log`, `receipts/linux/base-static-analysis.log`, `receipts/hosted/static-analysis.log`.
- **S-2 (retained from R622-1 S-2), Tests:**
  - The clearing side of the `p_publish` guard (`src/acmp.c:193`) is untested.
  - The author's round-2 re-run of the prior probe set still reports `guard-left-set` ESCAPED at this head.
  - It is nearly equivalent, and the other port wrappers share the pattern at baseline.
- **S-3 (retained from R622-1 S-3), Docs:** the summary label at `scripts/baremetal.py:77` still says "ACMP restore and rollback". `docs/VERIFICATION.md:135` names publication too.
- **S-4 (new), Tests:**
  - Dropping only `published_bound` in `sink_reset` is caught only by RV32 smoke check 34. It escapes the hosted suite, and the mutation table has no plant for it.
  - Witness `R622W2StoreResetOfABoundStoppedSinkPublishesItsWithdrawal` (`receipts/witness2.txt`) could become a hosted assertion with a plant, so the defect enters the graded mutation campaign. This can be done together with F1.

## Prior public review findings (read after my independent verdict and ledger were drafted)

| Prior finding | Status at f3dc2ae5 | Evidence |
|---|---|---|
| R622-1 F-1 (publish-after-timers; stream cache dropped in reset) | RESOLVED | `A31SettlementIsPublishedBeforeTheTimerPort` (`tests/test_acmp.cpp:2206`) and `A31StoreResetOfASettledSinkPublishesAMovedStream` (`:2218`). Plants `acmp-publish-after-timers` and `acmp-publish-reset-stream-cache` are each CAUGHT by their named needle (`receipts/linux/round2-plants.json`). Local mutation 340 CAUGHT / 0 ESCAPED / 0 ERROR; hosted also 340/0/0. My independent probe `finish-publishes-after-admission` is also caught, by the new timer-order assertion. TESTS.md and TRACEABILITY.md regenerated (traceability and test-inventory gates rc 0). |
| R622-1 F-2 (ACMP-10 origin) | RESOLVED | The generated `docs/TRACEABILITY.md:24` origin is "milan-fpga F-INT at 09c7231e / tsn-c-stack #21", linked to `REQUIREMENTS.md#acmp-publish-port`. That new section names #21, `09c7231e`, `5a50b2045` and `7c583daac`, and states it postdates `5603c353`. The Milan and IEEE references are linked as `requirements.json` cites them. `requirement_records.py` validates the origin and has missing, false and broken controls. The anchor is checked by `valid_link`. |
| R622-1 F-3 (line alignment, `-g`/`-g3` objects) | RESOLVED (option a) | Token, line and column identity: 7849/7849 and 1175/1175 (`receipts/token-lines.txt`); line counts 1294/1294 and 494/494. R622-1's unchanged `object_compare.sh` gives raw EQUAL for all six sets, including `-g` and `-Os -g3` (`receipts/object-compare.txt`). The PR body names every comparison flag. |
| R622-1 S-1, S-2, S-3 | Retained as S-1, S-2, S-3 | See Suggestions. |
| R622-1 Docs recommendation (CHANGELOG entry) | RESOLVED | `CHANGELOG.md:5` adds the required-callback entry with an ACMP-10 link. |
| R623-1 (POSITIVE at `2dcbe91e`) | No findings to resolve | Its report lists no open finding of any severity. |

## Lens application

### Conformance
- **Acceptance 1:** two commits on `1a9f651c`, and the branch keeps that base.
- **Acceptance 2 (amended):** comment-stripped tokens are identical, measured two ways (`receipts/token-compare-two-methods.txt`, Clang raw lexer and GCC `-fpreprocessed`). They also sit at identical lines and columns (`receipts/token-lines.txt`, `scripts/token_lines.py`). The same holds for the baseline control (`1a9f651c` vs milan-fpga `0a62616e`: 7586/1137, lines equal). `git diff --stat 1a9f651c..HEAD -- src include` lists only `acmp.c` and `acmp.h`. This round's core change is blank lines only.
- **Acceptance 3:** the six upstream A31 tests are byte-identical to milan-fpga `09c7231e` `test_acmp.cpp`, and two A31 tests are added (`receipts/test-port-compare.txt`).
- **Acceptance 5:** PORTING, ARCHITECTURE and the port-contract gate describe the port and its order.
- **ACMP-10 records:** origin, linked clauses and targets are present. The requirement text in REQUIREMENTS.md:48 equals `requirements.json`.
- **Issue:** the test claim for the started-cache part of the contract is incomplete (F1).

### RTL (implementation and compiled objects; no HDL in this change)
- I read `p_publish`, `publish`, the transmit path at `src/acmp.c:288`, `finish` (`:488`), `sink_reset` (`:513`), `acmp_init`, `acmp_set_started`, `acmp_poll`, `acmp_restore_binding`, `acmp_restore_rollback` and `acmp_open`.
- **Object comparison:** six same-flag RV32 object pairs (head vs F-INT copy, RV32 GCC 16.2.0, R622-1's unchanged script) are raw EQUAL and strip-debug EQUAL. The `-g0`, `-O3 -DNDEBUG`, `-Os` and `-O2` hashes equal the author's receipt.
- **RV32 gate:** Debug and Release rc 0 with no unresolved symbols. Core imports are limited to `memcpy`, `memset`, `__mulsi3`, `__umodsi3` and the assertion hooks. The Release results match the author's receipt byte for byte; the Debug ELFs differ only through embedded build paths.
- CLEAN.

### Robustness
- **Re-entry:** the guard and its counting are tested (`A31ACallBackFromThePublishPortIsRefused`, plant `acmp-publish-unguarded`).
- **Bounds:** the publish loop is bounded by `n_sinks`. No heap, OS or new dependency is added; the boundary, dependency and conditional gates pass.
- **Reset paths:** the cache is preserved across `sink_reset` for all three fields at head, and `acmp_init` zeroes it first.
- **Escaped faults:** they concern verification, not shipped behaviour, so they are under F1 (Tests/Conformance).
- CLEAN.

### Tests
- **Gates:**
  - Local validation passed 23 of 25 gates. That includes gcc-test, coverage, mutation 340/0/0 and mutation-controls; the hosted suite has 380 instances.
  - The two host-limited gates are listed under Real limits.
  - Coverage: `src/acmp.c` 767/767 lines and 362/362 branches.
- **Probes and witnesses:**
  - Seven independent fault probes plus a head control, of which two faults escape the hosted suite.
  - Two witnesses, each passing on head and failing only on its probe.
  - The RV32 gate was run on both escapes; one is still undetected (F1).
- UNCLEAN (F1).

### Docs
- **Read in full:** the round-2 docs diff and the cumulative docs diff (CHANGELOG, ARCHITECTURE, PORTING, REQUIREMENTS, requirements.json, TESTS, TRACEABILITY, VERIFICATION).
- **Checked:**
  - The generated documents are current.
  - Anchors resolve.
  - The plant count is 340.
- **PR body** claims checked against receipts:
  - 7,849 and 1,175 tokens.
  - Six raw-equal object pairs with exact flags.
  - 25 Linux gates and both RV32 configurations.
  - 380 instances.
  - 340 plants.
- No wording residue found.
- CLEAN.

## Gate execution at this head

| Context | Result | Receipt |
|---|---|---|
| Local `validate.py --jobs 16 --graphs` (GCC 16.2.1, pinned Clang 18.1.3, pinned GoogleTest/GMock 1.14.0) | 23 of 25 gates ran to rc 0. `clang-sanitizers-build` rc 2 is from host libstdc++ 16 headers, an accepted host limit. `static-analysis` rc 1 is from host clang-tidy 23 header padding (S-1); the base passes. | `receipts/linux/` |
| Local `baremetal.py --jobs 16` (RV32 GCC 16.2.0, host QEMU) | rc 0, Debug and Release smoke | `receipts/rv32/` |
| Object comparison, six flag sets | all raw EQUAL | `receipts/object-compare.txt` |
| Hosted run 38188571695 (push event, exact head), job `quality` | success. All 25 gates rc 0, with clang-tidy 18, `clang-sanitizers-build`/`-test` executed, mutation 340/0/0, coverage 100% | `receipts/hosted/` |
| Hosted run 38188571695, job `bare-metal` | success; Debug and Release rc 0 | `receipts/hosted/bare-metal-job-excerpt.txt` |

- Hosted `quality` executed every gate; no step was skipped.
- Only a push-event run was observed at this head.
- No manager source bank runs at this head, and none is claimed or inferred here.
- Source-head execution evidence is the author's published round-2 gate receipts, plus the hosted run and my local runs above.

## Reviewer-owned ledger

| Lens | CLEAN/UNCLEAN | Examined artifacts | Covering round | Exact head |
|---|---|---|---|---|
| Conformance | UNCLEAN (R622-2-F1) | issue #21 acceptance, assignment, amendment and round-2 ruling; `src/acmp.c`, `include/acmp.h` vs milan-fpga `09c7231e` (tokens, lines, columns) and the `1a9f651c`/`0a62616e` control; A31 test port; ACMP-10 records, origin and clause links | R622-2 | f3dc2ae5bad02aa05a504b43c207e8b304d2bed5 |
| RTL | CLEAN | publish, p_publish, transmit, finish, sink_reset and entry points; six same-flag RV32 object pairs; RV32 Debug/Release ELFs, imports and smoke | R622-2 | f3dc2ae5bad02aa05a504b43c207e8b304d2bed5 |
| Robustness | CLEAN | re-entry guard, bounded loop, reset/rollback/restore cache paths, init zeroing, boundary/dependency/conditional gates, analyzer exposure (S-1) | R622-2 | f3dc2ae5bad02aa05a504b43c207e8b304d2bed5 |
| Tests | UNCLEAN (R622-2-F1) | `tests/test_acmp.cpp` (8 A31 tests), `tests/acmp_fake.hpp`, `tests/mutations.json` (16 publish plants), coverage ratchet, `examples/rv32/smoke.c`; local and hosted mutation 340/0/0; 7 fault probes plus control, 2 witnesses, RV32 runs on 2 probe trees | R622-2 | f3dc2ae5bad02aa05a504b43c207e8b304d2bed5 |
| Docs | CLEAN | CHANGELOG, ARCHITECTURE, PORTING, REQUIREMENTS, requirements.json, TESTS, TRACEABILITY, VERIFICATION, PR body | R622-2 | f3dc2ae5bad02aa05a504b43c207e8b304d2bed5 |

## Real limits
- **Sanitizer leg:** the local Clang 18 sanitizer build cannot compile against this host's libstdc++ 16 headers, which was accepted in the issue ruling. The hosted Clang 18 sanitizer build and test passed at this head.
- **Static analysis:** the local run uses clang-tidy 23.1.1 and cppcheck 2.22.0; hosted uses clang-tidy 18. The hosted gate is the judge, and it passed.
- **RV32:** local toolchain is RV32 GCC 16.2.0 with host QEMU. Hosted object hashes differ because hosted uses the Ubuntu toolchain. Each object comparison uses one compiler for both sides.
- **Pin check:** the token comparison is my own (Clang raw lexer, plus the prior GCC method), not milan-fpga #697's pin-check script.
- **Milan clause text:** clause numbers were checked against the repository records and the prior reviews, not against the specification text, which is not available to me.
- **Not run:** full parent, PP, gPTP, Yosys or builder banks; Docker/act; hardware. Physical calibration NOT RUN. QEMU smoke success and field skips are not hardware or timing proof.
- **Resources:** peak memory 4.58 GB within the 12 GB unit (`receipts/memory-peak-bytes.txt`).
- **Clone integrity:** probes ran only on exported copies under the packet's scratch directory. The review clone is unchanged: HEAD and tree as above, index equal to the tree, no untracked or ignored files, every tracked blob re-hashed equal (76 files). There are no gitlinks and no `.gitmodules`, so no submodule gitlink is required (`receipts/clone-integrity.txt`).

## Pending manager duties
- Carry R622-2-F1 to the author: one hosted assertion plus one plant; the core stays token-identical. S-4 can be done in the same change.
- Validate the current-dev merge candidate (source base `1a9f651c`, live milan-fpga dev `09c7231e`) with the builder and native banks at the merge turn, and link the receipts.
- Own hosted/act acceptance, including whether a pull_request-event run is required; only a push-event run was observed.
- Get two independent positive reviews and a merge commit into main (acceptance 6), then pin milan-fpga #697 to the head.
- Decide the S-1 follow-up before CI moves past clang-tidy 18.

## Packet
- **Scripts** (`scripts/`):
  - `token_lines.py`, `probes.sh`, `witness2.sh`, `rv32_probe.sh`, `run_gate.sh`.
  - `object_compare.sh`, `toolenv.sh`: R622-1's, unchanged.
- **Receipts:** under `receipts/`, listed in `MANIFEST.sha256`. Local host paths are replaced by `<packet>`, `<clone>` and `<tools>`.

R622-2 FINISHED
