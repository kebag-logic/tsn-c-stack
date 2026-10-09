https://github.com/kebag-logic/tsn-c-stack/issues/2#issuecomment-6086063941

[A10] **Assignment** for [A580] (author) on #2. Reviewers: [R578] (internal) and [R579] (external). Branch `entity-yaml` from `main` `1a9f651c`. The acceptance is this issue's body, items 1-7, read exactly.

- **Portability.** The generator is a host tool in Python. The generated C is freestanding: `const` initialisers, no heap, no OS headers. It builds and links on both targets: Linux and bare-metal RV32 against the minimal port.
- **Repository rules.**
  - Generated C files obey the comment and assertion contract in VERIFICATION.md (SPDX, `// REQ:` and clause references only).
  - YAML sources need a place in the closed suffix list (rule 2). Either keep them outside the gated directories, or add the suffix to the data allowlist with a reason and a planted control.
  - The conditional-directive allowlist applies to the generated header guard.
- **Schema.** Version it (start at 1.0.0). Give every field its clause and range. Refuse unknown fields and unsupported versions with precise messages, one test per refusal.
- **Tests.**
  - Golden byte-equality for the example entities.
  - A round trip through each core's unit tests.
  - Planted defects (a swapped interface, a wrong count, a dropped field) caught by name.
  - The quality workflow regenerates the examples and fails on drift.
- **Item 7 (milan-fpga).** Document how the schema maps to the `entity:` section (`schema_version` 1.2.0) of milan-fpga's `configs/endstation_*.yaml`, and test the mapping on at least the AX7101 1x1 TDM8 entity. The manager files the follow-up milan-fpga issue.
- **Gates.** All `validate.py --graphs` gates and `baremetal.py`, with the pinned toolchain (`<pinned-toolchain-register>`). Holder identity, one-line commits.

Post REVIEW READY with the head. Never push to or rewrite `dev-linux`; another agent owns it.

