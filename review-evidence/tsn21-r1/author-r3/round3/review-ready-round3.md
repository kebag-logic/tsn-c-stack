[A602] REVIEW READY — `acmp-publish-port` @ `bc68ad8f3577e8f3dc24c4336e9b80a933df6c79`, parent `f3dc2ae5bad02aa05a504b43c207e8b304d2bed5`.

Round 3 gives each publication-cache field its own hosted assertion and restore-only plant. The new mandatory completeness gate discovers fields from the header; 30 negative controls reject missing or shared coverage, including a future field. The core files are byte-unchanged from Round 2, with token positions preserved and all six RV32 object comparisons raw-equal.

All 26 Linux gates and RV32 Debug/Release return 0: 382 hosted instances, adjusted 100% coverage, sanitizers, and 342 CAUGHT / 0 ESCAPED / 0 ERROR. Each individual cache fault is caught by its hosted assertion.

The exact-head reviewer witnesses and RV32 controls were rerun. Both formerly escaped hosted faults now fail their new repository assertions. The original probes script has one ambiguous RSV_OK replacement; a disclosed scratch-only correction uses the witness script’s precise context, and all seven probes are then caught. The head controls pass. HANDOFF.md and PR-BODY.md contain the Round 3 evidence and limitation. Peak service memory stayed below 5.4 GB.

One new commit; branch clean and unpushed. Manager publication, hosted acceptance and independent reviews remain pending. PR-BODY.md retains Relates to #21.
