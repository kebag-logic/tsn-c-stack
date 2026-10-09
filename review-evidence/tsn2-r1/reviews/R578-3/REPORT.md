[R578] POSITIVE - exact head 64888e91fa5bc86c6c0e4efbf707fff3174d10e1

Internal independent delta review, round R578-3, of kebag-logic/tsn-c-stack issue #2 / PR #20.
Exact head `64888e91fa5bc86c6c0e4efbf707fff3174d10e1`, tree `3c9a206d21786c0c4d5921a36e58aa66fb59aa47`.
Delta reviewed: `6f4ecc90..64888e91`, one commit. It touches five files: `scripts/milan_entity.py`, `scripts/entity_selftest.py`, `scripts/requirement_records.py`, `docs/ENTITY_YAML.md` and `docs/VERIFICATION.md`.
Earlier rounds stand for unchanged files. The full source-base diff `1a9f651c..64888e91` was scanned only to confirm that this delta is the only change since the R578-2 head.

## Verdict

POSITIVE. No BLOCKER, MAJOR or MINOR finding is open at this head.

- R578-2-F1 = R579-2-F1 (MINOR) is **resolved**.
- R578-2-S1 is **adopted**: 13 named mapper plants are registered in the repository and all are caught.
- R578-2-S2 is **adopted**.
- Three new RESIDUE prose items (R578-3-R1, R578-3-R2, R578-3-R3) and one new SUGGESTION (R578-3-S1) are recorded. None of them makes the verdict NEGATIVE.

My independent verdict was recorded in `receipts/independent-verdict.txt` (2026-10-09T20:10:59Z) before I read any prior public finding text. This report keeps that verdict. R578-3-R2 and R578-3-R3 came from my own later document checks, not from any prior finding; no prior review mentions either.

## Scope reconstruction

- **Rules.**
  - Repository rules come from `CONTRIBUTING.md` (there is no `AGENTS.md`).
  - A regression needs a failing assertion and a runnable planted defect.
  - Commits use one-line subjects with no body. The head commit has a one-line subject and no body or trailer.
- **Issue #2 frozen acceptance, item 7.** The milan-fpga `entity:` section is accepted unchanged, or a documented mapping covers the difference.
- **Round-3 assignment** (issue comment 6088075512):
  - Item 1: accept `firmware_rev` with the source rule (optional, non-negative int, never bool, default 0, AEM `firmware_version` only, identity unchanged).
  - Item 1: `firmware_version` stays refused and its refusal points to `entity.firmware_rev`.
  - Item 1: every unknown key is refused by name.
  - Item 1: one selftest per form, a mapping-table row, and a PR-body defaults sentence that matches.
  - Item 2: register the mapper plants in `scripts/entity_selftest.py`, including the eight earlier plants and an item-1 revert.
- **Interface authority.** Pinned milan-fpga `5603c353137e90c1fa95429f6d00ef7a2298d9ee`:
  - `sw/builder/endstation_builder.py` `_load_entity`, lines 3705-3752;
  - `avdecc/aem_descriptors.py` `firmware_version_string`, lines 72-94;
  - `hdl/common/csr/milan_csr.sv` `VERSION = 32'h0002_0060`.
  - These were fetched read-only. Their hashes are in `receipts/source-hashes.txt`, and the builder and config hashes are identical to the round-2 fetch. The `gen_aem_store.py`, `aem_descriptors.py` and `milan_csr.sv` hashes are in the "Executed evidence" table below.

## Findings

### R578-3-R1 - RESIDUE - Docs
- **Location:** `docs/ENTITY_YAML.md:244`: "The accepted entity keys are the keys read by the source entity loader."
- **Authority:** In the pinned builder, `_load_entity` (lines 3705-3752) reads `firmware_version`, `firmware_rev`, `name`, `vendor_name`, `serial_number`, `group_name`, `entity_id` and `locale`, and reads `entity_capabilities` through `_verify_entity_capabilities`. The other three accepted keys are read elsewhere: `entity_model_id` and `model_id_pin` in `load_config` (lines 4490-4491), and `vendor_oui` in `_vendor_oui` (line 3786).
- **Evidence:** I checked this with an AST lookup of the enclosing source functions. The accepted set at `scripts/milan_entity.py:56` exactly equals the set of `entity:` keys the source builder reads, minus the refused `firmware_version`. Only the attribution to "the entity loader" is loose.
- **Impact:** None on behaviour, tests or claims. A reader who checks `_load_entity` alone would not find three accepted keys there.
- **Exact fix:** "The accepted entity keys are the `entity:` keys the source builder reads."
- **Verification:** Text check only.

