# ACMP publish port handoff

Status: REVIEW READY for the assigned branch, with the sanitizer leg pending hosted CI under the acceptance amendment. The final status comment is linked under Delivery.

Branch/head: `acmp-publish-port` at `2dcbe91ead981591d5bfb652f6616f6edb325875`.
Parent/base: `1a9f651cdf7846b8e10ac246a6ef6916960fbb92`.
Reference dev: `09c7231eca343607c97c0d66abebb2553688712c`.
Reference parent before F-INT: `0a62616e08dd58928e73183ecdf16dbee330becd`.
Source commits read: `5a50b2045427313527197eb22cd0f8276ef4b015` and `7c583daace3a459bcf462deaf58acefee21cd41b`.

The [issue body](https://github.com/kebag-logic/tsn-c-stack/issues/21), [assignment](https://github.com/kebag-logic/tsn-c-stack/issues/21#issuecomment-6115109360) and [amendment](https://github.com/kebag-logic/tsn-c-stack/issues/21#issuecomment-6115181911) were read in full. The amendment permits comment rewrites, requires identity after comment stripping and an RV32 object comparison, and assigns the reproduced sanitizer host limit to the hosted job. The previous STOP is superseded by this completed port. TAKEN was not repeated.

One atomic implementation commit was made after its tests and applicable local gates passed, with the configured identity and a one-line subject. Post-commit privacy passes. The branch and reference checkout are clean. No other core file, reference repository file, remote branch, issue body, existing comment, repository setting or visibility was changed. No push or PR was made. There was no hardware or bench access.

## Change map

Locations below are at the final head. The only production core changes are in the two ACMP files.

| File:line | Change and purpose |
|---|---|
| `src/acmp.c:188` | Guarded `p_publish` callback and changed-triple walk at line 197, copied from the pinned reference. |
| `src/acmp.c:285` | Publish before a new frame is sent or queued. |
| `src/acmp.c:486` | Publish first in `finish`, before timer, admission, persistence and notification calls. |
| `src/acmp.c:514` | Preserve all three publication-cache fields across `sink_reset`. |
| `include/acmp.h:307` | Required `acmp_ports.publish` callback with bound, started, stream ID and stream-moved arguments. |
| `include/acmp.h:362` | Add `published_bound`, `published_started` and `published_stream` in the reference's field order. |
| `tests/acmp_fake.hpp:107` | Record publication identity, values and position relative to other callbacks; clear the log at line 150; provide the guarded-callback stimulus at line 228. |
| `tests/test_acmp.cpp:2045` | Import publication ordering helpers and six A31 cases, with source comments expressed as requirement IDs. Test bodies retain the reference's assertions. |
| `examples/rv32/smoke.c:141` | Supply the required publication port; record applied state and check it during BIND/UNBIND response sends. Extend restore/open/reset, stream settlement and START/STOP smoke at line 174. |
| `docs/PORTING.md:170` | Callback signature, changed-triple semantics, synchronous application, ordering, restore/open behavior, zero initialization and cache ownership; detailed contract at line 178, cache fields at line 266. |
| `docs/ARCHITECTURE.md:55` | Explain publication before frames and completion callbacks. |
| `docs/requirements.json:177`, `docs/REQUIREMENTS.md:33` | ACMP-10 and its local ordering contract, with protocol clause references. |
| `docs/TRACEABILITY.md:24`, `docs/TESTS.md:62` | Regenerated requirement-to-test and test-to-defect mappings. |
| `tests/mutations.json:5009` | Fourteen local publication plants, graded by named assertion messages. No reference mutation script was imported. |
| `tests/coverage.ratchet:5` | ACMP grows from 742 to 767 covered lines and from 348 to 362 covered branches, with no added exclusions. |
| `scripts/check_port_contracts.py:115` | Require the new callback and fields and protect six critical ordering phrases at line 264 through removal controls. |
| `docs/VERIFICATION.md:23` | Update the campaign count to 338 and describe the extended RV32 publication smoke. |

## Source identity and every residual byte difference

[ported-reference.diff](ported-reference.diff) is the complete byte-preserving unified diff from reference dev's ACMP source/header to the delivered files. [baseline-layout.diff](baseline-layout.diff) is the same raw-byte comparison from the pre-F-INT reference parent to the assigned baseline. Neither normalizes whitespace or comments. [identity-summary.json](identity-summary.json) records SHA-256 and sizes of all four file versions, plus every inserted line span. Removing those insertions reconstructs both baseline files byte for byte: none of the baseline bytes was modified or deleted.

The original #697 scratch comparison, `$VALIDATION_STORAGE/697c-a583/scripts/tokens.py`, was read and run unchanged with `--ignore-lines`. It uses compiler raw tokens, excludes comments and whitespace, and compares token kind and spelling. Its SHA-256 is `1ec77acbee6d3d8ca4c53bda594a7b87376a191301e5ece9338427dabd7745c5`. Both comparisons return 0: source **7849/7849 tokens**, header **1175/1175 tokens**, with **zero residual code tokens**. [token-comparison.log](token-comparison.log) records the run.

An independent Clang 18 raw-token pass also proves that the pre-F-INT reference and baseline have identical code tokens, and that the final reference and delivered files have identical code tokens. It enumerates every differing interval between those tokens in [residuals.json](residuals.json), including its exact byte strings, byte offsets and line numbers. [token-proof.json](token-proof.json) summarizes it. For **197 intervals** (95 in the source, 102 in the header), both sides are exactly their pre-F-INT/baseline byte strings, with the old offsets and lines recorded. These residuals are all pre-existing. There are **nine comment/adjacent-whitespace intervals** affected by the authorized F-INT insertion or comment rewriting:

| Delivered file:line / reference line | Cause and preserved meaning |
|---|---|
| `src/acmp.c:1` / 1 | F-INT added publication ordering to the reference's existing introductory prose. The baseline licence and tracing preamble remain byte-identical; ordering is documented in PORTING and ARCHITECTURE. |
| `src/acmp.c:184` / 186 | The inherited blank separator before the wire code remains at the insertion boundary before `p_publish`. |
| `src/acmp.c:194` / 194 | The new changed-triple prose becomes `REQ: ACMP-10`; its full meaning is in the API guide. |
| `src/acmp.c:211` / 212 | The inherited reference wire-section prose is still absent; insertion leaves a blank separator before `decode`. Together with the earlier separator, these account for the adjacent whitespace. |
| `src/acmp.c:481` / 484 | F-INT expanded the reference's finish-order prose; the baseline blank lines remain, with the full order in the guide. |
| `src/acmp.c:504` / 508 | F-INT expanded reset-cache prose to include publication; the baseline Milan clause reference remains unchanged and the cache contract is documented. |
| `include/acmp.h:1` / 1 | The new introductory published-before-promised block is relocated to API documentation. All baseline licence, tracing and blank bytes remain. |
| `include/acmp.h:305` / 323 | New callback prose becomes `REQ: ACMP-10`; the guide gives every argument, call order and startup obligation. |
| `include/acmp.h:360` / 383 | New cache prose becomes `REQ: ACMP-10`; the storage table states cache ownership and reset preservation. |

The nine intervals contain only comments and whitespace, checked by the lexer. Their exact contents and old content where applicable are in the residual ledger. They are explicitly the amendment's exception, not falsely described as pre-existing new prose. There is no additional executable-token exception, layout-field reorder, semantic adjustment or other-core change. The original byte-identity wording alone is not claimed satisfied.

## Equal RV32 objects

Both original file copies, including their own ACMP and wire headers, were built in scratch with the same flags and identical relative filenames. Only compiler intrinsic headers and the repository's minimal C-library headers were available. [rv32-object-identity.json](rv32-object-identity.json) records the exact flags, hashes and sizes.

| Configuration | Both objects' bytes | Both objects' SHA-256 |
|---|---:|---|
| RV32I/ILP32, C11, freestanding, O0, re-entry hook, `-g0` | 36176 | `43c1af51bdbf0cad4cab65a557d4eb75619eeebbbe6dc5754f5f87002ee673e7` |
| Same, O3 and NDEBUG | 30684 | `5e2bacf24eeb2268e4d11f5ac6221d35cb2d2d61c60a4f0fa19a50d7d19cd423` |

The equality comparison deliberately uses `-g0` on both copies so paths and moved comment line numbers do not enter DWARF. O0 retains debug behavior and the re-entry hook. The separate mandatory Debug gate uses its normal `-g`, links the full core archive and executes smoke; its ELF is not asserted equal to the reference firmware. The Release ACMP object's hash also equals the mandatory RV32 Release build's object. No linked firmware image or physical timing equivalence is claimed.

## Ported tests and defects

All six reference A31 cases are registered and pass. Their test bodies and helper expressions have the reference's code tokens; adaptations remove prose comments and add requirement annotations. The fake adds publication logging separately from the existing callback log so prior callback-budget assertions keep their original meaning.

| Test, delivered source location | Defect caught |
|---|---|
| `A31TheBindingIsPublishedBeforeTheResponseThatPromisesIt`, `tests/test_acmp.cpp:2052` | Missing or wrong binding/start/stream publication; response before publication; missing settlement or withdrawal; stale publication caches; duplicate GET/unbind publication. |
| `A31LeavingSettlementTakesTheStreamOffTheDatapath`, `tests/test_acmp.cpp:2085` | Retained old stream after rebind, reservation timeout or unregister; wrong sink/interface identity. |
| `A31OnlyAMovedTripleIsPublished`, `tests/test_acmp.cpp:2107` | Redundant publication when bound, started and stream ID did not change. |
| `A31TheStartedLevelIsPublishedBeforeItIsPromised`, `tests/test_acmp.cpp:2122` | Lost STREAMING_WAIT or START/STOP level; publication after response/notification; false stream-moved flag; redundant stopped publication. |
| `A31RestoredBindingsArePublishedWhenTheTransportOpens`, `tests/test_acmp.cpp:2157` | Premature boot publication, omitted open publication, lost restored started level, duplicate open, publication of rolled-back bindings, reset of the publication cache. |
| `A31ACallBackFromThePublishPortIsRefused`, `tests/test_acmp.cpp:2194` | Unguarded synchronous UNBIND or poll from the publish callback, rather than refusal and re-entry accounting. |

Fourteen new plants cover callback guard, transmit order, finish publication, change detection, complete cache reset, stream zeroing, stream-moved flag, interface, sink, started argument and each stale cache field. Every plant is caught by its named assertion, with no compilation errors, crashes or unrelated assertions counted as catches. Existing 324 plants also pass, for 338 total. The first exploratory run found two wrong killer selections and an insufficient cache-reset plant; those definitions were corrected, not relaxed. The final campaign has 338 CAUGHT, 0 ESCAPED, 0 ERROR.

The RV32 smoke checks exercise restore silence, publication before admission on open, quiet rollback followed by withdrawal, duplicate-open suppression, STREAMING_WAIT publication before the BIND response, full-width stream settlement and moved flag, START/STOP completion publication, redundant-stop suppression, and withdrawal before the UNBIND response. They run in both Debug and Release. The hosted campaign additionally checks re-entry and all original transition cases.

## Clauses reviewed

The supplied PDFs were used to check Milan v1.2 5.3.8.7 (started/stopped), 5.5.3.5.18 step 4 (settlement), 5.5.3.5.36 step 1 (withdrawal), and IEEE 1722.1-2021 7.4.35 and 7.4.36 (START/STOP). The callback and publication ordering are the assigned local integration contract supporting these behaviors. Standards text is not reproduced.

## Gate table

[linux-gates.json](linux-gates.json) and [rv32-results.json](rv32-results.json) are the final runner outputs. Each underlying command kept its own log and actual rc; commands were not piped. The hosted aggregate returns **1 solely because the accepted local sanitizer build returns 2**. It is not reported as an all-zero run. The RV32 aggregate returns **0**.

| Gate | Linux hosted | Bare-metal RV32 |
|---|---|---|
| Boundary and forbidden-dependency controls | 0 | Debug/Release dependency and symbol allowlists: 0 |
| Assertion needles and controls | 0 | Shared source contract |
| Assertion diagnostic templates and controls | 0 | Shared source contract |
| Dependency pin controls | 0 | No hosted test library linked |
| Comment contract and compiling controls | 0 | Includes RV32 assembly/link controls |
| Conditional matrix and controls | 0 | Shared C/C++/macro matrix plus both target builds |
| Port contract names and meaning-removal controls | 0 | Same callback contract |
| Registration controls | 0 | Hosted inventory |
| Licence | 0 | Same source check |
| Traceability selftest | 0; 43 requirements | Both target obligations retained |
| Test inventory | 0; 117 declarations, 378 executable instances | Focused smoke subset, not the hosted denominator |
| Coverage controls | 0 | Hosted controls |
| Privacy selftest / pre-commit scan / post-commit scan | 0 / 0 / 0 | Same tree/history |
| GCC configure / build / tests | 0 / 0 / 0; seven binaries | Not the target compiler |
| Coverage | 0; every adjusted line/branch 100%; ACMP 767/767 and 362/362 | No RV32 coverage claim |
| Clang sanitizer configure / build / tests | 0 / **2 host limit** / not run | Not applicable |
| Static analysis | 0 with clang-tidy 18.1.3 | Same production sources and minimal port |
| Mutation campaign | 0; all 338 plants | Hosted campaign only |
| Mutation report controls | 0 | Hosted controls |
| Graphs | 0 | Shared documentation |
| Target configure / compile / link / smoke | Hosted checks above | 0 for Debug and Release |
| ELF machine, ABI, full archive and unresolved-symbol checks | Not applicable | 0; RV32I/ILP32, zero unresolved final symbols |
| Reference non-comment token comparison | 0; source and header equal | Same code |
| Reference object byte comparison | Cross-build evidence | 0 for both O0/no-DWARF and O3/NDEBUG |

All final checks use the committed source bytes. The only check repeated after committing was the privacy/history gate, because the new commit changed that gate's input. No source changes followed validation.

### Host environment and limits

The baseline at `1a9f651c` already failed its Clang 18 sanitizer build against GCC 16 C++ headers. The final run reproduces incomplete `__normal_iterator` access and missing `__builtin_popcountg`, among related system-header errors. The original excerpt is [clang-baseline-build-excerpt.log](clang-baseline-build-excerpt.log); the complete final build log's hash and size are in the evidence manifests. The [amendment](https://github.com/kebag-logic/tsn-c-stack/issues/21#issuecomment-6115181911) makes hosted CI after publication the judge of this leg. No sanitizer runtime pass is claimed.

The supplied `clang-18` launcher refers to removed scratch files. `TSN_CLANG` selects the intact 18.1.3 executable under the supplied prefix, whose binary directory follows the required prefix on PATH. Matching shared libraries are included after the pinned test-library directory. GoogleTest/GMock remain 1.14.0. The host's clang-tidy 23 diagnosed padding in the required imported field order; the CI-generation clang-tidy 18.1.3 passes the unchanged analysis gate. The official Ubuntu package was extracted only in scratch, with its resource directory linked to the supplied Clang 18 headers. Its archive and executable hashes are recorded; no source reordering or new suppression was introduced.

Independent work ran concurrently with `--jobs 16` and `-j16`. The service cgroup's measured peak was 7900766208 bytes, below 9 GB and the 12 GB service cap. Builds, packages, logs and exports remain on disk under the assigned scratch. No work depends on a background job surviving this session.

## Main integration and acceptance status

Items 1, amended 2, 3 and 5 are implemented. The assigned branch's entire validation suite is run; item 4's local sanitizer exception is recorded and still requires hosted CI. The branch intentionally excludes main's later #19/#20 core changes. Main-only entity generation files and their gates do not exist at this pin and are not claimed tested by this branch's runner. The manager must validate the eventual main merge and resolve its ACMP example initializers, including main's `examples/entity_roundtrip.c`, to supply the required callback. This handoff does not represent the future merge result as tested.

Item 6 remains the manager's publication, PR, two reviews and merge-commit work. Consequently PR-BODY.md says **Relates to #21**, not Closes. Existing ACMP clients must supply the new callback, apply its state before returning, and initialize their publication storage as the guide specifies.

## Reproduction and artifacts

Scratch root: `$VALIDATION_STORAGE/tsn21-a602/`. The reference checkout is its `milan-fpga/` child, still clean at the pin. `env.sh` records the working pinned environment. `run-verified.sh` contains the unpiped runner commands and preserves each aggregate rc. The retained final work trees are `verified-linux/`, `verified-rv32/` and `object-identity/`. `prove-residuals.py` reproduces the exact byte-interval ledger with the repository's Clang 18 lexer. The earlier STOP packet is retained under `previous-output/`, with its earlier handoff in `round1-HANDOFF.md`.

From the branch, with the pinned dependencies available:

```sh
python3 scripts/validate.py --work build-validation --jobs 16 --graphs
python3 scripts/baremetal.py --work build-rv32 --jobs 16
```

On a hosted environment with compatible sanitizer headers, every leg must return zero. On this host, retain the actual sanitizer failure for comparison with the accepted baseline rather than rewriting its status.

`evidence-manifest-*.json` records SHA-256 and size for 800 final logs, results, mutation XML reports, test binaries, target images, objects, comparison scripts and the additional analyzer package. These files remain in scratch. No tree export, installed package, toolchain, environment or file over 200000 bytes is in this output directory. `output-manifest.json` inventories the small delivery files.

## Delivery

TAKEN (previous round): https://github.com/kebag-logic/tsn-c-stack/issues/21#issuecomment-6115119208

Final head: `2dcbe91ead981591d5bfb652f6616f6edb325875`.
Final status comment: https://github.com/kebag-logic/tsn-c-stack/issues/21#issuecomment-6115338952
