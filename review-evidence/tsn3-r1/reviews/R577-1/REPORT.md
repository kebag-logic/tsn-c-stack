[R577] POSITIVE - exact head 66b3a75746fbbca3cffdfc7d89f013ab14aa1cc0

Independent verdict recorded at 2026-10-09T17:31:28.357048+00:00 before reading prior public review findings or the remaining issue/PR comments. The supplied assignment, readiness and review-start scope comments were the only comments opened beforehand. The required public executable evidence was inspected after the independent diff pass. No blocking finding was found in that pass. Subsequent public-findings reconciliation retains one RESIDUE and one SUGGESTION. No BLOCKER, MAJOR or MINOR is open; all five lenses remain CLEAN.

Scope is [issue 3](https://github.com/kebag-logic/tsn-c-stack/issues/3), acceptance items 1-3, under the [frozen assignment](https://github.com/kebag-logic/tsn-c-stack/issues/3#issuecomment-6085285119). Item 4 belongs to the later consumer update. The source parent is `1a9f651cdf7846b8e10ac246a6ef6916960fbb92`; the reviewed tree is `231e90357e5efe0101ed7fdd42c8b5ae2b25a89f`. The change is one commit and 14 files. The diff adds only the three requested receive checks to production C; other changes supply tests, smoke checks, mutation records, coverage and documentation.

The standards were read directly from the local standards library, with document digests recorded in `receipts/standards-identity.json`. [IEEE 1722.1-2021](https://standards.ieee.org/ieee/1722.1/6670/) Figure 6-1 and clauses 6.2.2.3/.6 establish the version-zero and 56-octet control-data rules. The PDU has 12 octets through entity_id, then 56 more: 68 octets, or 82 with the 14-octet untagged Ethernet header. [IEEE 1722-2016](https://standards.ieee.org/ieee/1722/5979/) 4.4.3.4 supplies unsupported-version refusal; Figure 11 and 4.4.5.4 establish the control field layout and width. No standards text or images are included in the publishable packet.

| Wire field | Independent mapping | Implementation |
|---|---|---|
| EtherType | Ethernet octets 12-13 | bytewise big-endian read at 12 |
| subtype | PDU octet 0, frame octet 14 | frame[14] |
| version | PDU octet 1, three bits below h | frame[15] & 0x70 |
| message_type | PDU octet 1, low four bits | frame[15] & 0x0f |
| control_data_length | PDU octets 2-3, low 11 bits | big-endian frame[16:18] & 0x07ff |
| entity_id | PDU octets 4-11 | frame octets 18-25 |
| complete ADPDU | PDU offsets 0 through 67 | length >= 82 |

The receive guard precedes every input read and target/state handling. Refusal increments discarded once and returns. It invokes no port and changes no other core field. This holds in disabled DOWN, enabled DOWN, DELAY, blocked-output DELAY and WAITING. Valid global and local discovery still enters DELAY only from enabled WAITING; Milan v1.2 5.6.3.1, Table 5.51 and 5.6.3.5.4 support that behavior. Frame stripping, actual readable length, destination filtering, interface selection and serialized delivery remain port obligations.

Hosted tests exercise versions 1-7, every length 0-81, every incorrect 11-bit control length, two targets and five states. The refusal helper checks the complete state object and uses strict callbacks. Valid controls cover 82, 83 and 128-byte buffers. All four test declarations carry ADP-01. Required plants are `adp-unsupported-version-accepted`, `adp-short-frame-accepted`, `adp-wrong-control-length-accepted`, and the existing valid-control plant `own-discover-discarded`.

The independent probe passed 919,422 cases over seven state conditions, adding queued departures, protected short-buffer boundaries, unaligned reads, every 16-bit control word, trailing lengths through 128 and discard-counter wrap. Upper valid_time bits were varied to isolate the length mask; that experiment is not a claim that every such packet is a conformant DISCOVER transmission. The baseline passed address/undefined-behavior instrumentation. All three required plants and five further accounting, callback, mask and valid-control plants compiled and failed the independent oracle with status 1 rather than a crash. See `scripts/adp_probe.c`, `scripts/run_probes.py` and `receipts/probes.json`.

The qualifying local gate run used dependency version 1.14.0 and compiler/analyzer version 18.1.3 from a disposable pinned SDK. All 25 `validate.py --graphs` gates and both `baremetal.py` configurations passed. Both hosted compiler suites ran 388 instances across seven binaries. Adjusted line and branch coverage is 100%; ADP raw coverage is 205/207 lines and 97/104 branches, with the existing two-line/seven-branch exclusion register unchanged. All 327 plants were caught, with no escaped or errored plants. Comment, assertion diagnostic, dependency, registration, metadata and mutation-grading controls passed; three diagrams rendered. The first nonqualifying run used ambient compiler/analyzer commands for some steps and was superseded by the complete pinned rerun; its evidence is identified separately.

Exact-head [pull-request workflow 37964068147](https://github.com/kebag-logic/tsn-c-stack/actions/runs/37964068147) and [push workflow 37964060914](https://github.com/kebag-logic/tsn-c-stack/actions/runs/37964060914) report successful quality and bare-metal jobs. PR job steps show that validation actually executed; these are not skipped contexts. Hosted acceptance remains the manager's duty.

The [published author evidence](https://github.com/kebag-logic/tsn-c-stack/tree/e486ec19d255c73abb0a8ac4ee9b9ffe31c6eea4/review-evidence/tsn3-r1) reports 25 passing gates, two passing RV32 configurations and 327 caught plants. Its published manifest digests match, and all 14 changed-file digests match this head. This is author source-head evidence, not a manager source bank.

Reviewer-owned ledger:

| Lens | Status | Examined artifacts | Covering round | Exact head |
|---|---|---|---|---|
| Conformance | CLEAN | Issue 3 acceptance 1-3; src/adp.c:301-331; include/adp.h:77-93; IEEE 1722.1-2021 pp.47-50 and IEEE 1722-2016 pp.23,27-28; Milan v1.2 pp.102-104 | R577-1 | 66b3a75746fbbca3cffdfc7d89f013ab14aa1cc0 |
| RTL | CLEAN | Complete 14-file diff; unchanged include/adp.h and include/wire.h; CMakeLists.txt; examples/rv32/smoke.c:145-181; docs/ARCHITECTURE.md and PORTING.md; no HDL or gitlinks in this source tree | R577-1 | 66b3a75746fbbca3cffdfc7d89f013ab14aa1cc0 |
| Robustness | CLEAN | Length-first receive guard; all-storage snapshot and strict callbacks; independent guarded-buffer probe, all control words, unaligned input, counter wrap, queued output; sanitizer and RV32 runs | R577-1 | 66b3a75746fbbca3cffdfc7d89f013ab14aa1cc0 |
| Tests | CLEAN | tests/test_adp.cpp:700-819; tests/mutations.json; examples/rv32/smoke.c; fresh 327-plant campaign; 25 validation gates; 388 registered cases across seven binaries per hosted compiler; exact-head hosted job steps | R577-1 | 66b3a75746fbbca3cffdfc7d89f013ab14aa1cc0 |
| Docs | CLEAN | CONTRIBUTING.md; README.md; REQUIREMENTS ADP-01; PORTING input contract; DEV-08 removal; requirements.json; generated TRACEABILITY.md and TESTS.md; VERIFICATION.md; coverage ratchet and static-analysis suppression | R577-1 | 66b3a75746fbbca3cffdfc7d89f013ab14aa1cc0 |

No RTL is present or modified in this portable source repository. That lens covers the C/freestanding boundary, wire representation, callback ownership and the retained consumer interface. It does not claim hardware validation or extend approval to the parent product.

The independent snapshot is preserved in `receipts/independent-verdict.md`. Only after writing it and its ledger were the remaining issue/PR comments, formal reviews and inline comments opened. The issue's three comments confirm the frozen assignment and readiness. The PR has the two manager review-start notices and the [earlier public independent review](https://github.com/kebag-logic/tsn-c-stack/pull/19#issuecomment-6085778617). There are no formal review or inline-comment findings. No additional manager source-bank receipt was present. The source evidence remains the published author packet and the independent executions described here.

| Prior finding | Disposition at this exact head | Covering evidence |
|---|---|---|
| R576-1 F1: missing changelog entry | Retained as R577-F1, RESIDUE, Docs | `CHANGELOG.md:3-12` still has no entry recording this fix; the required current requirements and port documents are correct. |
| R576-1 S1: mask-isolation test strengthening | Retained as R577-S1, SUGGESTION, Tests and Conformance | Shipped fixtures leave h and valid_time zero. The independent all-control-word probe covers the length-mask distinction; an additional full-word-comparison plant is caught. The optional shipping-test enhancement remains. |

R577-F1 — RESIDUE — Docs. Location: `CHANGELOG.md:3-12`. Authority/evidence: the manager entry point in `README.md` points to the changelog; prior public F1 identifies the missing summary, and direct inspection confirms it. Impact: a missing narrative record of the implemented correction. No requirement, clause claim, measurement, generated artifact, executable behavior or privacy rule changes. Required outcome for the manager residue checklist: add this exact first Unreleased bullet:

`- Discard ADP discovery frames with a nonzero AVTP version, fewer than 82 bytes or a control_data_length other than 56, counting each in discarded in every receive state. Remove DEV-08 ([issue 3](https://github.com/kebag-logic/tsn-c-stack/issues/3)).`

Verification: inspect the new changelog entry and confirm the privacy/license checks still pass. This source review made no edit.

R577-S1 — SUGGESTION — Tests, Conformance. Locations: `tests/test_adp.cpp:95`, `tests/test_adp.cpp:788`, `src/adp.c:312-313`. Authority/evidence: prior public S1; direct fixture inspection; IEEE 1722.1-2021 Figure 6-1 and clauses 6.2.2.2/.5/.6; `receipts/probes-review-control-mask-removed.json`. Impact: no failure of frozen acceptance and no implementation defect. A future over-strict comparison of all 16 control-word bits could survive the shipped zero-valid_time fixtures. The independent baseline passed and the full-word-comparison plant failed with status 1. Required outcome for acceptance items 1-3: none. Suggested outcome: optionally add a separately labelled mask-isolation fixture and a corresponding plant, and state the intended tolerance for h. Verification: require the full-word-comparison plant to fail that new assertion while the baseline passes. Normative qualification: h is specified as zero, and valid_time is specified as zero for DISCOVER. A nonzero h or valid_time fixture must be labelled intentional malformed-input/tolerance testing, not a conformant valid DISCOVER control.

The earlier review's outstanding push-job observation is now resolved: the latest checks show all four jobs successful. Its direct-standards and pinned-compiler limits do not apply to the qualifying executions and direct text/figure checks recorded in this packet. Those earlier observations are not treated as independent proof for this verdict.

Pending manager duties: assess both independent reviews, carry R577-F1 to the residue checklist, accept hosted execution and any required local workflow acceptance, build and validate the current-dev merge candidate with its builder/native banks and publish candidate receipts, then carry out the consumer update under milan-fpga issue 697. Source-head evidence does not establish the final candidate based on live dev `5603c353137e90c1fa95429f6d00ef7a2298d9ee`. No manager source bank was run or inferred. Physical calibration NOT RUN; field skips are not hardware proof. Timing, physical transport, linked product identity and full device certification remain outside this source review.

Evidence and reproduction:

| Evidence | Packet receipt |
|---|---|
| Independent verdict before prior findings | [independent-verdict.md](receipts/independent-verdict.md) |
| Full pinned source gates | [gates.json](receipts/local/validation/gates.json), [validation.log](receipts/local/validation.log), [gate-run.json](receipts/gate-run.json) |
| Actual executed test totals | [executed-test-counts.json](receipts/executed-test-counts.json), both compiler instance logs under `receipts/local/validation/` |
| Raw named-assertion campaign XML and results | `receipts/local/mutations/`; [independent-regrade.json](receipts/independent-regrade.json), [published-regrade.json](receipts/published-regrade.json) |
| RV32 Debug and Release execution | [results.json](receipts/local/rv32/results.json), build/smoke logs and link maps under `receipts/local/rv32/` |
| Exact-head hosted steps | [hosted-jobs.json](receipts/hosted-jobs.json), [hosted-checks-latest.json](receipts/hosted-checks-latest.json) |
| Public scope, prior-finding inventory and source evidence | [public-records.json](receipts/public-records.json), [public-evidence-verification.json](receipts/public-evidence-verification.json) |
| Reproduction instructions and independent probes | [scripts/README.md](scripts/README.md), [probes.json](receipts/probes.json) |
| Source integrity | [source-final.json](receipts/source-final.json) |

The independent XML regrade confirms all 327 plants and 356 required killer entries. Each of the three new plants has five separately required state-specific killers; all fifteen match the owned assertion message. The existing valid-control plant also matches its named required assertion. Receipt copies redact host locations only; `receipts/receipt-provenance.json` records raw and published digests. Original command output remains in unpublished scratch. The initial ambient-compiler run is identified separately and is not the qualifying pinned gate receipt.

Both targets and the validation driver's independent suites/campaigns ran concurrently beneath foreground parent processes that joined their children. Drivers received an explicit jobs limit of two to bound aggregate compiler work; peak unit memory was 3,583,713,280 bytes under the 12 GiB cap. There were no hardware runs, parent-product banks, workflow emulation, source fixes, commits, pushes, external writes, merges, shared installations or edits to another checkout. No HDL execution was needed for the unchanged hardware boundary.

All 76 tracked files retain exact head blob bytes and modes; the index equals the reviewed tree. Final tracked, untracked and ignored status is empty after removing generated interpreter caches. The head has no submodule gitlinks or .gitmodules, so no required gitlink is missing. Disposable source copies, binaries, SDK extractions and standards extracts remain under `scratch/`, which is excluded from publication. Every publishable receipt and script is listed in `MANIFEST.sha256` using packet-relative paths.

R577-1 FINISHED