### R578-3-R2 - RESIDUE - Docs
- **Location:** `docs/ENTITY_YAML.md:195`. The "source loader" link anchors `#L3720-L3730`, which covers the `firmware_version` refusal and the `firmware_rev` check. The derivation the sentence describes, `firmware_version=rtl_firmware_version(rev)`, is at line 3734.
- **Impact:** A link-range precision issue only. The row's statements are correct (see `receipts/probe_firmware_rev.txt`).
- **Exact fix:** change the anchor to `#L3720-L3735`.
- **Verification:** Open the link and check that lines 3727-3735 are shown.

### R578-3-R3 - RESIDUE - Docs
- **Location:** `docs/ENTITY_YAML.md:168-169`. The new plant table, whose last row is at `:168`, is followed directly by the existing prose at `:169-172` with no blank line.
- **Authority:** GitHub-flavored Markdown ends a table only at a blank line or another block. A following plain line becomes a table row.
- **Evidence:** `receipts/probe_render.txt`, from a read-only GET of GitHub's rendered file:
  - At `6f4ecc90`: 0 absorbed rows.
  - At `64888e91`: 4 absorbed rows. Four sentences render as plant-table rows with empty "Planted defect" and "Required failing test" cells: "The quality workflow runs regeneration and all host checks.", "The RV32 gate checks ...", "The existing coverage denominator ... must remain at 100%." and "It measures production cores ...".
- **Classification:** RESIDUE, not MINOR.
  - The four sentences remain verbatim, and the defect is in prose layout only.
  - It changes no measurement, figure, verdict, test, code, generated artifact, conformance or clause claim, and touches no privacy rule.
  - The fix adds one blank line.
- **Impact:** A reader may take the four statements for plant rows that have no required test.
- **Exact fix:** Insert one empty line between `docs/ENTITY_YAML.md:168` (the `unknown-key-generic` row) and `:169` ("The [quality workflow]...").
- **Verification:** Rerun `scripts/probe_render.sh <dir> <new head>`. It should report 0 absorbed prose rows.

### R578-3-S1 - SUGGESTION - Conformance, Robustness
- **Location:** `scripts/milan_entity.py:64-66`.
- **Evidence:** `receipts/probe_firmware_rev.txt`, class `BOUND`. The source renders `firmware_version` as `"{major}.{minor}.{rev}"`. With the pinned `VERSION` 0x0002_0060 this is "2.96.rev", and the source refuses it above 63 bytes, so a revision of 59 or more decimal digits is refused. The mapper accepts any non-negative int.
- **Disposition:** Not a defect.
  - The rule the round-3 assignment froze is implemented exactly.
  - The value reaches no core field, and the projection is unchanged.
  - The exact bound depends on the gateware `VERSION`, which the mapper cannot see.
  - The documentation already says to validate the full product configuration with its own builder first (`docs/ENTITY_YAML.md:242-243`).
- **Option:** Refuse revisions longer than 51 decimal digits. That is the budget at the widest possible "65535.65535." prefix, so it can never refuse a source-valid value. This is the same class as the retained R578-2-S3.

## Prior public findings at this head

| ID | Disposition | Evidence at 64888e91 |
|---|---|---|
| R578-2-F1 = R579-2-F1 (MINOR) | **Resolved** | See note 1. |
| R578-2-S1 (SUGGESTION) | **Adopted** | 13 registered plants: `MAPPER_PLANTS` in `scripts/entity_selftest.py:453-468`, run by `mapper_plant` at `:478-491`. See note 2. |
| R578-2-S2 (SUGGESTION) | **Adopted** | `scripts/requirement_records.py:204` now reads "requirement must address both targets". The traceability check and selftest pass, including the `missing target` control (`receipts/traceability-*.txt`). |
| R578-2-S3 (SUGGESTION) | **Retained** as a suggestion | Unchanged and not adopted by the author. E5 and E11 are unchanged in `receipts/probe_differential.txt`. |
| R578-1-F1 / R579-1-F1 (MAJOR) | **Resolved** (round 2); not regressed | Differential at this head: 160,244 scalar and 60,084 MAC cases, 0 divergences. |
| R578-1-F2, R578-1-F3 (MINOR) | **Resolved** (round 2); not regressed | Defaults tests pass (196/196). Traceability check and selftest rc 0. |
| R578-1-R1, R578-1-R2 (RESIDUE) | **Resolved** (round 2) | Files are unchanged at those lines. |
| R578-1-S1, R578-1-S2 (SUGGESTION) | As disposed in round 2; R578-1-S2 **retained** | Unchanged. |

