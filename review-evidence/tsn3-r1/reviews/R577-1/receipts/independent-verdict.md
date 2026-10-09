[R577] POSITIVE - exact head 66b3a75746fbbca3cffdfc7d89f013ab14aa1cc0

Independent verdict recorded at 2026-10-09T17:31:28.357048+00:00 before reading prior public review findings or the remaining issue/PR comments. The supplied assignment, readiness and review-start scope comments were the only comments opened beforehand. The required public executable evidence was inspected after the independent diff pass. No open BLOCKER, MAJOR, MINOR, RESIDUE or SUGGESTION was found in this independent pass.

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
| Conformance | CLEAN | Issue 3 acceptance 1-3; src/adp.c:301-331; include/adp.h:87-91; IEEE 1722.1-2021 pp.47-50 and IEEE 1722-2016 pp.23,27-28; Milan v1.2 pp.102-104 | R577-1 | 66b3a75746fbbca3cffdfc7d89f013ab14aa1cc0 |
| RTL | CLEAN | Complete 14-file diff; unchanged include/adp.h and include/wire.h; CMakeLists.txt; examples/rv32/smoke.c:145-181; docs/ARCHITECTURE.md and PORTING.md; no HDL or gitlinks in this source tree | R577-1 | 66b3a75746fbbca3cffdfc7d89f013ab14aa1cc0 |
| Robustness | CLEAN | Length-first receive guard; all-storage snapshot and strict callbacks; independent guarded-buffer probe, all control words, unaligned input, counter wrap, queued output; sanitizer and RV32 runs | R577-1 | 66b3a75746fbbca3cffdfc7d89f013ab14aa1cc0 |
| Tests | CLEAN | tests/test_adp.cpp:700-821; tests/mutations.json; examples/rv32/smoke.c; fresh 327-plant campaign; 25 validation gates; 388 registered cases across seven binaries per hosted compiler; exact-head hosted job steps | R577-1 | 66b3a75746fbbca3cffdfc7d89f013ab14aa1cc0 |
| Docs | CLEAN | CONTRIBUTING.md; README.md; REQUIREMENTS ADP-01; PORTING input contract; DEV-08 removal; requirements.json; generated TRACEABILITY.md and TESTS.md; VERIFICATION.md; coverage ratchet and static-analysis suppression | R577-1 | 66b3a75746fbbca3cffdfc7d89f013ab14aa1cc0 |

No RTL is present or modified in this portable source repository. That lens covers the C/freestanding boundary, wire representation, callback ownership and the retained consumer interface. It does not claim hardware validation or extend approval to the parent product.

Prior-findings reconciliation and the remaining public scope/evidence comments are the next review step. This snapshot fixes the independent verdict and ledger before that step.

Pending manager duties: obtain the other independent review, accept hosted execution, build and validate the current-dev merge candidate with its builder/native banks and publish candidate receipts, then carry out the consumer update under milan-fpga issue 697. Source-head evidence does not establish the final candidate based on live dev `5603c353137e90c1fa95429f6d00ef7a2298d9ee`. No manager source bank was run or inferred. Physical calibration NOT RUN; field skips are not hardware proof. Timing, physical transport, linked product identity and full device certification remain outside this source review.
