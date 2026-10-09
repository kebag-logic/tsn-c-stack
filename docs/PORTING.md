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
Debug builds assert on re-entry. Release builds ignore it and increment the lifetime `adp_reentry_count` modulo 2^32.
A refused `adp_poll` returns false. A refused `adp_build` leaves its output unchanged.
Initialization does not reset this counter. Read it only from the dispatch context.
MAAP guards its instance and counts refused re-entry. Debug builds also assert.
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

Validate the full ADPDU before calling `adp_rx`.
Check AVTP version zero, the complete ADPDU length and `control_data_length` against the received buffer.
These checks belong to the adapter until [issue 3](https://github.com/kebag-logic/tsn-c-stack/issues/3) corrects the inherited receiver.
The core checks only its readable prefix, EtherType, subtype, message nibble and target.
In WAITING, matching discovery input with version 1, length 26 bytes, or `control_data_length` zero still enters DELAY.
It restarts the timer without increasing `discarded`. Valid discovery follows the same path.
See [ADP-01](REQUIREMENTS.md#adp-input-limit), [DEV-08](DEVIATIONS.md), and the [input controls](../tests/test_adp.cpp).
The affected clauses are [IEEE 1722.1-2021 6.2.2](https://standards.ieee.org/ieee/1722.1/6670/)
and [Milan v1.2 5.6.3.1](https://avnu.org/resource/milan-specification/).

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

## Persistence and startup

Initialize all cores before enabling transport.
Use ACMP binding restore and latch functions for the documented 20-byte records.
Byte zero holds bound, started and streaming-wait bits at positions zero, one and two. Byte one is reserved and zero.
The remaining fields are big-endian: a 16-bit talker unique ID, 64-bit talker entity ID and 64-bit controller entity ID.
An unbound record contains twenty zero bytes. The [binding tests](../tests/test_acmp.cpp) pin the format and refusal rules.
Restore before `acmp_open`. Roll back all restored bindings if the surrounding
store rejects the transaction. The store itself is outside this library.
Enable ADP and begin MAAP only after callbacks and input routing are ready.
SRP remains a separate [lwSRP](https://github.com/kebag-logic/lwSRP) component.
ACMP initialization refuses capacities above the public limits and interface indices outside the configured interface count.
It leaves the instance unchanged on refusal and makes no port calls on successful initialization.
Each sink and source uses its configured interface for routing, discovery and timers.
`acmp_tk_kind_changed` updates continuous registration only in SETTLED_RSV_OK; it is not a new registration event.
`acmp_set_started` refuses unbound or unknown sinks. `acmp_view` and `acmp_binding_latch` refuse unknown sinks.

For a developer, the [coding standard](CODING_STANDARD.md) explains the C subset.
For a tester, the [verification guide](VERIFICATION.md) covers malformed input,
backpressure, timer wrap and deliberate callback violations.