Notes:

1. **R578-2-F1 = R579-2-F1.**
   - `scripts/milan_entity.py:56-66`:
     - accepts `firmware_rev` with default 0 and `type(...) is int` and `>= 0`;
     - refuses `firmware_version` first, with the pointer to `entity.firmware_rev`;
     - names the first sorted unknown key (`milan.entity.<key>: unknown field`).
   - My round-2 `probe_differential.py` was rerun byte-unchanged (`cmp` against the round-2 copy). Compared with the round-2 receipt, exactly three lines changed:
     - E1 (`firmware_rev: 1`) is ACCEPTED, with identity equal to the golden;
     - E2 (`firmware_rev: 0`) is ACCEPTED, with identity equal to the golden;
     - E3 (`firmware_version`) is REFUSED with the pointer message.
   - The new probe `probe_firmware_rev.py` extracts the three source statements verbatim from `_load_entity`. It compares 37 YAML forms, each loaded by the side's own loader, and 7 key cases. Results:
     - 0 divergences, apart from the 4 pathological BOUND cases (R578-3-S1);
     - every accepted value leaves the whole projection equal to `configs/ax7101.yaml`.
   - Selftests exist per form: omitted, 0 and 1 are accepted with identity unchanged; true, false, -1, "1", 1.0 and null are refused with `milan.entity.firmware_rev: expected a non-negative integer`; `firmware_version` is refused; `typo` is refused by name.
   - The mapping-table rows are at `docs/ENTITY_YAML.md:195-196`, and the null rule is at `:230`.
   - The PR-body "Round 3" sentence ("applies every source entity default: `vendor_name`, `group_name`, `entity_id` and `firmware_rev`") matches the source. `_load_entity` defaults exactly these four; `locale` and `model_id_pin` have no default. The "Round 2" paragraph is a historical log, and the Round 3 sentence supersedes it.
2. **R578-2-S1.**
   - With `--select mapper_plant` at head, 13 of 13 pass (`receipts/baseline/selftest-mapper-plants.txt`).
   - The docs table at `docs/ENTITY_YAML.md:154-168` equals the registry, name for name and killer for killer (`receipts/probe_docs.txt`). Its rendering defect is R578-3-R3.
   - A non-matching `--select` exits 2 rather than passing vacuously.
   - Each control asserts that the fragment count is 1 and that the killer passes unplanted. When planted, the killer must FAIL with no error and no skip, and only the killer may fail.
   - Meta mutants T1-T3 weaken a killer, and the matching registered plant control then FAILs. This shows the controls are not vacuous.

## Five lenses

- **Conformance - CLEAN.**
  - Compared the mapper's `firmware_rev`/`firmware_version`/unknown-key behaviour with the pinned source's `_load_entity`, extracted by AST (`receipts/probe_firmware_rev.txt`).
  - The accepted key set equals the source's `entity:` key set.
  - The round-2 scalar/MAC differential shows 0 divergences in 220,328 cases.
  - All five pinned end-station configs still map (`receipts/probe_source_configs.txt`).
  - The clause citations in the new row (IEEE 1722.1-2021 7.2.1 Table 7-2; 6.2.2.8) are consistent with the repository's existing use (`src/adp.c:109`) and with the source's own docstring (Table 7-2 offset 116).
  - Open item: R578-3-S1 (suggestion).
- **RTL - CLEAN (no RTL or C in scope).**
  - The delta contains no RTL, C, header, generated configuration or golden file (`git diff --name-only 6f4ecc90..64888e91`: five files, Python and Markdown only).
  - The generated-C interface the mapper feeds is unchanged: examples check rc 0, and AX7101 projection equals the tracked golden.
  - The pinned simulator was not needed and was not used.
