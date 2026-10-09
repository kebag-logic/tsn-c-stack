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

The [comment gate](../scripts/check_comments.py) uses the Clang 18 lexer.
C and C++ use their respective language modes. Each comment token is checked.
Assembly forbids single quotes, conditional directives, macros and repeats.
Every assembly `#` after a preprocessor directive marker starts a checked comment.
Use numeric character values. Keep `#` out of assembly strings.
The [port contract gate](../scripts/check_port_contracts.py) keeps relocated interface names and critical contract phrases in the integrator guide.

## Conditional compilation

Only `#ifdef` and `#ifndef` may open a conditional region.
`#if`, `#elif`, their variants, `#pragma` and `#line` are forbidden.
Do not redefine or undefine a conditional macro inside a source file.
The two ACMP capacity defaults are the only configuration definitions allowed.
Each default immediately follows its matching `#ifndef`.

| Macro | Configuration |
|---|---|
| `__cplusplus` | C11 and C++20 header builds. |
| `NDEBUG` | Assertions enabled and disabled. |
| `CTRL_REENTRY_ASSERT` | Re-entry callback enabled and disabled. |
| `ADP_TEST_RELEASE` | Release and assertion test paths. |
| `ADP_TEST_COVERAGE` | Coverage dump call enabled and disabled. |
| `ACMP_MAX_SINKS` | Caller definition and header default, both 16. |
| `ACMP_MAX_SOURCES` | Caller definition and header default, both 16. |

The [conditional gate](../scripts/check_conditionals.py) compiles every combination
used by each file. Every non-guard region must compile both sides, including
nested regions. An unreachable side fails even when every build succeeds.
Public headers compile in C and C++ where they test `__cplusplus`.
The matrix supplements the [hosted and freestanding tests](VERIFICATION.md).

Include guards enclose the complete file. Their `#define` is on the next line.
They have no `#else`. These filename-based guard names preserve the imported headers:

| Header | Guard |
|---|---|
| [adp.h](../include/adp.h) | `ADP_H` |
| [acmp.h](../include/acmp.h) | `ACMP_H` |
| [maap.h](../include/maap.h) | `CTRL_MAAP_H` |
| [wire.h](../include/wire.h) | `CTRL_WIRE_H` |
| [acmp_fake.hpp](../tests/acmp_fake.hpp) | `ACMP_FAKE_HPP` |
| [adp_port.h](../examples/adp_port.h) | `EXAMPLE_ADP_PORT_H` |
| [assert.h](../examples/rv32/include/assert.h) | `TSN_PORT_ASSERT_H` |
| [string.h](../examples/rv32/include/string.h) | `TSN_PORT_STRING_H` |
