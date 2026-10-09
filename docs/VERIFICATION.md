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
| GCC C11 and core tests | `cmake -S . -B build-gcc -DTSN_COVERAGE=ON -DCMAKE_BUILD_TYPE=Debug`, then `cmake --build build-gcc -j16` and `ctest --test-dir build-gcc --output-on-failure -j16` | All tests pass. Warnings fail. |
| Coverage | `python3 scripts/coverage.py build-gcc` | 100% lines and branches after exact exclusions. |
| Mutation | `python3 scripts/mutation.py --work build-mutations --jobs 16` | All 311 core plants caught by their named assertions. |
| Sanitizers and Clang | `cmake -S . -B build-sanitize -DCMAKE_C_COMPILER=clang -DCMAKE_CXX_COMPILER=clang++ -DTSN_SANITIZERS=ON -DCMAKE_BUILD_TYPE=Debug`, then build and test as above | Address and undefined-behavior sanitizers pass. The full runner enables leak detection and stops on findings. |
| Static analysis | `python3 scripts/static_analysis.py` | No project findings after [listed suppressions](STATIC_ANALYSIS.md). |
| Boundary | `python3 scripts/check_boundary.py --selftest` | Compiler dependencies permit only C library and owned headers. Object symbols refuse heap and OS use. Ten forbidden controls compile and are refused with both compilers; two pass controls compile and pass. |
| Assertion needles | `python3 scripts/needle_audit.py --selftest` | Each needle has at least eight characters and identifies exactly one assertion message literal in its named test or helper. Substrings of the generated default diagnostics are refused. Other assertion forms are refused. |
| Assertion templates | `python3 scripts/assertion_templates.py --check --selftest --work build-assertion-templates` | Compile and run one failing instance of each of the 14 allowed forms with GoogleTest 1.14.0. Blank streamed messages and compare the generated default diagnostics. Compiling `EXPECT_NEAR`, `GTEST_ASSERT_LT`, `GTEST_FAIL` and token-pasted controls are refused. |
| Dependency pin | `python3 scripts/dependency_selftest.py --work build-dependency-controls --jobs 16` | Refuse a configure with only another package version. Compile and catch a header plant using the checked package flags, including a required header and link symbol, without ambient include or library paths. |
| Code comments | `python3 scripts/check_comments.py --selftest` | Every comment under the closed [contributor rules](CODING_STANDARD.md) is checked. Only SPDX, requirement IDs and short standard references pass. Each rule has a compiling control. |
| Conditional regions | `python3 scripts/check_conditionals.py --selftest --work build-conditionals --jobs 16` | Every permitted non-guard region compiles both sides. Every file-specific macro combination is compiled. Nested unreachable regions fail. |
| Port contracts | `python3 scripts/check_port_contracts.py --selftest` | Each relocated callback, field, precondition and counter name stays in its guide section. Critical phrases stay beside their contract names. Name and meaning removal controls fail. |
| Report controls | `python3 scripts/mutation_selftest.py --work build-report-controls --jobs 16` | Reject stale, partial, skipped and mismatched reports. A real catch followed by early exit in the same work directory must escape. |
| Registration controls | `python3 scripts/registration_selftest.py --work build-registration-controls` | Compile and execute indented, multiline and wrapper declarations. Refuse unknown IDs, missing plants and declarations missing from the source inventory. |
| Licence | `python3 scripts/check_license.py --selftest` | MIT source identifiers. Missing, wrong and mixed identifiers rejected. |
| Traceability | `python3 scripts/traceability.py --selftest` | Reconcile source declarations with executable GoogleTest registration. Every requirement has a test. Unknown IDs and untraced tests fail. Generated document is current. |
| Test sensitivity | `python3 scripts/test_inventory.py` | Every test declaration has a named plant. No unknown test names. |
| Coverage controls | `python3 scripts/coverage_selftest.py` | Drops, missing files, moved uncovered arcs and stale exclusions rejected. |
| Privacy | `python3 scripts/check_privacy.py` | Reachable metadata, historical blobs and current tree pass. |
| Graphs | `python3 scripts/render_graphs.py --output build-graphs` | Every Mermaid fence renders. |

