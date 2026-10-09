# tsn-c-stack

Portable C11 cores for ADP advertising, Milan ACMP and MAAP allocation.
The library uses fixed storage and callbacks. It needs no heap or operating system.
It has no mailbox, register-map or image dependency.

The code comes from [milan-fpga](https://github.com/kebag-logic/milan-fpga)
under [issue 697](https://github.com/kebag-logic/milan-fpga/issues/697).
The [import record](docs/IMPORT.md) describes the boundary and history.
SRP is supplied separately by [lwSRP](https://github.com/kebag-logic/lwSRP),
under its own [Apache-2.0 licence](https://github.com/kebag-logic/lwSRP/blob/main/LICENSE).
No SRP checkout is needed to build or test these cores.

## Build and test

Install a C11 compiler, a C++20 compiler, [CMake](https://cmake.org/),
[GoogleTest and GMock](https://github.com/google/googletest), and Python 3.10 or later.
On Ubuntu, the test packages are `libgtest-dev` and `libgmock-dev`.

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug
cmake --build build -j16
ctest --test-dir build --output-on-failure -j16
```

The library-only build uses `-DTSN_TESTS=OFF` and target `tsn`.
Use `-DCMAKE_C_COMPILER=clang -DCMAKE_CXX_COMPILER=clang++` for Clang.
Both compilers use `-Wall -Wextra -Werror` and ISO C11.
The tests use C++20. The library exposes C headers in [include](include/).

## Choose a task

| Persona | Start here |
|---|---|
| Developer | Read the [architecture](docs/ARCHITECTURE.md), [coding standard](docs/CODING_STANDARD.md), and [contribution rules](CONTRIBUTING.md). |
| Integrator | Read the [port contract](docs/PORTING.md) and run the [example port](examples/adp_port.c). |
| Tester | Run the [verification commands](docs/VERIFICATION.md). Check [traceability](docs/TRACEABILITY.md) and [test defects](docs/TESTS.md). |
| Manager | Review the [requirements](docs/REQUIREMENTS.md), [deviations](docs/DEVIATIONS.md), [change log](CHANGELOG.md), and two independent reviews. |

```mermaid
flowchart LR
  events[Serialized input events] --> cores[ADP ACMP MAAP]
  cores --> ports[Integrator callbacks]
  ports --> transport[Frames timers and state]
```

## Licence

[MIT](LICENSE). Copyright 2026 Kebag Logic.
See [security reporting](SECURITY.md) for defect handling.
