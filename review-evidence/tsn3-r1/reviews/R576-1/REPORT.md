[R576] POSITIVE - exact head 66b3a75746fbbca3cffdfc7d89f013ab14aa1cc0

# R576-1 internal independent review: tsn-c-stack PR #19 (Closes #3)

- Head `66b3a75746fbbca3cffdfc7d89f013ab14aa1cc0`, tree `231e90357e5efe0101ed7fdd42c8b5ae2b25a89f`, one commit on `main` `1a9f651cdf7846b8e10ac246a6ef6916960fbb92`.
- Scope: issue #3 acceptance items 1-3, read exactly, plus the assignment (issue comment 6085285119) and REVIEW READY (6085568903). Item 4 (milan-fpga consumer, milan-fpga#697) belongs to a later manager lane and is not judged here.
- Order of reconstruction: CONTRIBUTING.md, README.md, docs/CODING_STANDARD.md and docs/VERIFICATION.md; issue body and the three public issue comments; PR body; requirement and interface authorities (docs/REQUIREMENTS.md, docs/PORTING.md, docs/DEVIATIONS.md, include/adp.h); `git diff 1a9f651c..66b3a757`; the public evidence tree `review-evidence/tsn3-r1` at `e486ec19`; then reviewer execution.
- The independent verdict was recorded (`receipts/independent_verdict.txt`) before any earlier review or review comment was read. PR #19 has no earlier review, inline comment or finding. The only PR comment is the manager's review-start notice. Nothing earlier needs to be resolved or retained.

## Verdict

POSITIVE. No open BLOCKER, MAJOR or MINOR finding. One RESIDUE (F1, changelog wording) goes to the manager's residue checklist. One SUGGESTION (S1) is recorded.

## Acceptance check

| Item | Result | Evidence |
|---|---|---|
| 1 Behaviour | Met | `src/adp.c:306-317`: the first guard refuses `len < 82`, AVTP version bits `(byte 15 & 0x70) != 0` and `(be16(bytes 16-17) & 0x07FF) != 56`. It counts `discarded` once and returns before any target parsing, state test, timer or port call. Clause comments are at `src/adp.c:307-309`. Offsets: Ethernet header 14 bytes (DEV-06 untagged contract); AVTP control header byte 0 subtype, byte 1 sv(1) version(3) message_type(4), bytes 2-3 valid_time(5) control_data_length(11), bytes 4-11 entity_id; ADPDU 68 bytes (`ADP_PDU_BYTES`, Figure 6-1), so control_data_length = 68 - 12 = 56 and the frame minimum is 82. An independently built ADPDU matches the core's own encoder for bytes 12-17 (`receipts/state_probe.txt`). The clause numbers match the numbering already used in the repository: adp.c:105-107 for 6.2.2.1-6 and include/acmp.h:7-8 for 6.2.2.3 and IEEE 1722-2016 4.4.3.4. |
| 1 Every receive state | Met | The guard runs before `if (!a->enabled \|\| a->state != ADP_STATE_WAITING)` (`src/adp.c:323`). The reviewer's probe confirms the five test conditions. They reach disabled/DOWN, enabled DOWN with link down, DELAY with the delay timer, DELAY with no timer and an owed advertisement (blocked output), and WAITING with the advertise timer (`receipts/state_probe.txt`). |
| 1 No state, timer or transmit change | Met | Hosted: `refused_discovery` (`tests/test_adp.cpp:710`) swaps in a StrictMock port table with no expectations, so any callback fails. It then compares the whole `struct adp` byte for byte against a copy whose only change is `discarded + 1`. RV32: `examples/rv32/smoke.c:146-181` makes the same whole-struct comparison and checks the callback count. |
| 2 One test and plant per input, plus valid control | Met | Tests `RejectsUnsupportedVersion` (:736, versions 1-7), `RejectsShortFrame` (:753, every length 0-81 in exact-size heap buffers so the address sanitizer sees over-reads) and `RejectsWrongControlDataLength` (:770, every 11-bit value except 56). The valid control is `ValidDiscovery` (:788, lengths 82/83/128, global and own target). All are instantiated over five states (:817). Plants: `adp-unsupported-version-accepted`, `adp-short-frame-accepted`, `adp-wrong-control-length-accepted`, with the valid control covered by `own-discover-discarded` (now killed by `ValidDiscovery/4`). Every kill test carries `// REQ: ADP-01`. |
| 2 Fresh campaign catches every plant by name | Met | Reviewer's fresh campaign gives CAUGHT 327, ESCAPED 0, ERROR 0. The four relevant plants were caught by the named tests with the named messages (`receipts/mutation_focus.json`, `receipts/validation/mutation-status.json`). There are 356 required killer entries in tests/mutations.json. |
| 3 Docs | Met | ADP-01 rewritten in docs/REQUIREMENTS.md:20 and docs/requirements.json. New section `## ADP input validation` (REQUIREMENTS.md:38, PORTING.md:72). The discarded counter row is updated. DEV-08 is removed from docs/DEVIATIONS.md, and no `DEV-08` or `#adp-input-limit` reference remains in the tree. TRACEABILITY.md and TESTS.md are current: the `traceability` and `test-inventory` staleness gates returned 0. VERIFICATION.md and STATIC_ANALYSIS.md are updated to match (plant count 327, suppression line 136 verified as `p.room = true;`). |

