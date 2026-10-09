[R578] NEGATIVE - exact head 4c939ef18741916df85a355973db007b588604e0

Internal independent review R578-1 of kebag-logic/tsn-c-stack PR #20 (Relates to #2, assignment comment 6086063941, REVIEW READY 6086582177).
Reviewed head `4c939ef18741916df85a355973db007b588604e0`, tree `f1adface0d762b1b3a456a6159d750c50cf623f1` = `0a1a14a1` (generator, schema, tests, docs) merged with main `51870377` (PR #19). Diff base `1a9f651c`.
The verdict and findings below were fixed before any earlier review comment was read. No earlier public review finding exists on PR #20 (no reviews, no review comments; only the two review-start notices).

## Verdict

NEGATIVE. The generator, schema, golden checks, round trips, CI wiring, docs and merge are sound, and every gate passes on both targets. The milan-fpga mapper (acceptance item 7) does not parse the source schema's quoted hex-text fields with the source grammar. One builder-valid explicit entity ID is silently mapped to a different value (F1, MAJOR). Builder-valid declarations and defaulted fields are refused (F1, F2). ENTITY-01 is missing from the requirements document, and the generated matrix labels it as import baseline (F3, MINOR).

## Findings

### R578-1-F1 - MAJOR - Conformance, Robustness, Tests, Docs
- **Location:** `scripts/milan_entity.py:23-24` (`entity_id` via `int(x, 0)`), `:25-27` (`entity_model_id`/`model_id_pin` via `int(x, 0)`), `:31` (`vendor_oui` must be a YAML integer), `:33` (`entity_capabilities` compared with an int using `!=`). `scripts/entity_selftest.py:176-189` plants only unquoted integers. `docs/ENTITY_YAML.md:162-163,188` claims these are mapped or checked.
- **Authority:** Issue #2 item 7 says the documented mapping covers the difference, and milan-fpga is then switched to this generator. The pinned source grammar is milan-fpga `5603c353`, `sw/builder/endstation_builder.py`:
  - `HEX_TEXT` (line 1349) is `(?:0[xX])?([0-9A-Fa-f](?:_?[0-9A-Fa-f])*)`. `_hex_text` (1354) reads it as base 16 and refuses non-strings ("quote the hexadecimal value").
  - `entity.entity_id` is read through `_fmt64` (1390) and `derive_entity_id` (5009) uses `int(eid, 16)` (5018).
  - `vendor_oui` and `entity_capabilities` are read through `_declared_uint` (3773), from `_vendor_oui` (3778) and `_verify_entity_capabilities` (3795).
- **Evidence:** `receipts/probe_mapper.txt` (portable script `scripts/probe_mapper.py`):
  - P1: the explicit `entity_id: "1234567890123456"` is 0x1234567890123456 for the builder. The mapper **accepts** it as 0x000462D53C8ABAC0.
  - P2: `"020000FFFE000001"` is refused.
  - P3: `vendor_oui: "0x001BC5"` agrees with the resolved model ID but is refused.
  - P4: `entity_capabilities: "0x0000C588"` agrees with the resolved value but is refused as "contradicts".
  - P9 and P10: the selftest's integer plants are values the builder itself refuses.
- **Impact:** The silent case gives a generated ADP/ACMP entity ID that differs from the one the product's builder and ENTITY descriptor advertise. There is no diagnostic. The documented OUI and capability agreement checks can never pass for a valid source. The tests use source-invalid types, so they cannot detect either defect.
- **Required outcome:** Parse `entity_id`, literal `entity_model_id`, `model_id_pin`, `vendor_oui` and `entity_capabilities` with the source hex-text grammar: quoted, optional `0x`, single underscores, digit-count bound, base 16. Refuse non-string forms as the source does. Add selftest cases with source-valid strings: a digit-only explicit `entity_id`, a `0x`-less entity ID, and agreeing and contradicting `vendor_oui` and `entity_capabilities` strings.
- **Verification:** Rerun `scripts/probe_mapper.py`:
  - P1 maps to 0x1234567890123456 and P2 to 0x020000FFFE000001.
  - P3 and P4 are accepted, and contradicting strings are refused.
  - P9 and P10 are refused as unquoted.
  - Reintroducing `int(x, 0)` makes a named selftest case fail.

### R578-1-F2 - MINOR - Conformance, Robustness, Docs, Tests
- **Location:** `scripts/milan_entity.py:22` requires `entity_id`, `vendor_name` and `group_name`. `:42` passes `platform.mac_address` through unchanged. `docs/ENTITY_YAML.md:162,164,167,188` describes the mapping.
- **Authority:** Issue #2 item 7. The builder `_load_entity` (lines 3733, 3737, 3739) defaults `vendor_name` to "Kebag Logic", `group_name` to "" and `entity_id` to `mac-derived`. `MAC_OCTETS` (1351) accepts `:` or `-` separators.
- **Evidence:** `receipts/probe_mapper.txt` P5-P8: each builder-valid input is refused with "missing or invalid mapping input" or a MAC syntax error. None of the five pinned shapes uses these forms (`receipts/mapper-five-shapes.txt`: all five map), so the AX7101 test cannot show this.
- **Impact:** Valid 1.2.0 entity sections are refused. The mapping table says fields map "unchanged" and does not state the source defaults. This fails safe, hence MINOR.
- **Required outcome:** Apply the builder defaults and normalise `-` separators. Alternatively, document each case as a deliberate restriction with its own precise refusal. Test each case.
- **Verification:** Probes P5-P8 are accepted with builder-equivalent values, or refused with the documented messages. One selftest case per form.

### R578-1-F3 - MINOR - Docs, Conformance
- **Location:**
  - `docs/TRACEABILITY.md:53`: the ENTITY-01 origin is "Import baseline", linked to REQUIREMENTS.md.
  - `docs/REQUIREMENTS.md:18-36`: the requirement table has no ENTITY-01, and the requirement is defined nowhere else.
  - `docs/requirements.json:885`: the record has no origin.
  - `scripts/traceability.py:116`: a record without an origin defaults to "Import baseline".
- **Authority:** CONTRIBUTING.md says "A protocol change updates its requirement, tests and traceability". REQUIREMENTS.md:16 says that table retains the import baseline. ENTITY-01 originates in issue #2.
- **Impact:** The generated matrix misstates the provenance of a new requirement, and its link leads to a document that does not state the requirement. This is a generated-artifact claim, not wording-only.
- **Required outcome:** Add ENTITY-01 (text, clauses, issue-2 origin) to REQUIREMENTS.md. Make the matrix show the issue-2 origin instead of "Import baseline", then regenerate. Preferably, the traceability selftest refuses a record that is absent from REQUIREMENTS.md.
- **Verification:** ENTITY-01 has a row in REQUIREMENTS.md, the TRACEABILITY.md row names issue 2, and `traceability.py --selftest` passes.

### RESIDUE
- **R578-1-R1:** `docs/ENTITY_YAML.md:176` says "The mapping test produces the tracked AX7101 YAML exactly". The test compares parsed mappings (`scripts/entity_selftest.py:166`). The mapper's bytes differ from `configs/ax7101.yaml` in key order only, and the generated C is byte-identical (`receipts/ax7101-mapping.txt`). Exact fix: "The mapping test produces a mapping equal to the tracked AX7101 YAML and checks every ADP value."
- **R578-1-R2:** `docs/ENTITY_YAML.md:55` says "Quote MAC addresses and names.", but all four `configs/*.yaml` leave them unquoted. They parse as strings, and unquoted numbers are refused (probe R2). Exact fix: "Quote a MAC address or name when YAML would otherwise read it as a number, boolean or date. A value of another type is refused."

### SUGGESTION
- **R578-1-S1:** YAML 1.1 integer forms are accepted: `identify_control_index: 1:00` becomes 60, and leading-zero octal is accepted (`receipts/probe_generator.txt` R3/R4). The doc states that YAML integer scalars are accepted, so this is not a defect. Consider restricting integers to decimal and hexadecimal forms.
- **R578-1-S2:** The round trip (`examples/entity_roundtrip.c`, `tests/test_entity.cpp`) uses focused per-core oracles rather than rerunning the existing core suites with a generated configuration. This is accepted as meeting item 4, because all three named plants are caught. A parameterised run of one existing suite on a generated entity would also satisfy the literal reading.

## Acceptance items 1-7 at this head

1. **Schema:** Met.
   - Every field has a range and a clause (`docs/ENTITY_YAML.md:62-83`).
   - The ADPDU field (6.2.2.7-6.2.2.20), descriptor (7.2.1/7.2.6/7.2.8/7.2.12) and Table 6-2..6-4 numbering matches the reviewed baseline (`PORTING.md`, `adp.c`, `requirements.json` at `1a9f651c`).
   - Capability masks 0xC588 (required) and 0x73000 (cleared), the 0x03FFFFFF upper bound, and stream bits 0x0001/0x0800/0x4000 match Table 6-2..6-4 bit assignments.
   - The MAAP range `base + count <= 0x91E0F000FE00` matches `MAAP_POOL_SIZE` and `pool_range` in the core.
2. **Validation:** Met.
   - Exact-message refusal tests cover each issue category (version, unknown field at every level, missing MAC, count overflow, sink on a missing interface).
   - 44/44 selftests pass.
   - 20/20 planted generator and mapper defects are caught (`receipts/probe_generator_mutants.txt`).
   - Probes R1-R11 return precise messages.
3. **Generator:** Met.
   - Output is const and deterministic: two CLI runs per persona are byte-identical to the goldens (probe D1).
   - Generated objects have no imports on RV32 (`baremetal.py` check).
   - The schema guard name, the macro and `_Static_assert` are present, and the stale-header plant fails.
   - A maximum entity (4 interfaces, 16/16 streams, pool-end ranges) compiles with `-std=c11 -pedantic -Werror`, and the header compiles as C++20. It initialises all three cores (probe B).
4. **Tests:** Met.
   - Golden byte equality holds.
   - Round trips pass on Linux and RV32 (Debug and Release).
   - `entity-wrong-count`, `entity-swapped-interface` and `entity-dropped-field` are CAUGHT by their named assertions (oracle codes 36, 44, 56; `receipts/mutation-results.json`).
   - Core line and branch coverage stays at 100% after exclusions (`receipts/validate-coverage.log`).
5. **CI:** Met.
   - `validate.py` runs `entity_yaml.py --examples --check`, and probe D2 shows that config drift and golden drift each return rc 2.
   - The hosted quality job at this head logged `entity-golden: rc 0` and `entity-controls: rc 0`.
6. **Docs:** Met apart from F2/F3 and the residue.
   - ENTITY_YAML.md has integrator, tester and developer sections, the four persona examples, and a Mermaid graph that renders (graphs gate).
   - PORTING.md shows YAML as the primary path, with hand-written structs as the low-level option (lines 1-3, 345-349).
7. **milan-fpga mapping:** Not met (F1, F2).
   - The mapping is documented.
   - The fixture's hash and size match the pinned source.
   - Projecting the full pinned AX7101 file reproduces generated C byte-identical to the golden.
   - The nine ADP values agree with the builder's `adp_shape` and `derive_entity_id` logic.

## Repository contract and merge
- **Generated C:**
  - It contains only SPDX lines and short clause references. `comments` gate rc 0.
  - The guards are registered in `scripts/conditional_policy.py` and in the CODING_STANDARD guard table.
  - The `__cplusplus` regions compile on both sides. `conditionals` gate rc 0.
  - The `_SCHEMA_VERSION` macro is a constant and not used in a conditional.
- **YAML placement:** `configs/` and `configs/compat/` are outside the four gated directories. The suffix rule, which also checks untracked files, passes.
- **Merge:**
  - `scripts/static_analysis.py` keeps every suppression from both parents. It keeps `-Iexamples` for cppcheck and clang-tidy. The `redundantAssignment` suppression points to `examples/rv32/smoke.c:137`, which is the line where cppcheck reports the finding at this head.
  - Three-way check of `tests/mutations.json`: 330 = 324 base + 3 PR + 3 main, with 0 mismatches. `own-discover-discarded` takes the main version, which this PR did not change.
  - `src/`, `include/` and `tests/test_adp.cpp` are identical to main `51870377`.
  - Commit subjects are one line, and privacy gates pass.

## Executed evidence (this review, exact head)
- **Toolchain:** Pinned GoogleTest/GMock 1.14.0 through `PKG_CONFIG_PATH`, `CMAKE_PREFIX_PATH` and `LD_LIBRARY_PATH`. Clang 18.1.3 first on PATH. `receipts/environment.txt`.
- `python3 scripts/validate.py --work <scratch> --jobs 12 --graphs` returned rc 0. All 27 gates were 0 (`receipts/validate.log`, `validate-gates.json`). Mutation results: 330 CAUGHT, 0 ESCAPED, 0 ERROR.
- `python3 scripts/baremetal.py --work <scratch> --jobs 4` returned rc 0 for Debug and Release (`receipts/baremetal.log`, `rv32-results.json`). The Release ELF and all four generated objects are byte-identical to the author's published RV32 receipt. The Debug ELF differs, consistent with embedded paths.
- Probes: `probe_mapper.py`, `probe_generator.sh` and `probe_generator_mutants.py`, all run in disposable copies.
- **Hosted:** Both workflow runs at `4c939ef1` (pull_request run 37971416441, push run 37971409580) completed with quality and bare-metal jobs success. In each job the install, validate and evidence steps executed with success (`receipts/check-runs-4c939ef1.tsv`, `ci-job-steps.txt`, `gh-pr-checks.txt`). The hosted quality log shows the entity-golden, entity-controls, mutation and graphs gates at rc 0. Hosted acceptance remains the manager's.
- **Restoration:** After the probes, the clone matches HEAD exactly. Worktree and index equal HEAD, every tracked file hashes to its HEAD blob, and modes match. The head has no submodule gitlinks. The bytecode cache created by the gate run was removed.

## Reviewer-owned ledger

| Lens | State | Examined artifacts | Covering round | Exact head |
|---|---|---|---|---|
| Conformance | UNCLEAN (F1, F2, F3) | ENTITY_YAML schema table versus Tables 6-2..6-4, ADPDU and descriptor clauses, MAAP pool; generated ADP/ACMP/MAAP values; mapper versus pinned milan-fpga builder grammar and defaults | R578-1 | 4c939ef18741916df85a355973db007b588604e0 |
| RTL (implementation: generated C, core parity, both targets) | CLEAN | four golden pairs; boundary entity on the real cores (C11 pedantic, C++20 header); RV32 Debug/Release objects and imports; core sources identical to main | R578-1 | 4c939ef18741916df85a355973db007b588604e0 |
| Robustness | UNCLEAN (F1, F2) | refusal probes R1-R11; drift D2; CLI preserve-on-failure test; mapper probes P1-P10; five pinned source shapes | R578-1 | 4c939ef18741916df85a355973db007b588604e0 |
| Tests | UNCLEAN (F1, F2) | entity_selftest (44), 20 generator plants, 3 entity mutation plants plus the 330-plant campaign, round-trip oracles, coverage, hosted step logs | R578-1 | 4c939ef18741916df85a355973db007b588604e0 |
| Docs | UNCLEAN (F1, F2, F3; RESIDUE R1, R2) | ENTITY_YAML, PORTING, VERIFICATION, CODING_STANDARD, STATIC_ANALYSIS, REQUIREMENTS, TRACEABILITY, TESTS, requirements.json, PR body | R578-1 | 4c939ef18741916df85a355973db007b588604e0 |

## Real limits
- No licensed standards text was available. Clause and table numbers were checked against the reviewed baseline's numbering and the known field and bit layout, not against the documents themselves.
- The milan-fpga builder was not executed, because it needs its submodules. The nine AX7101 ADP values were checked against the builder's `adp_shape` and `derive_entity_id` source, the pinned source hash and size, and the author's published live-mapping receipt.
- The sanitizer build used the host default Clang. The pinned Clang 18 directory supplies the lexer used by the gates. Hosted CI used the runner's packages.
- Jobs were set to 12 and 4 to stay within the unit cap. No manager source bank runs at this head, and none is claimed. Physical calibration was NOT RUN, and no hardware was used.

## Pending manager duties
- Validate the merge-turn current-dev candidate (source base `1a9f651c`, live dev `7c1b52be`) with the builder and native banks, and link the receipts.
- Hosted and act acceptance.
- File the milan-fpga follow-up issue (item 7) after F1 and F2 are resolved.
- Carry R578-1-R1 and R578-1-R2 to the residue checklist.
- Branch `dev-linux` was out of scope for this review.

R578-1 FINISHED
