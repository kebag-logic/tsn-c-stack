The external reviewer checked the cited editions directly. No standards text is reproduced here. This audit covers the new requirement records and the added port contracts at `db950cfa959f501932a47d4113733a671f882a83`.

| Authority | Edition checked | SHA-256 of inspected PDF |
|---|---|---|
| [IEEE 1722.1](https://standards.ieee.org/ieee/1722.1/6670/) | 2021 | `ad7b822008c1b78bce8af1470f1ace177a22344aa48c0da939066d6db9a65b9c` |
| [Milan](https://avnu.org/resource/milan-specification/) | Consolidated revision 1.2, November 29, 2023 | `6bb902be1c1de8c44f4c4c583a645b0b37e0b2dac27870486ce229e68ce3bba8` |
| [IEEE 1722](https://standards.ieee.org/ieee/1722/5979/) | 2016, Annex B | `ba20762d444e6f7795ffc000bcaf6144e9618eff81cadd867863ed58000f8a8c` |

The standard landing links identify the publishers. Their current editions do not replace the frozen editions above. In particular, the Milan landing page now offers revision 1.3; the clause check used the identified revision 1.2 PDF.

| Imported IDs | Clauses checked | Assessment |
|---|---|---|
| MFDISC-01 | IEEE 1722.1 6.2.2.5, 6.2.2.15; Milan 5.6.2, 5.6.3.5 | Validity units, schedule and sequence references agree. The inherited departure-index interpretation is explicitly qualified by DEV-02. Transport acceptance and physical departure remain distinct. |
| MFDISC-02 | IEEE 1722.1 6.2.2.4, 6.2.2.7; Milan 5.6.3.1, 5.6.3.5, Table 5.51 | Global/own targets and state-dependent discovery processing agree. A discovery in DELAY must not restart the delay. |
| MFDISC-03 | Milan 5.6.3.5.6, .8, .10, .11 | The documented departure on shutdown, versus timer stop and DOWN on link loss, is the correct revision of the source row. |
| MFDISC-04; MFENTITY-01 | IEEE 1722.1 6.2.2.7–6.2.2.20; Milan 5.6.2 | The field encoding and caller configuration split is appropriate. Grandmaster and domain are interface state. Counts describe maximum simultaneous capacity. The new 82-byte vector has independent big-endian expectations and different source/sink counts and capabilities. |
| MFENTITY-02 | IEEE 1722.1 6.2.2.7 | EUI-64 and consistent identity are supported. MAC derivation and reboot stability are retained product policy, explicitly distinguished from the standard's permission to derive identity. |
| MFCONN-01 | IEEE 1722.1 8.2.1; Milan 5.5.2.1–5.5.2.5, 5.5.3, 5.5.4 | The IEEE PDU authority and Milan bind/probe behavior are correctly separated. The source CONNECT terminology is changed with a stated profile reason. |
| MFCONN-02 | Milan 4.3.3.2, 5.5.3.5.18 | Stream parameters and reservation precede the external transport's activation. Queue/shaper programming belongs to the integration. |
| MFCONN-03 | Milan 5.5.2.6, 5.5.3.5.2, 5.6.4.5 | Saved binding startup, discovery and reprobe support automatic reconnection. Admission and transport opening are local interface obligations. |
| MFCONN-04 | Milan 5.3.8.2, 5.3.8.3, 5.3.8.7, 5.5.3.5.2 | Bound state, binding parameters and started state need persistence. Durable transactions and rollback are assigned to the store/port, with the core codec tested separately. |
| MFMAAP-01 | IEEE 1722 B.2, B.3, B.4, Tables B.7/B.8; Milan 4.3.5.1 | Allocation, conflict handling, defense and release are correctly traced. Annex B distinguishes initial probing from its three retransmissions. |
| MFMAAP-02 | IEEE 1722 B.3.2, Table B.7; Milan 4.3.5.1, 5.5.4.1 | Loss of allocation must invalidate destination use. Stream assignment and the talker source view are external integration duties. |
| MFSRP-01 | Milan 5.5.3.5.18, .36, Tables 5.23/5.29/5.30 | Settlement starts reservation; leaving settlement clears it. Registered, withdrawn and changed-kind feedback remain distinct inputs. |
| MFSRP-02 | Milan 4.2.7.2, 4.3.3, 5.5.2.7 | External MSRP declarations/admission are correctly split from ACMP callbacks. The selection of lwSRP comes from the source decision. |
| MFSRP-03 | Milan 4.2.7.3, 4.3.2, 4.4.1 | MVRP membership follows the stream VLAN and interface. It is external to these cores. |
| MFSRP-04 | Milan 4.3.3.2, 5.5.2.7 | Admission and reservation-derived shaping are valid port duties. Adding FR-SRP-03 to the proposed mapping is justified by the same transport boundary as FR-CONN-02. |
| MFOWNER-01 | Milan 5.5.3.5, 5.6.3.5; IEEE 1722 B.3 | Serialized state-machine processing supports the local one-owner rule. Platform placement switches and ingress hardware are explicitly excluded. |
| MFSERVICE-01 | Milan 5.5.2.3, 5.6.3.5, 5.6.4.5; IEEE 1722 B.3.4 | The 10 ms quantity is expressly project policy. PORTING preserves original event/deadline starts, one total service allowance, normative waits, all matching sinks and refused sends. |
| MFLATENCY-01 | Milan 5.5.2.3, Table 5.26 | The 200 ms ACMP transaction limit is correct. The added NFR-LAT-02 mapping requires measured ingress/service/egress/network margin, not merely a core timer pass. |
| MFRECOVERY-01; MFRECOVERY-02 | Milan 5.5.3.5, 5.6.3.5, 5.6.4.5; IEEE 1722 B.3.2, Table B.7 | Core recovery and application event delivery/accounting are correctly split. No claim of complete recovery counters is made for the existing diagnostics. |
| MFBUILD-01 | [Pinned NFR-PORT-01](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/docs/reference/FR_NFR.md#L469) and [assignment](https://github.com/kebag-logic/tsn-c-stack/issues/14#issuecomment-6080704899) | Build policy is linked to its source, without an invented standards clause. The assignment extends it to Linux and RV32. |
| MFMEMORY-01 | [Memory decision](https://github.com/kebag-logic/milan-fpga/issues/665#issuecomment-5992455815) | Fixed caller-owned storage, no heap and no OS in protocol cores preserve the applicable decision. |
| MFQUALITY-01 | [Testing decision](https://github.com/kebag-logic/milan-fpga/issues/665#issuecomment-6008744385) | Hosted coverage and mutation apply to the common core. RV32 smoke execution is explicitly distinguished from a coverage denominator. |

The H-ADP, H-DISC, H-ACMP and H-MAAP port hooks retain the source's event and completion boundaries. H-SRP is assigned to the external reservation component. The excluded AECP, notification and counter-serving hooks correspond to absent components. IEEE 1722 B.3.3/B.3.4 supports the strict MAAP interval bounds in PORTING; service cannot extend a near-limit draw past them.

The independent [source audit](receipts/source-audit.txt) extracts the numbered IDs from both pinned upstream files, rather than using the implementation's hard-coded inventory as its oracle. All 114 IDs and source line links match. Its 116 dispositions comprise 12 ported rows, eight wholly assigned to the port, and 96 exclusions. Split rows state the excluded platform parts. The unnumbered product ownership and ingress rows are also addressed in REQUIREMENTS.md:67–86.
