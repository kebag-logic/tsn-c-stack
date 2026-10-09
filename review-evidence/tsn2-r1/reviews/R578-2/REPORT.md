[R578] NEGATIVE - exact head 6f4ecc9036f9ac2694b05a749cc9105d9c15c05f

Internal independent review R578-2 of kebag-logic/tsn-c-stack PR #20 (Relates to #2). This is a delta review of `4c939ef1..6f4ecc90`, one commit, under the round-2 assignment (issue 2 comment 6086821725) and the public review start (PR #20 comment 6087407523).
Reviewed head `6f4ecc9036f9ac2694b05a749cc9105d9c15c05f`, tree `49585d392468cbf85cdf21ef5c7546cec079c8be`. Diff base `1a9f651cdf7846b8e10ac246a6ef6916960fbb92`; delta parent `4c939ef18741916df85a355973db007b588604e0`.
I recorded the verdict and the open finding (`receipts/independent-verdict.txt`) before reading any earlier review comment. Only after that did I read R578-1 and R579-1.

## Verdict

NEGATIVE, on one new MINOR finding.

All four round-2 items are resolved at this head:
- **F1 (MAJOR, both reviews), scalar grammar:** resolved. The mapper now uses the pinned source's hex-text grammar. A differential run of the source's own parsers against the mapper found 0 divergences in 160,244 scalar cases and 60,084 MAC cases.
- **R578-1's probe:** all ten outcomes are as expected, run unchanged.
- **R578-1-F2, builder defaults:** resolved for `vendor_name`, `group_name`, `entity_id` and `-` MAC separators.
- **R578-1-F3, ENTITY-01:** resolved.
- **Gates:** all 27 Linux gates return 0, RV32 Debug/Release returns 0, 330/330 registered plants are caught, and 19/19 reviewer mapper plants are caught.

The open finding is in the same class as R578-1-F2. The mapper still refuses one source-valid builder key, `entity.firmware_rev`, which has a builder default. It reports it as an "unknown field", and neither the mapping documentation nor the tests cover it.

## Findings

### R578-2-F1 - MINOR - Conformance, Robustness, Tests, Docs
- **Location:**
  - `scripts/milan_entity.py:56-58`: the closed entity field set omits `firmware_rev`, and the refusal is the generic `milan.entity: unknown field or invalid mapping`, which does not name the field.
  - `docs/ENTITY_YAML.md:163-176`: the mapping table has no row for `firmware_rev`.
  - `docs/ENTITY_YAML.md:210`: says the mapper "refuses ... unknown entity fields".
  - PR body, "Round 2": says "Apply builder defaults".
- **Authority:**
  - Issue #2 acceptance item 7: either accept the milan-fpga `entity:` section unchanged, or have a documented mapping cover the difference.
  - Round-2 assignment item 2 (R578-1-F2): apply the builder's defaults, or document each case as a deliberate restriction with its own refusal and one test per form.
  - Pinned milan-fpga `5603c353` `sw/builder/endstation_builder.py` `_load_entity`, lines 3727-3735: `rev = ent.get("firmware_rev", 0)`, a non-negative int, carried only into the AEM `firmware_version` string.
  - The source refuses `firmware_version` and points users to `entity.firmware_rev` instead. Four of the five pinned end-station configs document `firmware_rev: N` (default 0) as the lever for a respin with no CSR-ABI change. Examples: `configs/endstation_ax7101_8x8.yaml:26`, `configs/endstation_arty_current.yaml:93`.
- **Evidence:**
  - `receipts/probe_differential.txt` E1/E2: the source-valid `firmware_rev: 1` and `firmware_rev: 0` are both REFUSED as "milan.entity: unknown field or invalid mapping".
  - E3: the source-invalid `firmware_version` gets the same message, so the diagnostic cannot tell a supported source key from a forbidden one.
  - None of the five pinned configs states the key today. All five map (`receipts/probe_source_configs.txt`), so the AX7101 test cannot reveal this.
- **Impact:**
  - A valid schema-1.2.0 entity section is refused. It is the form milan-fpga recommends for a firmware respin, and the follow-up of item 7 depends on it.
  - The documented mapping calls it unknown, and the refusal is not field-specific.
  - The refusal fails safe: no wrong core bytes are generated, hence MINOR. It is not wording-only, because it changes mapper behaviour, a refusal message and test coverage.
