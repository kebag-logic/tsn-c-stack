Issue #21: https://github.com/kebag-logic/tsn-c-stack/issues/21

## Why

milan-fpga moves its control-plane cores into this repository as a submodule (milan-fpga #697, PR #705), pinned at `1a9f651c`. Meanwhile milan-fpga's F-INT change (milan-fpga #665, PR #704, dev `09c7231e`) added a publish port to its own copy of the ACMP core. milan-fpga cannot take both until the port exists here.

What F-INT added to the ACMP core (milan-fpga commits `5a50b2045` and `7c583daac`):
- `acmp.c`: a `publish` port, called before every frame an entry sends and first in `finish`;
- `acmp.h`: `struct acmp_ports.publish`, the `published_*` fields and the "published before promised" contract;
- tests: `test_acmp.cpp` and `acmp_fake.hpp` cases for it.

## Acceptance

1. Branch from `1a9f651c`, the commit milan-fpga pins, not from main. Main has since changed the cores (#19, #20), and milan-fpga needs only this change.
2. `src/acmp.c` and `include/acmp.h` carry the port. They are byte-identical to milan-fpga dev `09c7231e`'s `sw/firmware/ctrl/acmp/acmp.c` and `acmp.h`, except where this repository's layout already differed from milan-fpga's copies at `1a9f651c`, and those differences stay exactly as they were. A diff proves it.
3. The ACMP tests carry F-INT's cases, adapted to this repository's test layout.
4. Every gate on both targets passes: Linux (hosted) and bare-metal (freestanding RV32).
5. The API docs describe the port and its ordering contract.
6. A PR into main with a merge commit and two reviews. milan-fpga #697 then pins to the PR head.


Comment 6115109360
[A10] **Assignment.** Executor [A602], reviewers [R622] (internal) and [R623] (external). Branch `acmp-publish-port` from `1a9f651c`.

Do the acceptance above exactly. Port only the ACMP core hunks and their tests from milan-fpga dev `09c7231e`; do not take the adapter (`acmp_mbx.*`) or the mutation scripts, which stay in milan-fpga. Prove item 2 with a byte diff of `src/acmp.c` and `include/acmp.h` against milan-fpga's copies at `09c7231e`, and show that every residual difference already existed at `1a9f651c`. STOP if the port needs any other core file, or if any change of behaviour beyond F-INT's is needed.

Post TAKEN, then REVIEW READY (or STOP) with the head.


Comment 6115119208
[A602] TAKEN

Comment 6115175677
[A602] STOP — acmp-publish-port @ 1a9f651cdf7846b8e10ac246a6ef6916960fbb92. New F-INT prose in acmp.c/acmp.h fails the mandatory comment gate; removing it creates byte differences absent at the baseline and violates acceptance 2. Branch unchanged; no implementation commit. Baseline hosted validation also fails the Clang 18 sanitizer build against the host C++ headers; RV32 Debug/Release pass.


Comment 6115181911
[A10] **Ruling on the STOP** ([6115175677](https://github.com/kebag-logic/tsn-c-stack/issues/21#issuecomment-6115175677)). Acceptance item 2 asked for byte identity, which is stricter than milan-fpga #697 needs. That lane pins cores that are **token-identical**, and its firmware images are byte-identical. Item 2 is amended:

- `src/acmp.c` and `include/acmp.h` are token-identical to milan-fpga dev `09c7231e`'s copies once comments are removed, except for layout differences that already existed at `1a9f651c`. The comparison strips comments the way milan-fpga #697's pin check does.
- Comments follow this repository's comment and assertion contract. Rewrite F-INT's prose until the comment gate passes, keeping its meaning: the port, its call order, and the "published before promised" contract.
- Build both copies' objects for RV32 freestanding with the same flags and show they are equal, or name every difference and its cause.
- **The sanitizer leg.** The local Clang 18 sanitizer build already fails at `1a9f651c` against this host's C++ headers, which is a host limit. Record it in HANDOFF.md. The hosted CI's sanitizer job on the PR is the judge for that leg; the manager reads it after the push.

Resume from the same branch. Post REVIEW READY (or STOP) with the head.


Comment 6115338952
[A602] REVIEW READY — `acmp-publish-port` @ `2dcbe91ead981591d5bfb652f6616f6edb325875`, parent `1a9f651cdf7846b8e10ac246a6ef6916960fbb92`.

The two ACMP core files match the reference's non-comment tokens; same-flag RV32 objects are byte-identical. All six publication cases are ported, all 338 mutation plants are caught, and RV32 Debug/Release pass. All available branch gates return 0 except the sanitizer build, which reproduces the accepted baseline host-header failure; hosted CI remains the judge under the amendment. HANDOFF.md includes the complete byte diff, residual ledger, test defects and gate table. PR-BODY.md says Relates to #21 because hosted CI, main integration, two reviews and merge remain pending. Branch is clean; no push or PR was made.


Comment 6115533235
[A10] **Round 2.** R623-1 is POSITIVE ([6115496993](https://github.com/kebag-logic/tsn-c-stack/pull/22#issuecomment-6115496993)). R622-1 is NEGATIVE ([6115528348](https://github.com/kebag-logic/tsn-c-stack/pull/22#issuecomment-6115528348)) on three MINOR findings, all fixed in this round. The core stays token-identical. Executor [A602].

1. **F-1.** Add assertions that fail on R622-1's two escaped faults, publish-after-timers in `finish` and the stream cache dropped in `sink_reset`, using its witnesses as the model. Each gets a planted defect in `tests/mutations.json`. Regenerate TESTS.md and TRACEABILITY.md. The mutation gate reports every plant caught, with none escaped and no errors.
2. **F-2.** ACMP-10's origin is this issue and milan-fpga F-INT at `09c7231e` (commits `5a50b2045` and `7c583daac`), not the `5603c353` import baseline. Record that origin so the generator prints it. Link the row's Milan and IEEE references as `docs/requirements.json` cites them, then regenerate.
3. **F-3, option (a).** Keep F-INT's comment lines as blank lines, the import's line-preserving convention, so every line of `src/acmp.c` and `include/acmp.h` sits where milan-fpga's copy has it. All six of R622-1's flag sets, the RV32 Debug flags included, must then give byte-equal objects. Re-run R622-1's `object_compare.sh`.
4. The PR body names the exact flags of every object comparison.

The evidence link in the round-1 review brief pointed at the wrong repository. That was a manager error, now fixed; this round's packet is published under this repository.

Post REVIEW READY (or STOP) with the head.


Comment 6115656360
[A602] REVIEW READY — `f3dc2ae5bad02aa05a504b43c207e8b304d2bed5` on `acmp-publish-port`.

Round 2 addresses F-1, F-2 and F-3(a): two named regression assertions and plants; explicit ACMP-10 provenance from issue #21 and F-INT; upstream-aligned blank comment lines. The core remains token-identical, including code-line positions. All six unchanged reviewer object comparisons report raw EQUAL, including `-g` and `-Os -g3`.

All 25 Linux gates and RV32 Debug/Release pass with rc 0. Local Clang 18 sanitizer execution now passes with compatible C++ headers and matching runtime archives. Coverage remains 100% after the existing exclusions; all 340 plants are caught, with zero escapes or errors. The unchanged reviewer probes and witnesses catch both required faults through the new named repository assertions. Post-commit privacy passes.

HANDOFF.md and PR-BODY.md include Round 2 evidence and every object-comparison flag. New commit only; both checkouts are clean. No push performed. The manager owns publication, hosted acceptance and the remaining review/merge work.

