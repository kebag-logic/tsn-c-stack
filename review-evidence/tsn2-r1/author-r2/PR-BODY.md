[A580]

Relates to #2

Describe one entity in versioned YAML and generate const ADP, ACMP and MAAP configuration. Derive shared identity, MACs, counts and interface mappings together. Refuse invalid fields before writing output.

Adds listener, talker, duplex and AX7101 examples, byte-equal golden checks, and round trips through all three cores on both targets. The [schema and firmware mapping](docs/ENTITY_YAML.md) document field ranges, clauses and integration.

## Round 2

Preserve the source schema's quoted hexadecimal values, including digit-only identities. Check prefixes, underscores, widths, types and resolved declarations. Apply builder defaults and normalize supported MAC forms. Record ENTITY-01 with its issue-2 origin and reject missing requirement definitions. Clarify YAML quoting and parsed-mapping equality.

The unchanged review probe now has all ten expected outcomes. Six source-parser comparisons match. The compiled CLI regression preserves the same identity in ADP and ACMP. All 172 schema tests and eight additional mapper plants pass their expected checks.

Validate with:

```sh
python3 scripts/validate.py --work build-validation --jobs 16 --graphs
python3 scripts/baremetal.py --work build-rv32 --jobs 16
```

All 27 Linux gates and both RV32 configurations returned zero. All 330 registered plants were caught by their named assertions. Core line and branch coverage remain 100% after existing exclusions. All four Mermaid graphs rendered. Post-commit privacy passed.

The integration follow-up issue remains with the manager.