## Reviewer execution at the exact head (pinned GoogleTest 1.14.0 through PKG_CONFIG_PATH, CMAKE_PREFIX_PATH and LD_LIBRARY_PATH; clang-18 first on PATH)

- The two targets ran concurrently in disposable work trees outside the clone (`scripts/run_gates.sh`).
- `validate.py --work ... --jobs 16 --graphs` returned 0, with all 25 gates at rc 0 (`receipts/validate.log`, `receipts/validate.rc`, `receipts/validation/gates.json`). This covers boundary, needles, assertion-templates, dependencies, comments, conditionals, port-contracts, registration-controls, license, traceability, test-inventory, coverage-controls, privacy-selftest, privacy, GCC configure/build/test, coverage, Clang sanitizer configure/build/test, static-analysis, mutation, mutation-controls and graphs. The registration gate reports 7 binaries and 388 instances. A direct listing gives 388 instances for each compiler. Coverage for src/adp.c is 205/205 lines and 97/97 branches after exclusions, which raises the ratchet. Three graphs rendered.
- `baremetal.py --work ... --jobs 16` returned 0 for Debug and Release with no unresolved final symbols (`receipts/baremetal.log`, `receipts/rv32/`). The Release ELF and all three Release core objects are byte-identical to the author's published RV32 receipt (ELF sha256 `527ec53332228dd3242a0b873eb1a7441070bf8c12cb4ea5b5f107eabbc2909f`). Debug differs only because of build-path-dependent debug information.
- The comment and assertion contract holds: the `comments`, `needles`, `assertion-templates` and `conditionals` gates returned 0. The new code comments are clause references and REQ tags only. The new hosted assertions are `EXPECT_EQ` only. The shared needle "malformed discovery increments discarded exactly once" occurs in exactly one message literal.
- Reviewer mutation probe (`scripts/probe/mutants.py`, `receipts/reviewer_mutants.json`), adp_tests under the address and undefined-behaviour sanitizers:
  - Killed: version mask restricted to bit 4, length bound 81, over-strict length bound (`<=`), 10-bit control-length mask, control length checked only for zero, refusal not counted, and checks applied only in WAITING. Each was killed by the expected named tests.
  - Survived: sv bit added to the version mask, and the 11-bit mask dropped so the full 16-bit word is compared (see S1). The unmutated control passed.
- Hosted CI at the head: the pull_request run 37964068147 is green for both jobs, `quality` (4m14s) and `bare-metal` (59s). Every executed step succeeded and no step was skipped (`receipts/ci_pr_quality_steps.tsv`, `receipts/ci_pr_baremetal_steps.tsv`). In the duplicate push run 37964060914, `bare-metal` succeeded. Its `quality` job was still in "Install host dependencies" when this report was written (`receipts/ci_push_quality_steps.tsv`, `receipts/check_runs_head.tsv`).
- The public author evidence agrees with the reviewer results: the gate list (25 gates), test counts, plant counts and Release RV32 hashes all match.

## Findings

### F1 - RESIDUE - Docs
- Location: `CHANGELOG.md:3-12`, the Unreleased section.
- Authority and evidence: every earlier change on `main` (ae982af, 18d7378, 74445d2, 1a9f651) added an Unreleased line, and README.md:56 points the manager persona to the change log. This PR changes protocol behaviour but adds no line. The Unreleased list still says "Record the inherited ADP input limits and caller validation obligations" (line 12) and nothing records their removal.
- Impact: prose only. It changes no code, test, generated artifact, measurement or clause claim, and no gate reads the file.
- Required outcome (exact fix): add as the first Unreleased bullet: `- Discard ADP discovery frames with a nonzero AVTP version, fewer than 82 bytes or a control_data_length other than 56, counting each in discarded in every receive state. Remove DEV-08 ([issue 3](https://github.com/kebag-logic/tsn-c-stack/issues/3)).`
- Verification: read CHANGELOG.md at the fixing head. The privacy and license gates still pass.

### S1 - SUGGESTION - Tests, Conformance
- Location: `src/adp.c:312-313`, `tests/test_adp.cpp:95` (`discover` always writes sv 0 and valid_time 0) and `tests/test_adp.cpp:788`.
- Evidence: `receipts/reviewer_mutants.json`.
  - The plant `version-mask-includes-sv` (refuse sv = 1) survives.
  - The plant `cdl-mask-dropped-full-word` (compare all 16 bits at offset 16, which refuses any nonzero valid_time) also survives.
  - The RV32 smoke cannot catch either one, because every discovery it builds has sv 0 and valid_time 0.
  - docs/PORTING.md and ADP-01 state the 11-bit `control_data_length` rule. The implementation is correct, but no test pins that the upper five bits are ignored.
