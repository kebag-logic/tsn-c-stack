[R623] NEGATIVE - exact head f3dc2ae5bad02aa05a504b43c207e8b304d2bed5

External independent delta review, round R623-3, issue #21 / PR #22. Tree: `d4ec359c00b7b34070e2b01d297607327260550a`. Compared the assigned source base `1a9f651cdf7846b8e10ac246a6ef6916960fbb92` through this head, including the round-2 delta from `2dcbe91ead981591d5bfb652f6616f6edb325875`.

The requested round-2 fixes pass their focused checks. One MINOR test-sensitivity finding remains: independent omissions of the bound and started cache restores escape the hosted ACMP suite. Production code at this head preserves both fields correctly. This verdict concerns the missing regression protection and the published acceptance contract.

Process and authority

Read the supplied instruction reference, repository CONTRIBUTING.md, README and verification/coding guides; reconstructed the issue body and public scope decisions; read requirements, port and architecture authorities; examined the complete base-to-head diff and both commits; then examined public executable evidence. This verdict and the ledger below were written before fetching any PR comments or review submissions. No other reviewer report was read. Public issue manager comments were part of the required scope reconstruction, including the later per-field ruling; the cache witnesses below were written independently.

Authorities: [issue acceptance](https://github.com/kebag-logic/tsn-c-stack/issues/21), [token-identity amendment](https://github.com/kebag-logic/tsn-c-stack/issues/21#issuecomment-6115181911), [round-2 scope](https://github.com/kebag-logic/tsn-c-stack/issues/21#issuecomment-6115533235), [subsequent per-field scope](https://github.com/kebag-logic/tsn-c-stack/issues/21#issuecomment-6115822525), `CONTRIBUTING.md:22`, `docs/REQUIREMENTS.md:47`, and `docs/PORTING.md:198`. Saved issue receipts distinguish the original acceptance from its amendments.

Finding R623-3-F-1

- Severity: MINOR. Attributable lenses: Conformance, Robustness, Tests.
- Locations: `src/acmp.c:524` and `src/acmp.c:525` are the independently mutated restore assignments; the coverage gap is in `tests/test_acmp.cpp:2157` and `tests/mutations.json:5069`. The stream-specific addition is at `tests/test_acmp.cpp:2218` / `tests/mutations.json:5234`.
- Evidence: `receipts/cache-probes/summary.json` and the corresponding stock/witness XML and logs. Replacing only `s->published_bound = published_bound;` with `(void)published_bound;` passes all 77 stock ACMP tests. Replacing only the started restore likewise passes all 77. Every compile and link succeeds. The reviewer witness suite runs 80 tests: unchanged head passes; each of those two plants fails its own named witness. The single-field stream plant is caught by the repository's new stream assertion, as required in round 2. All 340 listed plants are caught, but no listed plant isolates either missing bound or started restore; the existing whole-cache plant cannot establish individual-field sensitivity. The inventory gate counts tests and named plants, not preservation coverage for every cache field.
- Impact: with the started restore omitted, restoring a started binding as stopped can leave the publication receiver started because `acmp_open` emits no update. With the bound restore omitted, restoring a stopped bound sink as empty can leave the receiver bound. The current implementation avoids these faults; the stock hosted suite does not detect these particular regressions. RV32 controls catch the bound omission but pass the started and stream omissions, so bare-metal smoke cannot replace hosted field-specific checks.
- Required outcome: give each cache field (`published_bound`, `published_started`, `published_stream`) a hosted named assertion and a plant that drops only that field's restore. Add the manager-required check that refuses a cache field with no individual assertion/plant, including a subsequently introduced field. Regenerate TESTS.md and TRACEABILITY.md. Preserve core tokens and line positions.
- Verification: the unmodified suite must pass; each isolated field omission must fail its named hosted assertion; a missing field mapping must fail the completeness check; the complete mutation gate must report no escapes or errors; the six object pairs must remain byte-equal. `scripts/cache_probes.py` contains portable witnesses for all three existing fields. No source fix was made.

Independent checks

| Check | Result and artifact |
|---|---|
| F-1, publication after timers | `AcmpCore.A31SettlementIsPublishedBeforeTheTimerPort` fails with its required needle on `acmp-publish-after-timers`; local campaign XML and public author XML agree. |
| F-1, dropped stream cache | `AcmpCore.A31StoreResetOfASettledSinkPublishesAMovedStream` fails with its required needle on `acmp-publish-reset-stream-cache`; the independent isolated stream control also fails that test. |
| Complete mutation campaign | Local and exact-head hosted receipts each report 340 CAUGHT, 0 ESCAPED, 0 ERROR. These totals cover the listed plants only. |
| F-2 provenance | REQUIREMENTS.md explicitly identifies issue #21, F-INT at `09c7231e` and both F-INT commits. `requirements.json` and generated TRACEABILITY.md carry the same origin, with linked Milan/IEEE references. Local traceability selftest passes, including missing/false/broken addition-origin controls. |
| F-3 core identity | Non-comment lines match the public upstream reference exactly: 1,294 source lines and 494 header lines. Round-2 core changes are blank-line placement only. `receipts/final-integrity.json`. |
| F-3 objects | Re-ran the unchanged public R622-1 `object_compare.sh`; all six raw pairs EQUAL, including debug information. `receipts/local/objects.log`. The PR body lists the common and additional flags. |
| Upstream cases | All six F-INT test bodies match the public upstream bodies byte-for-byte; fake callback collection and re-entry behavior are ported into this repository's fixture. |
| Local portable gates | Mutation baseline executes all seven test binaries; port-contract selftest, traceability selftest, inventory, assertion-needle selftest and comments pass. RV32 Debug and Release pass. `receipts/local/campaigns.json`. |
| Exact-head hosted execution | Run `38188571695`, push event, explicitly reports head `f3dc2ae5bad02aa05a504b43c207e8b304d2bed5`; quality and bare-metal jobs execute and succeed, with no skipped steps in either job. All 25 quality gates return zero; GCC and sanitizer test logs each pass seven binaries; RV32 artifact contains successful Debug and Release results. `receipts/hosted-exact-head.json` and `receipts/hosted/`. |
| Coverage | Hosted core coverage remains 100% after the existing exclusions; ACMP is 767/767 lines and 362/362 branches. This is structural coverage, not proof of independent cache-field sensitivity. |

Object comparisons used RV32 GCC 16.2.0, the same source directory for both sides, shared wire/minimal-port headers, and common flags `-Isrc -I"$PORT_INCLUDE" -march=rv32i -mabi=ilp32 -ffreestanding -fno-builtin -nostdinc -isystem "$BUILTIN_INCLUDE" -std=c11 -Wall -Wextra -Werror`. Each ends with `-c src/acmp.c -o "$OUTPUT"`.

| Comparison | Additional flags | Raw equality |
|---|---|---|
| debug-g0 | `-DCTRL_REENTRY_ASSERT -g0` | EQUAL |
| debug | `-DCTRL_REENTRY_ASSERT -g` | EQUAL |
| release | `-DCTRL_REENTRY_ASSERT -O3 -DNDEBUG` | EQUAL |
| os | `-DCTRL_REENTRY_ASSERT -Os` | EQUAL |
| o2-noassert | `-O2` | EQUAL |
| os-g3 | `-Os -g3` | EQUAL |

Reviewer-owned ledger

| Lens | CLEAN/UNCLEAN | Examined artifacts | Covering round | Exact head |
|---|---|---|---|---|
| Conformance | UNCLEAN | Issue acceptance/amendments; ACMP-10 provenance and linked clauses; full source delta; identity/object comparisons; required per-field protection is missing (R623-3-F-1). | R623-3 | f3dc2ae5bad02aa05a504b43c207e8b304d2bed5 |
| RTL | CLEAN | Complete 18-file delta and tracked-tree inventory contain no RTL, register map, adapter or gitlink change. README/PORTING preserve the synchronous callback boundary; RV32 whole-core linkage and upstream object equality support the portable interface review. No RTL execution or hardware conclusion. | R623-3 | f3dc2ae5bad02aa05a504b43c207e8b304d2bed5 |
| Robustness | UNCLEAN | `publish`, guarded `p_publish`, `transmit`, `finish`, reset/restore/open and queued retry paths; re-entry, duplicate suppression, settlement and stream withdrawal cases; isolated cache probes demonstrate missing regression detection (R623-3-F-1). | R623-3 | f3dc2ae5bad02aa05a504b43c207e8b304d2bed5 |
| Tests | UNCLEAN | Eight publication cases, six upstream bodies, fake, 340 plants, inventory/generator/grader changes, hosted artifacts, RV32 smoke and all three independent per-field probes. Bound/started plants escape the 77-test stock ACMP suite (R623-3-F-1). | R623-3 | f3dc2ae5bad02aa05a504b43c207e8b304d2bed5 |
| Docs | CLEAN | REQUIREMENTS.md, requirements.json, generated TRACEABILITY.md and TESTS.md, PORTING.md, ARCHITECTURE.md, VERIFICATION.md, CHANGELOG and PR body; provenance, required callback, ordering, reset cache and exact object flags agree with code and receipts. | R623-3 | f3dc2ae5bad02aa05a504b43c207e8b304d2bed5 |

Limits and pending manager duties

This is a source-head portable-core delta review. No manager source bank exists or is inferred at this head. Source execution evidence consists of public author receipts, exact-head hosted artifacts and the focused independent commands in this packet. Manager validation of the final current-dev integration candidate is a separate merge-turn duty, using source base `1a9f651cdf7846b8e10ac246a6ef6916960fbb92` and live parent dev `09c7231eca343607c97c0d66abebb2553688712c`; the manager must publish builder/native candidate receipts when available. Hosted/act acceptance remains with the manager. Two positive reviews, merge integration and the consumer pin update remain pending.

No parent, PP, gPTP, synthesis or builder banks; no container/act or hardware execution. Physical calibration NOT RUN. Field skips are not hardware proof. No physical latency, transport timing, full-device certification or final firmware-image identity claim is made. Standards references were checked for accurate linked provenance and local-contract attribution, not independently recertified against complete standards text. Local sanitizer execution was not repeated; exact-head hosted sanitizer execution was inspected.

All source modifications for faults are in disposable packet scratch trees. The isolated source clone is clean: all 76 tracked file blobs and modes equal HEAD; the index tree equals the expected tree; the repository contains no gitlinks or required submodules. Nothing was committed, pushed, posted or merged. The independent verdict/hash were preserved before the public reconciliation below.

Public finding reconciliation

PR comments and review submissions were fetched only after the independent verdict and ledger were saved, at the timestamp in `receipts/independent-verdict-record.json`. The filtered receipt retains manager bodies and finding IDs only. No other reviewer report or review body was displayed or used. Review identifiers below are reconciled against the issue manager's public scope descriptions and this review's own executable evidence.

| Prior public item | Disposition at this head | Independent basis |
|---|---|---|
| R622-1 F-1 | RESOLVED for its two specified faults; cache-preservation class remains OPEN under R623-3-F-1. | Both round-2 plants fail their named assertions; separate bound/started restore omissions escape. |
| R622-1 F-2 | RESOLVED. | Correct generated origin, REQUIREMENTS.md origin and linked clauses; metadata controls pass. |
| R622-1 F-3 | RESOLVED. | Line-preserving core match and six raw object pairs EQUAL; PR body states every flag set. |
| R622-2 F-1 / manager's per-field ruling | RETAINED as R623-3-F-1. | Independently reproduced the started omission and additionally the isolated bound omission in the hosted suite. |
| F-2/F-3 references in R622-2 and F-1/F-2/F-3 references in R623-2 | Reconciled as above: original timer/stream, provenance and object obligations RESOLVED; broader per-field class OPEN. | Finding IDs alone do not create a separate observed defect; scope is taken from the issue manager's descriptions, not unread review bodies. |
| R623-2 P-1 | Addressed by this fresh run; prior review remains historical. | Independent verdict and ledger were written before PR comment retrieval. Other reviewer reports were never read. |
| R623-1 positive at 2dcbe91e | No approval carried forward automatically. | This report supplies a fresh five-lens ledger for f3dc2ae5. |

The inspected PR manager comments record review starts; they do not provide a manager source bank. The issue's round-2 and subsequent per-field decisions are retained in `receipts/issue21-scope-comments.json`. Public author source-manifest hashes match all 76 exact-head tracked files. Downloaded author receipts and the unchanged object script match their pinned Git blobs; hosted archive digests match the API metadata (`receipts/public-evidence-audit.json`).

Publication and reproduction

`REPRODUCE.md` and `scripts/` provide foreground, joined execution with no more than 16 parallel build jobs. `MANIFEST.sha256` lists every publishable file other than itself and REPORT.md; scratch is excluded. Receipt path normalization changes only local directory prefixes and records original hashes. No assertion text, outcome, measurement or return code is changed. The preserved independent verdict and its hash are unchanged.

There are no RESIDUE or SUGGESTION findings. The open MINOR above determines the NEGATIVE verdict. The manager must obtain the required fixes and fresh positive reviews before merge acceptance.

R623-3 FINISHED
