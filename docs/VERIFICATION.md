# Verification

For a tester, the complete local gate is:

```sh
python3 scripts/validate.py --work build-validation --jobs 16 --graphs
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
| Boundary | `python3 scripts/check_boundary.py --selftest` | C library and owned headers only. Seven forbidden controls rejected. |
| Licence | `python3 scripts/check_license.py --selftest` | MIT source identifiers. Missing, wrong and mixed identifiers rejected. |
| Traceability | `python3 scripts/traceability.py --selftest` | Every requirement has a test. Unknown IDs and untraced tests fail. Generated document is current. |
| Test sensitivity | `python3 scripts/test_inventory.py` | Every test declaration has a named plant. No unknown test names. |
| Coverage controls | `python3 scripts/coverage_selftest.py` | Drops, missing files, moved uncovered arcs and stale exclusions rejected. |
| Privacy | `python3 scripts/check_privacy.py` | Reachable metadata, historical blobs and current tree pass. |
| Graphs | `python3 scripts/render_graphs.py --output build-graphs` | Every Mermaid fence renders. |

Install [GoogleTest and GMock](https://github.com/google/googletest),
[CMake](https://cmake.org/), [GCC](https://gcc.gnu.org/),
[Clang](https://clang.llvm.org/), [cppcheck](https://cppcheck.sourceforge.io/),
[clang-tidy](https://clang.llvm.org/extra/clang-tidy/), and Python 3.10 or later.
The graph check needs [Mermaid CLI](https://github.com/mermaid-js/mermaid-cli).
The hosted [workflow](../.github/workflows/quality.yml) installs these dependencies.
No FPGA toolchain, simulator, platform checkout or submodule is used.

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
Compilation failures and crashes count as escapes, not caught mutations.
Every required killer must fail; an unrelated failed assertion is insufficient.
Header plants rebuild the affected test translation unit too.

The [traceability matrix](TRACEABILITY.md) is generated from requirement records
and test annotations. Regenerate it and the test inventory with `--write` after
an intentional test change. Review the resulting diff.
A coverage update uses `python3 scripts/coverage.py build-gcc --write` and refuses
a drop. Exclusion changes need an unreachable-state argument and independent review.

These tests establish portable-core behavior only.
They do not measure real transport latency, linked firmware identity, or device
certification. The [deviation register](DEVIATIONS.md) states the profile limits.