- **Robustness - CLEAN.**
  - Non-mapping entity, explicit null, bool (both values), float, quoted string, negative, list and mapping are each refused with a field-specific message.
  - YAML 1.1 integer spellings (`0x10`, `0b101`, `1_000`, `+5`, `-0`, `1:30`, `007`) resolve identically in the source's `safe_load` and in the mapper's `Loader`.
  - `firmware_version` takes precedence over `firmware_rev` and over unknown keys.
  - Several unknown keys report the first one in sorted order, deterministically.
  - Open item: R578-3-S1 (suggestion).
- **Tests - CLEAN.**
  - The full schema selftest passes 196/196 at head (`receipts/baseline/selftest-full.txt`). This includes 14 firmware tests and 13 registered plant controls.
  - I re-applied the mutants myself as file edits on disposable copies of the exported head tree, then ran the full selftest each time (`receipts/mutants.txt`, per-mutant logs in `receipts/mutant-logs/`): 18 of 18 caught by their named test failing an assertion (never an ERROR in the named test).
    - Five item-1 reverts, R1-R5: accept removed, bool/float accepted, negative accepted, `firmware_version` given the generic refusal, unknown key unnamed.
    - Seven further item-1 mutants, X1-X7: no default 0, null treated as default, string coerced, identity altered by the revision, wrong key named, pointer text dropped, zero refused.
    - Three of the original eight, O1-O3: base-0 parse, digit bound off by one (a variant of the registry edit), vendor default changed.
    - Three meta mutants, T1-T3.
  - X1, X7 and O1 also make unrelated mapping tests ERROR, because they refuse or misparse the base fixture. This collateral is labelled CAUGHT+COLL, and in each case the named test itself FAILs.
  - Traceability check and selftest rc 0.
  - Hosted `quality` and `bare-metal` at the exact head both succeeded, push and pull_request events, with no step skipped (`receipts/hosted-ci.txt`). In the quality job log, all 27 `validate.py --graphs` gates report rc 0, including `entity-golden` and `entity-controls`.
- **Docs - CLEAN.**
  - The `docs/ENTITY_YAML.md` plant table (`:144-168`) equals the registry.
  - The mapping rows (`:195-196`), null rule (`:230`) and refusal summary (`:239-247`) match the behaviour.
  - The `docs/VERIFICATION.md:21` row names the 13 plants, and the documented rerun command works as stated.
  - The PR-body Round 3 text matches the behaviour. Its stated 220,328 differential cases equal 160,244 + 60,084.
  - Open items: RESIDUE R578-3-R1, R578-3-R2 and R578-3-R3, which are prose only. R3 is the rendered table absorbing four prose lines.

## Executed evidence (this review, exact head)

All runs were on a `git archive` export of HEAD under `scratch/`, with the clone left untouched. Paths in receipts are redacted to `<packet>`.

| Check | Result | Receipt |
|---|---|---|
| Full entity selftest | 196 tests OK, rc 0 | `receipts/baseline/selftest-full.txt` |
| `--select mapper_plant` | 13 OK, rc 0 | `receipts/baseline/selftest-mapper-plants.txt` |
| `--select firmware` | 14 OK, rc 0 | `receipts/baseline/selftest-firmware.txt` |
| `--select` no match | rc 2, explicit message | `receipts/baseline/selftest-nomatch.txt` |
| Examples drift check | rc 0 | `receipts/baseline/examples-check.txt` |
| Reviewer mutants (18) | 18 caught by name, rc 0 | `receipts/mutants.txt`, `receipts/mutant-logs/` |
| Round-2 differential, unchanged | 0 scalar/MAC divergences; E1/E2 accepted, E3 refused | `receipts/probe_differential.txt` |
| Source-extracted firmware rule | 0 divergences; 4 BOUND (S1) | `receipts/probe_firmware_rev.txt` |
| Five pinned configs | all map | `receipts/probe_source_configs.txt` |
| Docs table vs registry | equal, 13 | `receipts/probe_docs.txt` |
| Rendered `ENTITY_YAML.md` (read-only GET) | 0 absorbed prose rows at 6f4ecc90; 4 at head (R3) | `receipts/probe_render.txt` |
| Traceability check and selftest (pinned GoogleTest 1.14.0, Clang 18 on PATH) | rc 0 / rc 0 | `receipts/traceability-check.txt`, `receipts/traceability-selftest.txt` |
| Hosted jobs at exact head | 4 jobs success, 32 steps success, 0 skipped | `receipts/hosted-ci.txt` |
| Clone integrity after probes | HEAD, tree, index, all 96 blobs bytes/modes OK, clean; 0 gitlinks in tree (none required) | `receipts/integrity.txt` |
| Source authority hashes | builder and configs identical to round 2; `gen_aem_store.py` 9d04942b..., `aem_descriptors.py` e279883f..., `milan_csr.sv` c3106a14... | `receipts/source-hashes.txt` |

