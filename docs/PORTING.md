# Porting

For an integrator, start with the [headers](../include/) and the compiled
[ADP example](../examples/adp_port.c). Its [test](../tests/test_port.cpp) checks
queued expiry and blocked output. It uses one static frame slot and no OS API.
It is an adapter example, not a network driver.

## Target builds

Support both Linux hosted builds and bare-metal RV32 builds.
Keep sockets, POSIX timers and threads in the port. Core headers and sources stay OS-independent.
The [boundary gate](../scripts/check_boundary.py) checks compiler dependencies and rejects unsupported external symbols, including heap and OS calls.

The [RV32 toolchain file](../cmake/rv32.cmake) selects RV32I, ILP32 and freestanding C11.
The [minimal port](../examples/rv32/) uses compiler intrinsic headers plus two local C-library headers.
It provides only `memcpy` and `memset`. These functions perform no allocation.
Compiler integer arithmetic helpers come from the matching RV32I [GCC runtime](https://gcc.gnu.org/onlinedocs/gccint/Libgcc.html).
Debug assertion failure and the ACMP re-entry hook terminate the validation image.
Production ports must supply their own failure policy when these checks are enabled.
The final link includes every core object and must have no undefined symbols.

Run `python3 scripts/baremetal.py --work build-rv32 --jobs 16` before submitting a change.
The [startup](../examples/rv32/start.S) and [link layout](../examples/rv32/link.ld) target the QEMU RISC-V `virt` machine.
They initialize global and stack pointers and clear BSS before calling the smoke checks.
The simulator completion register belongs only to this example port.
Replace startup, link layout, timers and frame transport for a real board.
The [verification guide](VERIFICATION.md#bare-metal-rv32) defines the checks and their limits.

## Ownership and dispatch

Keep instances, configuration objects and callback tables alive for the whole run.
ADP retains its entity and port pointers. ACMP copies configuration and retains
port/environment pointers. MAAP retains its port pointer.
Provide all required callbacks and valid pointers. Init is not a null-pointer validator.
Do not move an active example object: its callback context points to itself.
Serialize every input and all instance access. No interrupt or callback may re-enter.
Zero-delay timers must enqueue an expiry for a later dispatch.

ADP's port-call guard covers every instance, including `adp_build` and initialization.
Builds without `NDEBUG` assert on re-entry. Builds with `NDEBUG` ignore it and increment the lifetime `adp_reentry_count` modulo 2^32.
A refused `adp_poll` returns false. A refused `adp_build` leaves its output unchanged.
Initialization does not reset this counter. Read it only from the dispatch context.
MAAP guards its instance and counts refused re-entry. Builds without `NDEBUG` also assert.
ACMP guards port callbacks and counts refused re-entry on its instance.
Defining `CTRL_REENTRY_ASSERT` requires the port to implement `ctrl_reentry_assert`.
The [architecture](ARCHITECTURE.md) describes these guards; they provide no concurrency protection.

## Frames and buffers

`send` accepts an entire frame or returns false without taking any of it.
Copy bytes before returning true. Core frame buffers may be stack storage.
Do not retain a frame pointer. Provide receive buffers valid through the call.
Present untagged frames with the Ethernet header and no FCS.
Strip VLAN tags in the adapter before core delivery.
ADP sends 82 bytes, ACMP 70 bytes and MAAP 60 bytes including padding.
The wire helpers require enough readable or writable bytes for the requested field.

Drain transport queues promptly. Call `adp_poll`, `acmp_poll` and `maap_poll`
while they report work. ADP sends at most one owed frame per poll.
MAAP attempts at most two. ACMP attempts one owed frame per poll.
Inspect overflow and discarded-input counters; overflow is a service failure.

ADP retains at most two departures. Further shutdowns coalesce into the queued departure and increment `departing_coalesced`.
The oldest departure keeps its shutdown index. A queued departure carries zero.
Advertisements cannot pass either departure. Link loss or shutdown cancels an owed advertisement.
ACMP queues at most `ACMP_OWED_MAX` frames, in order. A command facing a full queue is dropped before changing state.
An overflowed probe increments `probes_lost`; its timeout recovers the attempt.
A queued probe starts its timeout only when accepted, if its sink still waits for the same sequence ID.
Changes caused by a command reach `env->changed` only after that command's response is accepted.
Use `acmp_change_pending` to inspect a notification held behind a response.

## ADP input validation

Supply the actual readable buffer length to `adp_rx` on the correct interface.
Keep the [untagged frame and buffer contract](#frames-and-buffers).
The core checks the complete 82-byte frame minimum before reading header or target fields.
It requires AVTP version zero and the 11-bit `control_data_length` value 56.
It also checks EtherType, subtype, discovery message type and target.
Each refusal increments `discarded` once, with no other state change or port call.
This applies in DOWN, DELAY and WAITING, including disabled input and an owed advertisement.
Valid discovery for zero or the local entity starts a delay only in enabled WAITING.
Extra trailing bytes are accepted. Destination filtering and interface selection remain adapter duties.
See [ADP-01](REQUIREMENTS.md#adp-input-validation) and the [input controls](../tests/test_adp.cpp).
The format authorities are [IEEE 1722.1-2021 Figure 6-1, 6.2.2.3 and 6.2.2.6](https://standards.ieee.org/ieee/1722.1/6670/)
and [IEEE 1722-2016 4.4.3.4 and 4.4.5.4](https://standards.ieee.org/ieee/1722/5979/).
Target and state handling follow [Milan v1.2 5.6.3.1 and Table 5.51](https://avnu.org/resource/milan-specification/).

## Callback checklist

| Core | Integrator supplies |
|---|---|
| [ADP](../include/adp.h) | Frame send; relative timer start/stop; link level; grandmaster/domain; entropy seed. Supply link and grandmaster change events. |
| [ACMP](../include/acmp.h) | Frame send; monotonic milliseconds; per-interface absolute timer; grandmaster/domain; entropy; bound-talker admission. Environment ports supply lock owner and live source state, SRP requests, persist requests and changed notifications. |
| [MAAP](../include/maap.h) | Frame send; relative timer start/stop; tentative or valid range publication; clock entropy. Supply operational link edges once per change. |

Cancel or replace the previous timer when asked. Ignore obsolete expiries.
Keep clock differences below half the 32-bit range.
Schedule MAAP service at least every 10 ms while it has work.
Hardware latency and network scheduling are integration obligations.
A probe timeout starts after the send callback accepts its probe.
Sample time after that callback returns, including any time spent sending.

ACMP stores no media state. Translate SRP feedback into its registered,
unregistered and kind-changed entry points. Deliver remote ADP frames on their
actual interface. Supply source allocation state when answering talker commands.
Use only MAAP ranges marked valid for stream destinations.
A range callback with zero count withdraws ownership immediately.
The MAAP ingress filter follows tentative ranges too. A range callback must also invalidate affected stream destinations.
Deliver operational link edges once per change; repeated up events start another probing cycle.
`maap_begin` accepts a valid preferred range only for the initial reservation, including a reservation delayed by link-down.
Later conflict recovery draws a fresh range. `preferred=0` requests a draw immediately.
Initialization requires an 8-bit interface index, a nonzero unicast 48-bit MAC, and a nonzero count within the pool.
It clears the instance even when those values are refused. Initialize only before attaching an active machine.

## ADP callbacks and public fields

The [ADP header](../include/adp.h) defines one instance per interface.
Every callback receives its table's `ctx` unchanged. Every callback pointer is required.
The `send` callback uses the supplied interface and follows the [buffer contract](#frames-and-buffers).
The `timer_start` callback replaces the interface's timer and delivers `adp_timer_expired` once after `delay_ms`.
The `timer_stop` callback cancels it. Zero-delay expiries still require a later dispatch.
The `gptp` callback returns the current grandmaster identity and domain for that interface.
The `link_up` callback returns the current link level. The `seed` callback supplies entropy when the machine starts.

| Public field or value | Meaning |
|---|---|
| `adp_entity` | Fixed ADPDU fields supplied by the entity model. Its `mac` is a 48-bit source address. |
| `interface` | AVB interface used for ports and the advertised interface index. |
| `enabled`, `link_up` | Whether the machine is started, and the last link level it acted on. |
| `available_index`, `current_configuration_index` | Advertisement sequence and configuration fields for outgoing ADPDUs. |
| `timer` | Which relative timer the port holds: `ADP_TIMER_DELAY`, `ADP_TIMER_ADVERTISE`, or `ADP_TIMER_NONE`. |
| `rng` | The random delay generator's xorshift32 state. |
| `available_owed` | An ENTITY_AVAILABLE due in DELAY that has not been accepted. |
| `departing_owed` | Number of unaccepted departures, from zero through `ADP_DEPARTING_OWED_MAX`. |
| `departing_index` | The available index carried by the oldest owed departure. |
| `ADP_DRAW_STARTUP` | Startup delay draw from zero to two seconds. |
| `ADP_DRAW_DELAY` | Other delay draws from zero to four seconds. |
| `ADP_DRAW_NONE` | No delay draw recorded yet. |

The delay rules trace to [Milan v1.2 5.6.3.5.2 and Table 5.50](https://avnu.org/resource/milan-specification/).
`adp_set_enable` starts or shuts down the machine. `adp_set_current_configuration` changes the next ADPDU's configuration index.
`adp_rx`, `adp_timer_expired`, `adp_link_change` and `adp_gm_change` deliver the respective input events.
`adp_build` writes the current ADPDU into a caller buffer of at least `ADP_FRAME_BYTES` bytes.
It uses the supplied message type and available index, with the grandmaster pair sampled during the call.
`adp_poll` retries the oldest departure first and returns true while output remains owed.

### ADP counters

These [diagnostics](../include/adp.h) count modulo 2^32. Read them from the serialized dispatch context.

| Field | Meaning |
|---|---|
| `gm_changed` | Grandmaster change events received. |
| `draws` | Random delays drawn. |
| `last_draw_ms`, `last_draw` | Most recent delay and its draw kind; these are diagnostic values, not counters. |
| `stray_expiries` | Timer expiries received when no timer is running. |
| `discarded` | Malformed or irrelevant ADPDUs refused by receive validation. |
| `deferred_sends` | Send attempts refused for lack of room. |
| `departing_coalesced` | Shutdowns coalesced into an already queued departure. |
| `adp_reentry_count` | Lifetime count of refused port callbacks across all instances, returned by the function of that name. |

## ACMP callbacks and public fields

The [ACMP header](../include/acmp.h) separates transport callbacks from entity environment callbacks.
Every pointer is required. Both tables pass their `ctx` unchanged and obey the [dispatch rule](#ownership-and-dispatch).

| Transport callback | Contract |
|---|---|
| `ports->send` | Submit the complete frame on the supplied interface. False leaves it owed for `acmp_poll`. |
| `ports->now_ms` | Return milliseconds modulo 2^32 from the clock used by every deadline. |
| `ports->timer` | Replace the interface timer with one expiry at `deadline_ms`. With `armed=false`, cancel it. |
| `ports->gptp` | Return the interface's current grandmaster identity and domain. |
| `ports->seed` | Supply entropy for random TMR_DELAY draws. |
| `ports->admit` | Admit the bound talker's ENTITY_AVAILABLE and ENTITY_DEPARTING on the sink's interface, with one admission entry per sink. |

The `ports->admit` callback receives the `interface`, `sink`, `bound` and `talker_entity_id` values.
With `bound=false`, withdraw that sink's admission entry.
The core calls it on bind, unbind and rebind. `acmp_open` also calls it for each restored binding.
The core still filters the admitted frames itself.

| Environment callback | Contract |
|---|---|
| `env->locked` | Return true when locked and write the locking controller's entity ID. |
| `env->source` | Fill the requested STREAM_OUTPUT's current `acmp_source_state`. |
| `env->srp` | A non-NULL `stream` starts SRP reservation and listening for that stream's packets. NULL stops listening and clears the stream parameters. |
| `env->persist` | A saved binding field changed. Mark that sink's record for the store's write policy. |
| `env->changed` | The sink's observable view changed. Command responses must be accepted before their change notification. |

The SRP start and stop obligations trace to [Milan v1.2 5.5.3.5.18 step 4 and 5.5.3.5.36 step 1](https://avnu.org/resource/milan-specification/).
The lock contract traces to [Milan v1.2 5.3.4.1](https://avnu.org/resource/milan-specification/).
The source owner fills `acmp_source_state.dest_mac_valid` when MAAP holds a destination MAC for that source.
It fills `acmp_source_state.asking_failed` when a Listener Asking Failed attribute is registered.
Its `stream` holds the current stream ID, destination MAC and VLAN.
These fields trace to [Milan v1.2 5.5.4.1 step 3 and Table 5.47](https://avnu.org/resource/milan-specification/).

`acmp_tk_registered` reports registration for the sink's settled stream.
Its `failed` argument is true when the registered Talker attribute is Talker Failed.
`acmp_tk_unregistered` reports that attribute's removal.
`acmp_tk_kind_changed` uses the same `failed` meaning for an existing registration, outside all protocol and port callbacks.
Only SETTLED_RSV_OK accepts that update. It changes REGISTERING_FAILED without changing state or starting a probe.
These inputs trace to [Milan v1.2 Tables 5.23, 5.29 and 5.30](https://avnu.org/resource/milan-specification/).

### ACMP configuration and views

The [configuration and view structures](../include/acmp.h) use the following fields.

| Structure and fields | Meaning |
|---|---|
| `acmp_config.n_interfaces` | Interface count from one through `ACMP_MAX_INTERFACES`. |
| `acmp_config.mac` | Each interface's 48-bit source MAC. |
| `acmp_config.n_sinks`, `sink_interface` | STREAM_INPUT count and each sink's interface. |
| `acmp_config.n_sources`, `source_interface` | STREAM_OUTPUT count and each source's interface. |
| `acmp_binding` | Talker entity ID, controller entity ID, talker unique ID and `streaming_wait` for one binding. |
| `acmp_stream` | Settled stream parameters: `stream_id`, 48-bit `dest_mac` and `vlan_id`. |
| `acmp_sink_view.state`, `bound`, `binding` | Connection state and binding reported by `acmp_view`. |
| `started` | Streaming control state. Undefined while unbound; the view returns false. |
| `probing_status`, `acmp_status` | GET_STREAM_INFO probing status and the last ACMP status. |
| `settled`, `stream` | Settlement and the last accepted PROBE_TX_RESPONSE parameters. Parameters are zero when not settled. |
| `talker_registered` | A matching Talker attribute is registered in SETTLED_RSV_OK. |
| `registering_failed` | That registered attribute is Talker Failed. |
| `talker_discovered` | Discovery currently knows the bound talker. |

`env->changed` reports changes to bound, started, probing status, ACMP status, stream fields, talker registration or registering failure.
The observable fields trace to [Milan v1.2 5.3.8.2–5.3.8.9 and Table 5.22](https://avnu.org/resource/milan-specification/).

### ACMP machine storage

The [public storage](../include/acmp.h) lets callers allocate fixed instances. The core owns active machine fields.

| Field group | Meaning |
|---|---|
| `acmp_sink.probe_controller`, `probe_talker`, `probe_talker_uid`, `probe_seq` | Saved identity and sequence of the last PROBE_TX_COMMAND, used to match its response. |
| `probe_retried` | The duplicate probe has been sent. |
| `stream`, `tk_failed` | Settled stream held for `env->srp`, and whether its registered Talker attribute is Talker Failed. |
| `disc_running`, `discovered`, `disc_interface_index`, `disc_available_index` | Discovery activity and the remote talker's last interface and available indices. |
| `timer`, `timer_deadline`, `timer_held` | Connection timer and absolute deadline. A held TMR_NO_RESP waits for its owed probe to leave. |
| `adp_armed`, `adp_deadline` | Discovery timer state and its absolute millisecond deadline. It runs beside the connection timer. |
| `admitted`, `admitted_talker` | Admission state last supplied to the ingress port for that sink. |
| `change_owed` | Owed frames whose acceptance releases this sink's pending change. |
| `reported` | View last reported through `env->changed`. |
| `saved` | Binding record last announced through `env->persist`. |
| `acmp_owed.interface`, `frame` | Output interface and complete frame waiting for room. |
| `probe_of` | One plus the sink index for a probe; zero for a response. |
| `release` | Bit s releases sink s's pending change when this frame leaves. |
| `acmp.sequence_id` | Sequence ID for the next new PROBE_TX_COMMAND. Duplicates retain the previous ID. |
| `rng`, `seeded` | TMR_DELAY xorshift32 state and whether port entropy has been mixed in. |
| `in_port` | A port callback is running. |
| `now_read`, `now` | Whether this entry sampled time, and its latest clock value. |
| `timer_armed`, `timer_at` | Timer state and absolute deadline held by each interface's port. |
| `owed`, `owed_head`, `owed_count` | Bounded output queue, oldest frame index and queued frame count. |

### ACMP counters

The [ACMP diagnostics](../include/acmp.h) count modulo 2^32.

| Field | Meaning |
|---|---|
| `rx_ignored` | ACMP input not addressed to this entity's talker or listener. |
| `rx_malformed` | Unreadable ACMP input, including a nonzero AVTP version. |
| `unknown_sink` | LISTENER_UNKNOWN_ID answers and probe responses ignored for an unknown sink. |
| `probe_mismatch` | Probe responses that do not match the sink's saved probe. |
| `refused_locked` | CONTROLLER_NOT_AUTHORIZED answers. |
| `adp_ignored` | ADPDUs no sink accepted, or ADPDUs the module cannot read, including a nonzero AVTP version. |
| `impossible` | Events marked impossible by [Milan v1.2 Table 5.30 or Table 5.54](https://avnu.org/resource/milan-specification/). |
| `busy_drops` | Commands dropped before state changes because the owed queue is full. |
| `probes_lost` | Probes dropped because the owed queue is full. Their timeout recovers the attempt. |
| `deferred_sends` | Send attempts refused for lack of room. |
| `reentries` | Calls refused while a port callback runs. |
| `draws` | Random TMR_DELAY draws. |
| `last_draw_ms` | Most recent delay in milliseconds; a diagnostic value rather than a counter. |

`ctrl_reentry_assert` is called once per refused ACMP entry when `CTRL_REENTRY_ASSERT` is defined.
The integrator supplies this hook and its failure policy.

## MAAP callbacks and public fields

The [MAAP header](../include/maap.h) defines one fixed machine per interface and range.
Every callback receives `ctx` unchanged and returns without waiting or delivering synchronous input.
All pointers and callback functions are required.
The `send`, `timer_start` and `timer_stop` callbacks follow the [buffer and relative-timer contracts](#adp-callbacks-and-public-fields).
Deliver MAAP expiries through `maap_timer_expired`.
The `range` callback updates the ingress filter even for a tentative range.
Only `valid=true` permits consumers to use its addresses. A zero `count` withdraws the range and invalidates affected stream destinations.
The `clock` callback returns the least-significant bits of the real-time clock for entropy.
This entropy source traces to [IEEE 1722-2016 B.3.6.1](https://standards.ieee.org/ieee/1722/5979/).

The `preferred` field holds the range supplied to `maap_begin`, consumed by the first reservation.
`maap_begin` is accepted only in INITIAL. It refuses an invalid preferred range.
`maap_port_operational` with link down withdraws the range; link up starts probing, including for a previously active range.
`maap_release` withdraws the range and disables the machine.
`maap_poll` attempts at most two sends, allowing the final retransmission and ANNOUNCE together.
It returns true while output or a deferred expiry remains owed.

### MAAP counters

These [diagnostics](../include/maap.h) count modulo 2^32. Queue overflow means failed service, never successful delivery.

| Field | Meaning |
|---|---|
| `conflicts` | Losing address conflicts that require withdrawal and a fresh reservation. |
| `discarded` | Malformed or irrelevant frames rejected by receive validation. |
| `stale_expiries` | Expiries received with no running timer. |
| `deferred` | Send attempts refused for lack of room. |
| `overflow` | Frames dropped because the pending queue is full. |
| `reentries` | Calls refused while the same instance is active. |

## Wire field preconditions

The [wire helpers](../include/wire.h) read and write big-endian fields one byte at a time.
They have no host alignment requirement and do not depend on host byte order.
`wire_be16`, `wire_be32` and `wire_be64` require two, four and eight readable bytes respectively.
`wire_put_be` requires `bytes` in the range one through eight and that many writable bytes.

## Persistence and startup

Initialize all cores before enabling transport.
Use ACMP binding restore and latch functions for the documented 20-byte records.
Byte zero holds bound, started and streaming-wait bits at positions zero, one and two. Byte one is reserved and zero.
The remaining fields are big-endian: a 16-bit talker unique ID, 64-bit talker entity ID and 64-bit controller entity ID.
An unbound record contains twenty zero bytes. The [binding tests](../tests/test_acmp.cpp) pin the format and refusal rules.
A refused `acmp_restore_binding` leaves that sink at its default unbound state.
`acmp_restore_rollback` drops every restored binding.
Restore before `acmp_open`. Call it after the binding walk and before the first input, once transport is ready.
It announces every restored binding to admission; a later call also announces those bindings. Roll back all restored bindings if the surrounding
store rejects the transaction. The store itself is outside this library.
Enable ADP and begin MAAP only after callbacks and input routing are ready.
SRP remains a separate [lwSRP](https://github.com/kebag-logic/lwSRP) component.
ACMP initialization refuses capacities above the public limits and interface indices outside the configured interface count.
It leaves the instance unchanged on refusal and makes no port calls on successful initialization.
Successful `acmp_init` starts every sink UNBOUND. Restored bindings enter PRB_W_AVAIL with discovery running.
`acmp_rx`, `acmp_adp_rx` and `acmp_timer_expired` take the actual ingress or timer interface.
`acmp_view` supplies the view used by GET_STREAM_INFO. `acmp_binding_latch` supplies the current saved record.
Each sink and source uses its configured interface for routing, discovery and timers.
`acmp_tk_kind_changed` updates continuous registration only in SETTLED_RSV_OK; it is not a new registration event.
`acmp_set_started` refuses unbound or unknown sinks. `acmp_view` and `acmp_binding_latch` refuse unknown sinks.

For a developer, the [coding standard](CODING_STANDARD.md) explains the C subset.
For a tester, the [verification guide](VERIFICATION.md) covers malformed input,
backpressure, timer wrap and deliberate callback violations.

## Entity configuration

The [imported identity requirements](REQUIREMENTS.md#mfentity-01) apply to both targets.
Populate advertisement values from the same entity description used by the application.
Check capabilities, stream counts, Identify index and interface selection before enabling ADP.
The grandmaster and domain come from the current per-interface time service.
They are not a substitute for the static entity fields.
Check consistency under [IEEE 1722.1-2021 6.2.2.7 through 6.2.2.20](https://standards.ieee.org/ieee/1722.1/6670/)
and [Milan v1.2 5.6.2](https://avnu.org/resource/milan-specification/).

The [authentication configuration obligation](REQUIREMENTS.md#mfentity-03) retains the source product policy.
Clear `AEM_AUTHENTICATION_REQUIRED` in the supplied `entity_capabilities` before enabling ADP.
Check the emitted capability field on Linux and bare-metal RV32.
[IEEE 1722.1-2021 6.2.2.9 and Table 6-2](https://standards.ieee.org/ieee/1722.1/6670/) define the field and flag.
The application must handle unauthenticated requests safely.
AECP authentication and application authorization remain outside this library.

The [stable identity obligation](REQUIREMENTS.md#mfentity-02) retains the source product's MAC-derived EUI-64 policy.
Derive and store that identity outside the cores. Supply the same identity to ADP and ACMP after restart.
[IEEE 1722.1-2021 6.2.2.7](https://standards.ieee.org/ieee/1722.1/6670/) permits MAC derivation; it does not require that particular derivation.
Test the application identity across cold starts and configuration changes.
The library neither derives identity nor reads device storage.

## Reservation and datapath

The [reservation requirements](REQUIREMENTS.md#mfsrp-01) split core signaling from external protocol work.
Connect `env->srp` to [lwSRP](https://github.com/kebag-logic/lwSRP).
Copy the requested stream parameters before returning from the callback.
Process declaration changes outside callbacks. Preserve sink and interface identity.
Deliver registration, withdrawal and registration-kind updates in order through the ACMP entry points.
Retain a withdrawal even when the same stream registers again before delivery.
Retire stale feedback when a binding is replaced or removed.
The integration must test those ordering and supersession cases.

Maintain Talker and Listener declarations, admission and MVRP membership in the external component.
Use the stream VLAN and the current SR class configuration for each interface.
The authority is [Milan v1.2 4.2.7.2, 4.2.7.3, 4.3.2, 4.4.1, 5.5.2.7 and 5.5.3.5](https://avnu.org/resource/milan-specification/).
No MSRP, MVRP or bandwidth admission algorithm is supplied by these cores.

The [datapath obligation](REQUIREMENTS.md#mfconn-02) covers connection programming.
The [admission obligation](REQUIREMENTS.md#mfsrp-04) covers permission to transmit media.
Apply the accepted stream identity, VLAN and priority to the transport.
Configure any installed queue or shaper from the reservation result.
Refused or withdrawn admission must close the media gate.
A successful ACMP response alone is insufficient to open it.
Test successful admission, refusal, withdrawal and replacement on each supported transport.

The [allocation-use obligation](REQUIREMENTS.md#mfmaap-02) connects MAAP to stream ownership.
Assign addresses only from a currently valid range.
On loss, invalidate affected source destinations and update `acmp_source_state.dest_mac_valid`.
Resume use only after the new allocation is valid.
Test address loss while connected and confirm that stale destinations are no longer used.
See [IEEE 1722-2016 B.3.2 and Table B.7](https://standards.ieee.org/ieee/1722/5979/)
and [Milan v1.2 4.3.5.1 and 5.5.4.1](https://avnu.org/resource/milan-specification/).

## Service measurement

The [service requirement](REQUIREMENTS.md#mfservice-01) retains `T_svc = 10 ms` for each core action.
It is a project figure, proposed for approval in the [source register](https://github.com/kebag-logic/milan-fpga/blob/5603c353137e90c1fa95429f6d00ef7a2298d9ee/docs/reference/FR_NFR.md#341-control-service-budget-and-normative-timing).
It is not a timeout specified by IEEE or Milan.
Measure it separately on Linux and bare-metal RV32 with the actual port and scheduler.
Host callback counts and RV32 simulator success do not prove elapsed time on either deployment.

Start reception timing when the port accepts a complete input for delivery.
Start event timing at event occurrence, before any dispatch queue delay.
Start an expiry at its original armed deadline.
Finish when the last required complete output is accepted by transport.
For actions without output, finish at state and timer commitment.
Count receive backlog, dispatch, all matching sinks, callbacks, persistence work and refused sends.
Do not restart the allowance after space becomes available or a discovery event enters ACMP.
A send accepted into a queue is a service endpoint; wire departure is a separate observation.

For a normative wait `W`, require `elapsed <= W + 10 ms`.
Record the full elapsed interval and the selected wait separately.
All overhead before and after the wait shares one allowance.
Zero random delay means `W = 0`.
Each retry retains its own normative timeout and cannot erase late service from the earlier action.
Dropped, unserved and overflowed accepted work fails the measurement.
Successful eventual recovery does not turn that failure into a pass.

| Hook | Portable observations and required cases | Timing authority |
|---|---|---|
| H-ADP | Startup, discovery, GM change, both link edges, shutdown/restart and original advertisement deadlines. Observe accepted AVAILABLE and DEPARTING. Exercise zero and maximum draws, blocked sends, ignored inputs and departure ordering. | [Milan v1.2 5.6.2, 5.6.3.5 and Table 5.51](https://avnu.org/resource/milan-specification/); [IEEE 1722.1-2021 6.2.2.5 and 6.2.2.15](https://standards.ieee.org/ieee/1722.1/6670/) |
| H-DISC | Received AVAILABLE/DEPARTING or original aging deadline through every matching sink and resulting output. Exercise all discovery cells, received validity 1, 10 and 31, index restart, interface/GM/domain mismatch and stale expiry. | [Milan v1.2 5.6.4.1, 5.6.4.5 and Table 5.54](https://avnu.org/resource/milan-specification/); [IEEE 1722.1-2021 6.2.2.5](https://standards.ieee.org/ieee/1722.1/6670/) |
| H-ACMP | Accepted request through matched response; originated probe through response receipt; original timer deadline through its action. Exercise each command, refusal, retry, identity guard, restored binding and blocked response. | [Milan v1.2 5.5.2.3, 5.5.3.5 and Table 5.26](https://avnu.org/resource/milan-specification/) |
| H-MAAP | Receive, link event or original deadline through PROBE, DEFEND, ANNOUNCE or state commitment. Exercise conflicts in every state, three retransmissions, loss/retry, extreme draws and blocked output. | [IEEE 1722-2016 B.3.2 through B.3.6, Tables B.7 and B.8](https://standards.ieee.org/ieee/1722/5979/) |
| H-SRP | Measure the external component's receive, registration and timer paths through completed declarations. Include withdrawal and queued feedback into ACMP. | [Milan v1.2 4.2.7.1.1 and Table 4.3](https://avnu.org/resource/milan-specification/); [lwSRP integration contract](https://github.com/kebag-logic/lwSRP/blob/main/doc/integrator.md) |

Use a monotonic elapsed-time source independent of grandmaster clock steps.
Record target, compiler options, clock rate, configured capacities, event identity and timestamp resolution.
Include clock resolution and instrumentation error in every upper bound.
Run each supported shape under simultaneous protocol traffic, maximum supported backlog and storage write-back.
Include timer wrap, scheduling stalls, saturation, reset and recovery.
Plant late-service and reordered-output defects; each named hook must reject its defect.
Check ingress acceptance in the adapter, including the [ADP validation duty](#adp-input-validation).
The source platform's bus and filter implementation is not required by the portable core.

For [ACMP latency](REQUIREMENTS.md#mflatency-01), record ingress, service, egress and network allowances separately.
Their sum must be strictly below 200 ms with positive measured margin.
The 10 ms service check does not replace that complete transaction check.
Preserve normative timer and spacing bounds independently.
MAAP probe intervals must remain strictly between 500 and 600 ms.
Announcement intervals must remain strictly between 30 and 32 seconds.
Service cannot extend a near-maximum draw beyond its upper bound.
The authority is [IEEE 1722-2016 B.3.3 and B.3.4](https://standards.ieee.org/ieee/1722/5979/).

## Recovery accounting

The [recovery requirements](REQUIREMENTS.md#mfrecovery-01) cover core transitions and application accounting separately.
Deliver link changes to ADP and MAAP. Deliver current GM data and GM-change events to ADP.
Keep ACMP discovery and reservation feedback current for each interface.
Detect peer loss through departure, aging and reservation withdrawal as applicable.
Bindings must remain available for automatic discovery and reprobe.
The application owns media restart after the reservation and destination become usable.

Count link edges, GM changes, peer-loss events, recovery attempts and recovery outcomes in the port.
Document counter width, wrap and snapshot rules. Read core diagnostics in the serialized dispatch context.
The ADP `gm_changed` and MAAP `conflicts` counters cover only their stated events.
ACMP malformed-input and probe counters do not count every recovery event.
Do not present them as a complete recovery ledger.
Record overflow, dropped work and late service even when a later retry succeeds.
Test each fault and counter increment without reinitializing the cores, on both targets' integrations.
See [Milan v1.2 5.5.3.5, 5.6.3.5 and 5.6.4.5](https://avnu.org/resource/milan-specification/)
and [IEEE 1722-2016 B.3.2](https://standards.ieee.org/ieee/1722/5979/).
