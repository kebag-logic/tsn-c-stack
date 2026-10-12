# Verification

For a tester, the Linux validation command is:

```sh
python3 scripts/validate.py --work build-validation --jobs 16 --graphs
python3 scripts/baremetal.py --work build-rv32 --jobs 16
```

It runs independent builds and campaigns concurrently.
Set the work directory on a disk with room for mutation binaries.
Temporary compiler and coverage files stay beneath that directory.
Each command writes its own log and return code. The final table is `gates.json`.
The runner clears external test filters and old coverage data.
No failing build, skipped test or empty test binary can establish a pass.

## Targets and commands

| Check | Command | Acceptance |
|---|---|---|
| Entity YAML | `python3 scripts/entity_yaml.py --examples --check` and `python3 scripts/entity_selftest.py --work build-entity-controls` | Schema refusals, exact golden bytes, version guard, planted drift, the AX7101 mapping and 13 registered mapper plants pass. [Round trips](ENTITY_YAML.md#validation-and-tests) execute on Linux and RV32. |
| GCC C11 and core tests | `cmake -S . -B build-gcc -DTSN_COVERAGE=ON -DCMAKE_BUILD_TYPE=Debug`, then `cmake --build build-gcc -j16` and `ctest --test-dir build-gcc --output-on-failure -j16` | All tests pass. Warnings fail. |
| Coverage | `python3 scripts/coverage.py build-gcc` | 100% lines and branches after exact exclusions. |
| Mutation | `python3 scripts/mutation.py --work build-mutations --jobs 16` | All 384 core plants and four generated configuration plants caught by their named assertions. |
| Sanitizers and Clang | `cmake -S . -B build-sanitize -DCMAKE_C_COMPILER=clang -DCMAKE_CXX_COMPILER=clang++ -DTSN_SANITIZERS=ON -DCMAKE_BUILD_TYPE=Debug`, then build and test as above | Address and undefined-behavior sanitizers pass. The full runner enables leak detection and stops on findings. |
| Static analysis | `python3 scripts/static_analysis.py` | No project findings after [listed suppressions](STATIC_ANALYSIS.md). |
| Boundary | `python3 scripts/check_boundary.py --selftest` | Compiler dependencies permit only C library and owned headers. Object symbols refuse heap and OS use. Ten forbidden controls compile and are refused with both compilers; two pass controls compile and pass. |
| Assertion needles | `python3 scripts/needle_audit.py --selftest` | Each needle has at least eight characters and identifies exactly one assertion message literal in its named test or helper. Substrings of the generated default diagnostics are refused. Other assertion forms are refused. |
| Assertion templates | `python3 scripts/assertion_templates.py --check --selftest --work build-assertion-templates` | Compile and run one failing instance of each of the 14 allowed forms with GoogleTest 1.14.0. Blank streamed messages and compare the generated default diagnostics. Compiling `EXPECT_NEAR`, `GTEST_ASSERT_LT`, `GTEST_FAIL` and token-pasted controls are refused. |
| Dependency pin | `python3 scripts/dependency_selftest.py --work build-dependency-controls --jobs 16` | Refuse a configure with only another package version. Compile and catch a header plant using the checked package flags, including a required header and link symbol, without ambient include or library paths. |
| Code comments | `python3 scripts/check_comments.py --selftest` | Every comment under the closed [contributor rules](CODING_STANDARD.md) is checked. Only SPDX, requirement IDs and short standard references pass. Each rule has a compiling control. |
| Conditional regions | `python3 scripts/check_conditionals.py --selftest --work build-conditionals --jobs 16` | Every permitted non-guard region compiles both sides. Every file-specific macro combination is compiled. Nested unreachable regions fail. |
| Port contracts | `python3 scripts/check_port_contracts.py --selftest` | Each relocated callback, field, precondition and counter name stays in its guide section. Critical phrases stay beside their contract names. Name and meaning removal controls fail. |
| ACMP cache preservation | `python3 scripts/check_acmp_cache.py --selftest --work build-acmp-cache-controls --jobs 16` | Every `published_*` field declared in `acmp_sink` has its own hosted assertion and a plant dropping only its restore in `sink_reset`. Missing and shared coverage controls fail, including a compiling future field with two streamed messages on one assertion. |
| Report controls | `python3 scripts/mutation_selftest.py --work build-report-controls --jobs 16` | Reject stale, partial, skipped and mismatched reports. A real catch followed by early exit in the same work directory must escape. |
| Registration controls | `python3 scripts/registration_selftest.py --work build-registration-controls` | Compile and execute indented, multiline and wrapper declarations. Refuse unknown IDs, missing plants and declarations missing from the source inventory. |
| Licence | `python3 scripts/check_license.py --selftest` | MIT source identifiers. Missing, wrong and mixed identifiers rejected. |
| Traceability | `python3 scripts/traceability.py --selftest` | Reconcile source declarations with executable GoogleTest registration. Tested requirements need a tagged test. Imported inspection and port obligations need linked evidence and a reason. Check the complete pinned source inventory, origins, both targets and clause links. Metadata defects, unknown IDs and untraced tests fail. Generated documents are current. |
| Test sensitivity | `python3 scripts/test_inventory.py` | Every test declaration has a named plant. No unknown test names. |
| Coverage controls | `python3 scripts/coverage_selftest.py` | Drops, missing files, moved uncovered arcs and stale exclusions rejected. |
| Privacy | `python3 scripts/check_privacy.py` | Reachable metadata, historical blobs and current tree pass. |
| Privacy commit rule | `python3 scripts/check_privacy.py --selftest` | The holder pair and the GitHub squash pair pass with a one-line message, and the exact owner squash passes. Mixed, reversed, case-varied and other-account pairs fail, and so does a multi-line message. |
| Graphs | `python3 scripts/render_graphs.py --output build-graphs` | Every Mermaid fence renders. |

Install [GoogleTest and GMock 1.14.0](https://github.com/google/googletest/tree/f8d7d77c06936315286eb55f8de22cd23c188571),
[CMake](https://cmake.org/), [GCC](https://gcc.gnu.org/),
[Clang](https://clang.llvm.org/), [cppcheck](https://cppcheck.sourceforge.io/),
[clang-tidy](https://clang.llvm.org/extra/clang-tidy/), Python 3.10 or later, and [PyYAML](https://pyyaml.org/wiki/PyYAMLDocumentation).
The graph check needs [Mermaid CLI](https://github.com/mermaid-js/mermaid-cli).
The hosted [workflow](../.github/workflows/quality.yml) installs these dependencies.
Comment and assertion lexing use Clang 18 (`clang-18`), pinned by the package name.
The lexer runs `-cc1 -dump-raw-tokens`, with C11 for `.c` and C++20 for `.cpp`.
All `.h` and `.hpp` files and their mutation fragments use both C11 and C++20.
Direct `#include` of a `.c` or `.cpp` file is forbidden in the four gated directories.
Quoted and angled source-include controls compile as C++20 and fail the gate.
Every `.h` or `.hpp` consumed there receives both language modes. A compiling digit-separator control checks both modes.
Set `TSN_CLANG` to a Clang 18 executable when it is outside the command search path.
The comment controls also need the RV32 cross compiler listed below.
The gate reads source bytes without newline conversion. Only printable ASCII, tab and LF pass.
Compiling controls refuse CR, form feed, vertical tab, other controls and non-ASCII text.
Only `.c`, `.h`, `.cpp`, `.hpp`, `.S` and `.ld` files and the two
[listed data files](CODING_STANDARD.md) are accepted in the checked directories.
A compiling included `.inc` control proves that an unscanned suffix fails.
Linker scripts forbid single quotes, backslashes, hashes and `VERSION`. Their comments use C11 raw tokens.
Linked escape, hash-comment and version-block controls pass fatal linking and fail the source gate.
A linked quote control fails the comment rule and `-Wl,--fatal-warnings`; valid tracing links cleanly.
Assembly forbids all preprocessor directives, including definitions that produce a hash comment.
Every `#` starts a comment checked against the tracing allowlist. Single quotes,
assembler conditionals, macros, repeats, `.include`, `.incbin` and `.end` are refused. Direct tracing remains accepted.
Linked controls refuse assembly source includes, binary includes and text after `.end`.
Compiling controls include plain and spliced directives and macro-produced prose and tracing.
The Linux job needs no FPGA tools, simulator, platform checkout or submodule.

The six [contributor rules](CODING_STANDARD.md) are the gate's complete comment and assertion contract.

| Rule | Accepted subset | Compiling control |
|---|---|---|
| Character set | Printable ASCII, tab and LF in every file under `src/`, `include/`, `tests/` and `examples/`. | CR, form feed, vertical tab, another control byte and non-ASCII are refused. |
| Suffixes | `.c`, `.h`, `.cpp`, `.hpp`, `.S`, `.ld`; data exceptions are [mutations.json](../tests/mutations.json) and [coverage.ratchet](../tests/coverage.ratchet). | An included `.inc` is refused. |
| Header modes | C11 and C++20 for every `.h`, `.hpp` and header plant fragment; no `.c` or `.cpp` includes. | A digit separator hiding a C++ comment is refused; tracing passes. |
| Linker scripts | No single quotes, backslashes, hashes or `VERSION`; C11 raw comment tokens; fatal RV32 linker warnings. | A quote plant links without fatal warnings, then fails both policy and fatal linking. |
| Assembly | No preprocessor directives, single quotes, `.if*`, `.macro`, `.rept`, `.irp`, `.irpc`, `.include`, `.incbin` or `.end`; every hash starts a checked comment. | Macro-produced comments and tracing are refused; direct tracing passes. |
| Assertions | `EXPECT` and `ASSERT` forms `_TRUE`, `_FALSE`, `_EQ`, `_NE`, `_LE`, `_GE`, plus `EXPECT_EXIT` and `EXPECT_CALL`. | Each allowed form produces a default diagnostic; `EXPECT_NEAR` is refused. |

The gate keeps honest contributors to the comment rule. It does not detect deliberately hidden text.
A deliberately obfuscated construction outside the listed rules is a review suggestion unless it occurs in the shipped tree.

The assertion gate refuses token pasting (`##`) and scans the named macros in all C and C++ files below `tests/`.
The template generator uses exactly GoogleTest and GMock 1.14.0, checked with `pkg-config`.
CMake requires the exact package-config version and does not fall back to an unversioned library search.
The mutation driver uses the compile and link flags from the same `pkg-config` packages whose versions it checks.
Package `-I` paths become `-isystem` paths, matching CMake's dependency-header handling.
Project warnings remain enabled, including signed comparisons under `-Werror`.
The dependency control copies the real pinned headers into a scratch prefix and supplies its path through package flags.
It catches a header plant without ambient include or library paths and confirms that project signedness errors still fail.
For a separate install, set `CMAKE_PREFIX_PATH` to its prefix and `PKG_CONFIG_PATH` to its `lib/pkgconfig` directory.
Run the same validation command without `CPATH`, `CPLUS_INCLUDE_PATH`, `C_INCLUDE_PATH` or `LIBRARY_PATH`.
The same generator preprocesses every public header in the installed `gtest/` and `gmock/` directories with `-dM -E`.
This includes `gtest/gtest-spi.h` and its failure-capturing assertions.
It records public assertion and result macros outside the fourteen allowed forms.
This includes `EXPECT_*`, `ASSERT_*`, `GTEST_*`, `FAIL*`, `SUCCEED` and `ADD_FAILURE*`.
CI regenerates both the refused names and the diagnostics.
The gate also refuses every identifier beginning `EXPECT_`, `ASSERT_` or `GTEST_` outside the allowlist, including trailing-underscore internals.
The four failure-capturing controls compile and pass at runtime, then fail the source gate.
The `GTEST_NONFATAL_FAILURE_` control compiles, fails at runtime and fails the source gate.
Templates record one failing instance of each permitted form, including an unmet mock expectation.
Streamed messages are removed. Only source line numbers are normalized.
The template list does not claim to enumerate every value-dependent diagnostic variation.
To regenerate, run `python3 scripts/assertion_templates.py --write --selftest --work build-assertion-templates`.
Review changes to the [generated list](../scripts/assertion-defaults.json). CI uses `--check`.

## Bare-metal RV32

Both targets are mandatory for every PR. The separate [bare-metal CI job](../.github/workflows/quality.yml)
installs a RISC-V cross compiler and [QEMU](https://www.qemu.org/) on the hosted runner.
On Ubuntu, install `gcc-riscv64-unknown-elf`, `binutils-riscv64-unknown-elf`, `qemu-system-misc` and CMake.

```sh
python3 scripts/baremetal.py --work build-rv32 --jobs 16
```

The [gate](../scripts/baremetal.py) builds Debug and Release concurrently with `-march=rv32i -mabi=ilp32 -ffreestanding`.
It removes default header search paths and checks the compiler dependency output.
Only core headers, compiler intrinsic headers and the minimal port's C-library subset are permitted.
The core imports must stay within the explicit port, memory and integer-helper allowlist.
The final ELF must be 32-bit RISC-V with the soft-float ABI and no unresolved symbols.
The whole core archive is linked, so unused entry points cannot hide a missing dependency.
Linker warnings are fatal through `-Wl,--fatal-warnings`.

The [smoke checks](../examples/rv32/smoke.c) reuse cases from the hosted tests:

| Check | Defect caught |
|---|---|
| ADP schedule and wire fields | Wrong advertisement period, frame size or entity byte order. |
| ADP valid and malformed discovery in every receive state | Acceptance of version 1, 26-byte input or zero control length; missing discard accounting; state, timer or callback side effects. |
| ADP blocked departure | Dropped queued frame or failure to reset the next advertisement index. |
| ACMP restore, admission, latch, rollback and publication | Wrong binding byte order, startup state, admission, rollback cache, bound/started/stream publication or response ordering. |
| MAAP pool bounds and probe schedule | Off-by-one range end, wrong retransmit count, premature validity or missing withdrawal. |

Any failed check exits the simulator with a nonzero status. A hang times out and fails the gate.
The gate writes `results.json`, per-build logs and link maps beneath the work directory.
The full GoogleTest, sanitizer, coverage and mutation campaigns run on Linux.
RV32 runs these focused smoke checks; it does not claim the Linux coverage denominator.
Neither target establishes physical transport latency or board behavior.

## Measurement and limits

Gcov measures the three production C files and the wire header.
It excludes tests, example glue and host library code from the denominator.
Release core objects include all input guards; ADP and MAAP debug assertion
behavior is also exercised in separate binaries. Debug assertion instructions
are outside the release coverage denominator.
The inherited [exclusion register](COVERAGE.md) names seven unreachable ADP arcs
and two unreachable statements. No other exclusions are permitted.
The [ratchet](../tests/coverage.ratchet) records each file separately.

The [mutation table](../tests/mutations.json) preserves the core substitutions
from the source campaigns. Platform-only substitutions are outside this export.
Where a former killer needed an adapter, a named core assertion now tests the
same defect. The [test inventory](TESTS.md) records the mapping.
Compilation failures and crashes fail the campaign; neither counts as a caught mutation.
Every required killer must fail with its assertion-specific message; an unrelated failed assertion is insufficient.
The [ACMP cache check](../scripts/check_acmp_cache.py) discovers `published_*` fields from
the header's compiler tokens, rather than a fixed list. Each field needs exactly one
restore-only plant and its own assertion owned by a named hosted ACMP test.
Assertion identity consists of the owning test and the definition's file, line and
column, retained through helper and callback traversal. Different streamed literals
on one assertion share that identity. Equal message text on separate assertions
does not make their identities equal; the needle must still be unique within its test.
The check rejects a missing test, assertion or plant, a duplicate plant, a shared
assertion, an unchanged restore, a multi-field substitution or a wrong source path.
Its future-field control fails without coverage. A compiling future-field control
with two literals on one assertion fails specifically for shared ownership, including
under optimized Python. Giving the field a separate assertion passes. Both variants
build and run their hosted restore-only campaigns; every selected plant is caught.
Direct, helper and nested callback controls also distinguish shared definitions from
separate assertions on the same line. The hosted mutation campaign establishes that each assertion actually
fails on its field's plant; RV32 smoke cannot satisfy that requirement.
The driver removes each previous XML report before running the binary.
It removes the previous campaign summary at startup. Unknown named tests record ERROR for their plant.
Gate decisions raise explicit errors and remain active under optimized Python.
It requires complete, unique results for exactly the selected executable registration.
Missing reports, partial results, skips, errors and inconsistent counts fail grading.
All killers have literal message needles. Streamed values remain in diagnostics but are excluded from needles.
The campaign adds fresh begin/end markers around assertion streams in temporary test copies.
Markers occupy separate diagnostic lines. The grader blanks everything outside them.
Default GoogleTest text, source locations, expected values and actual values cannot establish a kill.
The original XML retains the complete diagnostics for independent regrading.
Marker insertion changes no assertion expression or production source.
Compiling controls prove that a needle in a default value printout does not count.
The [assertion inventory](../scripts/assertion_messages.py) follows referenced helpers and callbacks in the same test file.
It excludes assertion arguments, unrelated streams, comments and other tests. Only the listed assertion forms supply message literals. Unsupported forms fail the source gate.
There are no inherited exceptions.
Header plants rebuild the affected test translation unit too.

The [traceability matrix](TRACEABILITY.md) is generated from requirement records
and test annotations. Regenerate it and the test inventory with `--write` after
an intentional test change. Review the resulting diff.
The [source inventory](requirement-origins.json) records every numbered source requirement and the two Mark II decisions.
The [record checker](../scripts/requirement_records.py) keeps its pinned inventory complete.
It generates the import and disposition tables in [requirements](REQUIREMENTS.md).
The traceability self-test plants missing origins, target omissions, lost source rows, false exclusions, broken links and unsupported exemptions.
Each must fail. A tested import with its last test removed must also fail.
Local issue requirements retain their linked origin and tests.
Removing any requirement definition from the requirements table must fail, even if its ID remains elsewhere in the document.
Inspection evidence establishes build or source properties on the stated targets.
Port obligations retain the integration checks in [PORTING](PORTING.md), including the unmeasured service bound.
A coverage update uses `python3 scripts/coverage.py build-gcc --write` and refuses
a drop. Exclusion changes need an unreachable-state argument and independent review.

These tests establish portable-core behavior only.
They do not measure real transport latency, linked firmware identity, or device
certification. The [deviation register](DEVIATIONS.md) states the profile limits.

## ACMP-11 contract sentence audit

This table covers every behavior sentence in [PORTING.md:310-353](PORTING.md#acmp-da-freshness)
and both sentences of [ACMP-11](REQUIREMENTS.md#acmp-da-freshness).
Compound sentences list each relevant plant. Repeated plants retain the same killer.
The IDs identify receipt rows; the source anchors identify the sentence start, including
sentences sharing a line. Caller obligations and authority statements have explicit
no-test reasons. No row asserts behavior outside the documented clock service contract.

For each distinct registered plant below, build and run all eight hosted binaries,
then physically remove only its named test declaration and rerun all eight.
The first run must complete with exactly that killer failing on its registered needle;
the second must complete with exactly one fewer instance, no failures and no skips.
Compilation failure, missing XML and unrelated failures cannot establish either result.
The review packet contains the portable full-suite runner, table-derived plant list,
per-row grading receipts and raw XML. The ordinary campaign remains required too:

```sh
python3 scripts/mutation.py --work build-mutations --jobs 16
python3 scripts/traceability.py --write
python3 scripts/test_inventory.py --write
```

`dafresh-wrong-interface` isolates an out-of-range interface; the separate
`r630-3-listener-range-only` isolates a valid but mismatched interface.
`dafresh-reset-retains-demand` preserves only the answer fields; Listener retention
and timestamp-only retention have separate plants. These subdivisions keep the
single-test-removal check meaningful as the contract acquires more assertions.

| Row | Sentence and scope | Killer | Registered plant |
|---|---|---|---|
| P01 | `docs/PORTING.md:312`: Return valid destination AND (fresh answered probe OR registered Listener), including withdrawal while still fresh. | `AcmpFresh.NoProbe`, `AcmpFresh.ListenerWithoutProbe`, `AcmpFresh.InvalidAddress`, `AcmpFresh.FreshProbeAfterListenerWithdrawal` | `dafresh-unanswered-clock`, `dafresh-listener-needs-probe`, `dafresh-ignore-address`, `r630-3-withdrawal-clears-probe` |
| P02 | `docs/PORTING.md:314`: Read destination validity through the existing source callback. | `AcmpFresh.InvalidAddress`, `AcmpFresh.QueryPorts` | `dafresh-ignore-address`, `dafresh-query-source-twice` |
| P03 | `docs/PORTING.md:314`: Read no SRP state through callbacks. | `AcmpFresh.QueryPorts` | `dafresh-query-calls-srp` |
| P04 | `docs/PORTING.md:315`: Supply Listener changes through the single Listener input. | `AcmpFresh.ListenerWithoutProbe`, `AcmpFresh.FreshProbeAfterListenerWithdrawal` | `dafresh-listener-needs-probe`, `r630-3-withdrawal-clears-probe` |
| P05 | `docs/PORTING.md:316`: Listener input makes no port calls; refuse unknown sources, mismatched interfaces and re-entry. | `AcmpFresh.InputGuardsAndReentry`, `AcmpFresh.ListenerInterfaceMismatch` | `dafresh-listener-calls-clock`, `r630-3-listener-bound-off-by-one`, `dafresh-wrong-interface`, `r630-3-listener-range-only`, `r630-3-listener-no-entry-guard` |
| P06 | `docs/PORTING.md:318`: Registration includes Asking Failed; it is not admission or a media licence. The boolean input represents any matching attribute; admission and media licensing remain adapter obligations. | `AcmpFresh.ListenerWithoutProbe` | `dafresh-listener-rejects-asking-failed` |
| P07 | `docs/PORTING.md:319`: Aggregate Listeners outside the core; withdraw only when the last matching registration leaves. No core test: external aggregation is a port obligation; the core receives only one boolean level, with withdrawal behavior covered by P04. | Not applicable; reason in scope | None |
| P08 | `docs/PORTING.md:321`: Keep the level current for the current Stream ID and configured interface. No core test for platform freshness or Stream ID association: the input has no Stream ID. Valid-interface enforcement and source isolation are tested by P05 and R02. | Not applicable; reason in scope | None |
| P09 | `docs/PORTING.md:323`: The entity generator supplies 15000 milliseconds. | `EntityYaml.DaFreshRoundTrip` | `dafresh-generated-window` |
| P10 | `docs/PORTING.md:324`: Read the configured interval directly, with no duplicate constant. | `AcmpFresh.ConfiguredWindow` | `dafresh-fixed-window` |
| P11 | `docs/PORTING.md:325`: Hand-written configurations supply milliseconds below the clock half range. | `AcmpFresh.WindowRange` | `dafresh-half-range` |
| P12 | `docs/PORTING.md:326`: Refuse intervals at or above 2^31 without changing the instance or calling ports. | `AcmpFresh.WindowRange` | `dafresh-half-range`, `dafresh-range-wipes-instance`, `dafresh-range-calls-clock` |
| P13 | `docs/PORTING.md:327`: Zero disables probe demand but preserves Listener demand. | `AcmpFresh.ZeroWindow` | `x-zero-never-expires`, `dafresh-zero-blocks-listener` |
| P14 | `docs/PORTING.md:328`: Each source owns answer timestamp, answer flag and Listener level; initialization clears all three. | `AcmpFresh.ListenerWithdrawalAndReset`, `AcmpFresh.InitClearsListener`, `AcmpFresh.SourceAndInterfaceIsolation` | `dafresh-reset-retains-demand`, `dafresh-reset-retains-timestamp`, `r630-3-init-keeps-listener`, `dafresh-wrong-source`, `r630-3-listener-writes-source-zero` |
| P15 | `docs/PORTING.md:331`: Start the window after accepting a probe response for a known source on its configured interface. | `AcmpFresh.WithinWindowAndRefresh`, `AcmpFresh.DeferredAnswer`, `AcmpFresh.OtherRepliesDoNotRefresh` | `dafresh-answer-stamped-before-send`, `dafresh-refused-answer`, `dafresh-incompatible-refresh` |
| P16 | `docs/PORTING.md:332`: SUCCESS and destination-allocation-failure answers record demand; invalid destination still closes the gate. | `AcmpFresh.FailedAllocationAnswer`, `AcmpFresh.InvalidAddress` | `dafresh-only-success`, `dafresh-ignore-address` |
| P17 | `docs/PORTING.md:333`: Unknown-ID, incompatible-interface and other command replies do not refresh demand. | `AcmpFresh.OtherRepliesDoNotRefresh` | `dafresh-state-reply-demand`, `dafresh-incompatible-refresh` |
| P18 | `docs/PORTING.md:334`: Queued and refused sends count only when poll accepts them. | `AcmpFresh.DeferredAnswer` | `dafresh-refused-answer` |
| P19 | `docs/PORTING.md:336`: The response-acceptance endpoint is the repository reading of answered. No executable test: authority attribution, with the endpoint behavior tested by P15 and P18. Fabric command acceptance can precede this endpoint under backpressure. | Not applicable; reason in scope | None |
| P20 | `docs/PORTING.md:337`: Preserve existing response bytes and command handling. Existing ACMP-08 response oracles remain unchanged; these are independent response-field witnesses, not an exhaustive wire equivalence proof. | `AcmpCore.A20ProbeTxIsAnsweredFromTheSource`, `AcmpCore.A20DisconnectGetTxStateAndGetTxConnection` | `acmp-probe-tx-reports-asking-failed`, `acmp-get-tx-state-unheld-mac` |
| P21 | `docs/PORTING.md:339`: Unsigned millisecond ages 0 through 14999 are fresh; 15000 and later are stale. | `AcmpFresh.WithinWindowAndRefresh`, `AcmpFresh.WindowEdge`, `AcmpFresh.StaleProbe` | `dafresh-no-renewal`, `dafresh-inclusive-edge`, `dafresh-expiry-equality` |
| P22 | `docs/PORTING.md:340`: The half-open edge applies across counter wrap. | `AcmpFresh.ClockWrap`, `AcmpFresh.WindowEdge`, `AcmpFresh.StaleProbe` | `dafresh-absolute-clock`, `dafresh-inclusive-edge`, `dafresh-expiry-equality` |
| P23 | `docs/PORTING.md:341`: Queries use current time, including after transport advances it. | `AcmpFresh.WithinWindowAndRefresh`, `AcmpFresh.QueryPorts` | `dafresh-answer-stamped-before-send`, `dafresh-query-clock-twice`, `dafresh-no-renewal` |
| P24 | `docs/PORTING.md:342`: Observed expiry clears the answer even under Listener or invalid-address masking, preventing wrap resurrection. | `AcmpFresh.StaleProbe`, `AcmpFresh.StaleProbeAfterListenerWrap`, `AcmpFresh.StaleProbeAfterInvalidAddressWrap` | `dafresh-expiry-equality`, `g-expiry-skipped-with-listener`, `g-expiry-skipped-invalid-da` |
| P25 | `docs/PORTING.md:345`: Query every source in serialized dispatch after events and on regular service ticks. No core test: scheduling and serialization are caller preconditions; callback re-entry refusal is tested by P26. The core owns no dispatcher. | Not applicable; reason in scope | None |
| P26 | `docs/PORTING.md:346`: Query uses the existing time/source ports, refuses callback re-entry and returns false for unknown sources. | `AcmpFresh.QueryPorts`, `AcmpFresh.InputGuardsAndReentry` | `dafresh-query-clock-twice`, `dafresh-query-source-twice`, `r630-3-declaring-no-entry-guard`, `r630-3-declaring-bound-off-by-one` |
| P27 | `docs/PORTING.md:348`: Query adds neither a timer nor a publication callback. | `AcmpFresh.QueryPorts` | `dafresh-query-calls-timer`, `dafresh-query-calls-publish` |
| P28 | `docs/PORTING.md:348`: Service stays inside the half-range clock contract; a full unobserved revolution cannot be inferred. No executable guarantee outside this precondition: a modulo-2^32 sample contains no revolution count. P22 and P24 test permitted serviced wraps, including 2^32 + 100 ms. | Not applicable; reason in scope | None |
| P29 | `docs/PORTING.md:351`: Refresh the platform gate on ticks even when poll reports no owed frames. DeferredAnswer checks poll returns false after acceptance while the query remains true; the regular platform tick itself is a caller obligation. | `AcmpFresh.DeferredAnswer` | `dafresh-refused-answer` |
| R01 | `docs/REQUIREMENTS.md:50`: ACMP-11 sentence 1: per-source valid destination AND (fresh answered probe OR Listener). | `AcmpFresh.NoProbe`, `AcmpFresh.ListenerWithoutProbe`, `AcmpFresh.InvalidAddress`, `AcmpFresh.FreshProbeAfterListenerWithdrawal` | `dafresh-unanswered-clock`, `dafresh-listener-needs-probe`, `dafresh-ignore-address`, `r630-3-withdrawal-clears-probe` |
| R02 | `docs/REQUIREMENTS.md:50`: ACMP-11 sentence 2: configured interval, wrapping clock, interface and source isolation. | `AcmpFresh.ConfiguredWindow`, `AcmpFresh.ClockWrap`, `AcmpFresh.SourceAndInterfaceIsolation`, `AcmpFresh.ListenerInterfaceMismatch` | `dafresh-fixed-window`, `dafresh-absolute-clock`, `dafresh-wrong-source`, `r630-3-listener-writes-source-zero`, `r630-3-listener-range-only` |
