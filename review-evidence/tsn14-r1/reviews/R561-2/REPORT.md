[R561] NEGATIVE - exact head 663f14de4a07bb1a777282fdfc83d30fd03843d4

The technical delta passes the executed checks, and every assigned source finding is resolved. One reviewer-procedure MINOR remains: the requested review order was violated. This packet must not count as the required cleared-context independent positive approval. No source correction is requested by this report.

The reviewed tree is `cff76b8564bc21ff16a57c2e32f4abe1b6d3e3e9`. The original comparison base is `18d737832c376f32660eb21fe2796e0b611507e3`. The round-two delta is the single commit from `db950cfa959f501932a47d4113733a671f882a83` to the exact head. [History](receipts/history.txt), the [complete diff](receipts/full.diff), and the [round-two diff](receipts/delta.diff) are retained.

Repository instructions, CONTRIBUTING, README and the documentation were inspected first. The public authority is [issue 14](https://github.com/kebag-logic/tsn-c-stack/issues/14), its [frozen assignment](https://github.com/kebag-logic/tsn-c-stack/issues/14#issuecomment-6080704899), the [privacy ruling](https://github.com/kebag-logic/tsn-c-stack/issues/14#issuecomment-6081168071), the [round-two assignment](https://github.com/kebag-logic/tsn-c-stack/issues/14#issuecomment-6082613435), and the [ready declaration](https://github.com/kebag-logic/tsn-c-stack/issues/14#issuecomment-6082886861). The [review-start record](https://github.com/kebag-logic/tsn-c-stack/pull/18#issuecomment-6082909379) identifies this head. The pinned upstream requirements and memory/testing decisions, local interface contracts, original-base diff and history were examined before public execution receipts. An [independent diff-pass record](receipts/independent-pass.txt) was written before the prior public finding comments were read.

**R561-2-F1 — MINOR — Conformance, RTL, Robustness, Tests, Docs — OPEN.**

- **Artifact:** This review's ordering and approval provenance; [review-order receipt](receipts/review-order.json).
- **Authority:** The assignment prohibits reading another reviewer's report before the reviewer's own verdict and ledger are written. It separately allows prior public FINDINGS after the independent diff pass.
- **Evidence:** Public PR comments [6082579082](https://github.com/kebag-logic/tsn-c-stack/pull/18#issuecomment-6082579082) and [6082605009](https://github.com/kebag-logic/tsn-c-stack/pull/18#issuecomment-6082605009) were retrieved after the independent diff pass. Their complete embedded round-one reports were read, beyond their finding sections, before this verdict and ledger were written. The preliminary pass record was not the required verdict and ledger. No other round-two report or private author material was read.
- **Impact:** The packet does not satisfy the required independence procedure. Successful tests cannot restore that assurance. All five approval lenses remain unclean on that procedural basis; no technical defect in this head is alleged by F1. This is not wording-only RESIDUE.
- **Required outcome:** Obtain a fresh cleared-context external review. That review must write its own verdict and ledger before reading another report, and limit earlier reconciliation to the authorized public findings. No author source change is required.
- **Verification:** The replacement packet records the required ordering, applies all five lenses, verifies the exact head and reconciles all public findings. The manager must not treat this packet as one of the two required positive reviews.

**Prior public findings and adopted suggestions at this head**

| ID | Prior severity and attributable lenses | Disposition | Artifact, required outcome and verification |
|---|---|---|---|
| R560-1-F1 | MINOR; Conformance, Tests, Docs | RESOLVED | `tests/test_adp.cpp:546` tags the enforcing startup test MFDISC-01. `tests/test_acmp.cpp:146` supplies the shared peer-loss assertions; declarations at `:1282` and `:1287` carry MFCONN-03 and MFRECOVERY-01. Baseline passes; unchanged p7, p8 and p9 each fail a correctly tagged test. Both peer-loss plants are killed by both new tests. Generated REQUIREMENTS, TRACEABILITY and TESTS pass currentness checks. See [probe results](receipts/probe-results.json), [named-mutation audit](receipts/target-mutation-audit.json), and [traceability output](receipts/validate/traceability.log). The former unsupported traceability claims are now enforced. |
| R560-1-F2; R561-1-F1 | MINOR; Tests, Docs | RESOLVED | The [captured PR body](receipts/pr-body.md) states exactly 25 `validate.py --graphs` gates. The [count check](receipts/gate-count.json) matches 25 distinct successful [gate records](receipts/validate/gates.json). The numerical evidence discrepancy is removed. |
| R560-1-R1 | RESIDUE; Docs | RESOLVED | `CHANGELOG.md:5` records the requirements port, source dispositions, advertisement and peer-loss tests, planted defects and pinned-anchor checks under Unreleased. The previously missing entry is present and matches the final scope. |
| R560-1-S1 | SUGGESTION, adopted by assignment; Conformance, Docs | RESOLVED | `docs/requirement-origins.json:513` maps NFR-SEC-01 to MFENTITY-03 as a port obligation. `docs/requirements.json:371` records both targets and justified verification. `docs/PORTING.md:347` requires clearing AEM_AUTHENTICATION_REQUIRED before enabling ADP and checking the emitted field on both targets; safe unauthenticated application handling remains external. The generated disposition no longer excludes this applicable configuration obligation. |
| R560-1-S2 | SUGGESTION, adopted by assignment; Robustness, Tests, Docs | RESOLVED | `scripts/requirement_records.py:17` contains the pinned line-to-ID map; `:223` checks exact ID anchors; `:297` plants a moved-anchor control. Independent parsing found all 114 row anchors correct. Moving each of all 116 row/decision anchors was rejected. See [anchor audit](receipts/anchor-audit.json) and the 25 metadata controls in the traceability receipt. |

No prior finding is retained or worsened as a source defect. There are no new source findings, open RESIDUE items or source suggestions. Zero submitted PR reviews and zero inline review comments were present in the inspected containers; prior findings were in the public conversation.

**Technical evidence**

The p7 and p8 substitutions were copied from the prior public probe receipts and run with the unchanged published `claim_probe.py`. Four disposable trees built concurrently, with four build workers each. The baseline completed with no failed tests. All seven binaries produced reports in each copy. The [registration audit](receipts/probe-registration-audit.json) confirms 372 executed instances per copy, with no skipped or incomplete cases.

| Probe | Defect | Required tagged failures observed |
|---|---|---|
| p7 | Peer loss clears `bound` | `AcmpCore.DepartingRetainsBindingAndReprobes` and `AcmpCore.AdpTimeoutRetainsBindingAndReprobes`; both carry MFCONN-03 and MFRECOVERY-01. |
| p8 | Peer loss disables discovery | The same two tagged tests fail the rediscovery assertion. |
| p9 | Startup uses the 0–4 s range | `AdpCore.A9DrawKinds`, now tagged MFDISC-01. |

The new helper establishes a real binding and discovery, delivers departure or aging separately, checks retained talker/stream/controller identifiers, and requires a waiting state with aging stopped. A new advertisement must start a delay, followed by exactly one PROBE_TX_COMMAND with the retained identities and a different sequence. It then checks the sink remains bound awaiting that response. The acceptance authority is Milan v1.2 5.5.1.2, 5.5.2.6 and 5.6.4.5.3/.4 as frozen in the public assignment. The startup test exercises 400 draws and catches the same 4-second substitution used by p9, against the startup obligation in 5.6.3.5.2.

The official mutation campaign independently catches `draw-kinds-merged`, `acmp-peer-loss-clears-binding` and `acmp-peer-loss-stops-discovery` through their named assertion messages. Both new tests kill each peer-loss plant. [Raw mutation XML](receipts/validate/mutations/) and [campaign results](receipts/validate/mutations/results.json) are retained; compiler failures were not counted as kills.

The unmodified exact-source `validate.py --graphs --jobs 16` returned 0 with all 25 gates passing. Registration reports seven binaries, 372 instances, 111 declarations and 42 total requirements. All 324 plants are CAUGHT, with zero ESCAPED or ERROR. GCC and Clang sanitizer tests pass. Coverage is 100% lines and branches after the unchanged two ADP statement and seven ADP branch exclusions. Static analysis, privacy, registration, dependency and report controls pass. Three graphs render. See [campaign return codes](receipts/campaigns.json), [coverage](receipts/validate/coverage.log), [mutation](receipts/validate/mutation.log), and [graphs](receipts/validate/graphs.log).

`baremetal.py --jobs 16` ran concurrently with the validator and returned 0. Both Debug and Release link all three cores as RV32I/ILP32, have no unresolved final symbols, and execute the documented smoke checks. [RV32 results](receipts/baremetal/results.json) include object and ELF hashes. The full hosted suite and the RV32 smoke subset remain explicitly distinct.

Execution used the supplied GoogleTest/GMock 1.14.0 and compiler files, with Clang 18.1.3. The supplied prefix remained first on PATH; a scratch-local launcher selected the supplied compiler bytes without executing the stale external-scratch wrapper. Compatible C++ headers and sanitizer runtime packages were extracted only under scratch. Host GCC 16.2.1, RV32 GCC 16.2.0, static-analysis versions and dependency details are recorded in [toolchain receipts](receipts/toolchain.json), [package hashes](receipts/sdk-packages.json), and [reproduction instructions](REPRODUCE.md). These local versions are not asserted identical to hosted versions. Peak unit memory was 4,477,210,624 bytes under the 12,884,901,888-byte cap. Campaign processes were kept attached and joined before completion; no shell-background job was left running.

Both `quality` and `bare-metal` jobs are green at this exact head in PR run [37944235910](https://github.com/kebag-logic/tsn-c-stack/actions/runs/37944235910) and push run [37944216211](https://github.com/kebag-logic/tsn-c-stack/actions/runs/37944216211). The validation steps executed successfully; they were not skipped. The PR quality log contains 25 successful gate lines and an explicit checkout of the exact head. The [hosted summary](receipts/hosted/summary.json), [checks](receipts/hosted/pr-checks.json), [quality extract](receipts/hosted/job-113866224073-extract.log) and [RV32 extract](receipts/hosted/job-113866224582-extract.log) retain that distinction. Hosted/act acceptance remains the manager's duty.

The source inventory has 25 imported requirements: nine tested, thirteen port obligations and three inspection records. Its 116 dispositions comprise 114 numbered rows and two decisions: twelve ported, nine wholly assigned to the port and 95 excluded. The unchanged portable boundaries retain identity, persistence, external reservation, transport programming, service measurement and complete recovery accounting as appropriate. The added authentication row introduces no AECP implementation claim.

The [initial public evidence](https://github.com/kebag-logic/tsn-c-stack/tree/5d38bb765891e64fcc1361db2bbf78ff4feb50ec/review-evidence/tsn14-r1) identifies author head `69a312e3914f96c2db5fa51f07b087a6cd6ff349` and its then-authorized privacy failure. The separate [published round-two author packet](https://github.com/kebag-logic/tsn-c-stack/tree/8623919ec00c5ac91e66d1c6eda0dbca8963ed83/review-evidence/tsn14-r1/author-r2) identifies this exact head and tree, 25 passing gates, 324 caught plants and passing RV32 configurations. All fifteen files covered by the two published manifests match their hashes. These are author source-head receipts. No manager source bank at this head is claimed or inferred.

**Reviewer-owned approval ledger**

Every lens was applied to its own artifacts. All remain UNCLEAN for approval because the cross-cutting procedural finding F1 is open; the technical observations above remain available for reproduction.

| Lens | CLEAN/UNCLEAN | Examined artifacts | Covering round | Exact head |
|---|---|---|---|---|
| Conformance | UNCLEAN — F1 procedure | Frozen issue acceptance; pinned source registers and decisions; requirements and origins; startup and peer-loss clause obligations; MFENTITY-03 and PORTING; anchor audit | R561-2 | 663f14de4a07bb1a777282fdfc83d30fd03843d4 |
| RTL | UNCLEAN — F1 procedure | Complete diff/tree; unchanged src, include, examples, cmake, build file and workflow; public core interfaces; RV32 dependency/import/link audits; hardware exclusions | R561-2 | 663f14de4a07bb1a777282fdfc83d30fd03843d4 |
| Robustness | UNCLEAN — F1 procedure | Departure/aging helper and production transitions; identity retention and fresh sequence; exact-anchor validation; 116 moved-anchor controls; malformed report and metadata controls | R561-2 | 663f14de4a07bb1a777282fdfc83d30fd03843d4 |
| Tests | UNCLEAN — F1 procedure | All 25 gates; seven binaries/372 instances; 324 plants and XML; unchanged p7/p8/p9 and passing baseline; RV32 configurations; executed hosted job steps; PR gate count | R561-2 | 663f14de4a07bb1a777282fdfc83d30fd03843d4 |
| Docs | UNCLEAN — F1 procedure | CONTRIBUTING, README, architecture, PORTING, requirements and dispositions, generated TRACEABILITY/TESTS, verification limits, CHANGELOG, PR body and published receipt attribution | R561-2 | 663f14de4a07bb1a777282fdfc83d30fd03843d4 |

**Limits and pending manager duties**

The final [integrity check](receipts/final-integrity.json) confirms all 76 tracked blob bytes and modes and all index entries match the exact head. Production sources and headers, examples, build configuration and workflow match the original base. No RTL files or required submodule gitlinks exist in this source tree. No RTL simulation or synthesis is claimed. All disposable trees, SDK extractions and builds stayed under packet scratch. No source fix, commit, push, GitHub write, merge, author contact, other-checkout edit, shared install or hardware operation occurred. The other development branch remained out of scope.

The fresh full-text Milan v1.2 download attempt returned HTTP 403. The delta clause review used the frozen public acceptance and the pinned source/interface authorities; it does not claim a fresh complete audit of all three standards. This access limit is recorded in [authority limits](receipts/authority-limits.json). The procedural independence failure above remains the decisive approval limit.

The manager must obtain a replacement cleared-context external review and the required second independent positive approval. At the merge turn, the manager must validate the current-dev merge candidate with builder and native banks and link those receipts on the PR. The source base is `18d737832c376f32660eb21fe2796e0b611507e3`; the assigned live dev is `5603c353137e90c1fa95429f6d00ef7a2298d9ee`. This source validation is distinct from that final candidate. Hosted/act acceptance remains with the manager.

Physical calibration is NOT RUN. Field skips are not hardware proof. The library tests establish no deployment service timing, wire-latency margin, cold-power persistence, complete recovery counters or device certification.

Publish only REPORT.md and files listed in [MANIFEST.sha256](MANIFEST.sha256). Scratch is excluded. Execution receipts preserve result fields and return codes; [normalization records](receipts/NORMALIZATION.json) identify location and terminal-sequence redaction.

R561-2 FINISHED
