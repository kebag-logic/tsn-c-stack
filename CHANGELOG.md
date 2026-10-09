# Change log

## Review follow-up

Require fresh complete mutation reports, specific assertion messages, compiler boundary checks and executable test registration.
Link each standard separately. Record the inherited ADP input limits and caller validation obligations.
Require Linux and freestanding RV32 validation in [CI](.github/workflows/quality.yml).
Link the complete RV32 library against a minimal port and run protocol smoke checks in Debug and Release.


## Unreleased

- Import the ADP, ACMP and MAAP cores and wire helpers with rewritten history.
- Apply the [MIT licence](LICENSE) to the exported sources and core tests.
- Add standalone builds, core mutation plants and the coverage ratchet.
- Add sanitizer, static-analysis, boundary, licence, privacy and traceability gates.
- Add the [quality documents](docs/VERIFICATION.md) and a [port example](examples/adp_port.c).

Relates to [milan-fpga issue 697](https://github.com/kebag-logic/milan-fpga/issues/697).
