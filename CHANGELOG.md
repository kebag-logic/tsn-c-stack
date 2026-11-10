# Change log

## Unreleased

- Walk only the sinks an ACMP entry changed. Each entry marks the sinks it changes, and its interface's timer for an expiry; completion and each publication before a new frame publish, re-arm, admit, persist and report only those, with the calls a walk over every sink makes, in its order and with its arguments ([ACMP-13](docs/REQUIREMENTS.md#acmp-changed-sink-walk)). Add `dirty`, `ACMP_DIRTY_WORDS` words, and `dirty_if` to `struct acmp`. A differential test drives random entries into a core and one with every sink marked before each entry, at 1, 8, 32 and 33 sinks, and requires the same calls.
- Size the ACMP owed-release mask from `ACMP_MAX_SINKS`: `acmp_owed.release` holds `ACMP_RELEASE_WORDS` 32-bit words, and no shift reaches the word width. With more than 32 sinks, sink 32 and sink 0 no longer share a bit, so each sink's change waits only behind its own owed response. A build whose mask cannot hold every sink is refused, and so is a build of more than 255 sinks, which `probe_of` cannot name. Add a 33-sink test binary under `-fsanitize=shift,undefined`. It checks that sinks 31 and 32, on both sides of the word boundary, wait only behind their own owed responses, and that a probe owed in a slot that held another sink's response holds no sink. The 16-sink tests check the same slot reuse ([issue 31](https://github.com/kebag-logic/tsn-c-stack/issues/31)).
- Exempt the merge of #29 from the one-line message rule by its exact commit; its identity and content are still checked.
- Never drop an ACMP command at the owed bound. With all `ACMP_OWED_MAX` frames owed, `acmp_rx` now returns false and leaves state unchanged; after each `acmp_poll` that frees room the port offers the kept command and the frames waiting behind it, in arrival order until one is declined, before it services timers. A BIND_RX waits for two free owed slots, so a deferred binding loses no probe; while it waits with one slot free, a timer probe of any sink is held and re-armed 1 ms on instead of owed, so it neither delays the BIND_RX nor is lost (`probes_held`). The port contract derives the answer pass of every kept command, n + 1 + f + r, with n the frames owed when the egress returns (`ACMP_OWED_MAX`, or one less when the first kept frame is a BIND_RX declined with one slot free), and the egress-hold budget for the deepest backlog a port keeps. Add `acmp_rx_ready`, true with two free owed slots, and rename `busy_drops` to `busy_declined` ([ACMP-12](docs/REQUIREMENTS.md#acmp-owed-bound)). Ports must keep declined frames.

- Add the required ACMP `publish` callback from milan-fpga F-INT. Publish changed bound, started and settled stream-ID state before new frames and first at completion; preserve the last publication across reset ([ACMP-10](docs/REQUIREMENTS.md#acmp-publish-port)). Integrators must supply the callback.

- Port the applicable [milan-fpga requirements](docs/REQUIREMENTS.md) with origins, linked clauses, both targets and verification methods. Record every source disposition. Test advertisement fields and peer-loss recovery with planted defects. Check each pinned source anchor.
- Accept GitHub squash merges in the privacy gate: the noreply author with GitHub as committer, still with a one-line message.
- Enforce the closed contributor rules for source bytes, suffixes, header modes, linker scripts and assembly. Restrict assertion forms and check generated GoogleTest defaults.
- Use compiler comment tokens and compile both sides of permitted conditional regions. Refuse assembly hiding mechanisms. Grade mutations only from delimited assertion messages. Require unique message needles with at least eight characters.
- Close comment scanner gaps for digit separators, zero conditions and assembly directive bodies.
- Require mutation needles to come from named assertion messages. Preserve critical port contract phrases.
- Require fresh complete mutation reports, specific assertion messages, compiler boundary checks and executable test registration.
- Link each standard separately. Record the inherited ADP input limits and caller validation obligations.
- Require Linux and freestanding RV32 validation in [CI](.github/workflows/quality.yml).
- Link the complete RV32 library against a minimal port and run protocol smoke checks in Debug and Release.
- Reduce code comments to licence, requirement and standard tracing.
- Preserve public contracts in the [porting guide](docs/PORTING.md) and check their documented names.
- Refuse hidden prose, disabled regions and generic mutation needles. Keep gate checks active under optimized Python.
- Import the ADP, ACMP and MAAP cores and wire helpers with rewritten history.
- Apply the [MIT licence](LICENSE) to the exported sources and core tests.
- Add standalone builds, core mutation plants and the coverage ratchet.
- Add sanitizer, static-analysis, boundary, licence, privacy and traceability gates.
- Add the [quality documents](docs/VERIFICATION.md) and a [port example](examples/adp_port.c).

Relates to [milan-fpga issue 697](https://github.com/kebag-logic/milan-fpga/issues/697).
