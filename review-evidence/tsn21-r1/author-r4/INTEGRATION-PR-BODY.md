[A602]

Relates to #21

Merge port head `405dc68310a18f669049ffc10cc23eef7300dcff` into main from `98dc9e3076714bebe113982ee18c3c1c496cf3c9`, preserving the port head as an ancestor without merging main into the consumer's source branch.

Integration head: `3c9ca52fc44b4a37e11149392363686f0ea426e0`. Its first parent is the main revision above and its second parent is the port head.

The merge combines ACMP publication and its assertion-identity completeness check with main's ADP receive validation and entity configuration generation. Requirement-origin checks retain both local entity provenance and ACMP-10 provenance. The requirement tables, test inventory, traceability and coverage ratchet are regenerated. All mutation records are preserved, with the entity plants kept in their required final positions. The entity round-trip example supplies the new callback and checks publication after restore; both sets of freestanding smoke checks remain active.

All 28 Linux gates and both freestanding RV32 configurations pass. The hosted suite has 401 instances, all 196 entity selftests pass, adjusted coverage is 100% in every ratcheted file, and all 348 mutations are caught with zero escapes or errors. Sanitizer and leak checks pass. With the pinned dependencies:

```sh
python3 scripts/validate.py --work build-validation --jobs 16 --graphs
python3 scripts/baremetal.py --work build-rv32 --jobs 16
```

The manager owns publication, independent review, final merge and the consumer pin update.
