[R622] POSITIVE - exact head bc68ad8f3577e8f3dc24c4336e9b80a933df6c79

Internal independent review, round R622-3, of kebag-logic/tsn-c-stack PR #22 for issue #21.
Head `bc68ad8f3577e8f3dc24c4336e9b80a933df6c79`, tree `6fc07b8c02bd3eef90f10b613b916a6b0abadb5d`,
one commit on round 2 `f3dc2ae5bad02aa05a504b43c207e8b304d2bed5`, source base `1a9f651cdf7846b8e10ac246a6ef6916960fbb92`.
Scope: the round-3 delta defined in issue comment 6115822525, plus re-confirmation of the round 1/2 acceptance at this head.

## Verdict

POSITIVE. No BLOCKER, MAJOR or MINOR finding is open. Four SUGGESTIONs are recorded below (one new, three retained); they do not affect the verdict.

The round-3 obligations hold at this head:

1. **One hosted assertion and one restore-only plant per cache field.** `tests/mutations.json` has exactly one plant for each of
   `published_bound`, `published_started` and `published_stream`. Each plant drops only that field's restore in `sink_reset`
   (`src/acmp.c:524-526`). Each plant's single killer is a distinct named `AcmpCore` test (`tests/test_acmp.cpp:2218`, `:2232`, `:2249`).
   In the local hosted campaign all three are CAUGHT, and each needle appears in the failure (`receipts/cache-plants.json`).
   Independently of the campaign driver, each plant applied alone to a disposable copy and run against the **full** 79-test hosted
   ACMP binary fails exactly its own named test and no other (`receipts/probes/drop-*-restore.json`). Hosted tests alone therefore catch
   each field's loss. RV32 smoke is not involved.
2. **The completeness gate.** `scripts/check_acmp_cache.py` takes the field list from the compiler tokens of `struct acmp_sink` in
   `include/acmp.h`, not from a fixed list. It runs as the mandatory `acmp-cache` gate in `scripts/validate.py:61`, which the CI
   workflow runs. Its own self-test refuses 30 controls and accepts a covered future field. I wrote 16 independent defect plants on
   disposable copies, plus 2 pass controls (`receipts/gate-probes.log`). The gate fails on each of: a future field declared only in the
   header; a future field restored but without a plant; a future field inside `#ifdef`; a future field in a multi-declarator; a future
   field whose plant shares the started assertion; a future field whose plant names a missing test; a removed bound plant; a bound plant
   sharing the started assertion, with the full or a shortened needle; an added non-hosted killer; a two-field substitution; a duplicated
   plant; a deleted started assertion message; a deleted started test; a removed source restore; and a plant retargeted to the header.
   It passes on unmodified head and on a fully covered future field. All 18 cases returned their expected rc.
3. **Core files unchanged.** `src/acmp.c` (blob `c5072a66`) and `include/acmp.h` (blob `49ac0407`) are byte-identical to round 2.
   So are `examples/rv32/smoke.c` and `tests/acmp_fake.hpp`. Against milan-fpga `09c7231e` copies (fetched read-only), the non-comment
   compiler tokens are equal in value, line and column: 7849/7849 source tokens and 1175/1175 header tokens (`receipts/token-compare.log`).
   All six same-flag RV32 GCC 16.2.0 object pairs are raw EQUAL: `-g0`, `-g`, `-O3 -DNDEBUG`, `-Os`, `-O2` with no hook, and `-Os -g3`
   (`receipts/object-compare.log`). The Release core object hash `5e2bacf2...` equals the `baremetal.py` Release `acmp.c` object.
4. **Gates.** Hosted CI run 38190657723 on this exact head executed both jobs; neither was skipped. `quality`: all 26 gates rc 0, with
   Ubuntu 24.04 clang-tidy 18. `bare-metal`: success. Locally, 24 of 26 Linux gates return rc 0, including mutation (342 CAUGHT /
   0 ESCAPED / 0 ERROR), coverage (adjusted 100%), traceability, test inventory (382 instances) and acmp-cache. RV32 Debug and Release
   pass with QEMU smoke (`receipts/rv32.log`, rc 0). Two local gates fail on host tools only:
   - **Clang sanitizer build:** rc 2. Pinned Clang 18 against the host's GCC 16 libstdc++ headers fails with an `stl_iterator.h`
     incomplete type. This is the host limit already ruled on in issue comment 6115181911. The hosted sanitizer job, which is the judge
     for this leg, passed.
   - **Static analysis:** rc 1. The host's unpinned clang-tidy 23 reports `optin.performance.Padding` on `struct acmp_sink`. The same
     tool gives rc 0 on the base and rc 1 at round 2 and at head, while CI's clang-tidy 18 gives rc 0. See S-2.

## Findings

