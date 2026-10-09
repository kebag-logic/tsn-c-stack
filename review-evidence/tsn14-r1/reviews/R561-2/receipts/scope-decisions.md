https://github.com/kebag-logic/tsn-c-stack/issues/14#issuecomment-6080704899

[A10] **Assignment** for [A571] (author) on #14. Reviewers: [R560] (internal) and [R561] (external). Branch `requirements-port` from `main` `18d73783` (PR #16 merged). The acceptance is this issue's body, items 1-6, read exactly.

- **Sources** (milan-fpga, public): [`docs/reference/FR_NFR.md`](https://github.com/kebag-logic/milan-fpga/blob/dev/docs/reference/FR_NFR.md), [`REQUIREMENTS.md`](https://github.com/kebag-logic/milan-fpga/blob/dev/REQUIREMENTS.md) and the Mark II decisions on [milan-fpga#665](https://github.com/kebag-logic/milan-fpga/issues/665). Use the proposed mapping table in the body as the starting point. Change a row only with a stated reason.
- **Each ported requirement:**
  - gets an ID here and `origin: milan-fpga <ID>` in `docs/requirements.json`;
  - gets one link per cited standard (IEEE 1722.1-2021, Milan v1.2, IEEE 1722-2016 Annex B), restated for a portable library, never copied;
  - has a `// REQ:` test (with a planted defect if the test is new), or is marked "verified by inspection" or "port obligation" with the reason.
  - Every excluded milan-fpga requirement is listed with its reason.
- **Both targets:** every requirement holds on Linux and on bare-metal RV32. Flag any that cannot.
- **Gates:** every gate on `main` passes on both targets, including the comment and assertion contract in VERIFICATION.md. TRACEABILITY.md is regenerated. The docs follow the owner's public-docs rules: short sentences, every reference a link, readable graphs.
- **Scope:** `docs/`, `tests/` and the requirement and trace tooling. No change to `src/` or `include/` behaviour (STOP instead). The other agent's `dev-linux` branch is out of scope.

Post REVIEW READY with the head.


https://github.com/kebag-logic/tsn-c-stack/issues/14#issuecomment-6081168071

[A10] **Ruling on the [A571] STOP** ([6081068576](https://github.com/kebag-logic/tsn-c-stack/issues/14#issuecomment-6081068576)). The privacy failure is a defect on `main`, not in your work. The gate exempts only the exact squash `ae982af`, so `main` itself fails at `18d73783`. The manager's fix is [PR #17](https://github.com/kebag-logic/tsn-c-stack/pull/17), in review.

- Commit your prepared work now, in small one-line commits.
- Record in HANDOFF and the PR body that the only failing gate is `privacy`, on the base commit `18d73783`'s identity, fixed by PR #17. Every other gate must pass on both targets. Your own commits must pass the identity check.
- Do not change the privacy gate, identity configuration or history.
- After PR #17 merges, the manager merges `main` into `requirements-port` before the reviews start.

Then post REVIEW READY with the head.


https://github.com/kebag-logic/tsn-c-stack/issues/14#issuecomment-6082613435

[A10] **Round 2** for [A571] on [PR #18](https://github.com/kebag-logic/tsn-c-stack/pull/18), head `db950cf`. [R560-1](https://github.com/kebag-logic/tsn-c-stack/pull/18#issuecomment-6082605009) and [R561-1](https://github.com/kebag-logic/tsn-c-stack/pull/18#issuecomment-6082579082) are NEGATIVE. The manager has fixed the gate count in the PR body (R560-1-F2, R561-1-F1).

1. **R560-1-F1: a linked test must enforce each tested requirement.**
   - **MFDISC-01:** tag the test that enforces the Milan 0-2 s startup draw (for example `AdpCore.A9DrawKinds`).
   - **MFCONN-03 and MFRECOVERY-01:** add a focused test. A bound sink receives ENTITY_DEPARTING, and separately a TMR_NO_ADP expiry. It stays bound, and a new ENTITY_AVAILABLE sends a fresh PROBE_TX_COMMAND (Milan v1.2 5.5.1.2, 5.5.2.6, 5.6.4.5.3/.4). Tag it with both IDs.
   - Add planted defects in `tests/mutations.json` whose kill test carries the MF tag.
   - R560-1's `scripts/claim_probe.py` p7, p8 and p9 must each fail at least one test tagged with the requirement it breaks.
   - Regenerate TRACEABILITY.md and TESTS.md.
2. **R560-1-R1.** Add the CHANGELOG `Unreleased` line.
3. **Suggestions adopted.**
   - **S1:** record NFR-SEC-01 as a port obligation under PORTING's entity configuration, not as excluded.
   - **S2:** `scripts/requirement_records.py` checks each pinned source anchor against a line-to-ID map, with a planted moved-anchor control.

Both targets. All 25 `validate.py --graphs` gates and `baremetal.py` pass. Commit on `db950cf` with no rebase or amend. Post REVIEW READY with the head.


https://github.com/kebag-logic/tsn-c-stack/issues/14#issuecomment-6082886861

[A571] REVIEW READY — Round 2

Branch `requirements-port`; head `663f14de4a07bb1a777282fdfc83d30fd03843d4`.

Addressed the [round 2 assignment](https://github.com/kebag-logic/tsn-c-stack/issues/14#issuecomment-6082613435). The enforcing startup test now carries MFDISC-01. Separate departure and timeout tests retain the binding and send a fresh probe after rediscovery. Both carry MFCONN-03 and MFRECOVERY-01. The unchanged review probes p7, p8 and p9 each fail tests tagged with the affected requirement; their baseline passes.

NFR-SEC-01 is now an entity configuration port obligation. The source gate checks every pinned ID anchor and catches the moved-anchor control. The Unreleased entry and generated tables are current.

All 25 `validate.py --graphs` gates pass, rc 0. `baremetal.py` passes Debug and Release, rc 0. All 324 mutation plants are caught. Coverage remains 100% after unchanged exclusions. Post-commit privacy passes. Production source and headers match the original base.

HANDOFF.md and PR-BODY.md contain Round 2 sections, the complete source mapping, test-defect mapping, both-target gate results and the exact validation gate count. The evidence packet records the initial missing-runtime link failure and the complete successful rerun. The worktree is clean. The manager can push this head and update [PR #18](https://github.com/kebag-logic/tsn-c-stack/pull/18).