- Impact: none on the frozen acceptance. Each of the three required inputs has its test and plant. These two variants are over-strict changes outside the acceptance.
- Suggested outcome: add a valid-control case with nonzero valid_time (for example 31) and control_data_length 56 that must not be discarded, and decide on sv handling explicitly.
- Verification: rerun the probe and expect `cdl-mask-dropped-full-word` to be killed.

## Reviewer-owned ledger

| Lens | Status | Examined artifacts | Covering round | Exact head |
|---|---|---|---|---|
| Conformance | CLEAN | `src/adp.c:301-327` guard order and masks; `include/adp.h:77-93` constants; header offsets checked against an independently built ADPDU and the core encoder; 56 = 68 - 12 and 82 = 14 + 68; clause citations checked for consistency with repository citations (adp.c:105-107, acmp.h:7-8) and the DEV-06 untagged contract; Milan Table 5.51 state handling of valid discovery unchanged (ValidDiscovery/0-4) | R576-1 | 66b3a75746fbbca3cffdfc7d89f013ab14aa1cc0 |
| RTL | CLEAN | The repository contains no HDL, so the lens applies to the portable C core and its freestanding RV32 build. Examined: the RV32 Debug and Release builds (mandatory flags, allowed imports, no unresolved final symbols, QEMU smoke including `adp_discovery_smoke` over 5 conditions x 4 inputs); Release object and ELF hashes reproduce the author's receipt | R576-1 | 66b3a75746fbbca3cffdfc7d89f013ab14aa1cc0 |
| Robustness | CLEAN | Length check precedes every frame read; exact-size buffers 0-81 bytes under the address sanitizer; zero-length (null data) input handled by the length test; every refusal is a single counter increment with no port call (StrictMock); trailing bytes accepted (83, 128); re-entry guard unchanged | R576-1 | 66b3a75746fbbca3cffdfc7d89f013ab14aa1cc0 |
| Tests | CLEAN | `tests/test_adp.cpp:703-817`, `tests/mutations.json` (3 new plants, valid-control kill replaced), `examples/rv32/smoke.c:146-181`; fresh campaign 327/327 caught by name; 388 instances per compiler; coverage ratchet raised; reviewer plants 7 killed and 2 over-strict survivors outside acceptance (S1) | R576-1 | 66b3a75746fbbca3cffdfc7d89f013ab14aa1cc0 |
| Docs | CLEAN (F1 RESIDUE carried) | docs/REQUIREMENTS.md, docs/requirements.json, docs/PORTING.md, docs/DEVIATIONS.md (DEV-08 removed), docs/TRACEABILITY.md and docs/TESTS.md (staleness gates 0), docs/VERIFICATION.md, docs/STATIC_ANALYSIS.md, PR body claims (25 gates, 388 instances, 327 plants, 356 killer entries, 3 graphs) reproduced; CHANGELOG.md (F1) | R576-1 | 66b3a75746fbbca3cffdfc7d89f013ab14aa1cc0 |

## Real limits

- The IEEE 1722-2016, IEEE 1722.1-2021 and Milan v1.2 texts were not available to the reviewer. Values and offsets were checked by layout arithmetic and an independent encoder. Clause numbers were checked for consistency with citations already accepted in the repository, not against the standard text.
- No manager source bank ran at this head, and none is claimed. Source-head execution evidence is the author's published receipts plus this reviewer's own runs.
- The reviewer's Clang sanitizer build and clang-tidy used the host Clang 23.1.1. The pinned tool root supplies only `clang-18`, which was used for comment and assertion lexing. The author's receipts and the hosted Ubuntu 24.04 job used Clang 18. All of these runs passed.
- The duplicate push-event `quality` job was still running when this report was written. The pull_request run at the same head is complete and green.
- Physical calibration was NOT RUN. Field skips are not hardware proof, and no hardware was used. QEMU smoke is the only target execution.
- The reviewer mutation probe covers adp_tests under GCC with sanitizers only. It is not a replacement for the campaign driver.

## Pending manager duties

- Hosted and act acceptance, including the outcome of push run 37964060914 `quality`.
- Current-dev merge candidate validation (builder and native banks) at the merge turn: source base `1a9f651c`, live dev `5603c353`.
- Carry F1 to the residue checklist.
- The second independent review (external role).
- Acceptance item 4 (milan-fpga consumer through milan-fpga#697).

## Clone restoration

The clone is unchanged after the review (`receipts/clone_integrity.txt`):
- The status shows nothing tracked, untracked or ignored.
- The working tree and index equal HEAD.
- The index blob ids and modes equal the HEAD tree.
- The working-tree bytes hash to the HEAD blobs.
- File executable modes match.
- The repository has no gitlinks or submodules.

Receipts use the placeholders `$PACKET`, `$CLONE` and `$TOOLS` for host locations.

R576-1 FINISHED
