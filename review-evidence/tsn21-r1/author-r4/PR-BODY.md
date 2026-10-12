[A602]

Relates to #21

Carry F-INT's ACMP publish callback from `09c7231eca343607c97c0d66abebb2553688712c`. Publish bound, started and settled stream-ID changes before new frames and first at entry completion. Preserve the publication cache across reset and reject callback re-entry. The API guide specifies synchronous state application and the published-before-promised ordering contract.

Port the six upstream cases and fake, with independent cache-loss assertions, publication-order plants, freestanding smoke checks and requirement provenance. The branch retains the `1a9f651cdf7846b8e10ac246a6ef6916960fbb92` lineage. Its ACMP source and header preserve F-INT's code tokens and their line and column positions; six raw freestanding object comparisons are byte-equal.

## Round 4

Address R623-4-F1 by comparing assertion identities: the owning test and the assertion definition's file, line and column, including helper and callback traversal. Different streamed operands on one assertion cannot satisfy two cache fields. Keep the literal inventory used to grade mutation failures.

Add the compiling future-field counterexample as a mandatory negative control. It fails specifically for shared assertion ownership, including with optimized execution. Its separate-assertion counterpart passes. Both control campaigns compile and catch every selected plant. Direct, helper and nested callback controls also distinguish shared definitions from separate assertions on one line.

The unchanged review probe confirms the shared-ownership rejection, a passing needle audit and five caught hosted plants. The production core files remain byte-unchanged from the preceding revision.

At `405dc68310a18f669049ffc10cc23eef7300dcff`, all 26 Linux gates and both freestanding RV32 configurations pass. The hosted suite has 382 instances, adjusted coverage is 100% in each ratcheted file, and all 342 mutations are caught with zero escapes or errors. Sanitizer and leak checks pass. Run with the pinned dependencies:

```sh
python3 scripts/validate.py --work build-validation --jobs 16 --graphs
python3 scripts/baremetal.py --work build-rv32 --jobs 16
```

A separate `integrate-21` branch starts at main `98dc9e3076714bebe113982ee18c3c1c496cf3c9` and merges this branch at `3c9ca52fc44b4a37e11149392363686f0ea426e0`, retaining the ADP receive validation and entity configuration work. The manager owns publication, independent review, final merge and the consumer pin update. Emulator smoke does not establish physical timing.
