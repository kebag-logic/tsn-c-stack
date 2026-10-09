# Porting

For an integrator, start with the [headers](../include/) and the compiled
[ADP example](../examples/adp_port.c). Its [test](../tests/test_port.cpp) checks
queued expiry and blocked output. It uses one static frame slot and no OS API.
It is an adapter example, not a network driver.

## Ownership and dispatch

Keep instances, configuration objects and callback tables alive for the whole run.
ADP retains its entity and port pointers. ACMP copies configuration and retains
port/environment pointers. MAAP retains its port pointer.
Provide all required callbacks and valid pointers. Init is not a null-pointer validator.
Do not move an active example object: its callback context points to itself.
Serialize every input and all instance access. No interrupt or callback may re-enter.
Zero-delay timers must enqueue an expiry for a later dispatch.

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
MAAP attempts at most two. ACMP drains its bounded response queue.
Inspect overflow and discarded-input counters; overflow is a service failure.

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

## Persistence and startup

Initialize all cores before enabling transport.
Use ACMP binding restore and latch functions for the documented 20-byte records.
Restore before `acmp_open`. Roll back all restored bindings if the surrounding
store rejects the transaction. The store itself is outside this library.
Enable ADP and begin MAAP only after callbacks and input routing are ready.
SRP remains a separate [lwSRP](https://github.com/kebag-logic/lwSRP) component.

For a developer, the [coding standard](CODING_STANDARD.md) explains the C subset.
For a tester, the [verification guide](VERIFICATION.md) covers malformed input,
backpressure, timer wrap and deliberate callback violations.
