[R579] NEGATIVE - exact head 4c939ef18741916df85a355973db007b588604e0

Independent verdict recorded before inspecting earlier review findings. All five lenses have been applied to repository artifacts. Full standards-text verification remains limited pending access; Linux validation is still running. These pending checks cannot remove the reproduced mapping defect.

R579-1-F1 — MAJOR — Conformance, RTL (implementation/interface projection), Robustness, Tests, Docs.
`scripts/milan_entity.py:25-36` interprets source hexadecimal strings inconsistently with the pinned milan-fpga schema 1.2.0 parser (`sw/builder/endstation_builder.py:1349-1386,3773-3805`). Source `entity_id: "1234567890"` denotes 0x1234567890; the mapper accepts it as decimal 1234567890 (0x499602d2). Bare hexadecimal IDs and model pins are refused, as are valid quoted vendor OUI and capabilities. Acceptance item 7 and docs/ENTITY_YAML.md:162-167 promise preservation and consistency of these source facts. The baseline AX7101 source matches its fixture hash and maps correctly, but six scalar variants fail the source contract. Evidence: receipts/mapping-probe.json; portable reproduction: scripts/mapping-probe.py. Required outcome: implement the pinned source hexadecimal grammar and bounds for each projected scalar, preserve identity, compare normalized OUI/capability values, and add regression cases for the alternate valid spellings and invalid grammar. Verify byte-identical baseline mapping, all scalar cases, golden regeneration and both target gates.

| lens | CLEAN/UNCLEAN | examined artifacts | covering round | exact head |
|---|---|---|---|---|
| Conformance | UNCLEAN | Issue body and assignment; schema table; pinned source scalar parsers; core headers; mapping probe | R579-1 | 4c939ef18741916df85a355973db007b588604e0 |
| RTL | UNCLEAN | No RTL changed; C generator, core configurations, source interface projection, generated objects; F1 affects emitted identity | R579-1 | 4c939ef18741916df85a355973db007b588604e0 |
| Robustness | UNCLEAN | Strict loader, range validation, escaping, output preservation, mapper; F1 | R579-1 | 4c939ef18741916df85a355973db007b588604e0 |
| Tests | UNCLEAN | Entity selftests, independent C round-trip oracles, three plants, target drivers; missing scalar variants expose F1 | R579-1 | 4c939ef18741916df85a355973db007b588604e0 |
| Docs | UNCLEAN | ENTITY_YAML, PORTING, coding/verification contracts and mapping table; F1 contradicts compatibility claims | R579-1 | 4c939ef18741916df85a355973db007b588604e0 |

This is the immutable independent-pass receipt. The final report will record completed validation, public evidence reconciliation, prior-review disposition, integrity checks and manager duties.
