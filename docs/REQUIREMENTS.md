# Requirements

These requirements describe this import, not complete device certification.
The cited editions are IEEE 1722.1-2021, Milan v1.2 and IEEE 1722-2016.
Clause labels refer to those editions. No standards text is reproduced.
Local port rules are identified as local requirements.
See [deviations](DEVIATIONS.md) and the generated [traceability matrix](TRACEABILITY.md).

| ID | Required behavior | Clause |
|---|---|---|
| ADP-01 | Encode the entity fields and reject unrelated or malformed discovery input. | [IEEE 1722.1-2021 6.2.2; Milan v1.2 5.6.3.1](https://standards.ieee.org/ieee/1722.1/6670/); [companion reference](https://avnu.org/resource/milan-specification/) |
| ADP-02 | Follow advertise, discover, link, grandmaster and shutdown transitions. | [Milan v1.2 5.6.3.5, Table 5.51; IEEE 1722.1-2021 6.2.2.15](https://avnu.org/resource/milan-specification/); [companion reference](https://standards.ieee.org/ieee/1722.1/6670/) |
| ADP-03 | Keep refused departures ordered before an advertisement. Bound storage and count coalescing. | [IEEE 1722.1-2021 6.2.5.2.2; Milan v1.2 5.6.3.5.8 and 5.6.3.5.11; local transport contract](https://standards.ieee.org/ieee/1722.1/6670/); [companion reference](https://avnu.org/resource/milan-specification/) |
| PORT-01 | Serialize input. Refuse synchronous callback re-entry. Preserve state on refusal. | [Local port contract supporting Milan v1.2 5.5.3.5 and 5.6.3.5; IEEE 1722-2016 B.3](https://avnu.org/resource/milan-specification/); [companion reference](https://sagroups.ieee.org/1722/) |
| ACMP-01 | Refuse configurations outside static capacities and initialize without port access. | [Local capacity contract supporting Milan v1.2 5.5.3.5.1](https://avnu.org/resource/milan-specification/) |
| ACMP-02 | Parse and build the Milan ACMP format, status codes and flags. Ignore foreign input. | [IEEE 1722.1-2021 8.2.1; Milan v1.2 5.5.2.2 and 5.5.3.1](https://standards.ieee.org/ieee/1722.1/6670/); [companion reference](https://avnu.org/resource/milan-specification/) |
| ACMP-03 | Bind, unbind and report each sink with lock checks and response-before-change ordering. | [Milan v1.2 5.5.2.4, 5.5.2.5 and 5.5.3.5, Tables 5.30 and 5.32](https://avnu.org/resource/milan-specification/) |
| ACMP-04 | Probe the bound talker, match responses, retry and consume reservation feedback. | [Milan v1.2 5.5.3.5, Tables 5.29 and 5.30](https://avnu.org/resource/milan-specification/) |
| ACMP-05 | Start probe deadlines after accepted sends. Keep the earliest per-interface timer across wrap. | [Milan v1.2 5.5.2.3, 5.5.3.5.3 and 5.5.3.5.16, Table 5.26](https://avnu.org/resource/milan-specification/) |
| ACMP-06 | Discover bound talkers by interface and grandmaster. Handle departure, index changes and aging. | [Milan v1.2 5.6.4.1 and 5.6.4.5, Table 5.54; IEEE 1722.1-2021 6.2.2.5](https://avnu.org/resource/milan-specification/); [companion reference](https://standards.ieee.org/ieee/1722.1/6670/) |
| ACMP-07 | Restore and latch bindings for fast connect without a storage-device dependency. | [Milan v1.2 5.5.3.5.2 and 5.5.2.4; local binding-record format](https://avnu.org/resource/milan-specification/) |
| ACMP-08 | Answer talker commands from live source state with the prescribed flags. | [Milan v1.2 5.5.4; IEEE 1722.1-2021 8.2.1](https://avnu.org/resource/milan-specification/); [companion reference](https://standards.ieee.org/ieee/1722.1/6670/) |
| ACMP-09 | Queue bounded responses and delay notifications until their responses are accepted. | [Milan v1.2 5.5.3.5; local transport and port work budgets](https://avnu.org/resource/milan-specification/) |
| MAAP-01 | Validate frame fields, destination, source, lengths and supported version behavior. | [IEEE 1722-2016 B.2, especially B.2.3](https://sagroups.ieee.org/1722/) |
| MAAP-02 | Reserve valid ranges using three probe retransmissions and randomized timer intervals. | [IEEE 1722-2016 B.3.3, B.3.6.1 and B.4, Tables B.8 and B.9](https://sagroups.ieee.org/1722/) |
| MAAP-03 | Resolve full-width range conflicts and priority. Defend the exact intersection. | [IEEE 1722-2016 B.3, Table B.7; Milan v1.2 4.3.5.1](https://sagroups.ieee.org/1722/); [companion reference](https://avnu.org/resource/milan-specification/) |
| MAAP-04 | Withdraw on loss and publish allocation only after accepted ANNOUNCE. Bound pending work. | [IEEE 1722-2016 B.3, Table B.7; local transport contract](https://sagroups.ieee.org/1722/) |
