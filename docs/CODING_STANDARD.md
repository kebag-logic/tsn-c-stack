# Coding standard

Code comments contain only SPDX lines, requirement IDs, or short references to standard clauses, tables and figures.
Put integration contracts in the [porting guide](PORTING.md) and [architecture](ARCHITECTURE.md).
The [comment gate](../scripts/check_comments.py) checks sources, headers, tests, examples and mutation fragments.

The library uses ISO C11. Public headers also compile as C++20.
Use `-Wall -Wextra -Werror` with GCC and Clang.
The [build](../CMakeLists.txt) disables language extensions.

Use fixed arrays and caller-owned state. Do not allocate or release heap storage.
Do not depend on threads, system calls, registers or device headers.
All external services belong behind callback tables.
Use explicit-width integers for wire fields and counters.
Use the [wire helpers](../include/wire.h) for byte order and unaligned fields.
Keep pointer lifetimes and buffer lengths explicit.

Prefix public identifiers with the module name. Use lower-case names and
underscores for functions and fields. Use upper-case names for constants.
Keep callbacks bounded. Do not wait for external progress inside a core call.
Treat synchronous re-entry as a contract violation.
Static arrays are the storage pools; there is no dynamic pool allocator.

Tests use [GoogleTest and GMock](https://github.com/google/googletest).
Spell protocol oracle values independently when checking constants.
Add assertions for malformed input, boundary values, ordering and blocked output.
Use fatal assertions before indexing output that a faulty core may omit.
See [verification](VERIFICATION.md) for coverage and mutation obligations.
Document static-analysis suppressions in the [suppression register](STATIC_ANALYSIS.md).

The [comment gate](../scripts/check_comments.py) checks every logical comment line, including assembly `#` comments.
Line splicing cannot hide prose behind an SPDX line. Disabled `#if 0` regions are refused.
The [port contract gate](../scripts/check_port_contracts.py) keeps relocated interface names in the integrator guide.
