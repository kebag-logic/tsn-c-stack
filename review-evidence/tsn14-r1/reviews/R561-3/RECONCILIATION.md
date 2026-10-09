Prior reports were opened only after [the independent verdict](INDEPENDENT.md) and [ledger](LEDGER.md) were written. Their immutable hashes and time are in [the freeze receipt](receipts/independent-freeze.json). No earlier verdict was used to form that independent conclusion.

| Prior finding | Severity and all attributable lenses | Current disposition | Authority, artifact, impact, required outcome and verification |
|---|---|---|---|
| R560-1-F1 | MINOR; Conformance, Tests, Docs | RESOLVED; agreement | [Original finding](https://github.com/kebag-logic/tsn-c-stack/pull/18#issuecomment-6082605009), acceptance item 3 and round-2 assignment. The prior unsupported traceability claim is removed by tests/test_adp.cpp:546 and tests/test_acmp.cpp:1281/:1286, with the helper at :148. The new tests and regenerated tables enforce the required behavior. Unchanged published p7/p8/p9 each fail correctly tagged tests; the baseline passes. Both new mutation plants fail both new tests at their named messages. See claim-results.json and both mutation campaigns. |
| R560-1-F2 and R561-1-F1 | MINOR; Tests, Docs | RESOLVED; agreement | [Internal finding](https://github.com/kebag-logic/tsn-c-stack/pull/18#issuecomment-6082605009) and [external finding](https://github.com/kebag-logic/tsn-c-stack/pull/18#issuecomment-6082579082). The incorrect evidence figure is corrected: current PR body says 25 gates; both local runs and exact-head hosted artifact have 25 successful entries. Required count reconciliation is met. |
| R560-1-R1 | RESIDUE; Docs | RESOLVED; agreement | CHANGELOG.md:5 now records the import, source dispositions, tests, plants and pinned-anchor check under Unreleased. The missing release-note wording has been supplied and matches the actual diff. |
| R560-1-S1, adopted | SUGGESTION; Conformance, Docs | RESOLVED; agreement | Round-2 assignment adopted the original suggestion. NFR-SEC-01 now maps to MFENTITY-03 in requirements.json and requirement-origins.json. PORTING.md:347 requires the caller to clear AEM_AUTHENTICATION_REQUIRED and check the emitted field on both targets. No authentication implementation is claimed. The records and generated disposition checks pass. |
| R560-1-S2, adopted | SUGGESTION; Robustness, Tests, Docs | RESOLVED; agreement | Round-2 assignment adopted the original suggestion. requirement_records.py:17 stores the ID/line map; :223 checks exact anchors; :297 plants a moved-anchor defect. All 114 numbered source lines were independently checked against downloaded bytes and match. The moved-anchor control fails as required. |
| R560-2-S1 | SUGGESTION; Tests | RETAINED as optional; agreement | Detailed disposition below. It does not leave a lens unclean. |
| R560-2-S2 | SUGGESTION; Docs | RETAINED as optional; agreement | Detailed disposition below. It does not leave a lens unclean. |
| R561-2-F1 | MINOR; Conformance, RTL, Robustness, Tests, Docs | Addressed by this replacement review; the R561-2 packet remains disqualified | [Procedure finding](https://github.com/kebag-logic/tsn-c-stack/pull/18#issuecomment-6083205085) required a fresh cleared-context review with its own verdict and ledger before reading earlier reports. The required outcome is supplied here: freeze time 2026-10-09T14:52:21.516969+00:00 precedes the first earlier-report retrieval. All five lenses were independently applied to the complete original-base diff. No source correction was needed; the old packet is not retroactively converted into an approval. |

R560-2-S1 — SUGGESTION — Tests — retained, optional.

- Artifact: tests/test_acmp.cpp:157, the timeout branch of peer_loss_recovery; src/acmp.c:1105, aging checked before connection timers.
- Authority/evidence: [R560-2](https://github.com/kebag-logic/tsn-c-stack/pull/18#issuecomment-6083096975), the current helper and timer dispatcher. The helper jumps to the ADP deadline, so its no-stale-probe assertion covers compressed delivery. The assigned separate expiry, binding retention and reprobe checks still execute and kill their plants.
- Impact: A stepped clock would add a more realistic timer history. This is additional test coverage, not evidence of incorrect source behavior or failure of the frozen acceptance.
- Optional outcome: Advance through preceding connection timer deadlines before aging, then check retained binding and exactly one fresh probe after rediscovery.
- Verification: Run that variant and the existing tagged mutations. The prior report records a passing stepped variant; this round independently examined the ordering but did not rerun that optional variant.

R560-2-S2 — SUGGESTION — Docs — retained, optional.

- Artifact: docs/VERIFICATION.md:36, Traceability acceptance row.
- Authority/evidence: [R560-2](https://github.com/kebag-logic/tsn-c-stack/pull/18#issuecomment-6083096975), requirement_records.py:223 and this round's source-audit.log. The row accurately lists inventory/origin/target/clause checks but does not enumerate the exact-anchor check.
- Impact: Discoverability of the new gate could improve; no existing claim is false.
- Optional wording: Add “exact pinned ID anchors” to that acceptance cell.
- Verification: Confirm the expanded wording matches the existing passing check and moved-anchor control. This is an enhancement, not an open wording defect requiring a RESIDUE entry.

Agreement by round: R560-1's substantive tagging defect and gate count are resolved. R561-1's gate-count finding is resolved; its earlier clean technical assessment was less comprehensive than R560-1's later tagging probes. R560-2's positive source conclusion is confirmed, with both optional suggestions retained. R561-2's technical resolutions are confirmed; its negative procedure conclusion remains valid for that old packet and is the reason for this independent replacement.

The public conversation contains the four reports and manager review-start notices; submitted reviews and inline-review containers are empty. The manager's issue ruling authorizes the privacy merge. No inspected manager comment supplies a source-bank run at this head. The round-2 author packet, linked by the later public report, separately pins this exact source head and supplies passing gate/mutation/probe receipts. Its attribution remains author source validation.
