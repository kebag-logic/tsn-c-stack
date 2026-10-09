[R579] NEGATIVE - exact head 6f4ecc9036f9ac2694b05a749cc9105d9c15c05f

Independent external delta review of kebag-logic/tsn-c-stack issue #2 / PR #20, round R579-2. The earlier MAJOR (R578-1-F1 = R579-1-F1) and both earlier MINOR findings (R578-1-F2, R578-1-F3) are resolved at this head; none is worsened. One new MINOR remains open: R579-2-F1. The mapper refuses the source-valid optional field `entity.firmware_rev`. The documented mapping does not cover that difference, and no test covers it. This leaves the Conformance, Robustness, Tests and Docs lenses unclean. RTL is CLEAN. No new BLOCKER, MAJOR or RESIDUE was found.

Reviewed tree: `49585d392468cbf85cdf21ef5c7546cec079c8be`. Round two is one commit after `4c939ef18741916df85a355973db007b588604e0`, changing nine Python/documentation files. The complete requested diff from `1a9f651cdf7846b8e10ac246a6ef6916960fbb92` and its history were also examined. The earlier merge brings in the ADP correction from `51870377`; round two changes no C core, public header, generated example, build configuration or mutation registry.

The [review start](https://github.com/kebag-logic/tsn-c-stack/pull/20#issuecomment-6087599944), [frozen acceptance](https://github.com/kebag-logic/tsn-c-stack/issues/2), [initial scope](https://github.com/kebag-logic/tsn-c-stack/issues/2#issuecomment-6086063941) and [round-two assignment](https://github.com/kebag-logic/tsn-c-stack/issues/2#issuecomment-6086821725) define the review. Contribution, README, coding, verification, requirements and integration contracts were reconstructed first, then pinned source/interface authorities, then the diff/history, then public executable evidence. No private author material, other checkout or unpublished reviewer report was used.

The [independent verdict and ledger](receipts/independent-verdict.md) and [ordering receipt](receipts/independence.json) were saved after local gates completed and before opening either earlier review's findings or probe. Subsequent reconciliation used the published [R578-1 findings](https://github.com/kebag-logic/tsn-c-stack/pull/20#issuecomment-6086810259) and [R579-1 findings](https://github.com/kebag-logic/tsn-c-stack/pull/20#issuecomment-6086815208). Review-submission and inline-comment lists were empty. An external usage limit interrupted the first session. On resumption, R579-2-F1 was found by the reviewer's own comparison of mapper and source entity keys. That was after the earlier findings had been read, but the defect appears in none of them. The [resume addendum](receipts/resume-addendum.md) records this ordering, and this report supersedes the first session's POSITIVE independent verdict.

**R578-1-F1 / R579-1-F1 — MAJOR — RESOLVED. Attributable lenses: Conformance, RTL/implementation interface, Robustness, Tests, Docs.**

Location: [scripts/milan_entity.py:15](https://github.com/kebag-logic/tsn-c-stack/blob/6f4ecc9036f9ac2694b05a749cc9105d9c15c05f/scripts/milan_entity.py#L15), model selection at line 65, `scripts/entity_selftest.py:209,219,233,250,307,389`, and `docs/ENTITY_YAML.md:184`.

Authority: acceptance item 7 and the pinned [source hexadecimal parser](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/sw/builder/endstation_builder.py#L1349). Original impact: silent identity substitution in generated ADP/ACMP and refusal of valid model, pin, OUI and capability spellings. Required outcome: preserve source values and precisely refuse source-invalid types and syntax.

All five fields now use string-only base-16 parsing, optional `0x`/`0X`, single inter-digit underscores and digit-count bounds including leading zeros. Model values reject zero/all-ones. A pin wins over a valid literal but cannot conceal an invalid literal. OUI and capability declarations are parsed before agreement checks. Portable-schema integers and resolved command-line arguments retain their separate contract.

Verification: the [unchanged reviewer probe](scripts/probe_mapper.py), SHA-256 `f5228744e72941122a8c69ac5d080baf1e267659b24e72f2c1dccf678194f348`, matches both published copies byte for byte. Its [fresh output](receipts/probe-mapper.log) gives P1 = `0x1234567890123456`, P2 = `0x020000FFFE000001`, accepted agreeing P3/P4 and field-specific quoting refusals for P9/P10. This is a diagnostic probe; its exit status alone was not used as the oracle. [Independent assertions](receipts/independent-probes.log) matched 213 scalar cases against isolated functions extracted from the pinned source. The compiled CLI regression passed for `"1234567890"`, checking `0x0000001234567890` in both ADP and ACMP. Fresh mapper plants caught base-zero parsing, missing width checks, accepted unquoted integers, repeated underscores and disabled pin agreement.

**R578-1-F2 — MINOR — RESOLVED for its named defaults and MAC forms. Attributable lenses: Conformance, Robustness, Tests, Docs. The sibling default `firmware_rev` is new finding R579-2-F1.**

Location: `scripts/milan_entity.py:34,60`, `scripts/entity_selftest.py:266,271,276,283,292`, and `docs/ENTITY_YAML.md:165,172,196`. Authority: acceptance item 7, pinned builder defaults at lines 3731–3740 and MAC grammar at lines 3279–3308. Original impact: rejection of valid omissions and hyphen-separated MACs. Required outcome: source-equivalent defaults/normalization, or individually documented and tested restrictions.

Omitted vendor name now defaults to `Kebag Logic`, group name to the empty string, and entity ID to `mac-derived`; explicit nulls do not request defaults. Colon/hyphen octets and the source's twelve-digit hexadecimal MAC forms are accepted; invalid, zero and multicast values are refused. P5–P8 pass. Independent assertions cover all three omissions together with a hyphen MAC and verify identity `0x020000FFFE000001`; 16 MAC cases match the source parser. Named tests cover each default and MAC form, and all three default mutations are caught. See [probe output](receipts/probe-mapper.log), [independent controls](receipts/independent-probes.log) and [eight mapper catches](receipts/mapper-plants/results.json).

**R578-1-F3 — MINOR — RESOLVED. Attributable lenses: Conformance, Docs. Tests additionally verifies the repair.**

Location: [docs/REQUIREMENTS.md:109](https://github.com/kebag-logic/tsn-c-stack/blob/6f4ecc9036f9ac2694b05a749cc9105d9c15c05f/docs/REQUIREMENTS.md#L109), `docs/requirements.json:885`, `docs/TRACEABILITY.md:53`, `scripts/requirement_records.py:185,252,284,294,348` and `scripts/traceability.py:113`. Authority: CONTRIBUTING's requirement/test/traceability rule and issue #2. Original impact: an absent requirement definition and false import-baseline provenance in a generated artifact. Required outcome: an explicit definition with text, clauses, issue origin and current traceability.

ENTITY-01 now has those elements and both target names; the generated matrix links issue 2. The checker refuses missing/wrong origins, local test exemptions and missing table definitions. [Traceability execution](receipts/validation/traceability.log) passed 43 missing-row controls, 28 metadata controls, 43 requirements and 117 test declarations reconciled with 391 executable instances. Independent controls also refused a newly added record absent from REQUIREMENTS.md. No-write regeneration checks passed.

**R579-2-F1 — MINOR — NEW, OPEN. Attributable lenses: Conformance, Robustness, Tests, Docs.**

Location: [scripts/milan_entity.py:56-58](https://github.com/kebag-logic/tsn-c-stack/blob/6f4ecc9036f9ac2694b05a749cc9105d9c15c05f/scripts/milan_entity.py#L56-L58) (entity allowlist and its generic refusal). The mapping table at [docs/ENTITY_YAML.md:162-176](https://github.com/kebag-logic/tsn-c-stack/blob/6f4ecc9036f9ac2694b05a749cc9105d9c15c05f/docs/ENTITY_YAML.md#L162-L176) has no `entity.firmware_rev` row. Lines 210 and 213 of the same file state the unknown-field refusal and claim that all five end-station shapes were inspected. `scripts/entity_selftest.py` has no `firmware_rev` control. The allowlist dates from `0a1a14a`; round two rewrote the surrounding projection and defaults without adding the field, and no earlier round raised it.

Authority:

- Acceptance item 7 requires the schema to accept the `entity:` section unchanged, or a documented mapping to cover the difference.
- Round-two assignment item 2 requires builder defaults to be applied, or each restriction documented with a precise refusal and a test.
- In the pinned [source builder](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/sw/builder/endstation_builder.py#L3720-L3735), `firmware_rev` is optional with default 0 and must be a non-negative, non-boolean integer. The builder's own `firmware_version` refusal tells users to use `entity.firmware_rev`.
- The source builder documentation lists this field in row 4b.
- Comments in four of the five pinned end-station configurations document optional `firmware_rev: N`.

The [source evidence receipt](receipts/firmware-rev-source-evidence.txt) records the hashes and line numbers.

Evidence: [the probe](scripts/probe_firmware_rev.py) loads the pinned AX7101 source. Its [output](receipts/probe-firmware-rev.log):

- The pinned AX7101 source maps as before.
- With `firmware_rev: 1` or `firmware_rev: 0` added, the mapper refuses with `milan.entity: unknown field or invalid mapping`.

The field is the only entity key the source reads that the mapper refuses, apart from `firmware_version`, which the source itself refuses.

Impact: the mapper refuses a source-valid `entity:` section and misreports a documented source field as unknown. The documented mapping does not record the difference, so item 7's compatibility contract is not met for this field. It fails closed and never generates a wrong identity, so the severity is MINOR, not MAJOR.

Required outcome, either of:

- Accept `entity.firmware_rev` under the source rule (non-boolean integer, 0 or more, default 0) and record it in the mapping table as AEM-only with no core field, like `entity.locale`. Add a named acceptance test and refusal tests for source-invalid values (boolean, negative, string).
- Document a deliberate restriction in the mapping table, with a field-specific refusal message and a named test.

Verification: after the first option, re-running `scripts/probe_firmware_rev.py` should report `FIRMWARE_REV_SOURCE_VALID_ACCEPTED PASS`; after the second, it should show the field-specific refusal. In either case, the named selftests should pass at the head and fail when the handling is removed.

Not a finding: the mapper does not apply the source's non-empty-string check to `entity.locale`. That value is never projected, and the documentation tells integrators to validate the complete product configuration with its own builder before projecting it (lines 211–212).

Earlier residue and suggestions are explicitly disposed of:

| ID | Severity / lenses | Disposition at this head |
|---|---|---|
| R578-1-R1 | RESIDUE / Docs | RESOLVED at `docs/ENTITY_YAML.md:179`. Exact requested fix: “The mapping test produces a mapping equal to the tracked AX7101 YAML and checks every ADP value.” Parsed mapping equality is correctly distinguished from byte-equal generated C goldens. |
| R578-1-R2 | RESIDUE / Docs | RESOLVED at `docs/ENTITY_YAML.md:57`. Exact requested fix: “Quote a MAC address or name when YAML would otherwise read it as a number, boolean or date. A value of another type is refused.” |
| R578-1-S1 | SUGGESTION / Robustness, Docs | Optional decimal/hex-only restriction not adopted. The retained YAML 1.1 contract is explicit at lines 54–55; `test_yaml_integer_compatibility` checks octal, sexagesimal, decimal and hex forms. Retained only as an optional future schema choice; no defect. |
| R578-1-S2 | SUGGESTION / Tests | RETAINED as an optional future parameterized core-suite extension. Existing focused round trips execute all three cores on both targets and catch the three required plants. No acceptance failure. |

**Executed evidence and acceptance.**

| Check | Exact-head result / receipt |
|---|---|
| Linux full kit | [All 27 gates returned zero](receipts/validation/gates.json), including regeneration, entity controls, boundary, assertions, dependency pin, comments, conditionals, registration, traceability, inventory, licence/privacy, static analysis and graphs. |
| Host tests | Eight binaries passed under [GCC](receipts/validation/gcc-test.log) and [Clang sanitizers](receipts/validation/clang-sanitizers-test.log). Registration identifies 391 instances. |
| Schema and compatibility | [172 selftests passed](receipts/validation/entity-controls.log): four goldens, stale-header refusal, deterministic output, invalid-input preservation, scalar grammar and compiled identity checks. |
| Fresh mutations | 330 CAUGHT, zero escaped/errors. [Independent audit](receipts/mutation-audit.json) verified all 359 required owned messages in 332 completed mutation XML reports. Wrong-count, swapped-interface and dropped-field plants fail their named assertions. Eight additional mapper plants also caught, with failure logs retained. |
| Coverage | [100% after existing exclusions](receipts/validation/coverage.log): wire 10/10 lines and 2/2 branches; ACMP 742/742 and 348/348; ADP adjusted 205/205 and 97/97; MAAP 209/209 and 140/140. No round-two ratchet/exclusion change. |
| Bare-metal RV32 | [Debug and Release passed](receipts/rv32/results.json), including four generated entity round trips, freestanding dependencies, generated objects without imports and final ELF without unresolved symbols. Release ELF/generated-object hashes match the author receipts; Debug hashes differ with build paths. |
| Documentation | Four Mermaid graphs rendered. Schema/range/mapping tables agree with implementation; YAML remains the primary integration path and handwritten structs remain available. |
| Hosted CI | [Checks](receipts/hosted-checks.json) and [job/step records](receipts/hosted-runs.json) identify successful push run [37974966938](https://github.com/kebag-logic/tsn-c-stack/actions/runs/37974966938) and PR run [37974976910](https://github.com/kebag-logic/tsn-c-stack/actions/runs/37974976910), both at the exact head. Both quality and bare-metal validation steps executed successfully in each run; none was skipped. |

The requested dependency prefix was supplied through all three environment variables, with the pinned lexical-compiler directory first on PATH. [Versions](receipts/environment.json): GoogleTest/GMock 1.14.0, lexical Clang 18.1.3, native Clang 23.1.1, GCC 16.2.1 and RV32 GCC 16.2.0. The native compiler is distinct from the pinned lexer. Drivers ran concurrently as attached foreground processes with `--jobs 4`; every child completed. Unit peak memory was 3,311,906,816 bytes against the 12 GiB cap.

Acceptance items 1–6 retain their schema, refusal, const-generation, round-trip, CI and integration documentation evidence. Round two repairs item 7's source grammar/defaults and requirement provenance. The full AX7101 source was independently hash/size checked and projected to the tracked YAML mapping. The source capability package at protocol-processor `2ad2f845dd583f8310075fa2380cb60a04fd091a` supplies `0x0000C588`; its gitlink was verified in the pinned source tree. Generated widths/shared identity match `adp_entity`, `acmp_config` and MAAP's initialization interface.

The supplied [public evidence tree](https://github.com/kebag-logic/tsn-c-stack/tree/942742507d7b8d794d51ebfc4164e559661d60b6/review-evidence/tsn2-r1) contains round-one author receipts. Exact-head receipts were read from [the published round-two directory](https://github.com/kebag-logic/tsn-c-stack/tree/34a849a73ec71baad70d4c447d9b22586100fb56/review-evidence/tsn2-r1/author-r2/evidence/round2). The [audit](receipts/public-evidence-audit.json) verifies 32 downloaded manifest entries and all nine changed-file hashes against this checkout. These are author source-validation receipts. The inspected manager comments provide scope/review starts; no manager source bank is claimed or inferred.

**Reviewer-owned ledger.**

| lens | CLEAN/UNCLEAN | examined artifacts | covering round | exact head |
|---|---|---|---|---|
| Conformance | UNCLEAN (R579-2-F1) | Frozen acceptance/scope; source parser/defaults/model selection; source entity key set versus mapper allowlist; schema/mapping; ENTITY-01; independent scalar/MAC/fixture controls; firmware_rev probe | R579-2 | 6f4ecc9036f9ac2694b05a749cc9105d9c15c05f |
| RTL | CLEAN | No HDL delta; implementation interface examined through source capability package/gitlink, C record widths, generated identity/MAAP arguments, compiled CLI and RV32 object/link checks | R579-2 | 6f4ecc9036f9ac2694b05a749cc9105d9c15c05f |
| Robustness | UNCLEAN (R579-2-F1) | Five scalar fields; malformed/non-string/width refusals; pin precedence; omitted/null defaults; MAC forms; refusal of source-valid firmware_rev with a generic unknown-field message; CLI output preservation and sanitizers | R579-2 | 6f4ecc9036f9ac2694b05a749cc9105d9c15c05f |
| Tests | UNCLEAN (R579-2-F1) | 172 schema controls (none for firmware_rev); 391 host instances; 330 registered plus eight mapper plants; 359 named-message checks; both target gates and hosted steps | R579-2 | 6f4ecc9036f9ac2694b05a749cc9105d9c15c05f |
| Docs | UNCLEAN (R579-2-F1) | ENTITY_YAML grammar/defaults and resolved residue; mapping table lacks entity.firmware_rev; REQUIREMENTS/TRACEABILITY origin; missing-row controls; PORTING, VERIFICATION, coding rules and graphs | R579-2 | 6f4ecc9036f9ac2694b05a749cc9105d9c15c05f |

Real limits: this verdict covers the exact source head; its executed evidence covers the round-two delta. It is not a complete independent rereading of IEEE/Milan standards or device certification; full normative text was not used in this round. The grammar/default/provenance corrections are established against their pinned source-interface and issue authorities. The earlier full normative-source verification limit remains a manager acceptance duty. Coverage measures production C/wire code, not Python branch coverage. The mapper consumes an externally resolved model ID; this review did not recompute the complete descriptor-model hash. Pure source parsing functions were exercised, not a full builder bank.

No parent, protocol-processor, gPTP, synthesis or full builder bank ran. No RTL simulation was needed for this Python/documentation delta. Physical calibration NOT RUN. Field skips, simulated smoke success and host tests are not hardware proof, transport timing measurements or cold-start persistence evidence.

Pending manager duties: carry R579-2-F1 to the author and obtain a re-review of its repair; obtain both independent positive reviews; complete outstanding normative-source acceptance; file/link the milan-fpga integration follow-up required by item 7; validate the final current-dev merge candidate with builder/native banks and publish receipts; own hosted/act acceptance and publication. Source validation is distinct from that merge-turn candidate. Assigned source base: `1a9f651cdf7846b8e10ac246a6ef6916960fbb92`; supplied live-dev reference: `7c1b52bee26b497080ee22b1c1986109f80a5ee7`. The separately owned development branch remained outside this review.

[Integrity verification](receipts/integrity.json) confirms all 96 tracked blobs, executable modes and index entries match the exact head/tree, with a clean worktree. This repository has no submodule gitlinks. No tracked-source restoration was necessary; fault plants stayed in disposable copies under `scratch/`. No source fixes, commits, pushes, merges, GitHub writes or author contact occurred.

Portable scripts reproduce gate execution, public-authority fetching, independent comparisons, the unchanged probe/eight mapper plants, the firmware_rev compatibility probe, mutation XML auditing and checkout integrity checks. Original working files remain in unpublished `scratch/`. Published raw log copies normalize only local checkout/work/dependency/home paths; [receipt provenance](receipts/receipt-provenance.json) records original and published hashes. `MANIFEST.sha256` lists publishable scripts and receipts and excludes `scratch/`.

R579-2 FINISHED
