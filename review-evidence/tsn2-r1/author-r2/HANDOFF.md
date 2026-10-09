# Entity YAML handoff

Status: Round 2 complete. Ready for independent review.
[REVIEW READY posted](https://github.com/kebag-logic/tsn-c-stack/issues/2#issuecomment-6087035547).
Branch: `entity-yaml`. Head: `6f4ecc9036f9ac2694b05a749cc9105d9c15c05f`.
Parent: `4c939ef18741916df85a355973db007b588604e0`. This is one new commit. No history was rewritten.
Original base: `1a9f651cdf7846b8e10ac246a6ef6916960fbb92`.
The branch retains the main merge at `51870377c5012766a8ea1d9798e3c499ca1060a3`.
The [pull request](https://github.com/kebag-logic/tsn-c-stack/pull/20) was confirmed at the parent when this round began.
The manager owns publication, independent re-review and the integration follow-up.

Commit: `Preserve source entity scalar grammar and requirement provenance`.
The [integrity receipt](evidence/round2/integrity.json) records the tree and changed-file hashes.
The worktree is clean. Core sources, public headers, examples and golden configurations are unchanged in this round.
The source checkout is clean at [5603c353](https://github.com/kebag-logic/milan-fpga/tree/5603c353137e90c1fa95429f6d00ef7a2298d9ee).
No push, PR creation, source-platform change or hardware access occurred.

Scope: [issue 2](https://github.com/kebag-logic/tsn-c-stack/issues/2),
[initial assignment](https://github.com/kebag-logic/tsn-c-stack/issues/2#issuecomment-6086063941),
and [Round 2 assignment](https://github.com/kebag-logic/tsn-c-stack/issues/2#issuecomment-6086821725).
The [internal review](https://github.com/kebag-logic/tsn-c-stack/pull/20#issuecomment-6086810259)
and [external review](https://github.com/kebag-logic/tsn-c-stack/pull/20#issuecomment-6086815208) define the correction checklist.

## Round 2

| Finding | Change and evidence |
|---|---|
| R578-1-F1 and R579-1-F1 | All five source hex fields use base 16, optional prefixes and single underscores. Non-strings and excess digits are refused. The [unchanged ten-case probe](evidence/round2/probe-mapper.log) has every expected outcome. The [six source-parser comparisons](evidence/round2/mapping-regression.json) all match. The [compiled CLI check](evidence/round2/cli-identity.json) emits `0000001234567890` in ADP and ACMP. |
| R578-1-F2 | Apply omitted vendor, group and entity-ID defaults. Normalize colon, hyphen and exact-width hex MAC strings. Tests check each form and preserve the resolved identity. |
| R578-1-F3 | Define ENTITY-01 in the generated requirements table with clauses and issue-2 origin. Regenerate traceability. The [metadata checks](evidence/round2/traceability.log) catch 28 defects and removal of every one of the 43 requirement definitions. |
| R578-1-R1 | State parsed-mapping equality for the AX7101 fixture. Golden C checks remain byte comparisons. |
| R578-1-R2 | Explain when YAML names and MACs need quoting. Non-string values are refused. |
| R578-1-S1 | Retain schema 1.0.0 integer compatibility. Document octal and sexagesimal forms. A named test locks their values. Recommend decimal without leading zeros or hexadecimal. |
| R578-1-S2 | Retain the per-core oracle round trips accepted by both reviews. Add a compiled CLI identity oracle for the demonstrated mapping gap. |

The [mapper probe](evidence/round2/probe_mapper.py) is unchanged from the internal review packet.
Its SHA-256 is `f5228744e72941122a8c69ac5d080baf1e267659b24e72f2c1dccf678194f348`.
P1 maps to `0x1234567890123456`; P2 maps to `0x020000FFFE000001`.
P3 through P8 are accepted. P9 and P10 request quoted hexadecimal strings.
The external review's regression scripts were adapted to expect corrected values.
The mapping script also selects the projected OUI and capability fields for those comparisons.
The [mapping script](evidence/round2/mapping-regression.py) and [CLI script](evidence/round2/cli-identity-regression.py) are included.
They extract only pure source scalar parsers. They do not execute a complete product builder bank.
The [five-shape check](evidence/round2/five-shapes.json) preserves all nine ADP fields against the pinned Round 1 resolved values.

### Source scalar refusals

The [selftest](https://github.com/kebag-logic/tsn-c-stack/blob/6f4ecc9036f9ac2694b05a749cc9105d9c15c05f/scripts/entity_selftest.py) runs 172 tests.
Every refusal below checks its complete diagnostic, including the field path.
For each of `entity_id`, `entity_model_id`, `model_id_pin`, `vendor_oui` and `entity_capabilities`,
the named test is `test_mapping_refuse_<field>_<form>`.

| Form names | Refused input | Exact message after the field path |
|---|---|---|
| `integer`, `boolean`, `float`, `null`, `list`, `mapping` | Non-string source scalars. | `quote the hexadecimal value as a YAML string` |
| `empty`, `prefix_only`, `leading_underscore`, `prefix_underscore`, `trailing_underscore`, `double_underscore`, `sign`, `negative`, `leading_space`, `trailing_space`, `newline`, `nonhex`, `unicode`, `separator` | Invalid source hexadecimal spelling. | `expected hexadecimal digits with optional 0x and single underscores between digits; no sign or whitespace` |
| `overflow`, `extra_zero`, `wide_underscores` | Too many digits, including leading zeros. | `expected at most N hexadecimal digits (B bits), including leading zeros`; N/B are 16/64 for identities, 6/24 for OUI, 8/32 for capabilities. |

| Other refusal or accepted control | Test |
|---|---|
| Reserved zero/all-ones model or pin. | `test_mapping_reserved_models` |
| Invalid literal cannot hide behind a pin; a valid pin takes precedence. | `test_mapping_pin_precedence_and_literal_validation` |
| Wrong source version, unknown key, missing MAC, conflicting literal/pin/OUI/capabilities, OUI I/G bit, non-boolean CRF enable. | `test_mapping_refusals` |
| MAC type, short/long hex width, mixed separators, zero and multicast values. | `test_mapping_mac_refusals` |
| Prefixed, unprefixed, lowercase, uppercase and underscored source fields. | `test_mapping_hex_spellings` |
| Minimum/maximum supported identities, OUI bounds, highest supported capability combination. | `test_mapping_hex_boundaries` |
| Digit-only and unprefixed explicit entity IDs. | `test_mapping_digit_only_entity_id`, `test_mapping_unprefixed_entity_id` |
| Each omitted builder default. | `test_mapping_default_vendor_name`, `test_mapping_default_group_name`, `test_mapping_default_entity_id` |
| Colon, hyphen and exact-width hexadecimal MACs. | `test_mapping_mac_spellings` |
| Public CLI output compiled into both core configurations. | `test_mapping_cli_compiled_identity` |
| Established portable integer scalar forms. | `test_yaml_integer_compatibility` |

### Regression sensitivity

The [eight additional mapper plants](evidence/round2/mapper-plants.json) all trigger their named failing assertions.
The [portable plant script](evidence/round2/mapper-plants.py) runs in disposable copies.
Its first setup attempt found an ambiguous replacement anchor. The final script uses a unique function anchor and returns zero.
The shipped source was unaffected by these plants.

| Plant | Named failing test |
|---|---|
| `base-zero`: restore base-zero conversion. | `test_mapping_digit_only_entity_id` |
| `unbounded-digits`: remove the digit-count bound. | `test_mapping_refuse_entity_id_extra_zero` |
| `unquoted-accepted`: accept source integers. | `test_mapping_refuse_entity_id_integer` |
| `double-underscore`: allow repeated separators. | `test_mapping_refuse_entity_id_double_underscore` |
| `vendor-default`: change the default vendor. | `test_mapping_default_vendor_name` |
| `group-default`: change the default group. | `test_mapping_default_group_name` |
| `entity-default`: change default derivation. | `test_mapping_default_entity_id` |
| `pin-agreement`: remove resolved-model agreement. | `test_mapping_refusals` |

## Schema fields, clauses and ranges

| Field | Range and meaning | Authority |
|---|---|---|
| `schema_version` | String `1.0.0` only. Local format version. | [Issue 2][issue] |
| `identity` | Mapping containing the six fields below. | [IEEE 1722.1-2021 7.2.1][atdecc] |
| `identity.entity_id` | Integer 1 through 2^64-2, or `mac-derived`. Derive from interface 0 by inserting FF FE after its first three MAC octets. Preserve the U/L bit. | [IEEE 1722.1-2021 6.2.2.7][atdecc]; [source identity policy](https://github.com/kebag-logic/tsn-c-stack/blob/6f4ecc9036f9ac2694b05a749cc9105d9c15c05f/docs/PORTING.md#entity-configuration) |
| `identity.model_id` | Integer 1 through 2^64-2. Resolve the complete product model outside this generator. | [IEEE 1722.1-2021 6.2.2.8][atdecc]; [Milan v1.2 5.6.2][milan] |
| `identity.name` | 0 through 64 UTF-8 bytes. Entity name metadata. | [IEEE 1722.1-2021 7.2.1][atdecc] |
| `identity.vendor_name` | 0 through 64 UTF-8 bytes. Vendor string metadata. | [IEEE 1722.1-2021 7.2.1 and 7.2.12][atdecc] |
| `identity.serial_number` | 0 through 64 UTF-8 bytes. Serial metadata. | [IEEE 1722.1-2021 7.2.1][atdecc] |
| `identity.group_name` | 0 through 64 UTF-8 bytes. Group metadata. | [IEEE 1722.1-2021 7.2.1][atdecc] |
| `capabilities` | Mapping containing the two fields below. | [IEEE 1722.1-2021 6.2.2.9 and 6.2.2.19][atdecc] |
| `capabilities.entity` | Integer 0 through 0x03FFFFFF. All bits in 0xC588 must be set. All bits in 0x73000 must be clear. | [IEEE 1722.1-2021 Table 6-2][atdecc]; [Milan v1.2 5.6.2][milan]; [authentication policy](https://github.com/kebag-logic/tsn-c-stack/blob/6f4ecc9036f9ac2694b05a749cc9105d9c15c05f/docs/PORTING.md#entity-configuration) |
| `capabilities.identify_control_index` | Integer 0 through 65535. Application Identify control index. | [IEEE 1722.1-2021 6.2.2.19][atdecc]; [Milan v1.2 5.3.3][milan] |
| `interfaces` | List of 1 through 4 mappings. Local ACMP capacity. Indices are 0 through length minus one. | [IEEE 1722.1-2021 7.2.8 and 6.2.2.20][atdecc]; [ACMP header](https://github.com/kebag-logic/tsn-c-stack/blob/6f4ecc9036f9ac2694b05a749cc9105d9c15c05f/include/acmp.h) |
| `interfaces[].mac` | Six hexadecimal octets separated by colons. Nonzero, unicast, distinct 48-bit values. | [IEEE 1722.1-2021 7.2.8][atdecc]; [MAAP initialization contract](https://github.com/kebag-logic/tsn-c-stack/blob/6f4ecc9036f9ac2694b05a749cc9105d9c15c05f/docs/PORTING.md#callback-checklist) |
| `inputs`, `outputs` | Lists of 0 through 16 stream mappings each. Local ACMP capacity. Indices are consecutive. | [IEEE 1722.1-2021 6.2.2.10, 6.2.2.12 and 7.2.6][atdecc]; [Milan v1.2 5.6.2][milan] |
| `inputs[].name`, `outputs[].name` | 0 through 64 UTF-8 bytes. Source labels for integration. The cores have no stream-name field. | [IEEE 1722.1-2021 7.2.6][atdecc] |
| `inputs[].interface`, `outputs[].interface` | Integer 0 through interface count minus one. | [IEEE 1722.1-2021 7.2.6][atdecc]; [Milan v1.2 5.5.3.5.1][milan] |
| `inputs[].kind`, `outputs[].kind` | `audio` or `clock`. Derive AUDIO or MEDIA_CLOCK capabilities. | [IEEE 1722.1-2021 Tables 6-3 and 6-4][atdecc] |
| `maap` | List of 0 through interface count mappings. Exactly one entry for each interface with outputs. | [IEEE 1722-2016 B.3.2][avtp] |
| `maap[].interface` | Integer 0 through interface count minus one. Must own an output. No duplicates. | [IEEE 1722-2016 B.3.2][avtp]; [local instance contract](https://github.com/kebag-logic/tsn-c-stack/blob/6f4ecc9036f9ac2694b05a749cc9105d9c15c05f/docs/PORTING.md#maap-callbacks-and-public-fields) |
| `maap[].preferred` | Integer zero for random allocation, or 0x91E0F0000000 through 0x91E0F000FE00 minus the output count on that interface. Reserve one address per output. | [IEEE 1722-2016 B.3.2, Table B.7, B.4 and Table B.9][avtp] |

The exact FF FE insertion is a product derivation policy permitted by [IEEE 1722.1-2021 6.2.2.7][atdecc].
The source firmware uses the same rule without toggling the U/L bit.
Model identity is resolved from the complete AEM shape outside this generator.
No partial-shape hash claims to identify a complete product model.

## Validation refusals and tests

All tests below belong to [entity_selftest.py](https://github.com/kebag-logic/tsn-c-stack/blob/6f4ecc9036f9ac2694b05a749cc9105d9c15c05f/scripts/entity_selftest.py).
There are 172 host tests, with additional named subcases.

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

The [shared C checks](https://github.com/kebag-logic/tsn-c-stack/blob/6f4ecc9036f9ac2694b05a749cc9105d9c15c05f/examples/entity_roundtrip.c) run in hosted GoogleTest and RV32 Debug and Release.
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

The source is [milan-fpga revision 5603c353](https://github.com/kebag-logic/milan-fpga/tree/5603c353137e90c1fa95429f6d00ef7a2298d9ee).
Its [end-station examples](https://github.com/kebag-logic/milan-fpga/tree/5603c353137e90c1fa95429f6d00ef7a2298d9ee/configs) use schema 1.2.0.
The [ADP generator](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/sw/firmware/ctrl/adp/adp_entity.py)
uses the [builder](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/sw/builder/endstation_builder.py).
The [SRP generator](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/sw/firmware/ctrl/srp/srp_entity.py)
uses that same ADP result for stream counts.

The entity section alone omits MAC and stream shape. Use the documented projection below.
The [mapper](https://github.com/kebag-logic/tsn-c-stack/blob/6f4ecc9036f9ac2694b05a749cc9105d9c15c05f/scripts/milan_entity.py) accepts a full source document and copies only the protocol configuration facts.
Resolve the complete AEM model ID and entity capability value with the source builder first.
This avoids inventing a second hash algorithm for a partial descriptor model.
The manager owns the follow-up that replaces the firmware generators with this interface.

| Source 1.2.0 fact | Portable 1.0.0 field or treatment |
|---|---|
| `entity.entity_id` | `identity.entity_id`. Preserve explicit hexadecimal identity. Omission defaults to `mac-derived`. |
| `entity.entity_model_id`, optional `model_id_pin`, `vendor_oui` | `identity.model_id`, resolved by the complete source builder. A pin takes precedence over a valid literal. The selected literal or pin and any declared OUI must agree with the supplied resolved value. |
| `entity.name`, `vendor_name`, `serial_number`, `group_name` | Corresponding fields in `identity`. Omitted `vendor_name` defaults to `Kebag Logic`. Omitted `group_name` defaults to the empty string. Name and serial remain required. |
| `entity.locale` | AEM localization only. Retained by the product descriptor generator. No core field. |
| Optional `entity.entity_capabilities` | Must agree with the resolved capability value. Source authority is the [protocol package](https://github.com/Mister-M-alt/protocol-processor-control-plane-avb-milan/blob/2ad2f845dd583f8310075fa2380cb60a04fd091a/hdl/adp/pp_adp_pkg.sv). |
| `platform.mac_address` | `interfaces[0].mac`. Normalize source MAC spellings to colon-separated octets. The supported projection has one protocol interface. |
| `streams.listeners`, `streams.talkers` | Audio `inputs`, `outputs` in source order, all on interface 0. Preserve stream names. |
| `clocking.crf_sink`, `clocking.crf_output.enabled` | Append one clock input or output when true. Omitted source `crf_output` means disabled. |
| Stream channel counts, formats and map modes | Kept in the source AEM and media generators. No fields in these cores. |
| Source Identify descriptor | Index zero, as checked by the source ADP generator. |
| `srp.stream_dmac_base` | No direct MAAP mapping. Request random dynamic allocation. |
| Board, SoC, gPTP dataset, transport, audio and reservation fields | Remain product responsibilities. They are outside this projection. |

The [AX7101 fact fixture](https://github.com/kebag-logic/tsn-c-stack/blob/6f4ecc9036f9ac2694b05a749cc9105d9c15c05f/configs/compat/ax7101.json) records the source hash and size, selected input facts, and all nine old ADP values.
The mapping test produces a mapping equal to the tracked AX7101 YAML and checks every ADP value.
One audio plus one CRF stream gives two inputs and two outputs.
Both stream capability values are 0x4801. Entity capabilities are 0xC588.
Its model ID is 0x001BC5C1935893E1 and its entity ID is 0x020000FFFE000001.

Source scalar rules follow the pinned [hexadecimal parser](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/sw/builder/endstation_builder.py#L1349).
Explicit `entity_id`, literal `entity_model_id`, `model_id_pin`, `vendor_oui` and `entity_capabilities` must be strings.
Quote them in YAML. They use base 16, even when they contain only decimal digits.
An optional `0x` or `0X` prefix and single underscores between digits are accepted.
Signs, whitespace, repeated underscores and non-hexadecimal characters are refused.
Count leading zeros in the width: identities allow at most 16 hex digits, OUI allows 6, and capabilities allow 8.
Reserved model identities and the OUI I/G bit are refused.
The portable schema's identity and capability ranges still apply after projection.
For example, `"1234567890123456"` maps to integer `0x1234567890123456`.
An unquoted source integer is refused with a field-specific request to quote it.
These source string rules are separate from the portable schema's integer fields and the resolved CLI arguments.

The source [MAC parser](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/sw/builder/endstation_builder.py#L3279)
accepts six two-digit octets with a shared `:` or `-` separator.
It also accepts exactly 12 hexadecimal digits using the string grammar above.
The mapper accepts these forms and requires a nonzero unicast value.
The [builder defaults](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/sw/builder/endstation_builder.py#L3731)
apply only to omitted keys. An explicit null does not request a default.

For the pinned AX7101 source, run:

```sh
python3 scripts/milan_entity.py source/configs/endstation_ax7101_1x1_tdm8.yaml --model-id 0x001BC5C1935893E1 --capabilities 0xC588 --output build-ax7101.yaml
python3 scripts/entity_yaml.py build-ax7101.yaml --output build-ax7101 --prefix ax7101
```

The mapper refuses unsupported source versions, unknown entity fields, missing projection inputs, conflicting model identity or capabilities, and non-boolean CRF enables.
Other source sections are intentionally outside its validation scope.
Validate the complete product configuration with its own builder before projecting it.
The live source generators and all five end-station shapes were inspected for this mapping.
No platform source change is part of this repository change.

## Gates on both targets

The fresh [27-gate Linux run](evidence/round2/gates.json) and [RV32 Debug/Release run](evidence/round2/rv32-results.json) returned zero.
The [post-commit privacy check](evidence/round2/postcommit-privacy.log) also returned zero.

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

All 330 registered plants were caught. All 359 required assertion messages were rechecked in their completed XML reports.
The [mutation summary](evidence/round2/mutation-summary.json) includes the three named entity plants.
The [plant inventory](evidence/round2/mutation-plants.json) records every result.
The [coverage receipt](evidence/round2/coverage.log) remains at 100% lines and branches after existing exclusions.
The [conditional matrix](evidence/round2/conditionals.json) covers 58 region sides in 33 files.
The inventory remains 117 declarations and 391 executable instances across eight binaries.
All four Mermaid graphs rendered, including the [entity graph](evidence/round2/ENTITY_YAML-0.svg).

The [environment receipt](evidence/round2/environment.json) records actual compiler versions.
The supplied dependency environment selects GoogleTest 1.14.0 and Clang 18.1.3 for lexical gates.
The unversioned hosted compiler is Clang 23.1.1. It passed the sanitizer build.
GCC is 16.2.1. The RV32 compiler is 16.2.0.
Independent builds and campaigns used 16 jobs. Peak service memory was 4,875,554,816 bytes, below 9 GB.
RV32 executes the minimal port and all four generated entity round trips in Debug and Release.
It audits dependencies, generated-object imports and final unresolved symbols.
Hosted sanitizers, GoogleTest, coverage and the complete mutation campaign run on Linux.
They do not establish a separate RV32 coverage denominator or physical hardware behavior.

Reproduce the required gates from the repository root:

```sh
python3 scripts/validate.py --work build-validation --jobs 16 --graphs
python3 scripts/baremetal.py --work build-rv32 --jobs 16
```

## Standards and evidence

The local licensed PDFs were consulted for [IEEE 1722.1-2021 6.2.2.7 through 6.2.2.20, Tables 6-2 through 6-4, and 7.2.1, 7.2.6, 7.2.8, 7.2.12][atdecc],
[Milan v1.2 5.6.2][milan], and [IEEE 1722-2016 B.4 and Table B.9][avtp].
The tables above distinguish schema limits and source derivation policy from wire fields.
The [PDF inventory](evidence/round2/standards.json) records only hashes and sizes. No normative text is included.

The [receipt manifest](evidence/round2/receipt-manifest.json) records original hashes and sizes.
Published logs normalize only checkout and scratch paths.
The large mutation report and all build products remain in scratch and are represented by hashes and sizes.
The output contains no toolchains, installed packages, environments, exported source trees or files above 200 KB.
The [earlier merge audit](evidence/merge-audit.json) and [original mapping receipt](evidence/live-mapping.json) remain available.
The [PR body](PR-BODY.md) uses `Relates to #2` because the manager still owns the integration follow-up issue.
Hosted service execution and independent acceptance of this unpushed head remain manager duties.

[atdecc]: https://standards.ieee.org/ieee/1722.1/6670/
[milan]: https://avnu.org/resource/milan-specification/
[avtp]: https://standards.ieee.org/ieee/1722/5979/
[issue]: https://github.com/kebag-logic/tsn-c-stack/issues/2