Scripts are portable and take their paths as arguments: `scripts/baseline.sh`, `mutants.py`, `probe_firmware_rev.py`, `probe_differential.py` (round-2 copy, byte-identical), `probe_source_configs.py`, `probe_docs.py`, `probe_render.sh`, `fetch_source.sh` and `integrity.sh`.

## Reviewer-owned ledger

| Lens | CLEAN/UNCLEAN | Examined artifacts | Covering round | Exact head |
|---|---|---|---|---|
| Conformance | CLEAN | mapper `firmware_rev`/`firmware_version`/unknown-key rule vs pinned `_load_entity` (AST-extracted) and `firmware_version_string`; source `entity:` key set; five pinned configs; 220,328-case scalar/MAC differential; new clause citations | R578-3 | 64888e91fa5bc86c6c0e4efbf707fff3174d10e1 |
| RTL | CLEAN (no RTL/C in delta) | delta file list; generated-example drift check; AX7101 projection equality | R578-3 | 64888e91fa5bc86c6c0e4efbf707fff3174d10e1 |
| Robustness | CLEAN | 37 YAML forms through both loaders; null/bool/float/string/list/mapping/negative refusals; key precedence and naming; non-mapping entity | R578-3 | 64888e91fa5bc86c6c0e4efbf707fff3174d10e1 |
| Tests | CLEAN | 196 selftests; 13 registered plant controls; 18 reviewer file-level mutants incl. 5 item-1 reverts, 3 of the original eight and 3 meta; traceability check and selftest; exact-head hosted jobs and steps | R578-3 | 64888e91fa5bc86c6c0e4efbf707fff3174d10e1 |
| Docs | CLEAN (RESIDUE R578-3-R1, R578-3-R2, R578-3-R3) | `docs/ENTITY_YAML.md` plant table (source and GitHub rendering), mapping rows, null rule, refusal summary; `docs/VERIFICATION.md` row (rendering checked); PR body Round 3 and defaults sentence; commit subject | R578-3 | 64888e91fa5bc86c6c0e4efbf707fff3174d10e1 |

Unchanged files are covered by R578-1 and R578-2 and were not re-reviewed.

## Real limits

- No manager source bank exists at this exact head, and none is claimed or inferred. The source-head execution evidence is:
  - the author's REVIEW READY gate claims (27 Linux gates, RV32 Debug/Release, 330 C plants), which I did not re-run;
  - the exact-head hosted jobs above;
  - this review's focused runs.
- The published evidence tree `review-evidence/tsn2-r1` at `94274250` holds round-1 author material for an earlier head. It is not evidence for this head.
- Not run: the full `validate.py` and `baremetal.py` banks, the C mutation campaign, coverage, RV32, Docker/act, hardware. The delta changes no C, so their round-2 results apply by file identity, but I did not re-execute them.
- Physical calibration: NOT RUN. Field skips are not hardware proof.
- The BOUND comparison in `probe_firmware_rev.py` reproduces the source's 63-byte check with the pinned RTL `VERSION`. It does not import the source modules.
- The other internal-round reviewer's round-2 probe was not executed. My own source-extracted probe covers its cases.

## Pending manager duties

- Carry RESIDUE R578-3-R1, R578-3-R2 and R578-3-R3 to the residue checklist with their exact fixes.
- Obtain the second independent review at this head.
- Validate the final current-dev merge candidate (source base `1a9f651cdf7846b8e10ac246a6ef6916960fbb92`, live dev `7c1b52bee26b497080ee22b1c1986109f80a5ee7`) with the builder and native banks, and publish the receipts. Source validation is distinct from that candidate.
- Own hosted/act acceptance.
- File or link the milan-fpga integration follow-up that issue item 7 requires.
- Publish this report.

R578-3 FINISHED
