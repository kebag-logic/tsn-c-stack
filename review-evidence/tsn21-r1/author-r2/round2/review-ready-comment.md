[A602] REVIEW READY — `f3dc2ae5bad02aa05a504b43c207e8b304d2bed5` on `acmp-publish-port`.

Round 2 addresses F-1, F-2 and F-3(a): two named regression assertions and plants; explicit ACMP-10 provenance from issue #21 and F-INT; upstream-aligned blank comment lines. The core remains token-identical, including code-line positions. All six unchanged reviewer object comparisons report raw EQUAL, including `-g` and `-Os -g3`.

All 25 Linux gates and RV32 Debug/Release pass with rc 0. Local Clang 18 sanitizer execution now passes with compatible C++ headers and matching runtime archives. Coverage remains 100% after the existing exclusions; all 340 plants are caught, with zero escapes or errors. The unchanged reviewer probes and witnesses catch both required faults through the new named repository assertions. Post-commit privacy passes.

HANDOFF.md and PR-BODY.md include Round 2 evidence and every object-comparison flag. New commit only; both checkouts are clean. No push performed. The manager owns publication, hosted acceptance and the remaining review/merge work.

Posted: https://github.com/kebag-logic/tsn-c-stack/issues/21#issuecomment-6115656360
