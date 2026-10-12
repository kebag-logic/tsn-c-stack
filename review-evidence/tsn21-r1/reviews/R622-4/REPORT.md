[R622] POSITIVE - exact head 405dc68310a18f669049ffc10cc23eef7300dcff

# R622-4: internal independent review, issue #21 / PR #22 (delta round 4)

- Reviewed head: `405dc68310a18f669049ffc10cc23eef7300dcff`, tree `68f17411e26213c2cef4afb80f2ff2cb9eb4d457`, parent `bc68ad8f3577e8f3dc24c4336e9b80a933df6c79` (one commit). Source base `1a9f651cdf7846b8e10ac246a6ef6916960fbb92`.
- Scope: the round-4 ruling (issue #21 comment 6116110744). Item 1 is R623-4-F1: identity-based cache completeness. Item 2 is the integration branch.
- Integration PR #23: `integrate-21` at `3c9ca52fc44b4a37e11149392363686f0ea426e0`. First parent is main `98dc9e3076714bebe113982ee18c3c1c496cf3c9`, second parent is `405dc683`. Its verdict is stated separately below.
- Reconstruction order: CONTRIBUTING.md and README. The repository has no AGENTS.md. Then docs (VERIFICATION, PORTING, STATIC_ANALYSIS); issue #21 body with the A10 assignment, the STOP ruling (token identity amendment) and the round 2/3/4 rulings; the round-4 diff and history; the author's published round-4 receipts (`review-evidence/tsn21-r1/author-r4` at `380d86e7`); hosted job logs at both heads.
- Prior review comments and other reviewers' material were not read before this verdict and ledger were written.

## Verdict

**PR #22 at `405dc683`: POSITIVE.** Every point the round-4 brief asked me to confirm holds at this head, by my own execution:

1. The completeness gate compares **assertion identities** as (owning test, file, line, column), and keeps them through helper and callback traversal. It does not compare message literals.
   - `scripts/check_acmp_cache.py:59-64` takes `message.identity`.
   - `scripts/assertion_messages.py:105-116` builds the identity from the assertion macro token, with the owner passed down into helpers (`:101`).
2. **R623-4's split-message future-field case is refused, specifically for shared ownership.**
   - In memory, my probes P1–P4 cover a direct assertion, a lambda, one literal holding both needles, and a helper called by the owning test. Each returns exactly `published_future: assertion is shared with another cache field`.
   - In a compiling probe of my own (a helper-hosted shared assertion in the real `tests/test_acmp.cpp`), the gate returns rc 1 with that exact diagnostic under plain and `-O` Python. In the same tree, the needle audit passes and the hosted restore-only campaign catches all five plants. So only the identity gate detects the sharing (`receipts/helper-compiling-probe.*`).
   - The repository's own compiling controls ran at both heads: shared gate rc 1 and separate gate rc 0, plain and `-O`. Both control campaigns were 5/5 CAUGHT (`receipts/{port,integ}/cache-controls/`).
3. **A future field with its own assertion passes.** This holds for P5 (separate assertions on the same line), for P6 (its own helper), and for the repository's compiling "separate" control, which ran its gate plain and `-O` (rc 0) and its campaign (5/5 CAUGHT).
4. **Every per-field hosted plant stays caught.** In the full campaign at `405dc683`, `acmp-publish-reset-{bound,started,stream}-cache` and `acmp-publish-reset-cache` are all CAUGHT; the summary is 342 CAUGHT, 0 ESCAPED, 0 ERROR.
5. **The core stays token-identical and all six raw object pairs are equal.**
   - My independent comparison against milan-fpga `09c7231e` (blobs `32951625…`/`b8a744da…`, verified by `git hash-object`) gives `src/acmp.c` 7849/7849 tokens and `include/acmp.h` 1175/1175 tokens, with spellings, lines and columns equal.
   - Six RV32 freestanding flag sets (debug-g0, debug `-g`, release `-O3 -DNDEBUG`, os, o2-noassert, os-g3) give raw EQUAL objects.
   - A one-statement planted difference makes all six DIFFER (sensitivity control).
   - The round-4 commit touches no core file.
6. **The gate's selftest detects regressions of the fix.** Eight planted regressions of the gate itself were all refused by its own selftest: compare literals, drop the column, drop line and column, drop the owner, per-literal identity, lose the helper owner, disable the ownership check, never record owners.
7. **The refactor is behaviour-preserving for every other consumer.** `inventory()` returns identical literal maps before and after the refactor for all 6 test files (573 literals). This covers the needle audit and mutation grading.

**Integration PR #23 at `3c9ca52f`: POSITIVE (stated separately; not this verdict line's subject).**
- **Parents:** first parent is main `98dc9e3`, second parent is `405dc683`. The port branch was not merged with main.
- **Conflicts:** a mechanical `git merge-tree` reproduction gives exactly 8 conflicted files. Each resolution keeps both sides:
  - `REQUIREMENTS.md`: main's "ADP input validation" heading and the ACMP publish section.
  - `VERIFICATION.md`: 345 core + 3 generated = 348 plants.
  - `examples/rv32/smoke.c`: main's prefix, ADP discovery smoke and entity calls, and the port's ACMP section verbatim, with the ACMP-10 tag.
  - `requirement_records.py`: `LOCAL_ORIGINS` and `ADDITIONAL_ORIGINS` together, with `origin_link` extended.
  - `traceability.py`: main's `origin_link`.
  - `coverage.ratchet`: acmp from the port, adp from main.
  - `mutations.json`: an exact record-level union (330 + 18 = 348). No record was altered or dropped and no extra record was added.
  - `TRACEABILITY.md`: generated.
- **Non-conflict edits:** besides the conflict resolutions, only three files differ from the mechanical merge:
  - `docs/TESTS.md` is regenerated: one inventory row gains ACMP-10.
  - `examples/entity_roundtrip.c` and `tests/test_entity.cpp` carry the semantic resolution. `ports->publish` is called unconditionally (`src/acmp.c:192`), so main's new positional `acmp_ports` initializer needs the callback. The merge supplies it, checks one publication per restored sink at open (codes 70–72), and tags ACMP-10. This is disclosed in the PR #23 body.
- **Generated documents are current:** rerunning `traceability.py --write`, `test_inventory.py --write` and `entity_yaml.py --examples` on a copy leaves 0 tracked changes.
- **Gates at `3c9ca52f`:**
  - My run: 27 of 28 Linux gates rc 0, plus RV32 Debug/Release rc 0 with smoke including "four generated entity round trips". The mutation campaign was 348 CAUGHT, 0 ESCAPED, 0 ERROR; entity selftests were 196 OK; coverage was 100% after exclusions in every ratcheted file.
  - The one local failure is `static-analysis`: a host-only analyzer version difference, explained under Real limits. At the pinned analyzer version, the hosted quality job ran all 28 gates rc 0, static-analysis included, as did hosted bare-metal Debug/Release.
- **Unchanged ACMP core:** `src/acmp.c` and `include/acmp.h` at the merge are byte-identical to `405dc683`.

## Findings

No open BLOCKER, MAJOR, MINOR or RESIDUE at `405dc683`, nor on the integration head.

| ID | Severity | Lenses | Location | Evidence | Impact | Outcome / verification |
|---|---|---|---|---|---|---|
| R622-4-S1 | SUGGESTION | Tests, Robustness | `scripts/assertion_messages.py:107`; `scripts/check_acmp_cache.py:59-64` | Probe P10 (`receipts/cache-gate-probes.log`): one helper assertion streaming both fields' literals, reached from two *different* owning tests (one per field), is accepted. The ruled identity includes the owning test, so the two identities differ. | This conforms to the round-4 ruling ("the test that owns the assertion and its definition location") and to VERIFICATION.md. A future field could still be covered by the same assertion definition as another field through a second test. | Optional. Either also refuse two cache fields whose identities share (file, line, column), or state this boundary in VERIFICATION.md. Verify by rerunning P10, which should then be refused or documented. |
| R622-4-S2 (retains R622-3-S-2 / R622-1 S-1) | SUGGESTION | Robustness, Docs | `include/acmp.h:353` (`struct acmp_sink`); `scripts/static_analysis.py` | A newer host clang-tidy reports `clang-analyzer-optin.performance.Padding` (32 bytes) on `acmp_sink` at `405dc683` but not at `1a9f651c` (`receipts/static-analysis-host-tidy23.log`). The pinned clang-tidy 18 (CI image, `Setting up clang-tidy (1:18.0-59~exp2)`) passes at both heads. | No defect at the pinned toolchain. The field order is fixed by token identity with milan-fpga, so moving the analyzer forward will fail this gate. | Optional. When the analyzer pin moves, add a location-tied suppression with its rationale to STATIC_ANALYSIS.md, or reorder upstream first. Verify by running the static-analysis gate with the new analyzer. |

## Lens evidence

- **Conformance:**
  - Round-4 ruling item 1: identities include owner and definition location through helpers, no literal comparison, the R623-4 counterexample is a mandatory negative control, the separate-assertion counterpart passes, and the VERIFICATION.md claim is enforced. Each part was checked by code reading and by probes P1–P10, the compiling probe and the gate mutants.
  - Item 2: lineage, merge parents and resolutions, as above.
  - Acceptance 2 as amended: token identity and same-flag object equality, checked independently.
  - Acceptance 4: both targets at both heads.
  - Acceptance 6 / CONTRIBUTING: every commit subject is one line, with no body or trailers.
  - ACMP-10 provenance is unchanged since round 3.
- **RTL (applied to the C core and its freestanding objects; no HDL is in scope):** the round-4 commit leaves `src/acmp.c` and `include/acmp.h` unchanged, with tokens, positions and six raw RV32 object pairs equal to F-INT. The RV32 Debug/Release whole-archive link, ABI/import checks and QEMU smoke pass at both heads, locally and hosted.
- **Robustness:**
  - The gate fails closed on a missing test or needle, an ambiguous helper, an unbalanced source and a timeout. Identity columns use the tokenizer's byte offsets, consistent with `data`.
  - `acmp_cache_controls.py` selects every fragment exactly once, overwrites its copy each run and checks complete campaign results.
  - The refactor preserves `inventory()` output. Gate decisions do not rely on `assert` (`-O` controls).
- **Tests:**
  - At `405dc683`: 26 Linux gates. 25 return rc 0 locally; static-analysis is rc 0 hosted at the pinned analyzer (see S2). RV32 Debug/Release rc 0.
  - 7/7 ctest binaries pass under GCC and under Clang sanitizers. Coverage is 100% after exclusions. Mutations: 342 CAUGHT, 0 ESCAPED, 0 ERROR. The gate reports "33 missing or invalid coverage controls refused".
  - The reviewer-owned negative controls described above were added.
- **Docs:**
  - VERIFICATION.md rows 30 and 161–176 match the implementation: the command line and argparse agree, the identity definition is as stated, controls (direct, helper, nested callback, optimized) exist, and both compiling variants run campaigns.
  - The PR #22 body names the round-4 change and the gates. The PR #23 body discloses the entity example adaptation.
  - The provenance URL in `acmp_cache_controls.py` resolves to the immutable probe (blob `7945a6bf`).

## Reviewer-owned ledger

| Lens | Status | Examined artifacts | Covering round | Exact head |
|---|---|---|---|---|
| Conformance | CLEAN | issue #21 acceptance + A10 rulings (assignment, STOP amendment, rounds 2–4); `check_acmp_cache.py`, `assertion_messages.py`, `acmp_cache_controls.py`, `validate.py`; merge `3c9ca52f` vs merge-tree; `receipts/token-compare.log`, `object-compare*.log`, `mutations-union-audit.json` | R622-4 | 405dc68310a18f669049ffc10cc23eef7300dcff |
| RTL | CLEAN | `src/acmp.c`, `include/acmp.h` vs milan-fpga `09c7231e` (tokens, positions, 6 raw RV32 objects + sensitivity control); RV32 Debug/Release local and hosted (`receipts/{port,integ}/rv32.log`, `hosted-quality-excerpt.log`) | R622-4 | 405dc68310a18f669049ffc10cc23eef7300dcff |
| Robustness | CLEAN | gate fail-closed paths; `receipts/gate-mutants.log` (8/8 refused); `inventory-equivalence.log` (573 literals identical); host vs pinned analyzer (`static-analysis-host-tidy23.log`) | R622-4 | 405dc68310a18f669049ffc10cc23eef7300dcff |
| Tests | CLEAN | full local kit + RV32 at both heads (`receipts/port/`, `receipts/integ/`); `cache-gate-probes.*` (11/11 as expected); `helper-compiling-probe.*`; hosted quality/bare-metal job logs at both heads | R622-4 | 405dc68310a18f669049ffc10cc23eef7300dcff |
| Docs | CLEAN | `docs/VERIFICATION.md` (rows + cache paragraph), PR #22 and PR #23 bodies, generated TESTS/TRACEABILITY/REQUIREMENTS currency (`integration-regeneration.log`), commit subjects | R622-4 | 405dc68310a18f669049ffc10cc23eef7300dcff |

## Real limits

- **Static analysis, host analyzer.** This host's analyzer is clang-tidy 23. The pinned clang-tidy 18 is not installed here, so my local `static-analysis` gate returned rc 1 at both heads on one padding diagnostic only. At the pinned version (hosted, ubuntu-24.04, `clang-tidy 1:18.0`) the gate was **executed** with rc 0 at `405dc683` (job 114630467551) and `3c9ca52f` (job 114630519342). I rely on those hosted executions for that leg (see S2).
- **Toolchain substitutions.**
  - The shared Clang 18.1.3 wrapper on this host points to a removed path. I used a private wrapper in my scratch directory around the same pinned Clang 18.1.3 root, and changed no shared install.
  - The local sanitizer leg used the host clang 23, which is not pinned. The hosted sanitizer leg ran under its image.
  - RV32 objects were built with the host `riscv64-elf-gcc` 16.2.0, not Ubuntu's `gcc-riscv64-unknown-elf`. Raw equality is a same-compiler comparison; the non-debug object hashes equal the author's published values.
- **Hardware.** QEMU smoke is not hardware. Physical calibration was NOT RUN, and field skips are not hardware proof.
- **No manager bank.** No manager source bank runs at this exact head. Source-head execution evidence is the author's published receipts plus my own local runs and the hosted jobs above. I neither claim nor infer a manager bank.
- **The integration verdict stands on its own.** It covers `3c9ca52f` only. The current-dev merge candidate (live dev `c20c85bd`) is not reviewed here.

## Pending manager duties

- Build and validate the current-dev merge candidate (builder and native banks) at the merge turn and link its receipts.
- Own hosted/act acceptance, the second independent review, the merge of PR #23 (and thereby PR #22's head into main), and the milan-fpga #697 pin to `405dc683`.
- Decide whether S1/S2 are carried forward; neither blocks.

## Reproduction

The scripts are in `scripts/` and need `TSN_GTEST` (GoogleTest 1.14.0 prefix) and `TSN_CLANG18` (a directory containing a working `clang-18`).
- `run_gates.sh <tree> <head> <out> 3 4` runs `validate.py --graphs` and `baremetal.py`.
- `token_compare.py`, `object_compare.sh`, `cache_gate_probes.py`, `gate_mutants.py`, `helper_compiling_probe.py`, `inventory_equivalence.py` and `merge_audit.py` are the reviewer probes.
- Job budget: at most 16 concurrent jobs. Probes ran on disposable copies; the review clone was verified afterwards (`receipts/clone-integrity.log`: HEAD and tree exact, 78 tracked blobs and modes match, index tree equals the HEAD tree, no gitlinks in this repository).

## Prior public findings at this head

(Read after the verdict and ledger above were written. Neither changed as a result.)

| Prior finding | Disposition at `405dc683` | Evidence |
|---|---|---|
| R623-4-F1 (MINOR: split streamed literals on one assertion pass as separate coverage) | **RESOLVED** | The gate now keys ownership on (owner, file, line, column) (`check_acmp_cache.py:59-64`, `assertion_messages.py:105-116`). The repository's compiling control, which reproduces the cited probe at `cccb8b15` (link resolves), gives gate rc 1 with exactly `published_future: assertion is shared with another cache field`, plain and `-O`. Its needle audit is rc 0 and its campaign 5/5 CAUGHT; the separate variant gives gate rc 0 and 5/5 CAUGHT, at both heads. My own helper-hosted compiling variant and in-memory probes P1–P4 are refused the same way, while P5/P6 (own assertion) pass. The gate's selftest refuses 8/8 planted regressions. The VERIFICATION.md claim is enforced. |
| R622-1 F-1, F-2, F-3 | RESOLVED (unchanged since round 2) | `acmp-publish-after-timers` and `acmp-publish-reset-stream-cache` are CAUGHT (342/0/0). The traceability gate passes. Tokens, positions and six raw object pairs are equal. |
| R622-2-F1 / R623-3-F-1 / R622-2 S-4 (per-field cache protection) | RESOLVED (unchanged since round 3) | The bound, started and stream restore-only plants are each CAUGHT, and the completeness gate passes, now on identities. |
| R623-2 P-1 (review-process independence) | Not a source finding. Answered by the manager with a fresh external round (issue #21 comment 6115822525). No action at this head. | — |
| R622-3-S-1 (cross-wired started restore not covered) | RETAINED as SUGGESTION | `src/` and `tests/` are untouched by this delta, so the prior probe result stands. Not rerun this round. |
| R622-3-S-2 (newer-analyzer padding) | RETAINED as R622-4-S2 | Reproduced: host clang-tidy 23 flags the head and not the base, while hosted clang-tidy 18 passes at both heads. |
| R622-3-S-3 (publish guard clearing side untested) | RETAINED as SUGGESTION | `src/acmp.c` and the tests are unchanged in this delta. Not rerun. |
| R622-3-S-4 (RV32 smoke label omits publication) | RETAINED as SUGGESTION | `scripts/baremetal.py:77` is unchanged. On `integrate-21` the label gains "four generated entity round trips" but still omits publication (`:94`). |

R622-4 FINISHED
