[R560] POSITIVE - exact head 663f14de4a07bb1a777282fdfc83d30fd03843d4

# R560-2 independent review: tsn-c-stack PR #18 for issue #14

- Repository: kebag-logic/tsn-c-stack. PR #18 (`requirements-port`), issue #14.
- Exact head `663f14de4a07bb1a777282fdfc83d30fd03843d4`, tree `cff76b8564bc21ff16a57c2e32f4abe1b6d3e3e9`.
- Delta under review: `db950cf..663f14d`, one author commit, "Close requirements review gaps in recovery and source tracing". The full PR diff from source base `18d737832c376f32660eb21fe2796e0b611507e3` was also checked for production bytes.
- Scope authority:
  - Issue #14 body, acceptance items 1-6.
  - The [assignment](https://github.com/kebag-logic/tsn-c-stack/issues/14#issuecomment-6080704899) and the [round 2 assignment](https://github.com/kebag-logic/tsn-c-stack/issues/14#issuecomment-6082613435).
  - [REVIEW READY](https://github.com/kebag-logic/tsn-c-stack/issues/14#issuecomment-6082886861), the PR body "Round 2" section and the [review start](https://github.com/kebag-logic/tsn-c-stack/pull/18#issuecomment-6082908481).
  - CONTRIBUTING, README and docs/VERIFICATION.md.
- Source authority: milan-fpga at the pinned commit `5603c353137e90c1fa95429f6d00ef7a2298d9ee`. Its `docs/reference/FR_NFR.md` and `REQUIREMENTS.md` were fetched read-only; hashes are in `receipts/upstream-sha256.txt`.
- Order kept: the independent pass over the delta, my own probes and the gates ran first. Prior public findings were read afterwards and are resolved below. No private author material, lane scratch or other reviewer's report for this round was read. The prior R560-1 probe script was used unchanged, as the round 2 assignment requires.

## Verdict

POSITIVE. No MINOR, MAJOR or BLOCKER finding is open at this head. All five prior findings, including both adopted suggestions, are resolved. Two new SUGGESTIONS are recorded; they do not affect the verdict.

- All 25 `validate.py --graphs` gates pass, rc 0. All 324 mutation plants are caught.
- `baremetal.py` passes in Debug and Release, rc 0.
- Hosted CI at the exact head is green in both jobs, for both the push and the pull_request run. No step was skipped.
- Production sources are unchanged: `src/`, `include/`, `examples/` and `CMakeLists.txt` are byte-identical to the source base.

## Resolution of prior public findings

| Finding | Status at this head | Evidence |
|---|---|---|
| R560-1-F1 (MINOR): linked tests did not enforce MFDISC-01, MFCONN-03 and MFRECOVERY-01 | RESOLVED | `AdpCore.A9DrawKinds` now carries MFDISC-01 (`tests/test_adp.cpp:546`). New `DepartingRetainsBindingAndReprobes` and `AdpTimeoutRetainsBindingAndReprobes` (`tests/test_acmp.cpp:1281-1289`, helper `:146-186`) carry ACMP-06, MFCONN-03 and MFRECOVERY-01. Plants `acmp-peer-loss-clears-binding` and `acmp-peer-loss-stops-discovery` (`tests/mutations.json`) name both tests and are CAUGHT. The unchanged R560-1 `claim_probe.py` probes were re-run here: p7, p8 and p9 each fail tagged tests, and the p0 baseline passes (`receipts/claim/claim_tags.txt`). TRACEABILITY.md and TESTS.md regenerate byte-identically (`receipts/regen.log`). |
| R560-1-F2 and R561-1-F1 (MINOR): PR body gate count | RESOLVED | The PR body says "All 25 `validate.py --graphs` gates pass". `receipts/validate/gates.json` has 25 entries, all rc 0. |
| R560-1-R1 (RESIDUE): no CHANGELOG Unreleased line | RESOLVED | `CHANGELOG.md:5` adds the requirements-port line. It is accurate for the PR. |
| R560-1-S1 (SUGGESTION, adopted): NFR-SEC-01 as a port obligation | RESOLVED | New MFENTITY-03 (`docs/requirements.json`, `docs/REQUIREMENTS.md:109`). The NFR-SEC-01 disposition is now "port obligation" (`docs/REQUIREMENTS.md:204`, `docs/requirement-origins.json`). The obligation sits in the Entity configuration section (`docs/PORTING.md:347-352`). It names the real `entity_capabilities` field (`include/adp.h:122`), which is encoded under IEEE 1722.1-2021 6.2.2.9 (`src/adp.c:110`). |
| R560-1-S2 (SUGGESTION, adopted): pinned anchors checked against a line-to-ID map | RESOLVED | `scripts/requirement_records.py` `source_ids()` now holds the 114-line map plus both decision comments. `validate()` requires exact URL equality. The selftest adds a "moved source anchor" control. An independent check (`scripts/anchor_check.py`, `receipts/anchor_check.log`) parsed the pinned upstream files: 114 of 114 defining rows equal the map, in both directions. All 116 catalogue URLs equal their pinned anchors. Three planted +1-line anchor moves are refused. |

R561-1 recorded no other findings.

## New findings

### S1 - SUGGESTION - Tests

- **Artifact.** `tests/test_acmp.cpp:156-161` (`peer_loss_recovery(true)`, used by `AdpTimeoutRetainsBindingAndReprobes`).
- **Observation.** `fire_adp(0)` moves the clock straight to the 20 s ADP deadline in one callback. The 200 ms probe-response timer is overdue at that point. `acmp_timer_expired` checks ADP aging before the probe timers (`src/acmp.c:1105-1110`). The sink therefore leaves at PRB_W_RESP with no retry sent. The assertion "peer loss sends no stale probe before rediscovery" depends on that compressed delivery. With an earliest-deadline clock, the sink would reach PRB_W_RETRY and send retries before aging.
- **Evidence that behaviour is right.** A disposable stepped-clock test, `r0-stepped-timeout` in `scripts/probes-own.json`, advances 50 ms per callback. It passes at this head. Retries are sent, aging expires at the deadline, and the binding is retained. After rediscovery, exactly one PROBE_TX_COMMAND is sent for the retained binding (`receipts/probes-own.jsonl`).
- **Suggestion.** Drive the timeout variant through the earlier timer deadlines, so expiry occurs in a realistic probing state.

### S2 - SUGGESTION - Docs

- **Artifact.** `docs/VERIFICATION.md:36`, the Traceability row.
- **Observation.** The row lists the pinned inventory, origins, both targets and clause links. It omits the exact ID-anchor check that this round adds. The PR body mentions that check. The row is not wrong.
- **Suggestion.** Add "exact pinned ID anchors" to the row's acceptance text.

## Lens evidence

- **Conformance.**
  - MFDISC-01 cites Milan v1.2 5.6.3.5. `A9DrawKinds` asserts every startup draw is 0-2 s and every other draw 0-4 s (`tests/test_adp.cpp:461-480`). It matches the `ADP_DRAW_STARTUP` path at `src/adp.c:241`.
  - The new ACMP tests follow 5.6.4.5.3 (DEPARTING: aging stopped, TK_NOT_DISCOVERED, EVT_TK_DEPARTED) and 5.6.4.5.4 (TMR_NO_ADP). They require the binding to stay set, as 5.5.2.6 and the bound-state rules require. Rediscovery takes PRB_W_DELAY and then one PROBE_TX_COMMAND with a new sequence ID (`src/acmp.c:550-572`, `:605-645`, `:716-727`).
  - MFENTITY-03 matches upstream NFR-SEC-01: authentication is advertised as not required. Its link resolves to `FR_NFR.md#L470`.
- **RTL** (production source; this repository has no RTL). No production byte changed in the PR (`git diff --quiet 18d7378 663f14d -- src include examples CMakeLists.txt`). RV32 Debug and Release link with no unresolved symbols, and the QEMU smoke checks pass (`receipts/baremetal/`).
- **Robustness.**
  - `requirement_records.py`: the map is exact and complete, and anchor moves are refused (`receipts/anchor_check.log`). 25 metadata controls are caught (`receipts/validate/traceability.log`).
  - Clone integrity after probes: 76 tracked entries match HEAD bytes and modes. Index and worktree are clean, and no gitlinks exist (`receipts/clone-integrity.txt`).
- **Tests.**
  - Thirteen disposable probes of my own (`scripts/probes-own.json`, `receipts/probes-own.jsonl`). Both baselines pass. Each of the 11 plants is killed by a test tagged with the requirement it breaks:
    - MFDISC-01: d1 0-4 s startup draw (A9), d2 wrong draw kind (A9), d3 armed delay differs from the draw (A0toA2Schedule).
    - MFCONN-03 and MFRECOVERY-01: c1 no passive state on departure, c2 aging expiry ignored, c3 DEPARTING unbinds, c4 expiry unbinds, c5 expiry stops discovery, c6 reprobe reuses the sequence ID, c7 rediscovery skips the delay, c8 DEPARTING keeps aging armed.
    - c4 and c5 are killed only by the new timeout test, so that test adds unique sensitivity.
  - Gate receipts: needle audit, test inventory and registration pass; 7/7 binaries; 100% lines and branches after unchanged exclusions.
- **Docs.**
  - REQUIREMENTS, TRACEABILITY and TESTS are generated and current.
  - PORTING Entity configuration uses short sentences, and each reference is a link.
  - VERIFICATION says 324 plants, matching the campaign.
  - CHANGELOG has the Unreleased line.
  - The PR body figures match the head: 25 requirements, 114 rows plus 2 decisions, 25 gates, 7 binaries, 324 plants and 3 graphs.
  - The commit subject is one line with no body.

## Reviewer ledger

| Lens | Status | Examined artifacts | Covering round | Exact head |
|---|---|---|---|---|
| Conformance | CLEAN | MFDISC-01, MFCONN-03, MFRECOVERY-01 and MFENTITY-03 records and clauses. Upstream NFR-SEC-01 at the pinned commit. ADP draw and ACMP discovery and probe paths in `src/`. | R560-2 | 663f14de4a07bb1a777282fdfc83d30fd03843d4 |
| RTL (production source; no RTL here) | CLEAN | `src/`, `include/`, `examples/`, `CMakeLists.txt` unchanged from base. RV32 Debug/Release link, import audit and QEMU smoke. | R560-2 | 663f14de4a07bb1a777282fdfc83d30fd03843d4 |
| Robustness | CLEAN | `scripts/requirement_records.py` map, validator and selftest. Independent anchor check and moved-anchor plants. Clone integrity after probes. | R560-2 | 663f14de4a07bb1a777282fdfc83d30fd03843d4 |
| Tests | CLEAN (S1 suggestion) | New ACMP tests and helper, A9 tag, two new plants. 25-gate validator, mutation campaign, claim probes p0/p7/p8/p9, 13 own probes including a stepped-clock control. Hosted jobs. | R560-2 | 663f14de4a07bb1a777282fdfc83d30fd03843d4 |
| Docs | CLEAN (S2 suggestion) | CHANGELOG, PORTING, REQUIREMENTS, VERIFICATION, TRACEABILITY, TESTS, requirement JSON files, PR body and commit message. | R560-2 | 663f14de4a07bb1a777282fdfc83d30fd03843d4 |

## Executed evidence (reviewer, exact head)

- Toolchain (`receipts/toolchain.txt`):
  - Pinned GoogleTest/GMock 1.14.0 via `PKG_CONFIG_PATH`, `CMAKE_PREFIX_PATH` and `LD_LIBRARY_PATH`. Pinned Clang 18.1.3 first on `PATH`.
  - Host GCC 16.2, RV32 GCC 16.2, QEMU 11.1, cppcheck 2.22 and clang-tidy 23.
- `validate.py --work <scratch> --jobs 16 --graphs`: rc 0, 25 of 25 gates at rc 0, wall time 2 min 2 s (`receipts/validate/`).
- `baremetal.py --work <scratch> --jobs 16`: rc 0, Debug and Release (`receipts/baremetal/`).
- Hosted (`receipts/hosted/`):
  - Push run 37944216211 and pull_request run 37944235910, both at `663f14de`.
  - Jobs `quality` and `bare-metal` succeeded in each run, with 7 of 7 steps successful and none skipped.
  - The manager owns hosted/act acceptance.

## Real limits

- Local GCC, RV32 GCC, cppcheck and clang-tidy versions differ from the hosted runner's. Clang 18 and GoogleTest 1.14.0 match the pins. Both hosted jobs pass at this exact head.
- No manager source bank runs at this head, and none is claimed or inferred. The author's round 2 gate receipts are not in the public evidence tree `5d38bb76`, which holds round 1 author material only. Source-head execution evidence here is this reviewer's runs plus the hosted jobs.
- Port obligations (service bound, wire deadlines, storage, recovery counting, authentication configuration) are not measured by either target or by this review. Physical calibration NOT RUN. RV32 QEMU smoke is not hardware proof.
- The standards were not re-read in full this round. Clause checks covered only the delta's citations against the source and the pinned upstream rows.

## Pending manager duties

- No residue item from this round. S1 and S2 are optional.
- Obtain the second independent review (R561-2) separately.
- At the merge turn, build and validate the current-dev merge candidate (builder and native banks), and link its receipts on the PR. The source base is 18d737832c376f32660eb21fe2796e0b611507e3; live dev is 5603c353137e90c1fa95429f6d00ef7a2298d9ee.
- Hosted/act acceptance remains with the manager.

R560-2 FINISHED