Install [GoogleTest and GMock 1.14.0](https://github.com/google/googletest/tree/f8d7d77c06936315286eb55f8de22cd23c188571),
[CMake](https://cmake.org/), [GCC](https://gcc.gnu.org/),
[Clang](https://clang.llvm.org/), [cppcheck](https://cppcheck.sourceforge.io/),
[clang-tidy](https://clang.llvm.org/extra/clang-tidy/), and Python 3.10 or later.
The graph check needs [Mermaid CLI](https://github.com/mermaid-js/mermaid-cli).
The hosted [workflow](../.github/workflows/quality.yml) installs these dependencies.
Comment and assertion lexing use Clang 18 (`clang-18`), pinned by the package name.
The lexer runs `-cc1 -dump-raw-tokens`, with C11 for `.c` and C++20 for `.cpp`.
All `.h` and `.hpp` files and their mutation fragments use both C11 and C++20.
This includes every header consumed by a C++ test unit. A compiling digit-separator control checks both modes.
Set `TSN_CLANG` to a Clang 18 executable when it is outside the command search path.
The comment controls also need the RV32 cross compiler listed below.
The gate reads source bytes without newline conversion. Only printable ASCII, tab and LF pass.
Compiling controls refuse CR, form feed, vertical tab, other controls and non-ASCII text.
Only `.c`, `.h`, `.cpp`, `.hpp`, `.S` and `.ld` files and the two
[listed data files](CODING_STANDARD.md) are accepted in the checked directories.
A compiling included `.inc` control proves that an unscanned suffix fails.
Linker scripts forbid single quotes. Their comments use C11 raw tokens.
A linked quote control fails the comment rule and `-Wl,--fatal-warnings`; valid tracing links cleanly.
Assembly forbids all preprocessor directives, including definitions that produce a hash comment.
Every `#` starts a comment checked against the tracing allowlist. Single quotes,
assembler conditionals, macros and repeats are refused. Direct tracing remains accepted.
Compiling controls include plain and spliced directives and macro-produced prose and tracing.
The Linux job needs no FPGA tools, simulator, platform checkout or submodule.

The six [contributor rules](CODING_STANDARD.md) are the gate's complete comment and assertion contract:
The gate keeps honest contributors to the comment rule. It does not detect deliberately hidden text.
A deliberately obfuscated construction outside the listed rules is a review suggestion unless it occurs in the shipped tree.

| Rule | Accepted subset | Compiling control |
|---|---|---|
| Character set | Printable ASCII, tab and LF in every file under `src/`, `include/`, `tests/` and `examples/`. | CR, form feed, vertical tab, another control byte and non-ASCII are refused. |
| Suffixes | `.c`, `.h`, `.cpp`, `.hpp`, `.S`, `.ld`; data exceptions are [mutations.json](../tests/mutations.json) and [coverage.ratchet](../tests/coverage.ratchet). | An included `.inc` is refused. |
| Header modes | C11 and C++20 for every `.h`, `.hpp` and header plant fragment. | A digit separator hiding a C++ comment is refused; tracing passes. |
| Linker scripts | No single quotes; C11 raw comment tokens; fatal RV32 linker warnings. | A quote plant links without fatal warnings, then fails both policy and fatal linking. |
| Assembly | No preprocessor directives, single quotes, `.if*`, `.macro`, `.rept`, `.irp` or `.irpc`; every hash starts a checked comment. | Macro-produced comments and tracing are refused; direct tracing passes. |
| Assertions | `EXPECT` and `ASSERT` forms `_TRUE`, `_FALSE`, `_EQ`, `_NE`, `_LE`, `_GE`, plus `EXPECT_EXIT` and `EXPECT_CALL`. | Each allowed form produces a default diagnostic; `EXPECT_NEAR` is refused. |

The assertion gate refuses token pasting (`##`) and scans the named macros in all C and C++ files below `tests/`.
The template generator uses exactly GoogleTest and GMock 1.14.0, checked with `pkg-config`.
CMake requires the exact package-config version and does not fall back to an unversioned library search.
The mutation driver uses the compile and link flags from the same `pkg-config` packages whose versions it checks.
The same generator preprocesses `gtest/gtest.h` and `gmock/gmock.h` with `-dM -E`.
It records public assertion and result macros outside the fourteen allowed forms.
This includes `EXPECT_*`, `ASSERT_*`, `GTEST_*`, `FAIL*`, `SUCCEED` and `ADD_FAILURE*`.
CI regenerates both the refused names and the diagnostics.
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
| ADP valid and inherited malformed discovery | Changed acceptance of version 1, 26-byte input or zero control length. |
| ADP blocked departure | Dropped queued frame or failure to reset the next advertisement index. |
| ACMP restore, admission, latch and rollback | Wrong binding byte order, startup state, admission or rollback. |
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
A coverage update uses `python3 scripts/coverage.py build-gcc --write` and refuses
a drop. Exclusion changes need an unreachable-state argument and independent review.

These tests establish portable-core behavior only.
They do not measure real transport latency, linked firmware identity, or device
certification. The [deviation register](DEVIATIONS.md) states the profile limits.
