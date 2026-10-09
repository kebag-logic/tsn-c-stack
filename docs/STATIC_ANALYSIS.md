# Static analysis

Run the [analysis gate](../scripts/static_analysis.py) from the repository root.
It runs production sources and both example ports through cppcheck and clang-tidy.
C11, the public include directory and release assertions match the library build.
Warnings fail. No project diagnostics remain after these listed suppressions.
System-header diagnostics are excluded by the analyzer default.

| Analyzer | Suppression | Scope and rationale |
|---|---|---|
| cppcheck | `constParameterPointer` | The decoder parameter at [maap.c](../src/maap.c#L262) could be const. Preserve the imported signature in this move. The function only reads it. |
| cppcheck | `constParameterCallback` | The read-only example callbacks at [gptp](../examples/adp_port.c#L32), [link_up](../examples/adp_port.c#L40) and [seed](../examples/adp_port.c#L46) must match the public mutable-context callback type. Changing it would require an incompatible function-pointer cast. |
| cppcheck | `redundantAssignment` | The [RV32 backpressure control](../examples/rv32/smoke.c#L136) changes transmit availability across a core call. The send callback reads the earlier value through its context pointer. |
| clang-tidy | `bugprone-signed-bitwise` | C integer promotion makes byte operands and literal shift counts signed. Values are nonnegative and bounded. The [wire tests](TESTS.md) and undefined-behavior run exercise these operations. |
| clang-tidy | `bugprone-easily-swappable-parameters` | Callback and wire helper signatures deliberately place related integer fields together. Preserve the source API. Field-level and interface-isolation tests check order. |
| clang-tidy | `clang-analyzer-security.insecureAPI.DeprecatedOrUnsafeBufferHandling` | Optional Annex K memory routines are not available on all embedded C libraries. Fixed-length copies use explicit bounds. Buffer boundary tests and the address sanitizer validate exercised accesses. |

The three named clang-tidy checks are disabled in the gate.
All other `clang-analyzer-*`, `bugprone-*` and `performance-*` checks remain enabled.
Cppcheck enables warning, style, performance and portability categories.
The cppcheck exception is tied to its source location.
These exceptions are reviewable policy choices, not a standards conformance waiver.
