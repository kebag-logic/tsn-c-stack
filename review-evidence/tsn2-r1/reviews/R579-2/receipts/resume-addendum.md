# R579-2 resume addendum

An external usage limit cut the first session after its report draft and before `MANIFEST.sha256` was written. No GitHub write occurred in either session.

When the work resumed, the reviewer re-checked the first session's receipts. They also compared the mapper's accepted `entity:` key set with every key the pinned source builder reads. Source revision: milan-fpga `5603c353137e90c1fa95429f6d00ef7a2298d9ee`, `sw/builder/endstation_builder.py`, SHA-256 `4372d698990537b1d7ca8b43c66283be8b70989a1cb18542975dde53cd20838f`.

The source reads these entity keys:

- `entity_id`
- `entity_model_id`
- `model_id_pin`
- `name`
- `vendor_name`
- `serial_number`
- `group_name`
- `vendor_oui`
- `locale`
- `entity_capabilities`
- `firmware_rev`
- `firmware_version`, which the source refuses

The mapper allowlist at `scripts/milan_entity.py:56` covers all of these except `firmware_rev`.

`firmware_rev` is optional in the source and defaults to 0:

- the builder reads it at line 3727;
- the builder's `firmware_version` refusal at line 3726 tells users to use it;
- the source builder documentation lists it in row 4b;
- comments in four of the five pinned end-station configurations document it.

This addendum was written after the first session had read the earlier public findings. The finding is the reviewer's own and does not appear in those findings. The first session's independent verdict (`independent-verdict.md`) remains as written; the final report supersedes its POSITIVE verdict.

Probe: `scripts/probe_firmware_rev.py`. Result: `probe-firmware-rev.log`, exit status 1.