| ID | Severity | Lenses | Location | Authority / evidence | Impact | Required outcome | Verification |
|---|---|---|---|---|---|---|---|
| R622-3-S-1 | SUGGESTION | Tests, Robustness | `src/acmp.c:525`; `tests/test_acmp.cpp:2249` | ACMP-10 "preserve the publication cache across restore/reset" (`docs/REQUIREMENTS.md:48`); the PORTING contract says sink reset preserves the last published triple. Probe `started-from-bound` (`s->published_started = published_bound;`) passes all 79 hosted ACMP tests (`receipts/probes/started-from-bound.json`). A 10-line witness kills it: bind stopped, restore a started record, open, expect a started publication (`receipts/witness-started-cross.log`: control rc 0, mutant rc 1). | The code at head is correct. A cross-wired restore would drop the publication of a restored start before the start is promised. Restore-only plants cannot reveal this, because a dropped started cache and a correctly preserved `false` cache are both zero. This fault class is outside the frozen round-3 acceptance, which specifies restore-only drops. | Optional: add a hosted assertion that restores a started record over a published stopped binding, and a cross-wired plant. | Rerun `scripts/witness_started_cross.py`; the mutant must fail a repository assertion. |
| R622-3-S-2 (retains R622-1 S-1) | SUGGESTION | Robustness, Docs | `scripts/static_analysis.py:11`; `include/acmp.h:353` | Host clang-tidy 23.1.1 reports excessive padding in `struct acmp_sink` from the port's added fields. The base is clean with the same tool (`receipts/static-analysis-history.log`). CI installs the unversioned Ubuntu 24.04 `clang-tidy` (18), which passes. | When the CI image's clang-tidy moves, the gate will fail on a struct whose layout acceptance item 2 freezes to upstream. | Optional: pin the clang-tidy major version in the workflow, or record a scoped suppression with its reason in `docs/STATIC_ANALYSIS.md` when the image moves. | Run `scripts/static_analysis.py` with clang-tidy 23 and expect rc 0 after the change. |
| R622-3-S-3 (retains R622-1 S-2) | SUGGESTION | Tests | `src/acmp.c:193` | Probe `guard-left-set` drops `a->in_port = false;` after `ports->publish`. It passes all 79 hosted ACMP tests (`receipts/probes/guard-left-set.json`), because in every current sequence a later port wrapper clears the flag. | No shipped defect. A future path that returns straight after publication would leave every entry refused, and no test would show it. | Optional: a focused hosted test with a plant for the clearing side of the publication guard. | Rerun the probe; a repository assertion must fail. |
| R622-3-S-4 (retains R622-1 S-3) | SUGGESTION | Docs | `scripts/baremetal.py:77` | The generated `smoke` label still reads "ACMP restore and rollback". `docs/VERIFICATION.md:136` names publication. | Generated RV32 result text understates what the smoke covers. It is not RESIDUE because it is generated output. | Optional: add publication to the label. | Inspect `results.json` from `baremetal.py`. |

No RESIDUE item.

## Lens ledger

| Lens | Status | Examined artifacts | Covering round | Exact head |
|---|---|---|---|---|
| Conformance | CLEAN | Acceptance items 1-6 as amended in 6115181911 and 6115822525; ACMP-10 row and origin in `docs/REQUIREMENTS.md` and `docs/TRACEABILITY.md`; PORTING publish contract; token equality with line and column against milan-fpga `09c7231e`; core blob identity with round 2 | R622-3 | bc68ad8f3577e8f3dc24c4336e9b80a933df6c79 |
| RTL (target and freestanding build; the repository has no HDL) | CLEAN | Six raw RV32 object comparisons; `baremetal.py` Debug and Release builds, links and QEMU smoke; core imports and unresolved symbols; Release object hash cross-check | R622-3 | bc68ad8f3577e8f3dc24c4336e9b80a933df6c79 |
| Robustness | CLEAN | `check_acmp_cache.py` logic and its failure modes (18 gate cases); 11 hosted fault probes plus control on `sink_reset` (restore drop, zeroed save, moved restore, cross-wire, all-drop), plus the publish-guard probe; host versus CI tool behaviour; S-1 to S-4 are SUGGESTIONs | R622-3 | bc68ad8f3577e8f3dc24c4336e9b80a933df6c79 |
| Tests | CLEAN | Two new tests and the stream test; three cache plants and their named needles; mutation campaign 342/0/0; per-plant full-suite isolation; registration and test inventory (382 instances); coverage 100% adjusted | R622-3 | bc68ad8f3577e8f3dc24c4336e9b80a933df6c79 |
| Docs | CLEAN | `docs/VERIFICATION.md` (342 plants, the new gate row and prose); regenerated `docs/TESTS.md` and `docs/TRACEABILITY.md` (line anchors 2218/2232/2249 checked; staleness gates pass); PORTING, ARCHITECTURE, REQUIREMENTS and CHANGELOG carried from round 2; privacy and licence gates | R622-3 | bc68ad8f3577e8f3dc24c4336e9b80a933df6c79 |

## Prior public findings at this head

I wrote the verdict and ledger above before reading any review comment on the PR. I then read only the finding IDs and finding rows of the earlier reports.

