[R622] NEGATIVE - exact head 2dcbe91ead981591d5bfb652f6616f6edb325875

# R622-1 independent review: tsn-c-stack issue #21 / PR #22

- Role: internal independent reviewer, cleared context, own detached clone.
- Exact head: `2dcbe91ead981591d5bfb652f6616f6edb325875`, tree `977d677410f6d44f4b54301a10273f41600c3edc`, single parent `1a9f651cdf7846b8e10ac246a6ef6916960fbb92` (the commit milan-fpga #697 pins).
- Reference: milan-fpga dev `09c7231eca343607c97c0d66abebb2553688712c` (merge of milan-fpga PR #704; F-INT commits `5a50b2045`, `7c583daac`). The F-INT parent's `acmp.c`/`acmp.h` blobs equal the import revision `6aa25dec` blobs (`36d929ac…`, `e5152daa…`), so `6aa25dec` is the baseline reference copy.
- Scope authorities: issue #21 body (acceptance 1-6), assignment comment 6115109360, STOP 6115175677, amendment 6115181911, REVIEW READY 6115338952; CONTRIBUTING.md, README.md, docs/CODING_STANDARD.md, docs/IMPORT.md, docs/REQUIREMENTS.md, docs/PORTING.md, docs/VERIFICATION.md.
- The repository has no AGENTS.md at this head.

## Verdict summary

The core port is right. `src/acmp.c` and `include/acmp.h` have exactly the reference's non-comment tokens (7849 and 1175). Two independent methods confirm this: raw Clang 18 lexing and GCC comment removal. Every code line the PR adds is byte-identical to F-INT's. The PR deletes no baseline line, and no other core file changes. The six F-INT test cases and the fake are ported with identical code. All 338 mutation plants are caught. Hosted CI at the exact head passed all 25 Linux gates, including the Clang 18 sanitizer leg, and both RV32 configurations.

Three MINOR findings remain open, so the verdict is NEGATIVE:

- **F-1:** two documented parts of ACMP-10 are not caught by any gate.
- **F-2:** ACMP-10's traceability origin is wrong.
- **F-3:** the new line layout breaks the repository's line-position invariant. It also produces a same-flag RV32 object difference under the repository's own Debug flags, which the public record does not name.

## Findings

### F-1 MINOR: Two ACMP-10 contract clauses are unverified; observable defects escape every gate
- **Lenses:** Tests, Conformance.
- **Where:**
  - `src/acmp.c:486` (`publish(a)` first in `finish`) and `src/acmp.c:522` (stream cache kept across `sink_reset`).
  - The contract text: `docs/PORTING.md:189` ("publishes first in `finish`, before timers, admission, persistence and change notification"), `docs/PORTING.md:203` ("Sink reset and rollback preserve the last published triple"), `docs/ARCHITECTURE.md:56`, `docs/requirements.json:178` and `docs/REQUIREMENTS.md:33` (ACMP-10, verification method test).
  - `scripts/check_port_contracts.py:264` makes "before timers" a required contract phrase.
- **Authority:** CONTRIBUTING.md says "A protocol change updates its requirement, tests and traceability. A regression needs a failing assertion and a runnable planted defect." ACMP-10 is declared test-verified.
- **Evidence:**
  - `receipts/probes.json` / `receipts/probes.txt` and `receipts/witness.txt`, produced by `scripts/probe.py` and `scripts/witness.sh`.
  - Ten disposable faults plus one control were run on exported copies of the head tree (GCC hosted suite). The RV32 smoke gate was then run on every hosted escape.
  - Two faults pass the full hosted suite (all A31 cases included) and both RV32 smoke configurations:
    - **`finish-publishes-after-timers`:** `rearm(a); publish(a); admit(a);`.
    - **`reset-drops-stream-cache-only`:** `published_stream` is not restored in `sink_reset`.
  - Neither fault is equivalent. Two disposable witness tests pass on the unmodified head and each fails on exactly its fault:
    - After a settling PROBE_TX_RESPONSE, the publish call must precede the timer-port call.
    - After a store reset of a settled sink, the next `acmp_open` must report `stream_moved=true`.
  - The repository's mutation table has no plant for either fault. `acmp-publish-reset-cache` drops all three cache fields and is caught only through the bound field.
- **Impact:**
  - An integrator relying on the documented order could see the timer port before publication with no gate failing.
  - Similarly, `stream_moved=false` could be reported for a withdrawn settled stream after a store reset or roll-back.
  - The requirement record and porting contract claim more than the verification establishes.
- **Required outcome:** add assertions that fail on these two defects, each with a planted defect in `tests/mutations.json`, and regenerate TESTS.md and TRACEABILITY.md. The witnesses in `scripts/witness.sh` are a sufficient model. These are tests, not core changes, so the core stays token-identical. The alternative is to narrow the contract text, the ACMP-10 record and the enforced phrase so they claim only what is tested.
- **Verification:** re-run `scripts/probe.py` and `scripts/witness.sh` against the new head. Both faults must be CAUGHT by a named assertion message. The mutation gate must report every plant caught, with no ESCAPED and no ERROR.

### F-2 MINOR: ACMP-10 is traced to the import baseline, which predates F-INT
- **Lenses:** Conformance, Docs.
- **Where:**
  - `docs/TRACEABILITY.md:24` (generated) gives ACMP-10's Origin as "[Import baseline](REQUIREMENTS.md)".
  - `docs/REQUIREMENTS.md:33` places ACMP-10 in the first table. `docs/REQUIREMENTS.md:9-14` declares that table to "trace to the requirements-port assignment" (issue #14) with "source snapshot … milan-fpga dev at 5603c353", and says "The first table retains the import baseline".
  - `scripts/traceability.py:116` prints "Import baseline" for any record without an `origin`.
- **Evidence:** `git merge-base --is-ancestor 09c7231e 5603c353` is false, and `5603c353:sw/firmware/ctrl/acmp/acmp.h` contains no `publish`. ACMP-10 actually originates from milan-fpga #665 F-INT (`09c7231e`, commits `5a50b2045` and `7c583daac`) through tsn-c-stack #21.
- **Impact:** the generated matrix and the requirements document give a false provenance for a new requirement. This is a traceability claim, not wording only.
- **Related cleanup:** in the same row, the clause cell's Milan and IEEE references are unlinked, and they are less specific than `docs/requirements.json` ("5.5.3.5.18 step 4 and 5.5.3.5.36 step 1"). Other rows follow the "Link each standard separately" convention.
- **Required outcome:**
  - Record ACMP-10's real origin (issue #21 / milan-fpga F-INT at `09c7231e`) so the generated Origin cell names it. For example, use a separately labelled row or table with its own origin entry, or an origin record the generator resolves.
  - Do not present ACMP-10 as part of the `5603c353` import baseline.
  - Link the clause cell's references as `docs/requirements.json` cites them.
  - Regenerate TRACEABILITY.md.
- **Verification:** `python3 scripts/traceability.py --selftest …` passes. The ACMP-10 row's Origin names the F-INT source, and REQUIREMENTS.md no longer claims the `5603c353` snapshot for it.

### F-3 MINOR: The new layout breaks the core line-position invariant and leaves a same-flag object difference unnamed
- **Lenses:** Conformance, RTL (implementation and compiled objects), Docs.
- **Where:**
  - The added lines in `src/acmp.c` (hunks at 185, 282, 483, 511) and `include/acmp.h` (hunks at 303, 358).
  - `docs/IMPORT.md:84`: "Core line positions stay fixed to preserve assertion locations and coverage instrumentation."
  - The PR body: "Same-flag RV32 objects are byte-identical at both tested optimization levels."
- **Authority:**
  - Amendment 6115181911 requires token identity "except for layout differences that already existed at `1a9f651c`".
  - It also says: "Build both copies' objects for RV32 freestanding with the same flags and show they are equal, or name every difference and its cause."
- **Evidence:** `receipts/object-compare.txt`, produced by `scripts/object_compare.sh`. Both copies are compiled in the same absolute directory with the same `wire.h` and port headers, using RV32 GCC 16.2.0 with `-march=rv32i -mabi=ilp32 -ffreestanding -fno-builtin -nostdinc -std=c11 -Wall -Wextra -Werror`.
  - **Baseline control (`6aa25dec` copy vs `1a9f651c`):** all six flag sets are byte-equal, including `-g` and `-Os -g3`. The files are line-for-line aligned: 1257/1257 and 464/464 lines.
  - **Head (`09c7231e` copy vs `2dcbe91e`):** these sets are byte-equal:
    - `-g0` (−O0), the method IMPORT.md documents;
    - `-O3 -DNDEBUG`, which equals the RV32 gate's Release `acmp.c` object `5e2bacf2…`;
    - `-Os`;
    - `-O2`.
  - **Head with `-g`:** the repository's RV32 Debug configuration flags (`baremetal.py` Debug compile command) give different objects. The `-Os -g3` set also differs.
  - **What differs:** only `.debug_info`, `.debug_abbrev`, `.debug_line` and, for `-g3`, `.debug_macro`. The objects are identical after `--strip-debug`.
  - **Cause:** the PR did not keep F-INT's comment lines as blank lines, which was the import's line-preserving convention. Line shifts relative to the reference copy are +2 / 0 / +1 / +3 / +4 across the file. `acmp.c` has 1290 lines against 1294, and `acmp.h` has 471 against 494.
  - **Public record:** the PR body does not name the flags of "both tested optimization levels" or this difference. The cited public evidence tree `milan-fpga/tree/2dd8faee…/review-evidence/tsn21-r1` returns 404, and the commit is not fetchable, so no published receipt names it.
- **Impact:**
  - The line-position property that held at `1a9f651c`, and that IMPORT.md records, no longer holds for ACMP.
  - A same-flag object comparison under the repository's own RV32 Debug flags fails, and the public record does not explain why.
  - Firmware binary images and `-g0` objects are unaffected.
- **Required outcome:** either option is enough.
  - (a) Restore line alignment by padding with blank lines as the baseline did, so all six flag sets are byte-equal again.
  - (b) Publish the object comparison with its exact flags, naming the debug-section difference and its cause as above, and have the manager confirm that `docs/IMPORT.md:84` does not bind later changes.
- **Verification:** `scripts/object_compare.sh` reports raw EQUAL for every set, or the published comparison names every differing set, section and cause.

## Residue
None recorded. The ACMP-10 clause-link inconsistency is folded into F-2 because it touches a clause citation.

## Suggestions (no effect on the verdict)
- **S-1 Robustness/Tests: newer clang-tidy reports padding in `struct acmp_sink`.**
  - The host analyzer (clang-tidy 23.1.1, header filter on by default) fails at head with `clang-analyzer-optin.performance.Padding` at `include/acmp.h:330`: 32 padding bytes, above the 24 allowed. The sink grows from 240 to 256 bytes on both x86-64 and RV32.
  - The baseline passes on the same host. Hosted clang-tidy 18 passes only because it suppresses header diagnostics: its log shows "Suppressed 337 warnings (337 in non-user code)".
  - The field order is fixed by token identity with F-INT, so this PR cannot fix it.
  - Recommended follow-up: reorder upstream in milan-fpga, or pin and document the header filter or a suppression in `scripts/static_analysis.py` / `docs/STATIC_ANALYSIS.md` before CI moves past clang-tidy 18.
  - Receipts: `receipts/local-head-validation/static-analysis*.log`, `receipts/baseline/static-analysis.log`, `receipts/hosted/static-analysis.log`.
- **S-2 Tests: the clearing side of the `p_publish` guard is not tested.**
  - A fault that leaves `a->in_port` set after the publish call escapes the hosted suite and the RV32 smoke (`receipts/probes.json`, `guard-left-set`).
  - It is nearly equivalent in reachable sequences, because a later port call in the same entry clears the flag. The other port wrappers have the same pattern at baseline.
- **S-3 Docs: stale RV32 smoke label.** The summary label at `scripts/baremetal.py:77` still says "ACMP restore and rollback". It could add publication to match `docs/VERIFICATION.md:135`.

## Lens application

### Conformance
- **Acceptance 1:** met. The head's parent is `1a9f651c` and the branch has one commit.
- **Acceptance 2 (amended):**
  - Token identity: reproduced (`receipts/token-compare.txt`). Head vs reference gives 7849/7849 and 1175/1175 tokens, EQUAL by both methods. The baseline control is EQUAL too. As a negative control, the base-to-head and reference-to-reference pairs both report DIFFER at the same first token, `p_publish`.
  - Code hunks: byte-identical to F-INT's (`receipts/fint-acmp.*.diff` vs `receipts/head-acmp.*.diff`). The head adds 40 lines to the core files and deletes none.
  - Comments: these are `// REQ: ACMP-10` only, the one form docs/CODING_STANDARD.md:3 allows besides SPDX and standard references. F-INT's meaning is carried to `docs/PORTING.md:173-204`, which covers the port, its call order, "published before promised" and the `acmp_set_started` return order, and to `docs/ARCHITECTURE.md:55-59`. The comment gate passed locally with pinned Clang 18.1.3 and on hosted CI.
  - Objects: see F-3.
- **No other core change:** `git diff --stat 1a9f651c..HEAD -- src include` lists only `acmp.c` and `acmp.h`.
- **Behaviour vs. F-INT:** identical code, so no new behaviour.
- **Requirements:** the ACMP-10 clause citations are plausible: Milan v1.2 5.3.8.7, 5.5.3.5.18 step 4 and 5.5.3.5.36 step 1, and IEEE 1722.1-2021 7.4.35/7.4.36. Its provenance is wrong (F-2) and part of its contract is unverified (F-1).

### RTL (implementation and compiled objects)
- I read `publish`, `p_publish`, `transmit`, `finish`, `sink_reset`, `acmp_poll`, `acmp_open`, `acmp_restore_binding`, `acmp_restore_rollback` and `acmp_set_started`.
- Every frame goes through `transmit` (`src/acmp.c:285`), which publishes before both the send and the owed path. `acmp_poll` retries only frames that were published when queued. `finish` publishes first. Restore and roll-back publish nothing.
- RV32 objects are byte-equal for `-g0`, `-O2`, `-Os` and `-O3`, but not under `-g`/`-g3` (F-3).
- RV32 gate at head: Debug and Release rc 0, with no unresolved symbols (`receipts/local-head-rv32/results.json`). Core imports are only `memcpy`, `memset`, `__mulsi3`/`__umodsi3` and the assertion hooks.

### Robustness
- Re-entry from the publish callback is refused and counted. This is tested by A31ACallBackFromThePublishPortIsRefused, which the `acmp-publish-unguarded` plant confirms.
- The publish loop is bounded by `n_sinks`. The cache persists across `sink_reset`. The zero triple is the initial cache value.
- No heap, OS or new dependency is added. The boundary and dependency gates pass.
- The struct size growth and analyzer exposure are covered in S-1.
- No robustness defect is attributable to the change. The test gap on reset-cache preservation is recorded under F-1 (Tests/Conformance).

### Tests
- The six F-INT cases and the fake additions are code-identical to F-INT, comments excluded (`receipts/test-port-compare.txt`: 145 and 22 non-comment lines IDENTICAL).
- The 14 new plants are each caught by their named assertion: locally 338 CAUGHT / 0 ESCAPED / 0 ERROR, and the same on hosted CI.
- Coverage is 767/767 lines and 362/362 branches for `acmp.c`, and the ratchet was raised, not lowered.
- RV32 smoke codes 30-45 are unique and catch three faults the hosted suite misses: publication after admission, after persistence, and dropping only the bound cache.
- Two faults escape everything (F-1).

### Docs
- Read the docs diff in full:
  - **PORTING:** callback row, ordering contract and public fields.
  - **Other docs:** ARCHITECTURE, REQUIREMENTS/requirements.json, TESTS (anchors L2052-L2194 verified against the source), TRACEABILITY and VERIFICATION (338 plants; smoke table).
  - **Unchanged files:** CHANGELOG.md and IMPORT.md.
- The PORTING statements match the code paths I read.
- The traceability origin is wrong (F-2).
- The object-equality claim and the IMPORT.md:84 invariant are covered by F-3.
- CHANGELOG.md has no entry for the new required callback, although each earlier PR added one. Recommended (wording only): add under "Unreleased": "- Add the required ACMP `publish` port from milan-fpga F-INT. Publish each changed bound, started and settled stream-ID triple before new frames and first at completion ([published before promised](docs/PORTING.md#acmp-callbacks-and-public-fields), ACMP-10). Integrators must supply the callback."

## Gate execution at this head

| Context | Result | Receipt |
|---|---|---|
| Local `validate.py --jobs 3 --graphs` (GCC 16.2.1, pinned Clang 18.1.3, pinned GoogleTest 1.14.0) | 22 of 24 gates rc 0, including comments, privacy, traceability, gcc-test, coverage, mutation 338/338 and mutation controls. `clang-sanitizers-build` rc 2: errors only in host libstdc++ 16 headers, and the baseline reproduces this. `static-analysis` rc 1: host clang-tidy 23 only, see S-1. | `receipts/local-head-validation/` |
| Local baseline `1a9f651c` sanitizer build, same toolchain | rc 2, errors only in host C++ headers | `receipts/baseline/sanitizer-error-files.txt` |
| Local `baremetal.py --jobs 4` | rc 0, Debug and Release | `receipts/local-head-rv32/` |
| Hosted run 38186240742 (push event, exact head) job `quality` | success; all 25 gates rc 0, including `clang-sanitizers-build`/`-test` (Clang 18.1.3, 7/7 tests), static analysis, mutation 338/338 and graphs | `receipts/hosted/` |
| Hosted run 38186240742 job `bare-metal` | success; Debug and Release rc 0 | `receipts/hosted/rv32-results.json` |

- Hosted `quality` executed every gate; no job or step was skipped.
- I saw only a push-event run. A pull_request-event run at this head was not observed.
- No manager source bank runs at this head, and none is claimed or inferred here.

## Reviewer-owned ledger

| Lens | State | Examined artifacts | Covering round | Exact head |
|---|---|---|---|---|
| Conformance | UNCLEAN (F-1, F-2, F-3) | issue #21 acceptance, assignment and amendment; `src/acmp.c`, `include/acmp.h` vs milan-fpga `09c7231e` and `6aa25dec`; token comparison; ACMP-10 records; IMPORT.md | R622-1 | 2dcbe91ead981591d5bfb652f6616f6edb325875 |
| RTL | UNCLEAN (F-3) | core code paths listed above; same-flag RV32 objects in six flag sets plus baseline control; RV32 gate objects and imports | R622-1 | 2dcbe91ead981591d5bfb652f6616f6edb325875 |
| Robustness | CLEAN | re-entry guard, reset and roll-back cache, owed-queue path, bounded loop, boundary and dependency gates, analyzer exposure (S-1) | R622-1 | 2dcbe91ead981591d5bfb652f6616f6edb325875 |
| Tests | UNCLEAN (F-1) | `tests/test_acmp.cpp`, `tests/acmp_fake.hpp`, `tests/mutations.json` (14 plants), coverage ratchet, `examples/rv32/smoke.c`; 10 independent probes plus 1 control; 2 witness tests | R622-1 | 2dcbe91ead981591d5bfb652f6616f6edb325875 |
| Docs | UNCLEAN (F-2, F-3) | PORTING, ARCHITECTURE, REQUIREMENTS, requirements.json, TESTS, TRACEABILITY, VERIFICATION, IMPORT, CHANGELOG, PR body | R622-1 | 2dcbe91ead981591d5bfb652f6616f6edb325875 |

## Prior public review findings
- At the end of my independent pass, PR #22 had no review objects, no inline review comments and no earlier review findings. Its only comments were the two review-start notices and a concurrent same-round reviewer verdict.
- I opened that verdict only after writing this verdict and ledger; see the addendum below. No earlier finding needs resolving or retaining.

## Real limits
- **Sanitizer leg:** the local Clang 18 sanitizer build cannot compile against this host's libstdc++ 16 headers, at baseline as well as head. The hosted Clang 18 sanitizer job is the judge for that leg, and it passed.
- **Local static analysis:** this uses host clang-tidy 23.1.1 and cppcheck 2.22.0, not the hosted versions (clang-tidy 18).
- **RV32 toolchain:** local RV32 used `riscv64-elf-gcc` 16.2.0 and host QEMU. Hosted RV32 used the Ubuntu 24.04 toolchain, so object hashes differ between the two. My object comparisons always use one compiler for both sides.
- **Public evidence:** the evidence tree `milan-fpga@2dd8faee…/review-evidence/tsn21-r1` was unavailable (HTTP 404, commit not fetchable). I relied on hosted CI artifacts for exact-head execution evidence.
- **Pin check:** I could not find milan-fpga #697's pin-check implementation at its public PR head `adb93604`. The token comparison is my own (Clang raw lexer plus GCC `-fpreprocessed`), not that script.
- **Not run (out of scope):** full parent, PP, gPTP, Yosys or builder banks; Docker/act; hardware. Physical calibration NOT RUN. RV32 QEMU smoke success is not hardware or timing proof.
- **Clone integrity:** all probes ran on exported copies under the packet's scratch directory. The review clone is unchanged: HEAD and tree as above, index and worktree clean, every tracked blob re-hashed equal, no gitlinks in this repository (`receipts/clone-integrity.txt`).

## Pending manager duties
- Validate the current-dev merge candidate (source base `1a9f651c`, live milan-fpga dev `09c7231e`) with the builder and native banks at the merge turn, and link the receipts.
- Own hosted/act acceptance. That includes confirming whether a pull_request-event run is required, and reading the hosted sanitizer leg (passed in run 38186240742).
- Get two independent positive reviews and a merge commit into main (acceptance 6), then pin milan-fpga #697 to the merged head.
- Rule on F-3(b) if that option is chosen: whether `docs/IMPORT.md:84` binds later changes.
- Decide the S-1 follow-up (analyzer header filter or padding) before CI moves past clang-tidy 18.

## Addendum: concurrent same-round review
I wrote this after the verdict, findings and ledger above were fixed. They are unchanged.

- **What it is:** the external reviewer's same-round verdict (PR #22 comment 6115496993) is POSITIVE with no open findings. Nothing in it needs resolving or retaining here.
- **Where it agrees:**
  - Token counts: 7849/1175 at head and 7586/1137 at baseline.
  - The `-g0`, `-Os` and `-O3` RV32 object hashes are identical to mine: `43c1af51…`, `825f6f3e…`, `5e2bacf2…`.
  - The hosted evidence and the unavailable evidence link.
- **Where it differs:**
  - Its object comparison used only `-g0`, so the `-g`/`-g3` debug-section difference in F-3 is outside what it measured.
  - It reports that moving completion publication after timers fails "in its disposable control". That matches my witness, which fails under the same fault. It is not evidence that a repository test or plant catches the fault. My F-1 probe ran the repository's full hosted suite and both RV32 smoke configurations, and the fault passed every one.
  - It does not discuss the ACMP-10 origin (F-2).
- **Verdict:** my verdict stays NEGATIVE on F-1, F-2 and F-3.

R622-1 FINISHED