- **Required outcome:** choose one of these:
  - Accept `firmware_rev` with the source's rule (a non-negative integer, not a boolean), drop it as AEM-only with no core field, and add a mapping-table row.
  - Or document a deliberate refusal in the table, with a field-specific message such as `milan.entity.firmware_rev: ...`.

  In either case, add one selftest per form (accepted value or refusal, and a source-invalid value). Make the unknown-key refusal name the offending key. Bring the PR body's "Apply builder defaults" sentence into line with the outcome.
- **Verification:** rerun `scripts/probe_differential.py <clone> <builder>`. E1/E2 should be accepted with an unchanged `identity`, or refused with the documented field-specific message. E3 stays refused. A named selftest fails when the chosen behaviour is reverted.

### SUGGESTION
- **R578-2-S1 (Tests):** the eight mapper plants from the author's REVIEW READY are not in the repository or in published evidence, so nobody else can rerun them. The 330-plant campaign covers only C. Consider registering named mapper plant controls in `scripts/entity_selftest.py`, like the golden-drift controls, so that CONTRIBUTING's "runnable planted defect" holds in the repository for the Python regression. This review substitutes 19 reviewer plants, all caught (`receipts/mapper-mutants/summary.txt`).
- **R578-2-S2 (Docs, Robustness):** `scripts/requirement_records.py:204` reports "imported requirement must address both targets" for the local ENTITY-01 (`receipts/probe_records.txt` R3, "one target"). Consider "requirement must address both targets".
- **R578-2-S3 (Robustness):** the mapper accepts values the source builder refuses:
  - a non-string `entity.locale` (E5);
  - a 64-byte `name`, where the source limit is 63 bytes (E11).

  Both are inside the documented "validate with the product builder first" scope, and neither reaches a core field. Validating them would make the mapper a stricter single entry point.
- **R578-1-S2 (retained as a suggestion):** the round trip uses per-core oracles rather than a parameterised run of an existing core suite. It is unchanged in this round and accepted as meeting item 4.

## Prior public findings at this head

| Finding | State at 6f4ecc90 | Evidence |
|---|---|---|
| R578-1-F1 / R579-1-F1 (MAJOR) | **Resolved** | See note 1. |
| R578-1-F2 (MINOR) | **Resolved** as stated | See note 2. The residual sibling `firmware_rev` is R578-2-F1. |
| R578-1-F3 (MINOR) | **Resolved** | See note 3. |
| R578-1-R1 (RESIDUE) | **Resolved** | `docs/ENTITY_YAML.md:179` uses the exact fix wording. |
| R578-1-R2 (RESIDUE) | **Resolved** | `docs/ENTITY_YAML.md:57-58` uses the exact fix wording. |
| R578-1-S1 (SUGGESTION) | **Addressed by documentation** | `docs/ENTITY_YAML.md:54-55` documents YAML 1.1 integer forms. `test_yaml_integer_compatibility` pins them. |
| R578-1-S2 (SUGGESTION) | **Retained** as a suggestion | Unchanged. |

