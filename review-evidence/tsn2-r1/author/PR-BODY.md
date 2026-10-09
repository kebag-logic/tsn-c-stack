[A580]

Relates to #2

Describe one entity in versioned YAML and generate const ADP, ACMP and MAAP configuration. Shared identity, MACs, counts and interface mappings are derived together. Invalid fields and inconsistent ranges are refused before output is written.

Adds listener, talker, duplex and AX7101 examples, golden checks and round trips through every core on both targets. Three compiling plants check wrong counts, swapped interfaces and a dropped field. The [firmware mapping](docs/ENTITY_YAML.md#mapping-from-milan-fpga) preserves the AX7101 identity and includes its CRF streams.

Merges [main `51870377c5012766a8ea1d9798e3c499ca1060a3`](https://github.com/kebag-logic/tsn-c-stack/commit/51870377c5012766a8ea1d9798e3c499ca1060a3) with a merge commit. All plants and suppressions from both parents are preserved. Traceability, the test inventory and all four golden entities were regenerated. Core sources and public headers match that base exactly.

Validate with:

```sh
python3 scripts/validate.py --work build-validation --jobs 16 --graphs
python3 scripts/baremetal.py --work build-rv32 --jobs 16
```

All 27 hosted gates and both freestanding RV32 configurations returned zero. Hosted tests, sanitizers and coverage passed. The inventory contains 117 test declarations and 391 executable instances. All 330 plants were caught by their named assertions. Core line and branch coverage remain at 100% after the existing exclusions. All four Mermaid graphs rendered. Post-commit privacy passed.

The integration follow-up issue remains with the manager.
