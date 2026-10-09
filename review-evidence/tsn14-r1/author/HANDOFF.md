# Requirements port handoff

Status: REVIEW READY under the manager ruling. Role: author. Lane: [A571].

[Final REVIEW READY status](https://github.com/kebag-logic/tsn-c-stack/issues/14#issuecomment-6081320203) was posted with the final head. TAKEN was not repeated.

The [manager ruling](https://github.com/kebag-logic/tsn-c-stack/issues/14#issuecomment-6081168071) authorizes commits with the inherited privacy failure recorded. [PR 17](https://github.com/kebag-logic/tsn-c-stack/pull/17) supplies the policy fix. Every other gate must pass. The manager will merge main before review.

Assignment: [issue 14](https://github.com/kebag-logic/tsn-c-stack/issues/14#issuecomment-6080704899).

Branch: `requirements-port`. Confirmed starting head: `18d737832c376f32660eb21fe2796e0b611507e3`.
Remote main matched that commit. The local main ref is older and was not moved.
[TAKEN status](https://github.com/kebag-logic/tsn-c-stack/issues/14#issuecomment-6080718397) was posted.

The source clone is read-only. Its dev head is `5603c353137e90c1fa95429f6d00ef7a2298d9ee`.
The mapping covers all 68 FR/NFR rows, all 46 numbered product rows and the two Mark II decisions.
It adds 24 local requirements. The original 17 requirements remain.
Twenty-six existing declarations have additional requirement tags.
One new ADP wire-vector test has eleven field defects. The campaign now has 322 plants.

Production sources and headers are unchanged. No push or pull request creation was performed.

## Commits and resumed validation

- [3d50085fc627f9cfb4c7f5817936cda1f1dd8dd9](https://github.com/kebag-logic/tsn-c-stack/commit/3d50085fc627f9cfb4c7f5817936cda1f1dd8dd9): Test ADP advertisement fields with independent wire bytes.
- [69a312e3914f96c2db5fa51f07b087a6cd6ff349](https://github.com/kebag-logic/tsn-c-stack/commit/69a312e3914f96c2db5fa51f07b087a6cd6ff349): Port applicable Milan requirements with origins and clause traceability.

Each step ran the complete gate set before its commit. Only the inherited privacy failure remains. Both commits use the configured identity, a one-line subject, no body and no trailers. The post-commit privacy scan reports no finding for either new commit.

The saved patch matched the prepared tree. All 114 numbered source IDs and pinned line links were independently matched against the read-only clone. The final files match the prepared files exactly.

## Mapping

| Source | Disposition | Local IDs | Reason |
|---|---|---|---|
| [milan-fpga FR-DISC-01](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/docs/reference/FR_NFR.md#L187) | ported | [MFDISC-01](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/docs/REQUIREMENTS.md#mfdisc-01) | Ported schedule and index handling. Transport acceptance remains subject to the existing departure interpretation and service obligation. |
| [milan-fpga FR-DISC-02](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/docs/reference/FR_NFR.md#L188) | ported | [MFDISC-02](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/docs/REQUIREMENTS.md#mfdisc-02) | Ported both discovery target forms and the Milan state-dependent delay rule. |
| [milan-fpga FR-DISC-03](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/docs/reference/FR_NFR.md#L189) | ported | [MFDISC-03](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/docs/REQUIREMENTS.md#mfdisc-03) | Changed the proposed shutdown/link-down equivalence. [Milan v1.2 5.6.3.5.6 and 5.6.3.5.10](https://avnu.org/resource/milan-specification/) stop timers on link down; 5.6.3.5.8 and 5.6.3.5.11 send departure on shutdown. |
| [milan-fpga FR-DISC-04](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/docs/reference/FR_NFR.md#L190) | ported | [MFDISC-04](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/docs/REQUIREMENTS.md#mfdisc-04); [MFENTITY-01](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/docs/REQUIREMENTS.md#mfentity-01) | Split encoding from descriptor consistency. Grandmaster identity is live per-interface port data, not a stored ENTITY descriptor field. |
| [milan-fpga FR-DISC-05](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/docs/reference/FR_NFR.md#L191) | port obligation | [MFENTITY-02](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/docs/REQUIREMENTS.md#mfentity-02) | Moved identity derivation and stability to the caller. The library has no device identity store. |
| [milan-fpga FR-ENUM-01](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/docs/reference/FR_NFR.md#L196) | excluded | None | AEM descriptors and enumeration are outside the ADP, ACMP and MAAP cores. |
| [milan-fpga FR-ENUM-02](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/docs/reference/FR_NFR.md#L197) | excluded | None | AEM descriptors and enumeration are outside the ADP, ACMP and MAAP cores. |
| [milan-fpga FR-CTRL-01](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/docs/reference/FR_NFR.md#L198) | excluded | None | AECP command handling, locks, notifications and counter serving are outside these cores. ACMP consumes external lock and change callbacks. |
| [milan-fpga FR-CTRL-02](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/docs/reference/FR_NFR.md#L199) | excluded | None | AECP command handling, locks, notifications and counter serving are outside these cores. ACMP consumes external lock and change callbacks. |
| [milan-fpga FR-CTRL-03](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/docs/reference/FR_NFR.md#L200) | excluded | None | AECP command handling, locks, notifications and counter serving are outside these cores. ACMP consumes external lock and change callbacks. |
| [milan-fpga FR-CTRL-04](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/docs/reference/FR_NFR.md#L201) | excluded | None | AECP command handling, locks, notifications and counter serving are outside these cores. ACMP consumes external lock and change callbacks. |
| [milan-fpga FR-CTRL-05](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/docs/reference/FR_NFR.md#L202) | excluded | None | AECP command handling, locks, notifications and counter serving are outside these cores. ACMP consumes external lock and change callbacks. |
| [milan-fpga FR-CTRL-06](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/docs/reference/FR_NFR.md#L203) | excluded | None | AECP command handling, locks, notifications and counter serving are outside these cores. ACMP consumes external lock and change callbacks. |
| [milan-fpga FR-MVU-01](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/docs/reference/FR_NFR.md#L208) | excluded | None | The Milan vendor-unique responder and its product feature policy are outside these cores. |
| [milan-fpga FR-MVU-02](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/docs/reference/FR_NFR.md#L209) | excluded | None | The Milan vendor-unique responder and its product feature policy are outside these cores. |
| [milan-fpga FR-MVU-03](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/docs/reference/FR_NFR.md#L210) | excluded | None | The Milan vendor-unique responder and its product feature policy are outside these cores. |
| [milan-fpga FR-CONN-01](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/docs/reference/FR_NFR.md#L215) | ported | [MFCONN-01](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/docs/REQUIREMENTS.md#mfconn-01) | Changed legacy CONNECT names to the Milan bind/probe profile under [Milan v1.2 5.5.2.1 and 5.5.2.2](https://avnu.org/resource/milan-specification/). Generic controller sequences are excluded. |
| [milan-fpga FR-CONN-02](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/docs/reference/FR_NFR.md#L216) | port obligation | [MFCONN-02](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/docs/REQUIREMENTS.md#mfconn-02) | Datapath programming remains a port obligation, as proposed. |
| [milan-fpga FR-CONN-03](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/docs/reference/FR_NFR.md#L217) | ported | [MFCONN-03](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/docs/REQUIREMENTS.md#mfconn-03) | Ported restore, discovery and reprobe. Cold boot and real link delivery remain integration duties. |
| [milan-fpga FR-CONN-04](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/docs/reference/FR_NFR.md#L218) | port obligation | [MFCONN-04](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/docs/REQUIREMENTS.md#mfconn-04) | Durable storage remains a port obligation. The existing codec, latch and rollback tests support it. |
| [milan-fpga FR-MAAP-01](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/docs/reference/FR_NFR.md#L223) | ported | [MFMAAP-01](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/docs/REQUIREMENTS.md#mfmaap-01); [MFMAAP-02](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/docs/REQUIREMENTS.md#mfmaap-02) | Ported allocation and defense. Split downstream destination assignment into a port obligation. |
| [milan-fpga FR-SRP-01](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/docs/reference/FR_NFR.md#L224) | ported | [MFSRP-01](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/docs/REQUIREMENTS.md#mfsrp-01); [MFSRP-02](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/docs/REQUIREMENTS.md#mfsrp-02) | Split tested ACMP callbacks from external lwSRP declarations and admission. |
| [milan-fpga FR-SRP-02](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/docs/reference/FR_NFR.md#L225) | port obligation | [MFSRP-03](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/docs/REQUIREMENTS.md#mfsrp-03) | MVRP belongs to lwSRP and the port; the core exposes stream VLAN parameters. |
| [milan-fpga FR-SRP-03](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/docs/reference/FR_NFR.md#L226) | port obligation | [MFSRP-04](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/docs/REQUIREMENTS.md#mfsrp-04) | Added as a port obligation because admission and shaping share the proposed FR-CONN-02 boundary. |
| [milan-fpga FR-CLK-01](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/docs/reference/FR_NFR.md#L250) | excluded | None | gPTP, PHC, timestamps and media-clock recovery belong to the time and media implementation. The port supplies current GM data. |
| [milan-fpga FR-CLK-02](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/docs/reference/FR_NFR.md#L251) | excluded | None | gPTP, PHC, timestamps and media-clock recovery belong to the time and media implementation. The port supplies current GM data. |
| [milan-fpga FR-CLK-03](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/docs/reference/FR_NFR.md#L252) | excluded | None | gPTP, PHC, timestamps and media-clock recovery belong to the time and media implementation. The port supplies current GM data. |
| [milan-fpga FR-CLK-04](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/docs/reference/FR_NFR.md#L253) | excluded | None | gPTP, PHC, timestamps and media-clock recovery belong to the time and media implementation. The port supplies current GM data. |
| [milan-fpga FR-CLK-05](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/docs/reference/FR_NFR.md#L254) | excluded | None | gPTP, PHC, timestamps and media-clock recovery belong to the time and media implementation. The port supplies current GM data. |
| [milan-fpga FR-STR-01](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/docs/reference/FR_NFR.md#L269) | excluded | None | AAF media, audio formats, channel maps and stream counters are outside a control library. |
| [milan-fpga FR-STR-02](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/docs/reference/FR_NFR.md#L270) | excluded | None | AAF media, audio formats, channel maps and stream counters are outside a control library. |
| [milan-fpga FR-STR-03](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/docs/reference/FR_NFR.md#L271) | excluded | None | AAF media, audio formats, channel maps and stream counters are outside a control library. |
| [milan-fpga FR-STR-03a](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/docs/reference/FR_NFR.md#L272) | excluded | None | AAF media, audio formats, channel maps and stream counters are outside a control library. |
| [milan-fpga FR-STR-03b](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/docs/reference/FR_NFR.md#L273) | excluded | None | AAF media, audio formats, channel maps and stream counters are outside a control library. |
| [milan-fpga FR-STR-04](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/docs/reference/FR_NFR.md#L274) | excluded | None | AAF media, audio formats, channel maps and stream counters are outside a control library. |
| [milan-fpga FR-STR-05](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/docs/reference/FR_NFR.md#L275) | excluded | None | AAF media, audio formats, channel maps and stream counters are outside a control library. |
| [milan-fpga FR-QOS-01](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/docs/reference/FR_NFR.md#L280) | excluded | None | Queue classification, shaping and bandwidth scheduling belong to the datapath. |
| [milan-fpga FR-QOS-02](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/docs/reference/FR_NFR.md#L281) | excluded | None | Queue classification, shaping and bandwidth scheduling belong to the datapath. |
| [milan-fpga FR-QOS-03](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/docs/reference/FR_NFR.md#L282) | excluded | None | Queue classification, shaping and bandwidth scheduling belong to the datapath. |
| [milan-fpga FR-MGT-01](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/docs/reference/FR_NFR.md#L287) | excluded | None | Identify outputs, AEM names and factory reset belong to product management. |
| [milan-fpga FR-MGT-02](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/docs/reference/FR_NFR.md#L288) | excluded | None | Identify outputs, AEM names and factory reset belong to product management. |
| [milan-fpga NFR-PERF-01](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/docs/reference/FR_NFR.md#L297) | excluded | None | Line rate and media packet rate need a real datapath and transport. |
| [milan-fpga NFR-PERF-02](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/docs/reference/FR_NFR.md#L298) | excluded | None | Line rate and media packet rate need a real datapath and transport. |
| [milan-fpga NFR-LAT-01](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/docs/reference/FR_NFR.md#L299) | excluded | None | Capture-to-render latency belongs to the media implementation. |
| [milan-fpga NFR-LAT-02](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/docs/reference/FR_NFR.md#L300) | port obligation | [MFLATENCY-01](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/docs/REQUIREMENTS.md#mflatency-01) | Added the applicable ACMP timing duty. AECP response timing is outside the cores. |
| [milan-fpga NFR-DET-01](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/docs/reference/FR_NFR.md#L301) | excluded | None | Media determinism is a datapath property. |
| [milan-fpga NFR-TIME-01](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/docs/reference/FR_NFR.md#L306) | excluded | None | Time synchronization, media-clock accuracy and PHC adjustment are outside these cores. |
| [milan-fpga NFR-TIME-02](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/docs/reference/FR_NFR.md#L307) | excluded | None | Time synchronization, media-clock accuracy and PHC adjustment are outside these cores. |
| [milan-fpga NFR-TIME-03](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/docs/reference/FR_NFR.md#L308) | excluded | None | Time synchronization, media-clock accuracy and PHC adjustment are outside these cores. |
| [milan-fpga NFR-SCUP-01](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/docs/reference/FR_NFR.md#L313) | excluded | None | Product shape generation, audio scale and device resource budgets are outside this library. Fixed core capacities remain explicit. |
| [milan-fpga NFR-SCUP-02](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/docs/reference/FR_NFR.md#L314) | excluded | None | Product shape generation, audio scale and device resource budgets are outside this library. Fixed core capacities remain explicit. |
| [milan-fpga NFR-SCUP-03](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/docs/reference/FR_NFR.md#L315) | excluded | None | Product shape generation, audio scale and device resource budgets are outside this library. Fixed core capacities remain explicit. |
| [milan-fpga NFR-SCUP-04](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/docs/reference/FR_NFR.md#L316) | excluded | None | Product shape generation, audio scale and device resource budgets are outside this library. Fixed core capacities remain explicit. |
| [milan-fpga NFR-SCOUT-01](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/docs/reference/FR_NFR.md#L321) | excluded | None | Hardware ownership, register ABI, future replicated endpoints and resource scaling are product duties. |
| [milan-fpga NFR-SCOUT-02](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/docs/reference/FR_NFR.md#L322) | port obligation | [MFOWNER-01](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/docs/REQUIREMENTS.md#mfowner-01) | Ported one-owner dispatch. Excluded build-selectable hardware placement, mailbox filters, AECP, SRP internals, time and media ownership. |
| [milan-fpga NFR-SCOUT-03](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/docs/reference/FR_NFR.md#L323) | port obligation | [MFSERVICE-01](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/docs/REQUIREMENTS.md#mfservice-01) | Ported the per-action 10 ms figure and applicable hooks as measurable port obligations. Excluded platform bus and audio/gPTP timing proofs. |
| [milan-fpga NFR-SCOUT-04](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/docs/reference/FR_NFR.md#L324) | excluded | None | Hardware ownership, register ABI, future replicated endpoints and resource scaling are product duties. |
| [milan-fpga NFR-SCOUT-05](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/docs/reference/FR_NFR.md#L325) | excluded | None | Hardware ownership, register ABI, future replicated endpoints and resource scaling are product duties. |
| [milan-fpga NFR-SCOUT-06](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/docs/reference/FR_NFR.md#L326) | excluded | None | Hardware ownership, register ABI, future replicated endpoints and resource scaling are product duties. |
| [milan-fpga NFR-SCOUT-07](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/docs/reference/FR_NFR.md#L327) | excluded | None | Hardware ownership, register ABI, future replicated endpoints and resource scaling are product duties. |
| [milan-fpga NFR-SCOUT-08](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/docs/reference/FR_NFR.md#L328) | excluded | None | Excluded the platform mailbox filter and bus-adapter campaign, as proposed. The portable input contract does not implement that hardware. |
| [milan-fpga NFR-RES-01](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/docs/reference/FR_NFR.md#L464) | excluded | None | Device utilization and headroom need a hardware implementation. |
| [milan-fpga NFR-REL-01](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/docs/reference/FR_NFR.md#L465) | ported | [MFRECOVERY-01](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/docs/REQUIREMENTS.md#mfrecovery-01); [MFRECOVERY-02](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/docs/REQUIREMENTS.md#mfrecovery-02) | Split tested core recovery from event detection, complete counters and media recovery at the port. |
| [milan-fpga NFR-REL-02](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/docs/reference/FR_NFR.md#L466) | excluded | None | Whole-system liveness monitors and restart policy belong to the application. |
| [milan-fpga NFR-OBS-01](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/docs/reference/FR_NFR.md#L467) | excluded | None | CSR, MAC, gPTP and AVDECC counter exposure are outside this library. Core diagnostics remain documented. |
| [milan-fpga NFR-MAINT-01](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/docs/reference/FR_NFR.md#L468) | excluded | None | The shared hardware/software entity generator is outside this library. Caller data must satisfy the entity port contract. |
| [milan-fpga NFR-PORT-01](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/docs/reference/FR_NFR.md#L469) | ported | [MFBUILD-01](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/docs/REQUIREMENTS.md#mfbuild-01) | Extended bare-metal portability to mandatory Linux and RV32 builds under the assignment. |
| [milan-fpga NFR-SEC-01](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/docs/reference/FR_NFR.md#L470) | excluded | None | AEM authentication and advertisement policy belong to the entity configuration and AECP owner. |
| [milan-fpga REQ-CSR-01](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/REQUIREMENTS.md#L128) | excluded | None | Register maps, interrupts and clock-domain crossings are product hardware contracts. |
| [milan-fpga REQ-CSR-02](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/REQUIREMENTS.md#L132) | excluded | None | Register maps, interrupts and clock-domain crossings are product hardware contracts. |
| [milan-fpga REQ-CSR-03](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/REQUIREMENTS.md#L135) | excluded | None | Register maps, interrupts and clock-domain crossings are product hardware contracts. |
| [milan-fpga REQ-CSR-04](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/REQUIREMENTS.md#L138) | excluded | None | Register maps, interrupts and clock-domain crossings are product hardware contracts. |
| [milan-fpga REQ-CSR-05](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/REQUIREMENTS.md#L140) | excluded | None | Register maps, interrupts and clock-domain crossings are product hardware contracts. |
| [milan-fpga REQ-PTP-01](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/REQUIREMENTS.md#L146) | excluded | None | PHC, gPTP, timestamps and AVTP uncertainty are outside these cores. |
| [milan-fpga REQ-PTP-02](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/REQUIREMENTS.md#L148) | excluded | None | PHC, gPTP, timestamps and AVTP uncertainty are outside these cores. |
| [milan-fpga REQ-PTP-03](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/REQUIREMENTS.md#L150) | excluded | None | PHC, gPTP, timestamps and AVTP uncertainty are outside these cores. |
| [milan-fpga REQ-PTP-04](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/REQUIREMENTS.md#L152) | excluded | None | PHC, gPTP, timestamps and AVTP uncertainty are outside these cores. |
| [milan-fpga REQ-PTP-05](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/REQUIREMENTS.md#L154) | excluded | None | PHC, gPTP, timestamps and AVTP uncertainty are outside these cores. |
| [milan-fpga REQ-PTP-06](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/REQUIREMENTS.md#L156) | excluded | None | PHC, gPTP, timestamps and AVTP uncertainty are outside these cores. |
| [milan-fpga REQ-PTP-07](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/REQUIREMENTS.md#L165) | excluded | None | PHC, gPTP, timestamps and AVTP uncertainty are outside these cores. |
| [milan-fpga REQ-PTP-08](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/REQUIREMENTS.md#L167) | excluded | None | PHC, gPTP, timestamps and AVTP uncertainty are outside these cores. |
| [milan-fpga REQ-PTP-09](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/REQUIREMENTS.md#L170) | excluded | None | PHC, gPTP, timestamps and AVTP uncertainty are outside these cores. |
| [milan-fpga REQ-CBS-01](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/REQUIREMENTS.md#L241) | excluded | None | Credit-based shaper hardware and its verification are outside these cores. |
| [milan-fpga REQ-CBS-02](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/REQUIREMENTS.md#L243) | excluded | None | Credit-based shaper hardware and its verification are outside these cores. |
| [milan-fpga REQ-CBS-03](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/REQUIREMENTS.md#L245) | excluded | None | Credit-based shaper hardware and its verification are outside these cores. |
| [milan-fpga REQ-CBS-04](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/REQUIREMENTS.md#L247) | excluded | None | Credit-based shaper hardware and its verification are outside these cores. |
| [milan-fpga REQ-CBS-05](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/REQUIREMENTS.md#L249) | excluded | None | Credit-based shaper hardware and its verification are outside these cores. |
| [milan-fpga REQ-CBS-06](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/REQUIREMENTS.md#L251) | excluded | None | Credit-based shaper hardware and its verification are outside these cores. |
| [milan-fpga REQ-CBS-07](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/REQUIREMENTS.md#L253) | excluded | None | Credit-based shaper hardware and its verification are outside these cores. |
| [milan-fpga REQ-CBS-08](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/REQUIREMENTS.md#L255) | excluded | None | Credit-based shaper hardware and its verification are outside these cores. |
| [milan-fpga REQ-CLS-01](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/REQUIREMENTS.md#L265) | excluded | None | Packet classifiers and egress queues belong to the transport. Core framing preconditions remain port duties. |
| [milan-fpga REQ-CLS-02](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/REQUIREMENTS.md#L267) | excluded | None | Packet classifiers and egress queues belong to the transport. Core framing preconditions remain port duties. |
| [milan-fpga REQ-CLS-03](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/REQUIREMENTS.md#L268) | excluded | None | Packet classifiers and egress queues belong to the transport. Core framing preconditions remain port duties. |
| [milan-fpga REQ-CLS-04](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/REQUIREMENTS.md#L270) | excluded | None | Packet classifiers and egress queues belong to the transport. Core framing preconditions remain port duties. |
| [milan-fpga REQ-CLS-05](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/REQUIREMENTS.md#L272) | excluded | None | Packet classifiers and egress queues belong to the transport. Core framing preconditions remain port duties. |
| [milan-fpga REQ-CLS-06](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/REQUIREMENTS.md#L274) | excluded | None | Packet classifiers and egress queues belong to the transport. Core framing preconditions remain port duties. |
| [milan-fpga REQ-CLS-07](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/REQUIREMENTS.md#L276) | excluded | None | Packet classifiers and egress queues belong to the transport. Core framing preconditions remain port duties. |
| [milan-fpga REQ-CLS-08](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/REQUIREMENTS.md#L278) | excluded | None | Packet classifiers and egress queues belong to the transport. Core framing preconditions remain port duties. |
| [milan-fpga REQ-CLS-09](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/REQUIREMENTS.md#L280) | excluded | None | Packet classifiers and egress queues belong to the transport. Core framing preconditions remain port duties. |
| [milan-fpga REQ-CLS-10](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/REQUIREMENTS.md#L282) | excluded | None | Packet classifiers and egress queues belong to the transport. Core framing preconditions remain port duties. |
| [milan-fpga REQ-MAC-01](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/REQUIREMENTS.md#L288) | excluded | None | MAC, PHY, MDIO, interrupts and hardware statistics belong to the transport. |
| [milan-fpga REQ-MAC-02](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/REQUIREMENTS.md#L290) | excluded | None | MAC, PHY, MDIO, interrupts and hardware statistics belong to the transport. |
| [milan-fpga REQ-MAC-03](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/REQUIREMENTS.md#L292) | excluded | None | MAC, PHY, MDIO, interrupts and hardware statistics belong to the transport. |
| [milan-fpga REQ-MAC-04](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/REQUIREMENTS.md#L294) | excluded | None | MAC, PHY, MDIO, interrupts and hardware statistics belong to the transport. |
| [milan-fpga REQ-MAC-05](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/REQUIREMENTS.md#L297) | excluded | None | MAC, PHY, MDIO, interrupts and hardware statistics belong to the transport. |
| [milan-fpga REQ-MAC-06](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/REQUIREMENTS.md#L298) | excluded | None | MAC, PHY, MDIO, interrupts and hardware statistics belong to the transport. |
| [milan-fpga REQ-MAC-07](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/REQUIREMENTS.md#L300) | excluded | None | MAC, PHY, MDIO, interrupts and hardware statistics belong to the transport. |
| [milan-fpga REQ-MAC-08](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/REQUIREMENTS.md#L302) | excluded | None | MAC, PHY, MDIO, interrupts and hardware statistics belong to the transport. |
| [milan-fpga REQ-VER-01](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/REQUIREMENTS.md#L307) | excluded | None | Product RTL, image builders, board acceptance and release campaigns are outside portable-core verification. |
| [milan-fpga REQ-VER-02](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/REQUIREMENTS.md#L309) | excluded | None | Product RTL, image builders, board acceptance and release campaigns are outside portable-core verification. |
| [milan-fpga REQ-VER-03](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/REQUIREMENTS.md#L311) | excluded | None | Product RTL, image builders, board acceptance and release campaigns are outside portable-core verification. |
| [milan-fpga REQ-VER-04](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/REQUIREMENTS.md#L314) | excluded | None | Excluded the product-wide bare-metal-only and generated-platform gates. This library instead requires its own full gates on Linux and RV32. |
| [milan-fpga REQ-VER-05](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/REQUIREMENTS.md#L317) | excluded | None | Product RTL, image builders, board acceptance and release campaigns are outside portable-core verification. |
| [milan-fpga REQ-VER-06](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/REQUIREMENTS.md#L322) | excluded | None | Product RTL, image builders, board acceptance and release campaigns are outside portable-core verification. |
| [milan-fpga #665 memory](https://github.com/kebag-logic/milan-fpga/issues/665#issuecomment-5992455815) | ported | [MFMEMORY-01](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/docs/REQUIREMENTS.md#mfmemory-01) | Ported no heap, static state, portable C11 and no OS in the cores. No platform allocator is imported. |
| [milan-fpga #665 testing](https://github.com/kebag-logic/milan-fpga/issues/665#issuecomment-6008744385) | ported | [MFQUALITY-01](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/docs/REQUIREMENTS.md#mfquality-01) | Ported host GoogleTest/GMock, coverage and mutation requirements. Platform suites and upstream lwSRP tests stay with their owners. |

## Local verification and port obligations

| ID | Method | Reason and evidence |
|---|---|---|
| MFDISC-01 | test | [Traceability](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/docs/TRACEABILITY.md) names the tested behavior and its declarations. |
| MFDISC-02 | test | [Traceability](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/docs/TRACEABILITY.md) names the tested behavior and its declarations. |
| MFDISC-03 | test | [Traceability](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/docs/TRACEABILITY.md) names the tested behavior and its declarations. |
| MFDISC-04 | test | [Traceability](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/docs/TRACEABILITY.md) names the tested behavior and its declarations. |
| MFENTITY-01 | port obligation | The library encodes caller data. It has no descriptor store or gPTP implementation. [Entity configuration contract](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/docs/PORTING.md#entity-configuration) |
| MFENTITY-02 | port obligation | MAC derivation and restart stability are source product policy. IEEE permits MAC derivation; the core accepts a caller-supplied identifier. [Entity identity contract](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/docs/PORTING.md#entity-configuration) |
| MFCONN-01 | test | [Traceability](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/docs/TRACEABILITY.md) names the tested behavior and its declarations. |
| MFCONN-02 | port obligation | This library owns no media queues or shaper. Their programming depends on the selected transport. [Reservation and datapath contract](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/docs/PORTING.md#reservation-and-datapath) |
| MFCONN-03 | test | [Traceability](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/docs/TRACEABILITY.md) names the tested behavior and its declarations. |
| MFCONN-04 | port obligation | The record codec and rollback are tested. Durable writes, power loss and boot ordering need an external store. [Persistence contract](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/docs/PORTING.md#persistence-and-startup); [Binding tests](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_acmp.cpp) |
| MFMAAP-01 | test | [Traceability](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/docs/TRACEABILITY.md) names the tested behavior and its declarations. |
| MFMAAP-02 | port obligation | The range callback reports allocation. The application assigns addresses to streams and owns media use. [Reservation and datapath contract](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/docs/PORTING.md#reservation-and-datapath) |
| MFSRP-01 | test | [Traceability](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/docs/TRACEABILITY.md) names the tested behavior and its declarations. |
| MFSRP-02 | port obligation | MSRP and bandwidth admission are outside the three cores. The selected SRP component is lwSRP. [Reservation contract](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/docs/PORTING.md#reservation-and-datapath); [SRP component](https://github.com/kebag-logic/lwSRP) |
| MFSRP-03 | port obligation | ACMP exposes the VLAN in stream parameters. MVRP runs in lwSRP, outside this library. [Reservation contract](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/docs/PORTING.md#reservation-and-datapath) |
| MFSRP-04 | port obligation | Added beside the proposed SRP rows because reservation enforcement shares the datapath boundary. No shaper is supplied. [Reservation contract](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/docs/PORTING.md#reservation-and-datapath) |
| MFOWNER-01 | port obligation | Single ownership is portable. Placement switches and platform ingress hardware are excluded parts of the source row. [Dispatch contract](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/docs/PORTING.md#ownership-and-dispatch) |
| MFSERVICE-01 | port obligation | Ten milliseconds is project policy, proposed in the source register. Execution time depends on the scheduler and transport; no target timing is claimed. [Service measurement contract](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/docs/PORTING.md#service-measurement) |
| MFLATENCY-01 | port obligation | Added because the source latency row also applies to ACMP. The core timer tests do not establish a wire deadline. AECP timing is excluded. [Service measurement contract](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/docs/PORTING.md#service-measurement) |
| MFRECOVERY-01 | test | [Traceability](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/docs/TRACEABILITY.md) names the tested behavior and its declarations. |
| MFRECOVERY-02 | port obligation | The cores expose selected counters, not a complete recovery event ledger. Media recovery and complete event counting belong to the application. [Recovery accounting contract](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/docs/PORTING.md#recovery-accounting) |
| MFBUILD-01 | verified by inspection | This is a build property. Hosted dependency audits and Debug and Release RV32 links inspect every core object. [Hosted boundary audit](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/scripts/check_boundary.py); [RV32 link and execution gate](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/scripts/baremetal.py); [Both target verification](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/docs/VERIFICATION.md) |
| MFMEMORY-01 | verified by inspection | Static arrays are the pools. Source and symbol audits check the cores on both targets; test framework allocation is outside the core contract. [C subset](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/docs/CODING_STANDARD.md); [Hosted boundary audit](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/scripts/check_boundary.py); [RV32 audit](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/scripts/baremetal.py) |
| MFQUALITY-01 | verified by inspection | Coverage and mutation run on Linux for the shared core source. RV32 runs the linked smoke suite. No RV32 coverage denominator is claimed. [Verification gates](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/docs/VERIFICATION.md); [Coverage exclusions](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/docs/COVERAGE.md); [Test defects](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/docs/TESTS.md) |

## Tests and defects

| Test | Defect caught | Requirements |
|---|---|---|
| [AcmpCore.A0EverySinkStartsUnboundAndNothingIsCalled](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_acmp.cpp#L206) | acmp-init-reads-the-seed | ACMP-01 |
| [AcmpCore.A0InitRefusesWhatTheStaticSizesCannotHold](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_acmp.cpp#L167) | acmp-init-no-interface; acmp-init-too-many-sinks; acmp-init-too-many-sources; acmp-init-sink-interface; acmp-init-source-interface | ACMP-01 |
| [AcmpCore.A10NoResponseSendsTheDuplicateThenGivesUp](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_acmp.cpp#L608) | acmp-duplicate-takes-a-new-sequence-id; acmp-second-timeout-keeps-status-0; acmp-no-duplicate | ACMP-04 |
| [AcmpCore.A11RetryWaitsForTheTalkerOrDelays](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_acmp.cpp#L629) | acmp-retry-ignores-discovery; acmp-retry-zeroes-the-status | ACMP-04 |
| [AcmpCore.A12DelaySendsANewProbe](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_acmp.cpp#L649) | acmp-sequence-id-never-advances; acmp-delay-resends-the-old-probe | ACMP-04 |
| [AcmpCore.A13NoTalkerAttributeReprobes](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_acmp.cpp#L664) | acmp-no-tk-keeps-srp; acmp-reprobe-ignores-discovery | ACMP-04 |
| [AcmpCore.A14RegisteredSettlesTheReservation](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_acmp.cpp#L686) | acmp-registered-anywhere; acmp-registered-keeps-no-tk | ACMP-04, MFSRP-01 |
| [AcmpCore.A15UnregisteredReprobes](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_acmp.cpp#L711) | acmp-reprobe-ignores-discovery; acmp-unregistered-anywhere; acmp-unregistered-keeps-srp | ACMP-04, MFSRP-01, MFRECOVERY-01 |
| [AcmpCore.A16OneCounterForEveryNewProbe](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_acmp.cpp#L775) | acmp-sequence-id-never-advances; acmp-sequence-id-per-sink | ACMP-04 |
| [AcmpCore.A17EachInterfaceTimerHoldsItsEarliestDeadline](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_acmp.cpp#L789) | acmp-timer-at-the-latest-deadline; acmp-timer-port-called-every-time; acmp-timer-never-stopped; acmp-expiry-takes-every-interface; acmp-expiry-not-consumed | ACMP-05 |
| [AcmpCore.A18AZeroDelayProbesInTheSameExpiry](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_acmp.cpp#L817) | acmp-zero-delay-waits; acmp-delay-up-to-4s | ACMP-05 |
| [AcmpCore.A18TheSeedIsTakenAtTheFirstDraw](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_acmp.cpp#L841) | acmp-seed-at-every-draw; acmp-rng-left-at-0 | ACMP-05 |
| [AcmpCore.A19AFullQueueDropsTheCommandBeforeItActs](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_acmp.cpp#L1055) | acmp-full-queue-acts | ACMP-09 |
| [AcmpCore.A19AProbeWithoutRoomIsLostAndRecovered](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_acmp.cpp#L1072) | acmp-lost-probe-uncounted; acmp-lost-probe-held | ACMP-09 |
| [AcmpCore.A19AResponseWithoutRoomIsOwedAndItsChangeWaits](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_acmp.cpp#L1017) | acmp-poll-drains-everything; acmp-change-not-held-for-its-response | ACMP-09 |
| [AcmpCore.A19NothingPassesAnOwedFrame](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_acmp.cpp#L1041) | acmp-response-passes-an-owed-frame; acmp-poll-newest-first | ACMP-09 |
| [AcmpCore.A19TwoOwedResponsesForOneSinkReleaseTogether](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_acmp.cpp#L1092) | acmp-first-owed-releases-every-change | ACMP-09 |
| [AcmpCore.A1BindFromUnboundRespondsThenProbes](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_acmp.cpp#L223) | acmp-header-no-resp-2s; acmp-header-cdl-84; acmp-bind-count-0; acmp-probe-without-fast-connect; acmp-probe-before-response; acmp-no-resp-2s; acmp-bind-starts-no-discovery; acmp-bind-change-before-response; acmp-nothing-persisted; acmp-streaming-wait-ignored; acmp-frames-to-the-own-mac; acmp-header-version-1 | ACMP-03, ACMP-02, MFCONN-01 |
| [AcmpCore.A1BindWithoutStreamingWaitBindsStarted](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_acmp.cpp#L273) | acmp-new-bind-never-started; acmp-bind-response-always-streaming-wait | ACMP-03, ACMP-02 |
| [AcmpCore.A20DisconnectGetTxStateAndGetTxConnection](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_acmp.cpp#L912) | acmp-disconnect-always-succeeds; acmp-get-tx-state-echoes-the-listener; acmp-get-tx-state-registering-failed-0; acmp-get-tx-state-unheld-mac; acmp-get-tx-connection-supported | ACMP-08, MFCONN-01 |
| [AcmpCore.A20ProbeTxIsAnsweredFromTheSource](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_acmp.cpp#L859) | acmp-probe-tx-reports-asking-failed; acmp-probe-tx-echoes-every-flag; acmp-probe-tx-any-interface; acmp-probe-tx-no-destination-mac-check; acmp-unknown-source-answered | ACMP-08, MFCONN-01 |
| [AcmpCore.A21MalformedFramesAreCounted](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_acmp.cpp#L997) | acmp-short-pdu-read; acmp-longer-pdu-refused | ACMP-02 |
| [AcmpCore.A21MessagesNotForThisEntityAreIgnored](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_acmp.cpp#L976) | acmp-every-listener-is-this-one; acmp-every-talker-is-this-one | ACMP-02 |
| [AcmpCore.A22AvailableDiscoversWhenTheGrandmasterMatches](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_acmp.cpp#L1110) | acmp-header-valid-time-in-seconds; acmp-discovery-reads-no-grandmaster; acmp-discovery-reads-no-domain; acmp-valid-time-in-seconds | ACMP-06 |
| [AcmpCore.A22DepartingAndAging](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_acmp.cpp#L1213) | acmp-departing-taken-undiscovered; acmp-departing-interface-unchecked; acmp-departing-keeps-aging; acmp-no-aging | ACMP-06, MFCONN-03, MFRECOVERY-01 |
| [AcmpCore.A22DiscoveredStartsTheProbeFromPrbWAvail](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_acmp.cpp#L1141) | acmp-discovered-probing-stays-passive; acmp-grandmaster-read-twice | ACMP-06 |
| [AcmpCore.A22DiscoveredStateCells](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_acmp.cpp#L1156) | acmp-discovered-interface-unchecked; acmp-restart-on-a-smaller-index-only; acmp-restart-raises-no-discovered; acmp-restart-mismatch-keeps-aging; acmp-refresh-notes-no-index; acmp-grandmaster-sampled-for-the-refresh | ACMP-06, MFCONN-03, MFRECOVERY-01 |
| [AcmpCore.A22OnlyBoundSinksOfThatTalkerOnThatInterface](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_acmp.cpp#L1240) | acmp-discovery-on-every-interface; acmp-discovery-on-unbound-sinks; acmp-grandmaster-sampled-per-sink; acmp-discovery-takes-the-first-sink | ACMP-06 |
| [AcmpCore.A22OtherAdpFramesAreIgnored](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_acmp.cpp#L1263) | acmp-adp-short-frame-taken; acmp-adp-ethertype-unchecked; acmp-adp-subtype-unchecked; acmp-adp-discover-taken | ACMP-06 |
| [AcmpCore.A23EveryEntryRefusesACallFromInsideAPort](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_acmp.cpp#L1283) | acmp-reentry-unguarded; acmp-reentry-untrapped; acmp-send-port-unflagged; acmp-owed-probe-timer-runs; acmp-open-unguarded | PORT-01 |
| [AcmpCore.A23EveryPortIsGuarded](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_acmp.cpp#L1319) | acmp-reentry-unguarded; acmp-timer-port-unflagged; acmp-gptp-port-unflagged; acmp-clock-port-unflagged; acmp-seed-port-unflagged; acmp-lock-port-unflagged; acmp-source-port-unflagged; acmp-srp-port-unflagged; acmp-persist-port-unflagged; acmp-changed-port-unflagged; acmp-bind-reads-the-clock-twice; acmp-admit-port-unflagged | PORT-01 |
| [AcmpCore.A24ARestoredBindingFastConnects](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_acmp.cpp#L1344) | acmp-restore-lands-in-prb-w-resp; acmp-restore-starts-no-discovery; acmp-record-unique-id-little-endian; acmp-restore-unique-id-little-endian | ACMP-07, MFCONN-03 |
| [AcmpCore.A24StartedIsSavedAndReported](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_acmp.cpp#L1393) | acmp-started-not-saved | ACMP-07 |
| [AcmpCore.A24TheRecordIsTheProcessorsPayloadOneFlagAtATime](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_acmp.cpp#L1424) | acmp-record-flags-swapped; acmp-record-flag-defines-swapped; acmp-record-valid-bit-moved | ACMP-07 |
| [AcmpCore.A24UnboundRecordsRefusalsAndRollback](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_acmp.cpp#L1364) | acmp-roll-back-keeps-the-bindings; acmp-unbound-record-not-zero; acmp-longer-record-applied | ACMP-07 |
| [AcmpCore.A25OnlyTable522ItemsAreReported](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_acmp.cpp#L1458) | acmp-second-timeout-keeps-status-0; acmp-discovery-notifies; acmp-status-not-notified | ACMP-02 |
| [AcmpCore.A26AnotherAvtpVersionIsDiscardedBeforeItIsRead](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_acmp.cpp#L1485) | acmp-version-unchecked; acmp-adp-version-unchecked; acmp-version-bits-misread | ACMP-02 |
| [AcmpCore.A27AProbeOwedPastAnUnbindARebindOrASuccessStartsNothing](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_acmp.cpp#L1617) | acmp-owed-probe-sequence-unchecked; acmp-stop-keeps-the-hold | ACMP-05 |
| [AcmpCore.A27AStalledDuplicateGetsItsWholeInterval](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_acmp.cpp#L1573) | acmp-owed-probe-timer-runs; acmp-owed-probe-never-starts | ACMP-05 |
| [AcmpCore.A27AnOwedProbeStartsItsTimerWhenItLeaves](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_acmp.cpp#L1536) | acmp-owed-probe-timer-runs; acmp-owed-probe-never-starts; acmp-owed-probe-no-resp-2s; acmp-owed-probe-unnamed; acmp-owed-probe-names-the-next-sink; acmp-held-timer-expires; acmp-held-timer-armed | ACMP-05 |
| [AcmpCore.A28EveryTimerExpiresAtItsDeadlineAcrossTheWrap](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_acmp.cpp#L1671) | acmp-due-unsigned; acmp-no-adp-due-unsigned; acmp-no-resp-deadline-saturates; acmp-retry-deadline-saturates; acmp-no-tk-deadline-saturates; acmp-delay-deadline-saturates; acmp-no-adp-deadline-saturates | ACMP-05 |
| [AcmpCore.A28TheEarliestDeadlineIsChosenAcrossTheWrap](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_acmp.cpp#L1736) | acmp-due-unsigned; acmp-earliest-unsigned | ACMP-05 |
| [AcmpCore.A29RestoredBindingsAreAdmittedWhenTheTransportOpens](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_acmp.cpp#L1796) | acmp-restore-announced; acmp-reset-forgets-the-admitted; acmp-open-does-nothing | ACMP-07, MFCONN-03 |
| [AcmpCore.A29TheAdmitPortFollowsEachSinksBoundTalker](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_acmp.cpp#L1762) | acmp-admit-never-called; acmp-admit-on-every-entry; acmp-admit-ignores-another-talker; acmp-admit-on-interface-0 | ACMP-06 |
| [AcmpCore.A2GetRxStateInEveryState](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_acmp.cpp#L282) | acmp-getrx-count-unbound; acmp-getrx-no-fast-connect | ACMP-03, ACMP-02, MFCONN-01 |
| [AcmpCore.A2GetRxStateReportsStreamingWaitAndRegisteringFailed](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_acmp.cpp#L315) | acmp-header-registering-failed-bit; acmp-sw-read-from-fast-connect; acmp-getrx-no-registering-failed; acmp-registered-kind-dropped; acmp-view-without-registering-failed | ACMP-03, ACMP-02 |
| [AcmpCore.A2UnknownSinkIsAnsweredListenerUnknownId](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_acmp.cpp#L327) | acmp-header-listener-unknown-is-2; acmp-unknown-sink-silent | ACMP-03, ACMP-02 |
| [AcmpCore.A30ADuplicateTakenAtOnceRunsFromTheClockAfterItsSend](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_acmp.cpp#L1866) | acmp-probe-timer-before-its-send; acmp-taken-probe-timer-from-the-entry-clock | ACMP-05 |
| [AcmpCore.A30AProbeTakenAtOnceRunsFromTheClockAfterItsSend](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_acmp.cpp#L1830) | acmp-probe-timer-before-its-send | ACMP-05 |
| [AcmpCore.A30ATimerDueAfterAnEarlierSinksSendIsTakenInTheSameExpiry](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_acmp.cpp#L1899) | acmp-expiry-due-at-its-first-read | ACMP-05 |
| [AcmpCore.A3UnbindInEveryState](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_acmp.cpp#L350) | acmp-unbind-not-persisted; acmp-unbind-echoes-the-talker; acmp-unbind-keeps-srp; acmp-unbind-srp-after-response; acmp-unbind-keeps-discovery; acmp-unbind-change-before-response | ACMP-03, ACMP-02, MFCONN-01, MFSRP-01 |
| [AcmpCore.A4LockedByAnotherControllerRefusesBindAndUnbind](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_acmp.cpp#L386) | acmp-not-authorized-is-13; acmp-lock-ignored | ACMP-03, ACMP-02 |
| [AcmpCore.A4TheLockingControllerPassesAndGetRxStateIsNotLocked](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_acmp.cpp#L418) | acmp-lock-refuses-the-holder; acmp-get-rx-state-locked | ACMP-03, ACMP-02 |
| [AcmpCore.A5RebindTheSameSourceUpdatesAndExits](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_acmp.cpp#L431) | acmp-rebind-same-reprobes; acmp-rebind-same-keeps-the-controller | ACMP-03, ACMP-02 |
| [AcmpCore.A6BindAnotherSourceRestartsTheSink](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_acmp.cpp#L458) | acmp-rebind-not-persisted; acmp-bind-new-keeps-srp | ACMP-03, ACMP-02 |
| [AcmpCore.A6TheSameTalkerAnotherSourceIsANewBinding](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_acmp.cpp#L488) | acmp-bind-same-talker-is-the-same-source | ACMP-03, ACMP-02 |
| [AcmpCore.A7EachGuardTermIsChecked](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_acmp.cpp#L512) | acmp-guard-controller-dropped; acmp-guard-talker-dropped; acmp-guard-unique-id-dropped; acmp-guard-sequence-id-dropped | ACMP-04 |
| [AcmpCore.A7ResponsesKeyOnTheListenerUniqueId](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_acmp.cpp#L500) | acmp-response-keyed-on-the-source | ACMP-04 |
| [AcmpCore.A7ResponsesOutsideProbingAreIgnored](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_acmp.cpp#L545) | acmp-responses-taken-outside-probing | ACMP-04 |
| [AcmpCore.A7TheGuardReadsTheSentProbeNotTheBinding](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_acmp.cpp#L534) | acmp-guard-reads-the-binding | ACMP-04 |
| [AcmpCore.A8SuccessSettles](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_acmp.cpp#L570) | acmp-header-no-tk-5s; acmp-vlan-masked; acmp-no-tk-1s; acmp-settle-starts-no-srp; acmp-settle-swaps-stream-fields | ACMP-04, MFSRP-01 |
| [AcmpCore.A9FailureWaitsForTheRetry](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_acmp.cpp#L593) | acmp-header-retry-2s; acmp-failure-status-dropped; acmp-failure-retries-at-200ms | ACMP-04 |
| [AcmpCore.CommandPortBudgets](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_acmp.cpp#L1939) | acmp-get-rx-state-reads-the-clock; acmp-probe-response-reads-the-clock-twice; acmp-unbind-reads-the-clock; acmp-talker-reads-the-clock | PORT-01 |
| [AcmpCore.DepartingStopsEveryProbingTimer](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_acmp.cpp#L1921) | acmp-probing-status-not-notified | ACMP-06 |
| [AcmpCore.DiscoveryPortBudgets](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_acmp.cpp#L1977) | acmp-available-reads-the-clock-twice; acmp-departing-samples-the-grandmaster; acmp-aging-samples-the-grandmaster | PORT-01 |
| [AcmpCore.KindChangesOnlyTheSettledView](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_acmp.cpp#L744) | acmp-kind-lost; acmp-kind-any-state | ACMP-04, MFSRP-01 |
| [AcmpCore.TimerPortBudgets](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_acmp.cpp#L1958) | acmp-expiry-reads-the-clock-twice; acmp-second-no-resp-samples-the-grandmaster; acmp-retry-samples-the-grandmaster; acmp-delay-reads-the-clock-again; acmp-no-tk-samples-the-grandmaster | PORT-01 |
| [AdpCore.A0toA2Schedule](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_adp.cpp#L535) | gm-change-ignored; advertise-expiry-skips-delay; advertise-period-wrong; link-up-draws-startup-kind; frame-misses-config-index | ADP-02, PORT-01, MFDISC-01, MFDISC-04, MFRECOVERY-01 |
| [AdpCore.A10toA14DepartingIndex](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_adp.cpp#L551) | departing-sends-zero | ADP-03, ADP-02, MFDISC-01, MFDISC-03 |
| [AdpCore.A15OwedDepartingAcrossARestart](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_adp.cpp#L555) | available-replaces-owed-departing | ADP-03, ADP-02, MFDISC-03 |
| [AdpCore.A16SecondShutdownQueuesItsOwn](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_adp.cpp#L559) | second-departing-dropped; second-shutdown-overwrites-index | ADP-03, ADP-02 |
| [AdpCore.A17RoomBackBeforeAPoll](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_adp.cpp#L563) | available-passes-owed-departing | ADP-03, ADP-02 |
| [AdpCore.A18LinkLossKeepsTheOwedDeparting](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_adp.cpp#L567) | link-loss-drops-owed-departing | ADP-03, ADP-02, MFDISC-03 |
| [AdpCore.A19IgnoredInputsKeepTheOwedAvailable](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_adp.cpp#L571) | gm-change-drops-owed-available; discover-drops-owed-available; stray-expiry-drops-owed-available | ADP-03, ADP-02 |
| [AdpCore.A20LinkLossDropsTheOwedAvailable](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_adp.cpp#L575) | link-loss-keeps-owed-available | ADP-03, ADP-02, MFDISC-03 |
| [AdpCore.A21DepartingCapacity](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_adp.cpp#L579) | departing-queue-unbounded; coalesced-departing-uncounted; coalesce-drops-queued-departing; coalesce-overwrites-oldest-index | ADP-03, ADP-02 |
| [AdpCore.A22GeneratorNeverStuckAtZero](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_adp.cpp#L583) | seed-left-at-zero | ADP-02, PORT-01 |
| [AdpCore.A23RepeatedEnableOrDisableChangesNothing](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_adp.cpp#L585) | enable-not-idempotent | ADP-02, PORT-01 |
| [AdpCore.A24OtherEtherTypeOrSubtypeDiscarded](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_adp.cpp#L587) | other-subtype-accepted | ADP-01, ADP-02 |
| [AdpCore.A3toA5DiscoverAndDiscard](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_adp.cpp#L539) | own-discover-discarded; down-answers-discover; foreign-discover-answered | ADP-01, ADP-02, MFDISC-02 |
| [AdpCore.A6toA8DeferredSends](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_adp.cpp#L543) | departing-keeps-index; delay-ignores-link-down; shutdown-in-down-departs | ADP-03, ADP-02 |
| [AdpCore.A9DrawKinds](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_adp.cpp#L547) | draw-kinds-merged | ADP-02, PORT-01 |
| [AdpCore.AdvertisementFieldsMatchCaller](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_adp.cpp#L628) | adp-config-entity-id; adp-config-model-id; adp-config-entity-capabilities; adp-config-talker-count; adp-config-talker-capabilities; adp-config-listener-count; adp-config-listener-capabilities; adp-config-grandmaster; adp-config-domain; adp-config-identify-index; adp-config-interface-index | ADP-01, MFDISC-04 |
| [AdpCore.EntityFieldsUseIndependentCounts](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_adp.cpp#L612) | frame-sources-from-sinks | ADP-01, ADP-02, MFDISC-04 |
| [AdpCore.LinkLevelsAndDisabledInputs](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_adp.cpp#L590) | link-down-departs | ADP-02, PORT-01, MFDISC-03, MFRECOVERY-01 |
| [AdpCore.MockedPortOrder](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_adp.cpp#L671) | advertise-period-wrong | ADP-02, PORT-01 |
| [AdpInputControl.InheritedDiscoveryAcceptance](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_adp.cpp#L702) | own-discover-discarded | ADP-01, ADP-02 |
| [AdpPortEntry.RefusesBeforeTouchingState](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_adp_reentry.cpp#L188) | reentry-not-ignored | PORT-01 |
| [AdpReentry.AdvertiseInlineExpiry](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_adp_reentry.cpp#L132) | reentry-guard-removed; reentry-uncounted | PORT-01 |
| [AdpReentry.DelayInlineExpiryOnGmChange](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_adp_reentry.cpp#L160) | reentry-guard-removed | PORT-01 |
| [ExamplePort.DefersExpiryAndRetainsBlockedOutput](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_port.cpp#L8) | departing-keeps-index | PORT-01 |
| [MaapCell.TableB7](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_maap.cpp#L139) | maap-table-b7-0; maap-table-b7-1; maap-table-b7-2; maap-table-b7-3; maap-table-b7-4; maap-table-b7-5; maap-table-b7-6; maap-table-b7-7; maap-table-b7-8; maap-table-b7-9; maap-table-b7-10; maap-table-b7-11; maap-table-b7-12; maap-table-b7-13; maap-table-b7-14; maap-table-b7-15; maap-table-b7-16; maap-table-b7-17; maap-generic-initial-handles-conflict; maap-generic-probe-state-defends; maap-generic-probe-defend-uses-priority | MAAP-03, MFMAAP-01 |
| [MaapCore.BeginBeforePortOperationalRetainsRange](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_maap.cpp#L318) | maap-begin-down-forgets-range | MAAP-02 |
| [MaapCore.ConstantsStrictTimersAndSeed](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_maap.cpp#L117) | maap-constant-probe_base; maap-constant-probe_variation; maap-constant-announce_base; maap-constant-announce_variation; maap-seed-clock-ignored; maap-zero-seed-sticks | MAAP-02 |
| [MaapCore.DefendEchoAndIntersection](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_maap.cpp#L219) | maap-defend-multicast; maap-defend-echo-own-range; maap-intersection-too-long | MAAP-03, MFMAAP-01 |
| [MaapCore.DisjointAdjacentZeroAndDefendRange](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_maap.cpp#L232) | maap-adjacent-overlaps; maap-zero-count-conflicts; maap-defend-checks-request | MAAP-03 |
| [MaapCore.InitAndPreferredRangeBounds](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_maap.cpp#L271) | maap-range-end-off-by-one | MAAP-02 |
| [MaapCore.InitialAndThreeRetransmissions](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_maap.cpp#L94) | maap-initial-send-absent; maap-retransmit-count; maap-probe-count-not-decremented; maap-wire-version; maap-wire-length; maap-wire-source; maap-wire-padding; maap-allocation-seam-disconnected | MAAP-02, MFMAAP-01 |
| [MaapCore.LinkBounceDrawsAfterSuppliedRange](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_maap.cpp#L338) | r2-saved-range-never-consumed | MAAP-02, MFRECOVERY-01 |
| [MaapCore.MalformedAndVersionCompatibility](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_maap.cpp#L244) | maap-malformed-ethertype; maap-malformed-subtype; maap-malformed-version; maap-malformed-reserved-zero; maap-malformed-reserved-high; maap-malformed-cdl-short; maap-malformed-cdl-truncated; maap-malformed-cdl-current; maap-malformed-source-zero; maap-malformed-source-group; maap-malformed-destination; maap-malformed-own-probe; maap-valid-minimum-refused; maap-future-version-refused | MAAP-01 |
| [MaapCore.PriorityAfterTiedOctets](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_maap.cpp#L179) | maap-reverse-five-octets; maap-compare-mac-lsb-only | MAAP-03 |
| [MaapCore.QueueBoundAndWithdrawal](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_maap.cpp#L380) | maap-overflow-uncounted; maap-poll-unbounded; maap-release-leaves-output | MAAP-04 |
| [MaapCore.ReentrantPortsAreCountedAndIgnored](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_maap.cpp#L394) | maap-reentry-not-counted | PORT-01 |
| [MaapCore.ReleaseLossAndRetry](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_maap.cpp#L294) | maap-down-start-keeps-owner; maap-port-up-keeps-claim; maap-release-keeps-enable | MAAP-04, MFMAAP-01, MFRECOVERY-01 |
| [MaapCore.RestartDrawsNewRange](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_maap.cpp#L196) | maap-restart-reuses-range | MAAP-02 |
| [MaapCore.ReverseOctetPriority](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_maap.cpp#L170) | maap-numeric-mac-priority; maap-generic-equal-mac-wins | MAAP-03 |
| [MaapCore.StalledOutputRetainsOrderAndOriginalExpiry](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_maap.cpp#L361) | maap-expiry-forgotten-on-stall; maap-allocation-before-commit; maap-probe-announce-reordered; maap-stall-unqueued | MAAP-04 |
| [MaapCore.UniformDrawRejectsIncompleteBucket](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_maap.cpp#L209) | maap-biased-random-bucket | MAAP-02 |
| [MaapDebug.SynchronousExpiryAsserts](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/tests/test_maap_debug.cpp#L9) | maap-debug-no-assert | PORT-01 |

The traceability self-test also catches 24 planted metadata defects and a tested import whose last test is removed.

## Gates

The main contract runs source gates and complete campaigns on Linux. It runs the freestanding link and focused smoke suite on RV32.
The RV32 column below states that distinction. It does not claim hosted instrumentation ran on the bare-metal target.
Every gate command was run directly, with its return code captured separately. No gate was piped.
The validation driver stopped its build phase after the privacy failure. The same remaining commands ran in a separate concurrent campaign with the same environment and options.

| Gate | Linux | Bare-metal RV32 applicability | Evidence |
|---|---|---|---|
| boundary | rc 0 | Shared source/metadata gate | [Log]($VALIDATION_STORAGE/tsn14-a571/resume/step2/linux/boundary.log) |
| needles | rc 0 | Shared source/metadata gate | [Log]($VALIDATION_STORAGE/tsn14-a571/resume/step2/linux/needles.log) |
| assertion-templates | rc 0 | Shared source/metadata gate | [Log]($VALIDATION_STORAGE/tsn14-a571/resume/step2/linux/assertion-templates.log) |
| dependencies | rc 0 | Shared source/metadata gate | [Log]($VALIDATION_STORAGE/tsn14-a571/resume/step2/linux/dependencies.log) |
| comments | rc 0 | Shared source/metadata gate | [Log]($VALIDATION_STORAGE/tsn14-a571/resume/step2/linux/comments.log) |
| conditionals | rc 0 | Shared source/metadata gate | [Log]($VALIDATION_STORAGE/tsn14-a571/resume/step2/linux/conditionals.log) |
| port-contracts | rc 0 | Shared source/metadata gate | [Log]($VALIDATION_STORAGE/tsn14-a571/resume/step2/linux/port-contracts.log) |
| registration-controls | rc 0 | Shared source/metadata gate | [Log]($VALIDATION_STORAGE/tsn14-a571/resume/step2/linux/registration-controls.log) |
| license | rc 0 | Shared source/metadata gate | [Log]($VALIDATION_STORAGE/tsn14-a571/resume/step2/linux/license.log) |
| traceability | rc 0 | Shared source/metadata gate | [Log]($VALIDATION_STORAGE/tsn14-a571/resume/step2/linux/traceability.log) |
| test-inventory | rc 0 | Shared source/metadata gate | [Log]($VALIDATION_STORAGE/tsn14-a571/resume/step2/linux/test-inventory.log) |
| coverage-controls | rc 0 | Shared source/metadata gate | [Log]($VALIDATION_STORAGE/tsn14-a571/resume/step2/linux/coverage-controls.log) |
| privacy | rc 1 | Inherited base defect; delivery authorized by the manager | [Post-commit log]($VALIDATION_STORAGE/tsn14-a571/resume/postcommit-privacy.log) |
| gcc-configure | rc 0 | Hosted campaign for shared cores; RV32 smoke below | [Log]($VALIDATION_STORAGE/tsn14-a571/resume/step2/linux/gcc-configure.log) |
| gcc-build | rc 0 | Hosted campaign for shared cores; RV32 smoke below | [Log]($VALIDATION_STORAGE/tsn14-a571/resume/step2/linux/gcc-build.log) |
| gcc-test | rc 0 | Hosted campaign for shared cores; RV32 smoke below | [Log]($VALIDATION_STORAGE/tsn14-a571/resume/step2/linux/gcc-test.log) |
| coverage | rc 0 | Hosted campaign for shared cores; RV32 smoke below | [Log]($VALIDATION_STORAGE/tsn14-a571/resume/step2/linux/coverage.log) |
| clang-sanitizers-configure | rc 0 | Hosted campaign for shared cores; RV32 smoke below | [Log]($VALIDATION_STORAGE/tsn14-a571/resume/step2/linux/clang-sanitizers-configure.log) |
| clang-sanitizers-build | rc 0 | Hosted campaign for shared cores; RV32 smoke below | [Log]($VALIDATION_STORAGE/tsn14-a571/resume/step2/linux/clang-sanitizers-build.log) |
| clang-sanitizers-test | rc 0 | Hosted campaign for shared cores; RV32 smoke below | [Log]($VALIDATION_STORAGE/tsn14-a571/resume/step2/linux/clang-sanitizers-test.log) |
| mutation | rc 0 | Hosted campaign for shared cores; RV32 smoke below | [Log]($VALIDATION_STORAGE/tsn14-a571/resume/step2/linux/mutation.log) |
| static-analysis | rc 0 | Hosted campaign for shared cores; RV32 smoke below | [Log]($VALIDATION_STORAGE/tsn14-a571/resume/step2/linux/static-analysis.log) |
| mutation-controls | rc 0 | Hosted campaign for shared cores; RV32 smoke below | [Log]($VALIDATION_STORAGE/tsn14-a571/resume/step2/linux/mutation-controls.log) |
| graphs | rc 0 | Shared documentation | [Log]($VALIDATION_STORAGE/tsn14-a571/resume/step2/linux/graphs.log) |
| rv32-debug | Hosted driver | rc 0; linked execution | [Log]($VALIDATION_STORAGE/tsn14-a571/resume/step2/rv32/results.json) |
| rv32-release | Hosted driver | rc 0; linked execution | [Log]($VALIDATION_STORAGE/tsn14-a571/resume/step2/rv32/results.json) |
| New commit identities | rc 0 | Shared commit metadata | [Log]($VALIDATION_STORAGE/tsn14-a571/resume/new-commit-identities.log) |

Results:

- Twelve preflight gates passed; privacy failed on the required base commit.
- GCC and Clang sanitizer builds each passed all seven test binaries. Registration contains 370 instances from 109 declarations.
- The full mutation campaign caught all 322 plants, with zero escaped plants and zero errors. All eleven new advertisement field plants were caught by the new test's own diagnostic.
- Mutation report controls, static analysis and all three Mermaid renders passed.
- RV32 Debug and Release linked every core object and executed their smoke checks with rc 0. Both final images have no unresolved symbols.
- Coverage remains 100% lines and branches after the existing exclusions. No exclusion or ratchet changed.

| Coverage file | Raw lines | Raw branches | After existing exclusions |
|---|---|---|---|
| Wire header | 10/10 | 2/2 | 100% / 100% |
| ACMP core | 742/742 | 348/348 | 100% / 100% |
| ADP core | 203/205 | 93/100 | 100% / 100% |
| MAAP core | 209/209 | 140/140 | 100% / 100% |

The ADP exclusions remain the two unreachable statements and seven unreachable arcs already documented on the base.
Neither target suite proves port timing, wire deadlines, cold-power storage or complete recovery event accounting.
Those duties are explicit port obligations on both deployment targets.

## Unnumbered source rows and hooks

| Source subject | Disposition | Local boundary and reason |
|---|---|---|
| Boot, identity and saved state | Port obligation | [Entity configuration](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/docs/PORTING.md#entity-configuration) and [persistence](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/docs/PORTING.md#persistence-and-startup). Device boot and diagnostics stay with the application. |
| Per-function placement and one owner | Split | [Dispatch](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/docs/PORTING.md#ownership-and-dispatch) retains one owner. Hardware placement switches, default-image selection and release acceptance are excluded. |
| gPTP, PHC, framing, timestamps and media | Excluded | No time or media implementation is imported. The [callback contracts](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/docs/PORTING.md) consume transport and grandmaster data. |
| ADP ingress tuple and identity | Port obligation | Use the [input contract](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/docs/PORTING.md#adp-input-validation) and [ACMP admission callback](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/docs/PORTING.md#acmp-callbacks-and-public-fields). The platform filter implementation is excluded. |
| ACMP ingress tuple and identity | Port obligation | The [frame contract](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/docs/PORTING.md#frames-and-buffers) supplies untagged frames on the correct interface. The core still checks its own entity targets. Hardware token buckets are excluded. |
| MAAP ingress tuple and identity | Port obligation | Follow the [MAAP callback contract](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/docs/PORTING.md#maap-callbacks-and-public-fields). Its receiver tests cover multicast and DEFEND destination rules. Hardware filtering is excluded. |
| AECP ingress | Excluded | There is no AECP core here. |
| MSRP and MVRP ingress | Port obligation | The [external reservation component](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/docs/PORTING.md#reservation-and-datapath) owns these frames. This library has no MRP codec. |
| Filter mismatch counters and token buckets | Excluded | These are platform ingress properties. They do not become new counters in the cores. |

| Hook | Disposition | Reason |
|---|---|---|
| H-ADP | Port obligation | Measure accepted input or event through accepted advertisement or state commitment. |
| H-DISC | Port obligation | Keep one service allowance through every matching sink and any resulting connection output. |
| H-ACMP | Port obligation | Measure request/response and original timer deadlines, including transport stalls. |
| H-MAAP | Port obligation | Measure allocation, defense, retransmit and loss actions without relaxing normative intervals. |
| H-SRP | External port obligation | The reservation component owns its MRP receive and timer service. |
| H-AECP | Excluded | No AECP responder is imported. |
| H-NOTIFY | Excluded | No AECP notification engine is imported. |
| H-COUNTERS | Excluded | No AECP counter-serving engine is imported. |

The [service contract](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/docs/PORTING.md#service-measurement) gives each applicable hook's observations, load cases and named late-service/reordering defect duties.

## Delivery and inherited privacy failure

Head: `69a312e3914f96c2db5fa51f07b087a6cd6ff349` on `requirements-port`. The worktree is clean.
The only failing gate is `privacy`, on the required base commit `18d737832c376f32660eb21fe2796e0b611507e3`.
Its stored identity differs from the unchanged policy. Both new commit identities pass.
The [manager ruling](https://github.com/kebag-logic/tsn-c-stack/issues/14#issuecomment-6081168071) authorizes this delivery with that failure recorded.
[PR 17](https://github.com/kebag-logic/tsn-c-stack/pull/17) supplies the fix. The manager merges main into this branch before review starts.
No privacy policy, identity configuration or history was changed.

The requirements mapping, exclusions, clauses, verification methods and generated traceability are complete.
Real integration timing, durable storage and recovery accounting remain explicit port obligations on both targets.
The PR body uses `Relates to #14` while the inherited all-gates-pass prerequisite remains unresolved.
Publication, the main merge and independent review remain manager duties.
No push, pull request creation, hardware access or settings change occurred.

The [final patch]($VALIDATION_STORAGE/tsn14-a571/resume/requirements-port-final.patch) is 226144 bytes. SHA-256: `926ebfffb618ff7b88a035933527a68f7c6d075948bf7951bdcb3430c8bcaa3a`.
The original prepared patch is preserved in scratch. Large artifacts stay outside this packet.
The [integrity receipt](INTEGRITY.json), [gate table](GATES.json), [artifact hashes and sizes](EVIDENCE.json),
[mutation summary](MUTATIONS.json), [source inspection](SOURCES.md) and [PR body](PR-BODY.md) complete the packet.

## Reproduction

The [main validation commands](https://github.com/kebag-logic/tsn-c-stack/blob/requirements-port/docs/VERIFICATION.md) use 16 jobs. The local dependency prefix is read-only. No installation was copied into the output directory.

```sh
export CMAKE_PREFIX_PATH=$VALIDATION_STORAGE/697-a569/round7/gtest-install
export PKG_CONFIG_PATH=$VALIDATION_STORAGE/697-a569/round7/gtest-install/lib/pkgconfig
export TSN_CLANG=$VALIDATION_STORAGE/697-a569/round6/clang18/bin/clang-18
unset CPATH CPLUS_INCLUDE_PATH C_INCLUDE_PATH LIBRARY_PATH
python3 scripts/validate.py --work $VALIDATION_STORAGE/tsn14-a571/resume/step2/linux --jobs 16 --graphs
python3 scripts/baremetal.py --work $VALIDATION_STORAGE/tsn14-a571/resume/step2/rv32 --jobs 16
```

The [separate campaign receipt]($VALIDATION_STORAGE/tsn14-a571/resume/step2/remaining-gates.json) records the remaining commands and their individual return codes.
The [campaign runner]($VALIDATION_STORAGE/tsn14-a571/resume/step2/remaining_gates.py) reproduces those commands without changing or bypassing the privacy gate.
The first preflight attempt was stopped after detecting that new IDs needed the existing comment grammar. IDs were corrected; the complete preflight was rerun. That superseded interruption is retained separately from the final gate table.

## Requirement metadata controls

Each named control in the [record checker](https://github.com/kebag-logic/tsn-c-stack/blob/69a312e3914f96c2db5fa51f07b087a6cd6ff349/scripts/requirement_records.py) introduces the stated defect. The checker must reject it.

| Control | Required result |
|---|---|
| missing source | Reject the planted metadata defect. |
| duplicate source | Reject the planted metadata defect. |
| unknown source | Reject the planted metadata defect. |
| changed pin | Reject the planted metadata defect. |
| moving source link | Reject the planted metadata defect. |
| missing origin | Reject the planted metadata defect. |
| different origin | Reject the planted metadata defect. |
| missing target | Reject the planted metadata defect. |
| empty text | Reject the planted metadata defect. |
| missing clauses | Reject the planted metadata defect. |
| unlinked clause | Reject the planted metadata defect. |
| duplicate authority | Reject the planted metadata defect. |
| unknown method | Reject the planted metadata defect. |
| missing port reason | Reject the planted metadata defect. |
| missing inspection reason | Reject the planted metadata defect. |
| missing evidence | Reject the planted metadata defect. |
| broken evidence | Reject the planted metadata defect. |
| broken contract anchor | Reject the planted metadata defect. |
| legacy exemption | Reject the planted metadata defect. |
| false exclusion | Reject the planted metadata defect. |
| orphan import | Reject the planted metadata defect. |
| unknown local ID | Reject the planted metadata defect. |
| duplicate local ID | Reject the planted metadata defect. |
| missing exclusion reason | Reject the planted metadata defect. |
| Last test removed from tested import | Reject the untested imported requirement. |
| Justified inspection or port obligation | Accept its documented verification method. |

## Resources

Resumed service peak memory: 5888114688 bytes. This remained below 9 GB.
Long campaigns ran in detached sessions with logs and return-code files. All campaign processes have exited.
Every output file is below 200,000 bytes. Binaries, packages, source clone, PDF extracts, full mutation XML and rendered graphs remain in scratch or their original locations.