1. **R578-1-F1 / R579-1-F1:**
   - `hex_text`, at `scripts/milan_entity.py:15-24`, is the source `HEX_TEXT`/`_hex_text` (builder L1349-1377), with the same regex, string-only rule, digit bound including leading zeros, and base 16.
   - Reserved model IDs (L1380), the OUI I/G bit (L3784-3792), pin precedence with literal validation (L4491-4498) and the MAC parser (L3279-3308) match the source.
   - `probe_mapper.py` (R578-1's script, byte-identical, sha256 `f5228744...`) gives P1 = 0x1234567890123456, P2 = 0x020000FFFE000001 and P3-P8 accepted. P9 and P10 are refused as unquoted.
   - R579-1's six cases all map to their source values (`receipts/probe_r579_cases.txt`).
   - The compiled CLI identity test emits 0x0000001234567890 in ADP and ACMP (`entity-controls` passed).
   - The differential run found 0 divergences.
   - A planted `int(...,10)` for digit-only strings is caught by `test_mapping_digit_only_entity_id` and three other tests.
2. **R578-1-F2:**
   - Defaults are implemented at `scripts/milan_entity.py:60-62`, and `-`/`:`/12-digit MAC forms at `:34-48`.
   - P5-P8 are accepted with builder-equivalent values.
   - One test per form: `test_mapping_default_vendor_name`, `test_mapping_default_group_name`, `test_mapping_default_entity_id` and `test_mapping_mac_spellings`/`_refusals`.
3. **R578-1-F3:**
   - The ENTITY-01 row is in `docs/REQUIREMENTS.md:109` with its issue-2 origin, text and clauses.
   - The `docs/TRACEABILITY.md:53` origin is issue 2.
   - `requirements.json` carries origin, targets and the test method.
   - In `requirement_records.py`, `documented()`/`check_document()` refuse a record missing from REQUIREMENTS.md, and the selftest removes each of the 43 rows.
   - Probe R1 (an added record with no row is refused), R2 (the removed ENTITY-01 row is refused) and R3 (wrong or missing origin and a non-test method are refused) all pass.

## Five lenses (artifact-specific)

- **Conformance:**
  - Checked the mapper against pinned builder `5603c353` (sha256 `4372d698...`, 310,308 bytes). Its functions were executed verbatim by AST extraction.
  - Checked the AX7101 fixture against the pinned config (sha256 `6e1463f6...`, 12,389 bytes, matched in `configs/compat/ax7101.json`).
  - All five pinned shapes map.
  - ENTITY-01 clauses are unchanged from the round-1 baseline.
  - The portable range for entity_id is 1..2^64-2 (E7/E8 refused precisely). This restriction is documented at `docs/ENTITY_YAML.md:191`.
  - **UNCLEAN** (F1).
- **RTL (implementation: generated C and both targets):**
  - Round 2 changes no C, header, golden or generated file.
  - `entity-golden` returns rc 0.
  - The RV32 generated-object hashes and the smoke test pass for all four entities (`receipts/gates/rv32-results.json`).
  - The compiled CLI identity check produces matching ADP and ACMP identities.
  - **CLEAN.**
- **Robustness:**
  - Differential grammar run: 220,328 cases, plus 14 refusal forms × 5 fields.
  - Non-string forms (int, bool, float, null, list, mapping) are refused as the source does.
  - Null versus default behaviour is documented and refused.
  - The YAML loader types match `yaml.safe_load` for Y1-Y7.
  - **UNCLEAN** (F1).
- **Tests:**
  - 172 entity selftests pass.
  - 19/19 reviewer mapper plants are caught. Each has named failing tests, and the unplanted control passes.
  - 330/330 registered plants are caught, as are the 43 missing-row controls and 28 metadata controls.
  - No test covers `firmware_rev`.
  - **UNCLEAN** (F1).
- **Docs:**
  - Reviewed `docs/ENTITY_YAML.md`, REQUIREMENTS, TRACEABILITY, VERIFICATION and requirements.json in the delta, plus the PR body.
  - The scalar, MAC and default rules match the code.
  - The `firmware_rev` gap and the "Apply builder defaults" claim make this lens **UNCLEAN** (F1).

## Executed evidence (this review, exact head, disposable clones under scratch/)
- **Toolchain** (`receipts/gates/*.env`):
  - GoogleTest 1.14.0 through `PKG_CONFIG_PATH`, `CMAKE_PREFIX_PATH` and `LD_LIBRARY_PATH`. pkg-config reports 1.14.0.
  - The pinned directory first on PATH supplies `clang-18` 18.1.3. Unversioned `clang`/`clang++` resolve to host 23.1.1, which the sanitizer build uses (recorded, not claimed as 18).
  - GCC 16.2.1, riscv64-elf-gcc 16.2.0, QEMU 11.1.2.
- **Linux:** `validate.py --work build-validation --jobs 6 --graphs` returned rc 0, with 27/27 gates at 0 (`receipts/gates/validate/gates.json` and per-gate logs).
  - Mutation: `{"CAUGHT": 330, "ESCAPED": 0, "ERROR": 0}`. `receipts/gates/mutation-plants.json` lists every plant and the sha256 of the full results.
  - Coverage: 100% lines and branches after the existing exclusions.
  - Traceability: 43 requirements, 117 declarations, 391 instances.
- **RV32:** `baremetal.py --work build-rv32 --jobs 4` returned rc 0 for Debug and Release (`receipts/gates/baremetal.log`, `rv32-results.json`).
- **Probes:**
  - `probe_mapper.py` (unchanged).
  - `probe_differential.py`.
  - `probe_mapper_mutants.py` (19 plants, each in its own copy).
  - `probe_records.py`.
  - `probe_r579_cases.py`.
  - `probe_source_configs.py`.
  - Gate runner `run_gates.sh`, which needs `TSN_TOOLS`.
  - `fetch_source.sh`.
  - `integrity.sh`.
- **Hosted, exact head** (`receipts/hosted-ci.txt`):
  - pull_request run 37974976910 and push run 37974966938.
  - In each, the `quality` and `bare-metal` jobs ran and succeeded, and their install, validate and evidence steps ran with success. No step was skipped.
  - Hosted acceptance remains the manager's.
- **Author source-head receipts:** the round-2 REVIEW READY (issue 2 comment 6087035547) reports 27 gates, RV32 and 330 plants. The published evidence tree `942742507d7b.../review-evidence/tsn2-r1` is round-1 author evidence for head `4c939ef1`. I found no published round-2 author receipt files, and the eight author mapper plants are not public.
- **Restoration** (`receipts/integrity.txt`):
  - The review clone is at the exact head and tree, and the index tree matches.
  - The worktree is clean, including untracked and ignored files, after I removed the bytecode cache my probes created.
  - All 96 tracked blobs match by bytes and mode.
  - The head has no submodule gitlinks.
- **Process:** no source fix, commit, push, GitHub write or other checkout edit was made.

## Reviewer-owned ledger

| lens | CLEAN/UNCLEAN | examined artifacts | covering round | exact head |
|---|---|---|---|---|
| Conformance | UNCLEAN (R578-2-F1) | mapper vs pinned builder 5603c353 grammar, defaults, model/OUI/caps rules and entity keys; five pinned configs; ENTITY-01 clauses and origin | R578-2 | 6f4ecc9036f9ac2694b05a749cc9105d9c15c05f |
| RTL (generated C, both targets) | CLEAN | unchanged goldens (entity-golden rc 0); RV32 Debug/Release objects and smoke; compiled CLI identity in ADP and ACMP | R578-2 | 6f4ecc9036f9ac2694b05a749cc9105d9c15c05f |
| Robustness | UNCLEAN (R578-2-F1) | 220,328-case differential; non-string and malformed refusals; null vs default; loader typing; source-valid key refusal | R578-2 | 6f4ecc9036f9ac2694b05a749cc9105d9c15c05f |
| Tests | UNCLEAN (R578-2-F1) | 172 entity selftests; 19 reviewer mapper plants; 330-plant campaign; requirement and record controls; hosted step results | R578-2 | 6f4ecc9036f9ac2694b05a749cc9105d9c15c05f |
| Docs | UNCLEAN (R578-2-F1) | ENTITY_YAML mapping and scalar sections, REQUIREMENTS, TRACEABILITY, VERIFICATION, requirements.json, PR body | R578-2 | 6f4ecc9036f9ac2694b05a749cc9105d9c15c05f |

## Real limits
- No licensed standards text was available. Clause claims were checked against the reviewed baseline numbering only, and ENTITY-01's clauses are unchanged from round 1.
- The milan-fpga builder was not executed as a whole, because it needs its submodules. Its parsers were executed verbatim from the pinned source, and the remaining behaviour was compared by reading the source.
- The author's eight mapper plants are not public and were not run. The 19 reviewer plants substitute for them.
- Concurrency: the Linux bank used `--jobs 6` (its driver runs up to four tasks concurrently) and RV32 used `--jobs 4`. The mapper plant probe used 3 workers.
- No manager source bank runs at this head, and none is claimed or inferred.
- Physical calibration was NOT RUN. Field skips and simulated smoke success are not hardware proof.

## Pending manager duties
- Arrange correction and re-review of R578-2-F1.
- Validate the merge-turn current-dev candidate with the builder and native banks (source base `1a9f651c`, live dev `7c1b52be`), and link the receipts.
- Hosted and act acceptance.
- File the milan-fpga follow-up issue for item 7.
- Obtain the required two positive reviews.
- Branch `dev-linux` was out of scope and untouched.

R578-2 FINISHED
