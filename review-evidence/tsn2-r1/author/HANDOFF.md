# Entity YAML handoff

Status: merge and fresh verification complete. Ready for review.

Branch: `entity-yaml`. Head: `4c939ef18741916df85a355973db007b588604e0`.
Confirmed original base: `1a9f651cdf7846b8e10ac246a6ef6916960fbb92`.
Confirmed prior head: `0a1a14a1cc0e8cc99cb7a21ed43c391f7001dc6d`.
New base: [main `51870377c5012766a8ea1d9798e3c499ca1060a3`](https://github.com/kebag-logic/tsn-c-stack/commit/51870377c5012766a8ea1d9798e3c499ca1060a3).
The merge has both the prior head and new base as parents. No history was rewritten.
The branch was not pushed. The manager owns publication and the integration follow-up.

Scope: [issue 2](https://github.com/kebag-logic/tsn-c-stack/issues/2) and [assignment](https://github.com/kebag-logic/tsn-c-stack/issues/2#issuecomment-6086063941).
[Resume TAKEN](https://github.com/kebag-logic/tsn-c-stack/issues/2#issuecomment-6086451774) was posted at the start.
Core sources and public headers match the new base exactly.
The source firmware checkout remains clean at its pinned revision.

## Merge reconciliation

The [merge audit](evidence/merge-audit.json) records the exact tested tree.
All 327 main plants and the three entity plants are retained.
The shared `own-discover-discarded` plant keeps the updated main assertion target.
All diagnostic suppressions from both parents are retained.
The RV32 backpressure suppression and its documentation now point to merged line 137.
The example include search paths remain in both analyzers.

The [traceability matrix](https://github.com/kebag-logic/tsn-c-stack/blob/4c939ef18741916df85a355973db007b588604e0/docs/TRACEABILITY.md) and [test inventory](https://github.com/kebag-logic/tsn-c-stack/blob/4c939ef18741916df85a355973db007b588604e0/docs/TESTS.md) were regenerated.
All four golden entities were regenerated and remain byte-identical to the prior head.
The inventory contains 43 requirements, 117 test declarations and 391 executable instances.
The campaign contains 330 plants. Every plant was caught by its required named assertions.
The [per-plant results](evidence/mutation-plants.json) preserve every name and status.
The [summary](evidence/mutation-summary.json) records 359 required assertion matches.

| Added main plant | Named test family | Required assertion |
|---|---|---|
| `adp-unsupported-version-accepted` | `AllStates/AdpInputControl.RejectsUnsupportedVersion/0` through `/4` | malformed discovery increments discarded exactly once |
| `adp-short-frame-accepted` | `AllStates/AdpInputControl.RejectsShortFrame/0` through `/4` | malformed discovery increments discarded exactly once |
| `adp-wrong-control-length-accepted` | `AllStates/AdpInputControl.RejectsWrongControlDataLength/0` through `/4` | malformed discovery increments discarded exactly once |

## Implementation

The [generator](https://github.com/kebag-logic/tsn-c-stack/blob/4c939ef18741916df85a355973db007b588604e0/scripts/entity_yaml.py) emits const ADP records per interface, one const ACMP configuration, and const MAAP argument records per interface.
MAAP has no configuration struct in its public API. The generated record supplies its existing initialization and begin arguments.
Names are stored as metadata. Stream names remain validated source labels because the cores have no corresponding field.
Counts, stream capabilities, MACs and identity share one validated input.
Schema version checks compile in C11 and generated headers compile in C++20.
Four example configurations are committed as source and golden output.
YAML stays outside the closed C suffix directories.

## Schema fields, clauses and ranges

| Field | Range and meaning | Authority |
|---|---|---|
| `schema_version` | String `1.0.0` only. Local format version. | [Issue 2][issue] |
| `identity` | Mapping containing the six fields below. | [IEEE 1722.1-2021 7.2.1][atdecc] |
| `identity.entity_id` | Integer 1 through 2^64-2, or `mac-derived`. Derive from interface 0 by inserting FF FE after its first three MAC octets. Preserve the U/L bit. | [IEEE 1722.1-2021 6.2.2.7][atdecc]; [source identity policy](https://github.com/kebag-logic/tsn-c-stack/blob/4c939ef18741916df85a355973db007b588604e0/docs/PORTING.md#entity-configuration) |
| `identity.model_id` | Integer 1 through 2^64-2. Resolve the complete product model outside this generator. | [IEEE 1722.1-2021 6.2.2.8][atdecc]; [Milan v1.2 5.6.2][milan] |
| `identity.name` | 0 through 64 UTF-8 bytes. Entity name metadata. | [IEEE 1722.1-2021 7.2.1][atdecc] |
| `identity.vendor_name` | 0 through 64 UTF-8 bytes. Vendor string metadata. | [IEEE 1722.1-2021 7.2.1 and 7.2.12][atdecc] |
| `identity.serial_number` | 0 through 64 UTF-8 bytes. Serial metadata. | [IEEE 1722.1-2021 7.2.1][atdecc] |
| `identity.group_name` | 0 through 64 UTF-8 bytes. Group metadata. | [IEEE 1722.1-2021 7.2.1][atdecc] |
| `capabilities` | Mapping containing the two fields below. | [IEEE 1722.1-2021 6.2.2.9 and 6.2.2.19][atdecc] |
| `capabilities.entity` | Integer 0 through 0x03FFFFFF. All bits in 0xC588 must be set. All bits in 0x73000 must be clear. | [IEEE 1722.1-2021 Table 6-2][atdecc]; [Milan v1.2 5.6.2][milan]; [authentication policy](https://github.com/kebag-logic/tsn-c-stack/blob/4c939ef18741916df85a355973db007b588604e0/docs/PORTING.md#entity-configuration) |
| `capabilities.identify_control_index` | Integer 0 through 65535. Application Identify control index. | [IEEE 1722.1-2021 6.2.2.19][atdecc]; [Milan v1.2 5.3.3][milan] |
| `interfaces` | List of 1 through 4 mappings. Local ACMP capacity. Indices are 0 through length minus one. | [IEEE 1722.1-2021 7.2.8 and 6.2.2.20][atdecc]; [ACMP header](https://github.com/kebag-logic/tsn-c-stack/blob/4c939ef18741916df85a355973db007b588604e0/include/acmp.h) |
| `interfaces[].mac` | Six hexadecimal octets separated by colons. Nonzero, unicast, distinct 48-bit values. | [IEEE 1722.1-2021 7.2.8][atdecc]; [MAAP initialization contract](https://github.com/kebag-logic/tsn-c-stack/blob/4c939ef18741916df85a355973db007b588604e0/docs/PORTING.md#callback-checklist) |
| `inputs`, `outputs` | Lists of 0 through 16 stream mappings each. Local ACMP capacity. Indices are consecutive. | [IEEE 1722.1-2021 6.2.2.10, 6.2.2.12 and 7.2.6][atdecc]; [Milan v1.2 5.6.2][milan] |
| `inputs[].name`, `outputs[].name` | 0 through 64 UTF-8 bytes. Source labels for integration. The cores have no stream-name field. | [IEEE 1722.1-2021 7.2.6][atdecc] |
| `inputs[].interface`, `outputs[].interface` | Integer 0 through interface count minus one. | [IEEE 1722.1-2021 7.2.6][atdecc]; [Milan v1.2 5.5.3.5.1][milan] |
| `inputs[].kind`, `outputs[].kind` | `audio` or `clock`. Derive AUDIO or MEDIA_CLOCK capabilities. | [IEEE 1722.1-2021 Tables 6-3 and 6-4][atdecc] |
| `maap` | List of 0 through interface count mappings. Exactly one entry for each interface with outputs. | [IEEE 1722-2016 B.3.2][avtp] |
| `maap[].interface` | Integer 0 through interface count minus one. Must own an output. No duplicates. | [IEEE 1722-2016 B.3.2][avtp]; [local instance contract](https://github.com/kebag-logic/tsn-c-stack/blob/4c939ef18741916df85a355973db007b588604e0/docs/PORTING.md#maap-callbacks-and-public-fields) |
| `maap[].preferred` | Integer zero for random allocation, or 0x91E0F0000000 through 0x91E0F000FE00 minus the output count on that interface. Reserve one address per output. | [IEEE 1722-2016 B.3.2, Table B.7, B.4 and Table B.9][avtp] |

The exact FF FE insertion is a product derivation policy permitted by [IEEE 1722.1-2021 6.2.2.7][atdecc].
The source firmware uses the same rule without toggling the U/L bit.
Model identity is resolved from the complete AEM shape outside this generator.
No partial-shape hash claims to identify a complete product model.

## Validation refusals and tests

All tests below belong to [entity_selftest.py](https://github.com/kebag-logic/tsn-c-stack/blob/4c939ef18741916df85a355973db007b588604e0/scripts/entity_selftest.py).
There are 44 host tests, with additional named subcases.

| Refusal | Exact diagnostic | Test |
|---|---|---|
| version | `entity.schema_version: supported version is 1.0.0` | `EntityTests.test_refuse_version` |
| root type | `entity: expected a mapping` | `EntityTests.test_refuse_root_type` |
| interfaces empty | `interfaces: expected list with 1..4 entries` | `EntityTests.test_refuse_interfaces_empty` |
| interfaces count | `interfaces: expected list with 1..4 entries` | `EntityTests.test_refuse_interfaces_count` |
| sink count | `inputs: expected list with 0..16 entries` | `EntityTests.test_refuse_sink_count` |
| source count | `outputs: expected list with 0..16 entries` | `EntityTests.test_refuse_source_count` |
| sink interface | `inputs[0].interface: expected integer in 0..1` | `EntityTests.test_refuse_sink_interface` |
| source interface | `outputs[0].interface: expected integer in 0..1` | `EntityTests.test_refuse_source_interface` |
| mac format | `interfaces[0].mac: expected six colon-separated hexadecimal octets` | `EntityTests.test_refuse_mac_format` |
| missing mac | `interfaces[0].mac: required field missing` | `EntityTests.test_refuse_missing_mac` |
| mac zero | `interfaces[0].mac: expected nonzero unicast MAC` | `EntityTests.test_refuse_mac_zero` |
| mac multicast | `interfaces[0].mac: expected nonzero unicast MAC` | `EntityTests.test_refuse_mac_multicast` |
| mac duplicate | `interfaces[1].mac: duplicate MAC` | `EntityTests.test_refuse_mac_duplicate` |
| entity id zero | `identity.entity_id: expected integer in 1..18446744073709551614` | `EntityTests.test_refuse_entity_id_zero` |
| model id ones | `identity.model_id: expected integer in 1..18446744073709551614` | `EntityTests.test_refuse_model_id_ones` |
| name length | `identity.name: expected UTF-8 string of 0..64 bytes without controls` | `EntityTests.test_refuse_name_length` |
| name control | `identity.name: expected UTF-8 string of 0..64 bytes without controls` | `EntityTests.test_refuse_name_control` |
| name c1 control | `identity.name: expected UTF-8 string of 0..64 bytes without controls` | `EntityTests.test_refuse_name_c1_control` |
| name surrogate | `identity.name: expected UTF-8 string of 0..64 bytes without controls` | `EntityTests.test_refuse_name_surrogate` |
| name type | `identity.name: expected UTF-8 string of 0..64 bytes without controls` | `EntityTests.test_refuse_name_type` |
| capability range | `capabilities.entity: expected integer in 0..67108863` | `EntityTests.test_refuse_capability_range` |
| capability milan | `capabilities.entity: requires Milan flags 0xC588 and clears 0x73000` | `EntityTests.test_refuse_capability_milan` |
| capability auth | `capabilities.entity: requires Milan flags 0xC588 and clears 0x73000` | `EntityTests.test_refuse_capability_auth` |
| kind | `inputs[0].kind: expected audio or clock` | `EntityTests.test_refuse_kind` |
| maap missing | `maap: exactly one reservation is required per output interface` | `EntityTests.test_refuse_maap_missing` |
| maap duplicate | `maap[1].interface: duplicate reservation` | `EntityTests.test_refuse_maap_duplicate` |
| maap interface | `maap[1].interface: expected integer in 0..1` | `EntityTests.test_refuse_maap_interface` |
| maap pool | `maap[0].preferred: complete range must be in the MAAP dynamic pool` | `EntityTests.test_refuse_maap_pool` |
| maap range | `maap[0].preferred: expected integer in 0..281474976710655` | `EntityTests.test_refuse_maap_range` |
| maap no outputs | `maap[0].interface: has no outputs` | `EntityTests.test_refuse_maap_no_outputs` |


| Additional refusal or control | Test |
|---|---|
| Every required field is dropped at every mapping level. | `test_dropped_required_fields` |
| An unknown field is inserted at every mapping level. | `test_unknown_fields_at_each_level` |
| Duplicate YAML key; non-string key; alias; malformed YAML; custom tag; multiple documents. | `test_yaml_refusals` |
| Boolean, float, quoted integer, null and out-of-range integer. | `test_integer_boolean_and_float_refusals` |
| Invalid C prefix. | `test_invalid_prefix` |
| Missing or edited generated file. | `test_missing_golden_file`, `test_golden_planted_drift` |
| Unsupported schema CLI input leaves both existing outputs unchanged; exit 2. | `test_invalid_cli_preserves_outputs` |
| Stale header schema macro fails C compilation with the expected message. | `test_schema_header_guard` |
| Unsupported source schema; unknown entity key; missing MAC; conflicting pin, capabilities or OUI; non-boolean CRF enable. | `test_mapping_refusals` |
| Maximum capacities, 64-byte UTF-8 name, maximum IDs and index, final legal MAAP range. | `test_valid_boundaries` |
| Explicit ID and C string escaping. | `test_explicit_identity_and_literal_escaping` |

Validation completes before file writes. An I/O error is reported with exit 2.
The two output files are not written as an atomic pair.
The generator validates this documented static subset. Complete AEM, media and product capability support remains a port obligation.

## Golden and round-trip sensitivity

`test_golden_bytes` regenerates all four examples and requires byte equality for both files.
It also changes mapping key order and regenerates in another directory.
There are no timestamps, host paths or runtime random choices in generated bytes.

The [shared C checks](https://github.com/kebag-logic/tsn-c-stack/blob/4c939ef18741916df85a355973db007b588604e0/examples/entity_roundtrip.c) run in hosted GoogleTest and RV32 Debug and Release.
They use independent expected constants for all four examples.
ADP checks emitted Ethernet and protocol fields.
ACMP restores bindings and checks admission by interface.
MAAP checks probes, range counts, preferred allocation, validity and withdrawal.

| Named plant | Mutation | Required named assertion |
|---|---|---|
| `entity-wrong-count` | AX7101 source count 2 becomes 1. | `EntityYaml.AdpRoundTrip`: generated ADP fields match the independent entity oracle |
| `entity-swapped-interface` | Duplex sink mapping 1,0 becomes 0,1. | `EntityYaml.AcmpRoundTrip`: generated ACMP interfaces preserve binding admission routes |
| `entity-dropped-field` | Talker preferred address initializer is removed; C supplies zero. | `EntityYaml.MaapRoundTrip`: generated MAAP arguments preserve range and interface ownership |

All plants compile. A crash, skipped test, missing report or unrelated assertion cannot count as a catch.
The golden drift control rejects the same three plants.
The full campaign now contains 330 plants. The declaration inventory contains 117 tests and 391 executable instances.
The existing production coverage denominator and exclusions are unchanged.
The final measurement shows 100% line and branch coverage on all four measured files after the existing exclusions.
Python generator branch coverage is not part of that denominator.

## Firmware mapping

Read-only source revision: [5603c353137e90c1fa95429f6d00ef7a2298d9ee](https://github.com/kebag-logic/milan-fpga/tree/5603c353137e90c1fa95429f6d00ef7a2298d9ee).
All five end-station YAML files and both firmware entity generators were read.
Their pinned protocol and gPTP dependencies were fetched for read-only evaluation.
The [fixture](https://github.com/kebag-logic/tsn-c-stack/blob/4c939ef18741916df85a355973db007b588604e0/configs/compat/ax7101.json) records the AX7101 source hash and size and all nine legacy ADP values.
The live projection was checked against every source shape. All returned success.
The offline gate checks the exact AX7101 projection and every ADP value.

| Source 1.2.0 fact | Portable 1.0.0 field or treatment |
|---|---|
| `entity.entity_id` | `identity.entity_id`. Preserve explicit identity or `mac-derived`. |
| `entity.entity_model_id`, optional `model_id_pin`, `vendor_oui` | `identity.model_id`, resolved by the complete source builder. A literal, pin or OUI must agree with the supplied resolved value. |
| `entity.name`, `vendor_name`, `serial_number`, `group_name` | Corresponding fields in `identity`, unchanged. |
| `entity.locale` | AEM localization only. Retained by the product descriptor generator. No core field. |
| Optional `entity.entity_capabilities` | Must agree with the resolved capability value. Source authority is the [protocol package](https://github.com/Mister-M-alt/protocol-processor-control-plane-avb-milan/blob/2ad2f845dd583f8310075fa2380cb60a04fd091a/hdl/adp/pp_adp_pkg.sv). |
| `platform.mac_address` | `interfaces[0].mac`. The supported projection has one protocol interface. |
| `streams.listeners`, `streams.talkers` | Audio `inputs`, `outputs` in source order, all on interface 0. Preserve stream names. |
| `clocking.crf_sink`, `clocking.crf_output.enabled` | Append one clock input or output when true. Omitted source `crf_output` means disabled. |
| Stream channel counts, formats and map modes | Kept in the source AEM and media generators. No fields in these cores. |
| Source Identify descriptor | Index zero, as checked by the source ADP generator. |
| `srp.stream_dmac_base` | No direct MAAP mapping. Request random dynamic allocation. |
| Board, SoC, gPTP dataset, transport, audio and reservation fields | Remain product responsibilities. They are outside this projection. |

AX7101 has one audio stream and one CRF stream per direction.
Its source and sink counts are both 2. Both stream capability values are 0x4801.
Entity capabilities are 0xC588. Identify index is zero.
Entity ID: 0x020000FFFE000001. Model ID: 0x001BC5C1935893E1.
The source SRP FE01 address is in the static pool. MAAP instead requests a dynamic random range.
The [schema guide](https://github.com/kebag-logic/tsn-c-stack/blob/4c939ef18741916df85a355973db007b588604e0/docs/ENTITY_YAML.md#mapping-from-milan-fpga) documents the projection commands and scope.
The manager still owns the follow-up integration issue.
The PR body therefore uses `Relates to #2` until that acceptance dependency is recorded.

## Gates on both targets

All 27 hosted gate records and both RV32 configurations returned zero.
Post-commit privacy also returned zero.

| Gate | Linux rc | RV32 applicability |
|---|---|---|
| entity-golden | 0 | Shared source/configuration gate; rc 0 |
| entity-controls | 0 | Shared source/configuration gate; rc 0 |
| boundary | 0 | Separate freestanding audit below; rc 0 |
| needles | 0 | Hosted test contract; no RV32 GoogleTest |
| assertion-templates | 0 | Hosted test contract; no RV32 GoogleTest |
| dependencies | 0 | Hosted test contract; no RV32 GoogleTest |
| comments | 0 | Shared source/configuration gate; rc 0 |
| conditionals | 0 | Shared source/configuration gate; rc 0 |
| port-contracts | 0 | Shared source/configuration gate; rc 0 |
| registration-controls | 0 | Hosted test contract; no RV32 GoogleTest |
| license | 0 | Shared source/configuration gate; rc 0 |
| traceability | 0 | Shared records; RV32 smoke checks below |
| test-inventory | 0 | Shared records; RV32 smoke checks below |
| coverage-controls | 0 | Hosted test contract; no RV32 GoogleTest |
| privacy-selftest | 0 | Shared source/configuration gate; rc 0 |
| privacy | 0 | Shared source/configuration gate; rc 0 |
| gcc-configure | 0 | Hosted campaign; RV32 uses smoke checks |
| gcc-build | 0 | Hosted campaign; RV32 uses smoke checks |
| gcc-test | 0 | Hosted campaign; RV32 uses smoke checks |
| coverage | 0 | Hosted campaign; RV32 uses smoke checks |
| clang-sanitizers-configure | 0 | Hosted campaign; RV32 uses smoke checks |
| clang-sanitizers-build | 0 | Hosted campaign; RV32 uses smoke checks |
| clang-sanitizers-test | 0 | Hosted campaign; RV32 uses smoke checks |
| mutation | 0 | Hosted campaign; RV32 uses smoke checks |
| static-analysis | 0 | Shared source/configuration gate; rc 0 |
| mutation-controls | 0 | Hosted campaign; RV32 uses smoke checks |
| graphs | 0 | Shared source/configuration gate; rc 0 |
| Post-commit privacy | 0 | Shared commit and source gate; rc 0 |
| RV32 Debug build, link, dependency audit and execution | Not applicable | rc 0 |
| RV32 Release build, link, dependency audit and execution | Not applicable | rc 0 |

The first merge run caught all 330 plants and passed both RV32 builds.
Its only failing gate was the stale line number on the existing RV32 backpressure suppression.
The suppression was moved to its actual merged location.
A fresh complete hosted campaign and both RV32 configurations then passed on the committed source tree.
The conditional matrix compiled 58 region sides across 33 files. All four Mermaid graphs rendered.

The Linux target runs GCC, Clang with address and undefined-behavior sanitizers, GoogleTest, coverage and all mutation plants.
RV32 runs freestanding Debug and Release builds and QEMU execution against the minimal port.
RV32 audits generated objects for forbidden headers and any imports.
It does not run GoogleTest, hosted sanitizers or claim a second coverage denominator.
Source, comment, assertion, traceability and inventory gates apply to both target source sets.

## Evidence and review

Head: `4c939ef18741916df85a355973db007b588604e0`.
Commit subject: `Merge main into entity-yaml and preserve validation coverage`.
Configured identity and one-line commit policy passed. The worktree is clean.
The new base is the merge's second parent. The local main branch remains at the original base.
The tracking reference is at the new base.

- [Hosted gate records](evidence/gates.json)
- [RV32 records](evidence/rv32-results.json)
- [Merge audit](evidence/merge-audit.json)
- [Mutation summary](evidence/mutation-summary.json)
- [Every named plant](evidence/mutation-plants.json)
- [Conditional matrix](evidence/conditionals.json)
- [Coverage](evidence/coverage.txt)
- [Generator tests](evidence/entity-controls.log)
- [Pinned firmware mapping from round one](evidence/live-mapping.json)
- [SHA-256 and sizes](evidence/manifest.json)
- [Rendered entity graph](evidence/ENTITY_YAML-0.svg)
- [PR body](PR-BODY.md)

The peak service memory was 5,748,908,032 bytes (5.35 GiB), below the 9 GB limit.
Validation used 16 jobs with the pinned GoogleTest 1.14.0 and Clang 18 toolchain.
Reproduce both target gates from the repository root:

```sh
python3 scripts/validate.py --work build-validation --jobs 16 --graphs
python3 scripts/baremetal.py --work build-rv32 --jobs 16
```

All 27 hosted gate records and both RV32 configurations returned zero.
Entity, traceability and inventory regeneration also returned zero. Post-commit privacy returned zero.
The output directory contains only review documents and small evidence files.
Large logs and build products are represented by SHA-256 and byte size.
The manifest includes the first run's static-analysis failure and the fresh successful campaign.
No source firmware changes, hardware access, push, PR creation or branch rewrite occurred.

[atdecc]: https://standards.ieee.org/ieee/1722.1/6670/
[milan]: https://avnu.org/resource/milan-specification/
[avtp]: https://standards.ieee.org/ieee/1722/5979/
[issue]: https://github.com/kebag-logic/tsn-c-stack/issues/2