| Prior finding | Disposition at bc68ad8f | Evidence at this head |
|---|---|---|
| R622-1 F-1 (publish after timers in `finish`; stream cache dropped in `sink_reset`) | RESOLVED | `acmp-publish-after-timers` is CAUGHT by `A31SettlementIsPublishedBeforeTheTimerPort`, and `acmp-publish-reset-stream-cache` is CAUGHT by `A31StoreResetOfASettledSinkPublishesAMovedStream` (local campaign 342/0/0). The full-suite probe `drop-stream-restore` fails only that test. |
| R622-1 F-2 (ACMP-10 origin) | RESOLVED | `docs/REQUIREMENTS.md:40` and the generated `docs/TRACEABILITY.md` row name issue #21 and F-INT at `09c7231e` with the linked Milan and IEEE clauses. The traceability gate passes. |
| R622-1 F-3 (line positions and unnamed object difference) | RESOLVED | Tokens are equal in value, line and column against `09c7231e`. All six raw object pairs are EQUAL, including `-g` and `-Os -g3`. The PR body names every flag set. |
| R622-1 S-1, also R622-2 S-1 and R623-2 S-1 (newer-analyzer padding) | RETAINED as R622-3-S-2 (SUGGESTION) | Reproduced with clang-tidy 23. CI's clang-tidy 18 passes. |
| R622-1 S-2, also R622-2 S-2 and R623-2 S-2 (guard clearing side untested) | RETAINED as R622-3-S-3 (SUGGESTION) | Probe `guard-left-set` escapes the hosted ACMP suite. |
| R622-1 S-3, also R622-2 S-3 and R623-2 S-3 (RV32 smoke label) | RETAINED as R622-3-S-4 (SUGGESTION) | The label is unchanged at `scripts/baremetal.py:77`. |
| R622-2-F1 (dropping the started cache in `sink_reset` escapes every gate) | RESOLVED | Plant `acmp-publish-reset-started-cache` is CAUGHT by `A31StoreRestoreOfAStoppedRecordPublishesTheStop` with its needle. The full-suite probes `drop-started-restore`, `zero-started-save` and `move-started-restore-before-memset` each fail that test. The completeness gate covers the class, including future fields. |
| R622-2 S-4 (dropping the bound cache is caught only by RV32 smoke) | RESOLVED | Plant `acmp-publish-reset-bound-cache` is CAUGHT by the hosted `A31StoreResetOfABoundStoppedSinkPublishesItsWithdrawal`. The full-suite probes `drop-bound-restore`, `zero-bound-save` and `bound-from-started` fail that test, with no RV32 run involved. |
| R623-3-F-1 (per-field protection missing for bound and started) | RESOLVED | As for R622-2-F1 and R622-2 S-4. Each field has its own hosted assertion and restore-only plant, and `check_acmp_cache.py` enforces this (gate probes). |
| R623-2 P-1 (review-process finding; no source change requested) | Not a source finding; nothing at this head to verify | Per issue comment 6115822525, the manager answers it with a fresh external run. The disposition belongs to the manager and the external role. |

The new S-1 is a different fault class (cross-wired restore). None of the earlier reports raised it.

## Real limits

- No manager source bank exists at this head, and none is claimed. Source-head execution evidence is the author's published receipts,
  this review's local runs and the exact-head hosted CI run 38190657723.
- The local Clang sanitizer leg cannot build on this host (Clang 18 against GCC 16 libstdc++). Only hosted CI executed it.
- The local static-analysis leg used host clang-tidy 23, not CI's clang-tidy 18. No clang-tidy 18 binary was available locally.
- The `graphs` gate (Mermaid rendering) was not run locally because the renderer is not installed here. Hosted CI ran it with rc 0. The round 3 change touches no diagram.
- RV32 smoke ran under QEMU only. Physical calibration was NOT RUN. Field skips and QEMU execution are not hardware proof and establish no target timing.
- R622-2's `probes.sh`, `witness2.sh` and RV32 plant controls were not re-executed in this review. Independent probes written for
  this review cover the same faults: the dropped started cache and the dropped stream cache.
- The milan-fpga reference copies were fetched read-only from `09c7231e` and were not compared against any other milan-fpga revision.

## Pending manager duties

- Build and validate the current-dev merge candidate at the merge turn (base `1a9f651c`, live dev `c20c85bd`), run the builder and native banks, and link the receipts.
- Hosted and act acceptance, and the second positive review.
- The merge commit, and the milan-fpga #697 pin to the PR head.
- The PR body still says "Relates to #21". The manager decides the closing keyword at merge.

## Receipts

Under this packet: `receipts/` (logs, rc values and JSON) and `scripts/` (portable drivers: `toolenv.sh`, `token_compare.py`,
`object_compare.sh`, `probe.py` with `probes.json`, `gate_probes.py`, `witness_started_cross.py`, `run_bg.sh`).
After all probes the clone was verified at exact head (`receipts/restore-verify.log`): worktree and index equal HEAD, 77 entries all mode 100644,
every tracked file hashes to its HEAD blob, no untracked or ignored files, and no submodule gitlinks (none are required in this repository).

R622-3 FINISHED
