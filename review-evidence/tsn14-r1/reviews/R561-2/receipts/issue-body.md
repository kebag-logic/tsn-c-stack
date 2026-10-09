Port the milan-fpga requirements that apply to this repository's scope into [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md) and `docs/requirements.json`. Keep their traceability to milan-fpga and to the standards. Owner request, 2026-10-09.

## Sources in milan-fpga

- [`docs/reference/FR_NFR.md`](https://github.com/kebag-logic/milan-fpga/blob/dev/docs/reference/FR_NFR.md): functional (`FR-*`) and non-functional (`NFR-*`) requirements, the control service budget (section 3.4.1) and its test hooks (section 3.4.2).
- [`REQUIREMENTS.md`](https://github.com/kebag-logic/milan-fpga/blob/dev/REQUIREMENTS.md): product ownership and protocol rows.
- The Mark II firmware decisions on [milan-fpga#665](https://github.com/kebag-logic/milan-fpga/issues/665): bare-metal first, no heap, static pools, GoogleTest with 100 % branch coverage.

## Proposed mapping

| milan-fpga ID | Here | Note |
|---|---|---|
| FR-DISC-01 … 05 | ADP | Advertise, discover, depart, advertised fields, EUI-64 entity ID. |
| FR-CONN-01, 03, 04 | ACMP | Commands as talker and listener, fast-connect and state restore, persisted bindings as a port obligation. |
| FR-CONN-02 | PORTING (obligation) | Datapath programming is the integrator's job, not a core requirement. |
| FR-MAAP-01 | MAAP | Allocate and defend stream addresses. |
| FR-SRP-01, 02 | ACMP-to-SRP boundary | Through lwSRP and the port. SRP itself is not in the cores. |
| NFR-SCOUT-02, 03 and the section 3.4.1 hooks | Service budget | Per-core service bound (T_svc 10 ms) as an integrator-checkable figure, on both targets. |
| NFR-REL-01 | Recovery | Link flap, grandmaster change, peer loss recover without a restart, and are counted. |
| NFR-PORT-01 | Build | Bare-metal RV32I build with no OS dependency. It extends to the owner's Linux and bare-metal rule. |
| #665 Mark II rules | Quality | No heap, static pools, GoogleTest and GMock, 100 % branch coverage. |
| AECP, AEM, MVU, gPTP, CRF, AAF, QoS, fabric, CSR (FR-CTRL, FR-ENUM, FR-MVU, FR-CLK, FR-STR, FR-QOS, NFR-SCOUT-04 … 08 and others) | Not ported | Not in this repository's scope. List them in `docs/REQUIREMENTS.md` as excluded, with the reason. |

## Acceptance

1. Each ported requirement gets an ID here, keeping its origin (`origin: milan-fpga FR-DISC-01` in `requirements.json`), and its standard clause with one link per cited standard.
2. Text is restated for a portable library, not copied. FPGA-specific words (fabric, CSR, mailbox) are removed or become port obligations in [PORTING](docs/PORTING.md).
3. Every ported requirement has at least one test tagged `// REQ:`, or is marked "verified by inspection" or "port obligation" with the reason. The traceability and inventory gates pass. Tests added for an uncovered requirement carry a planted defect.
4. Each excluded milan-fpga requirement is listed with the reason.
5. The requirements hold on both targets (Linux and bare-metal). A requirement that cannot is flagged.
6. TRACEABILITY.md is regenerated, and the docs follow the owner's public-docs rules.

Sequencing: after the open follow-up PR (review fixes and comment reduction) merges, because it edits the same requirement files. Relates to [kebag-logic/milan-fpga#697](https://github.com/kebag-logic/milan-fpga/issues/697).

