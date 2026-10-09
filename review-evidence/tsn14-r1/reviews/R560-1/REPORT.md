[R560] NEGATIVE - exact head db950cfa959f501932a47d4113733a671f882a83

# R560-1 independent review: tsn-c-stack PR #18 for issue #14

- Repository: kebag-logic/tsn-c-stack. PR #18 (`requirements-port`), issue #14.
- Exact head `db950cfa959f501932a47d4113733a671f882a83`, tree `b7885c12e7e6077c1dabf07f1a0a53046c42d15a`.
- Source base `18d737832c376f32660eb21fe2796e0b611507e3`. Head = author commits `3d50085` (ADP advertisement vector) and `69a312e` (requirements port), plus the manager merge of `main` `74445d28` (PR #17).
- Acceptance: issue #14 body items 1-6, the assignment ([6080704899](https://github.com/kebag-logic/tsn-c-stack/issues/14#issuecomment-6080704899)), the STOP ruling ([6081168071](https://github.com/kebag-logic/tsn-c-stack/issues/14#issuecomment-6081168071)) and REVIEW READY ([6081320203](https://github.com/kebag-logic/tsn-c-stack/issues/14#issuecomment-6081320203)).
- Source authority: milan-fpga at the pinned commit `5603c353137e90c1fa95429f6d00ef7a2298d9ee` (`docs/reference/FR_NFR.md`, `REQUIREMENTS.md`) and milan-fpga #665 comments 5992455815 and 6008744385.
- Standards inspected: IEEE 1722.1-2021, Milan v1.2 and IEEE 1722-2016 Annex B. File hashes equal the author's [SOURCES.md](https://github.com/kebag-logic/tsn-c-stack/blob/5d38bb765891e64fcc1361db2bbf78ff4feb50ec/review-evidence/tsn14-r1/author/SOURCES.md) (`receipts/source/standards-sha256.txt`).

## Verdict

NEGATIVE. Two MINOR findings are open.

All 25 `validate.py` gates pass at this head with GoogleTest 1.14.0 and Clang 18. `baremetal.py` passes in Debug and Release. Hosted CI at the exact head is green in both jobs, for push and pull_request runs.

The port is substantively sound. All 114 numbered source rows and both Mark II decisions are dispositioned. All 114 line anchors land on their own rows. The cited clauses match the standards. Texts are restated, and FPGA wording is removed. Production sources are byte-identical to the base.

The two MINOR defects are:

- F1: three tested requirements claim behaviour that their linked tests do not enforce. Planted defects prove this.
- F2: the PR body states the wrong gate count.

## Findings

### F1 - MINOR - Tests, Conformance, Docs

- **Artifacts.** The tests linked to three tested imports do not enforce parts of their requirement text:
  - `docs/requirements.json:225` (MFDISC-01), `:420` (MFCONN-03) and `:704` (MFRECOVERY-01).
  - The generated rows `docs/REQUIREMENTS.md:103`, `:111` and `:122`, which say "Tested through the linked declarations".
  - The matrix rows `docs/TRACEABILITY.md:28`, `:36` and `:47`.
  - The tags at `tests/test_acmp.cpp:1155`, `tests/test_acmp.cpp:1212` and `tests/test_adp.cpp:546`.
- **Authority.**
  - Issue #14 acceptance item 3: tested requirements carry `// REQ:` tests, and tests for uncovered requirements carry a planted defect.
  - [CONTRIBUTING](https://github.com/kebag-logic/tsn-c-stack/blob/db950cfa959f501932a47d4113733a671f882a83/CONTRIBUTING.md): a requirement change updates its tests and traceability.
  - [Milan v1.2](https://avnu.org/resource/milan-specification/) 5.6.3.5.2 sets the 0-2 s startup draw. 5.5.1.2 and 5.5.2.6 keep a binding until a controller unbinds it. 5.6.4.5.3/.4 return a departed talker to discovery.
- **Evidence.** Each plant is a disposable copy of the exact head (`scripts/claim_probe.py`, `receipts/probes/`). The baseline `p0` passes all tests. Each plant fails no test tagged with the requirement it breaks:
  - **p9 (MFDISC-01).** The startup draw uses 0-4 s instead of 0-2 s. Only `AdpCore.A9DrawKinds` fails, which is tagged `ADP-02, PORT-01`. MFDISC-01 claims "Advertise with the Milan schedule" and cites Milan 5.6.3.5.
  - **p7 (MFCONN-03).** Peer loss (`tk_departed`) clears `bound`. Only `A2GetRxStateInEveryState`, `A3UnbindInEveryState` and `A5RebindTheSameSourceUpdatesAndExits` fail. None is tagged MFCONN-03 ("Retain the binding during peer loss").
  - **p8 (MFRECOVERY-01).** Peer loss stops the sink's discovery, so the sink can never reconnect. Only `A12`, `A18`, `A19`, `DepartingStopsEveryProbingTimer` and `TimerPortBudgets` fail. None is tagged MFRECOVERY-01 ("Keep bound sinks eligible to reconnect without core reinitialization"). None is tagged MFCONN-03.
  - **Cross-check.** The author's published mutant table ([HANDOFF](https://github.com/kebag-logic/tsn-c-stack/blob/5d38bb765891e64fcc1361db2bbf78ff4feb50ec/review-evidence/tsn14-r1/author/HANDOFF.md)) lists no mutant for these behaviours under the MF-tagged tests.
  - **What is covered.** The whole suite catches each plant, so code behaviour is covered. The traceability claim is not: a test linked to each requirement must catch it.
- **Impact.** The generated REQUIREMENTS.md and TRACEABILITY.md overstate verification for three ported requirements. The traceability gate cannot detect when the coverage that actually enforces them is lost.
- **Required outcome.**
  - MFDISC-01: tag the enforcing test, such as `AdpCore.A9DrawKinds`, with MFDISC-01.
  - MFCONN-03 and MFRECOVERY-01: tag tests that enforce binding retention and rediscovery after peer loss. Alternatively, add a focused test: a bound sink receives ENTITY_DEPARTING and, separately, a TMR_NO_ADP expiry. It stays bound, and a new ENTITY_AVAILABLE sends a fresh PROBE_TX_COMMAND. Add planted defects in `tests/mutations.json` whose kill test carries the MF tag.
  - Regenerate TRACEABILITY.md and TESTS.md.
- **Verification.**
  - Rerun `scripts/claim_probe.py` p7, p8 and p9 on the new head. Each must fail at least one test tagged with the requirement it breaks.
  - `validate.py --graphs` and `baremetal.py` pass.

### F2 - MINOR - Docs

- **Artifact.** PR #18 body, line 20: "With GoogleTest 1.14.0 and Clang 18, all 24 `validate.py` gates pass at the head."
- **Authority and evidence.** At this head, the PR's own command (`validate.py --work build-validation --jobs 16 --graphs`) records 25 gates. The merge of `main` adds `privacy-selftest` (PR #17), and `--graphs` adds `graphs`. My run records 25 entries, all rc 0 (`receipts/validate/gates.json`).
- **Impact.** The published validation figure is wrong for the stated command and head. All gates do pass, so only the count is wrong. A figure claim is not wording-only residue.
- **Required outcome.** State 25 gates, or name the gate list, for the head that is reviewed.
- **Verification.** The PR body count equals `len(gates.json)` from `validate.py --graphs` at the reviewed head.

### R1 - RESIDUE - Docs

- **Artifact.** `CHANGELOG.md:5`, Unreleased. Every merged PR has a change-log line. PR #17 has one, and this PR adds none.
- **Fix.** Add after line 5: `- Port the applicable milan-fpga requirements with origins, linked clauses, both targets and verification methods. Record every source disposition. Add an independent ADP advertisement vector with eleven field defects.`

### S1 - SUGGESTION - Conformance

- **Artifact.** `docs/requirement-origins.json:514` excludes NFR-SEC-01. That row requires advertising AEM_AUTHENTICATION as not required.
- **Why it matters.** That bit is a caller-supplied ADP `entity_capabilities` field. It is already covered by the MFENTITY-01 entity-configuration port obligation.
- **Suggestion.** Consider recording it as a port obligation under [Entity configuration](https://github.com/kebag-logic/tsn-c-stack/blob/db950cfa959f501932a47d4113733a671f882a83/docs/PORTING.md#entity-configuration) rather than as excluded. The current reason is not wrong.

### S2 - SUGGESTION - Robustness

- **Artifact.** `scripts/requirement_records.py:110` checks only that a source URL ends in `#L<n>` at the pinned file. A wrong line number would pass.
- **Current state.** All 114 anchors are correct today (`receipts/source/inventory-check.txt`).
- **Suggestion.** Add the pinned line-to-ID map to `source_ids()`, so the gate catches a moved anchor.

## Prior public findings

No reviews, review comments or findings exist on PR #18 at this head. The only PR comments are the two review-start notices. Nothing needs to be resolved or retained.

## Acceptance items 1-6

| Item | Result | Evidence |
|---|---|---|
| 1. ID, `origin: milan-fpga <ID>`, one link per cited standard; clauses correct | Met | All 24 MF records have an origin, both targets and distinct clause URLs. Each clause text names the standard of its link. I checked every cited clause in the three standards. Notable checks: Milan 5.6.3.5.6/.10 (link down: stop timer, go DOWN) and .8/.11 (shutdown: DEPARTING), which justify the FR-DISC-03 change; 5.6.2 (`valid_time` 10); 5.5.2.2 (bind/probe renames); 5.5.2.3/Table 5.26 (200 ms); 5.3.8.2/.3/.7 (persisted binding and started state); 4.2.7.2/4.2.7.3/4.3.2/4.3.3.2/4.4.1 (SRP/MVRP); 4.3.5.1 (MAAP); IEEE 1722.1-2021 6.2.2.4-6.2.2.20 (6.2.2.7 allows MAC derivation); IEEE 1722-2016 B.2, B.3.2 (Table B.7), B.3.3 (Table B.8), B.3.4 and B.4. Build, memory and testing rows cite their source decisions instead of standards, which is correct for local policy. |
| 2. Restated, not copied; FPGA words removed or turned into port obligations | Met | No 6-word run is shared with the source rows or #665 text. No fabric, CSR, mailbox, FPGA, RTL, hart or ring-register words appear in the MF texts, reasons or new PORTING sections. Platform duties are new PORTING sections. |
| 3. `// REQ:` test or justified inspection/port obligation; gates pass; new tests carry planted defects | Partly met (F1) | The traceability and inventory gates pass, and 24 metadata controls are caught. The new `AdvertisementFieldsMatchCaller` vector matches my hand decode of the 82-byte ADPDU. Its 11 field defects are caught. Probes p1-p6 are caught by MF-tagged tests. Probes p7, p8 and p9 are not (F1). |
| 4. Every excluded source requirement listed with a reason | Met | 68 FR/NFR rows and 46 REQ rows at the pinned commit equal the catalogue. The product-ownership table and the hooks in sections 3.4.1 and 3.4.2 are dispositioned in prose. |
| 5. Linux and bare-metal RV32; flag what cannot hold on both | Met | Every MF record lists both targets, and the gate enforces it. Service timing, wire deadlines, durable storage and complete recovery counters are flagged as integration evidence on each target. Coverage is stated as Linux only, with no RV32 denominator claimed. RV32 Debug and Release link and run their smoke checks. |
| 6. TRACEABILITY.md regenerated; owner docs rules | Met in the tree; F2 and R1 against the PR body and change log | The generated tables are current (gate). All 622 relative links and anchors resolve, and all new external links resolve. No new prose sentence exceeds 28 words. |

## Mapping decisions

The author changed or added these rows relative to the issue's proposed table. Each has a reason, and I accept each:

- FR-DISC-03: link down stops advertising and does not send DEPARTING. This matches Milan v1.2 5.6.3.5.6 and .10.
- FR-DISC-04: split into encoding (MFDISC-04, tested) and descriptor consistency (MFENTITY-01, port obligation).
- FR-DISC-05: moved to a port obligation (MFENTITY-02). IEEE 1722.1-2021 6.2.2.7 allows MAC derivation but does not require it, and the core takes a caller identity.
- FR-CONN-01: restated in the Milan bind/probe profile (5.5.2.2).
- FR-MAAP-01: split, with the downstream address use as a port obligation (MFMAAP-02).
- FR-SRP-01: split into tested ACMP callbacks and the lwSRP port. FR-SRP-02 is a port obligation.
- FR-SRP-03 and NFR-LAT-02 (ACMP part): added as port obligations, with reasons.
- NFR-SCOUT-02: kept as one-owner dispatch only.
- NFR-SCOUT-03: the 10 ms figure is kept as a measurable integrator obligation on both targets, and is honestly marked as proposed project policy.
- NFR-REL-01: split into tested core recovery and port-side event counting. The issue's "are counted" becomes the MFRECOVERY-02 obligation, with the reason that the cores expose selected counters only.
- NFR-PORT-01 and the two #665 decisions: verified by inspection, with linked audits.

There is no `src/`, `include/`, `examples/`, `cmake/`, `CMakeLists.txt` or `.github/` change. All six trees hash identically at the base and at the head.

## Executed evidence (reviewer, exact head)

- **Toolchain** (`receipts/toolchain.txt`, `receipts/toolchain-packages.tsv`, `scripts/provision_tools.sh`):
  - Ubuntu 24.04 Clang/clang-tidy 18.1.3, cppcheck 2.13.0, the libstdc++-13 headers and the RV32 GCC 13.2.0/binutils 2.42. Each `.deb` was verified Release → Packages → SHA-256.
  - GoogleTest/GMock 1.14.0 built from tag commit `f8d7d77c`. The host GCC 16 was used for the GCC build.
  - No shared install was made.
- **`validate.py --jobs 16 --graphs`.** rc 0, with all 25 gates at rc 0 (`receipts/validate/`). The run took 1 min 59 s, with a peak RSS of 0.45 GB for the driver.
  - Coverage is 100 % lines and branches after the unchanged exclusions.
  - The mutation campaign catches all 322 plants (322 CAUGHT).
  - Mutation controls, sanitizers (7/7 test binaries), static analysis and three graphs pass.
  - Privacy and the privacy self-test pass.
- **Two earlier attempts** are kept as receipts:
  - Attempt 1 failed only at `clang-sanitizers-build`. Ubuntu Clang 18 met the host GCC 16 libstdc++ headers, a host clash. The hosted runner pairs Clang 18 with GCC 13 headers.
  - Attempt 2 failed six lexing gates. My wrapper put a driver flag before `-cc1`.
  - Neither failure is a head defect.
- **`baremetal.py --jobs 16`.** rc 0 (`receipts/baremetal/`).
  - Debug and Release are ELF32 RISC-V soft-float with no unresolved symbols.
  - Core imports stay inside the allowed set.
  - The QEMU smoke checks pass for ADP, ACMP and MAAP.
- **Hosted CI.** `quality` and `bare-metal` passed at `db950cfa`, in pull_request run 37939539328 and push run 37939485799. Every step ran and none was skipped (`receipts/hosted/check-runs.txt`). The manager owns hosted acceptance.
- **Source inventory.** 114/114 rows match, and 114/114 anchors are exact (`scripts/source_inventory_check.py`, `receipts/source/`).
- **Probes** (`receipts/probes/`):

| Probe | Claim | Plant | Tests that fail |
|---|---|---|---|
| p0 | baseline | none | none |
| p1 | MFDISC-01 `valid_time` 10 | 31 | A0toA2Schedule, AdvertisementFieldsMatchCaller |
| p2 | MFDISC-02 keeps a running delay | DISCOVER in DELAY restarts | A3toA5DiscoverAndDiscard, A19 |
| p3 | MFDISC-03 no DEPARTING on link down | sends DEPARTING | LinkLevelsAndDisabledInputs |
| p4 | MFDISC-01 departure resets the index | reset removed | A10toA14 and seven others |
| p5 | MFDISC-01 index advances | increment removed | A0toA2Schedule, A10toA14 and others |
| p6 | MFDISC-03 shutdown sends departure | send deferred | A10toA14DepartingIndex |
| p7 | MFCONN-03 keeps the binding on peer loss | binding cleared | A2, A3, A5 only, none tagged MFCONN-03 (F1) |
| p8 | MFRECOVERY-01 can reconnect after peer loss | discovery stopped | A12, A18, A19, DepartingStopsEveryProbingTimer, TimerPortBudgets only, none tagged MFRECOVERY-01 or MFCONN-03 (F1) |
| p9 | MFDISC-01 Milan startup draw 0-2 s | uses 0-4 s | A9DrawKinds only, not tagged MFDISC-01 (F1) |

- **Clone integrity.** After the probes, the review clone is at the exact head and tree. The worktree and index are clean, with no ignored residue. All 76 tracked blob bytes and modes equal `HEAD`. There are no gitlinks or submodules, so no gitlink applies.

## Reviewer ledger

| Lens | Status | Examined artifacts | Covering round | Exact head |
|---|---|---|---|---|
| Conformance | UNCLEAN (F1) | All 24 MF records and their clauses against IEEE 1722.1-2021, Milan v1.2 and IEEE 1722-2016 text. The 114-row inventory and anchors. The mapping changes. NFR-SEC-01 (S1). | R560-1 | db950cfa959f501932a47d4113733a671f882a83 |
| RTL (production source; this repository has no RTL) | CLEAN | `src/`, `include/`, `examples/`, `cmake/` and the build files are byte-identical to the base. The RV32 core object and import audit passes. The ADP encoder fields were checked against the new vector. | R560-1 | db950cfa959f501932a47d4113733a671f882a83 |
| Robustness | CLEAN (S2 open as a suggestion) | `requirement_records.py` and the `traceability.py` exemption logic, including its 24 controls. Merge integrity: `check_privacy.py` and `validate.py` equal `main` 74445d28. Commit-message rules. | R560-1 | db950cfa959f501932a47d4113733a671f882a83 |
| Tests | UNCLEAN (F1) | The new ADP vector and its 11 plants. All MF `// REQ:` tags. Ten disposable probes. The full validator and the RV32 run. Hosted jobs. | R560-1 | db950cfa959f501932a47d4113733a671f882a83 |
| Docs | UNCLEAN (F1, F2; R1 residue) | REQUIREMENTS, PORTING, VERIFICATION, TESTS, TRACEABILITY, IMPORT, CHANGELOG and the PR body. 622 relative links and the new external links. Sentence length. | R560-1 | db950cfa959f501932a47d4113733a671f882a83 |

## Real limits

- The local GCC build used host GCC 16, not the runner's GCC 13. Clang, clang-tidy, cppcheck, GoogleTest and the RV32 toolchain match the hosted versions. The hosted jobs at this exact head also pass.
- No manager source bank runs at this head, and none is claimed or inferred. Source-head execution evidence is the author's published receipts plus this reviewer's runs.
- The service bound, wire deadlines, durable storage and recovery accounting are port obligations. Neither target's suite measures them, and this review does not either. Physical calibration was NOT RUN. RV32 QEMU smoke is not hardware proof.
- The standards were read from local copies whose hashes equal the author's recorded inspection files. No standard text is reproduced here.

## Pending manager duties

- Carry R1 to the residue checklist.
- After F1 and F2 are fixed, request a new review round at the new head.
- At the merge turn, build and validate the current-dev merge candidate (builder and native banks) and link its receipts on the PR. The source base is 18d737832c376f32660eb21fe2796e0b611507e3, and the live dev is 5603c353137e90c1fa95429f6d00ef7a2298d9ee.
- Keep hosted/act acceptance and the second independent review (R561) separate from this report.

R560-1 FINISHED
