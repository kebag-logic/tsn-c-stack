https://github.com/kebag-logic/milan-fpga/issues/665#issuecomment-5992455815

[A10] **Owner directive, 2026-10-05 12:14: bare-metal first, and reuse lwSRP.** "The solution need to be baremetal first in mind, re-use the lwSRP available on the kebag logic github."

What this changes for #665 and every lane under it:

1. **Bare-metal first.** The firmware runs with no OS: a single event loop driven by the mailbox doorbell, interrupts and fabric-posted timer events.
   - No heap: every allocation comes from static pools sized from the entity model at build time.
   - No dynamic threads, and no OS service in protocol code.
   - An RTOS port (lwSRP has Zephyr glue, for example) may come later as an adapter. It is not the design target.
2. **SRP is lwSRP**, from https://github.com/kebag-logic/lwSRP (MRP, MSRP with FourPacked listener declarations, MVRP, MMRP; ports-and-adapters C11). F4 integrates lwSRP and does not write SRP again:
   - an end-station adapter on the mailbox contract, in place of its switch-oriented `sim_adapter`;
   - a bare-metal port: `shlan_malloc`/`shlan_calloc`/`shlan_free` on a static pool, `shlan_printf` on a debug sink, and `shlan_timer_tick()` at the centisecond, driven by the fabric's timer event;
   - fixes found during integration go to lwSRP as PRs, not as a private copy.
3. **F0's HAL must carry lwSRP's port layer.** The contract must carry MRP PDUs and the timer event in the form lwSRP's `mrp_pdu` codec and timer port take.
4. **The same pattern applies to the other protocols.** ADP, ACMP, MAAP and AECP are written as portable C11 ports-and-adapters modules like lwSRP, host-testable with cgreen and behave where that fits.

F0 (A542) is restarted with this directive, keeping its partial work.

Do not edit or delete any existing comment.


https://github.com/kebag-logic/milan-fpga/issues/665#issuecomment-6008744385

[A10] Owner directive (2026-10-06): all the Mark II software must be fully unit-tested. Decision and plan:

**Framework: GoogleTest with GoogleMock.** It is packaged for the build host and the hosted runners (`libgtest-dev`, `libgmock-dev`). GoogleMock mocks the seams the firmware already has: the mailbox HAL, the flash port and lwSRP's port layer. The firmware stays C11; the tests are C++ and include the C headers through `extern "C"`.

**What "fully tested" means for #665:**
- Every public function in `sw/firmware/ctrl` and `sw/firmware/ctrl_nvm` has unit tests, including every protocol state-machine transition and every error return.
- CI measures line and branch coverage with gcov for each PR. The target is 100 % branch coverage of the protocol and saved-state code. Every exclusion is listed with its reason in the test README, and a ratchet gate refuses any drop in coverage.
- The suites print the `checks: N   failures: M` tally that `scripts/suite_tally.py` reads, through a GoogleTest event listener. The existing mutation arms stay and are graded as before.
- lwSRP: its own upstream suites run unchanged at the pinned commit. GoogleTest covers only our adapter. A coverage gap in lwSRP is fixed upstream by a PR.

**Order:**
- F0 (#668) and F1 (#669) merge as they are; their hand-rolled checks and mutation arms pass.
- **FT** (new lane, follows F0): the GoogleTest harness, the tally listener, CI wiring and the coverage gate. It also ports the F0 and F1 host checks (`test_check.h`, `test_adp.c`, the ctrl_nvm checks) to GoogleTest.
- F2 to F5 start on top of FT, and each lands with its GoogleTest unit tests at the coverage target.

