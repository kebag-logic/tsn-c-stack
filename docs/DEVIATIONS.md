# Deviations and scope

This import preserves core behavior. Passing unit tests is not a claim of complete
Milan or IEEE device certification. The [requirements](REQUIREMENTS.md) list the
covered clauses. The [traceability matrix](TRACEABILITY.md) names their tests.

| ID | Clause | Decision and rationale |
|---|---|---|
| DEV-01 | [Milan v1.2 5.5 and 5.6](https://avnu.org/resource/milan-specification/) | Implement the Milan connection and discovery profile. Generic controller operations, AEM enumeration and media transport are outside these cores. |
| DEV-02 | [IEEE 1722.1-2021 6.2.2.15 and 6.2.5.2.2](https://standards.ieee.org/ieee/1722.1/6670/) | A departing frame carries the current index. Reset affects the next advertisement. This preserves the source interpretation of departure construction. |
| DEV-03 | [Milan v1.2 5.6.3.5.8 and 5.6.3.5.11](https://avnu.org/resource/milan-specification/) | Two departures may be owed. Further identical zero-index departures coalesce and increment a diagnostic. This bounds storage during repeated shutdowns. |
| DEV-04 | [Milan v1.2 Table 5.50 and Table 5.29](https://avnu.org/resource/milan-specification/) | ADP and ACMP use finite-resolution pseudorandom delays. Entropy comes from the integrator. This is not a security random source. |
| DEV-05 | [IEEE 1722-2016 Annex B, Table B.7](https://sagroups.ieee.org/1722/) | MAAP uses a fixed output queue. Overload is counted and requires prompt port service. Timing on a real transport is outside host unit tests. |
| DEV-06 | [IEEE 1722.1-2021 8.2.1](https://standards.ieee.org/ieee/1722.1/6670/) | Receivers expect untagged frame layout. The integrator removes VLAN tags. This keeps parsing independent of the network driver. |
| DEV-07 | [Milan v1.2 5.5.3.5.2](https://avnu.org/resource/milan-specification/) | Binding serialization is a local 20-byte format. This library supplies no persistent store. The integrator provides durable transaction semantics. |

The 2021 and 2016 editions above are the import baseline.
Later amendments and corrigenda have not been audited by this lane.
The [coverage exclusions](COVERAGE.md) are unreachable-state proofs, not waived
protocol requirements. Capacity limits are explicit in the [public headers](../include/).
