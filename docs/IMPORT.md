# Import record

This repository exports the portable cores from
[milan-fpga revision 6aa25dec](https://github.com/kebag-logic/milan-fpga/tree/6aa25dec977c6ad78bf4ff6275de47fb81d0c246).
The [assignment](https://github.com/kebag-logic/milan-fpga/issues/697#issuecomment-6074245112)
and the [MIT decision](https://github.com/kebag-logic/milan-fpga/issues/697#issuecomment-6074086970)
authorize this boundary and licence change.
The [repository decision](https://github.com/kebag-logic/milan-fpga/issues/697#issuecomment-6074093506)
and [name decision](https://github.com/kebag-logic/milan-fpga/issues/697#issuecomment-6074191062)
set the destination.

The [export script](../scripts/export_history.py) filters history and renames paths.
It rewrites identities to the configured holder identity.
It replaces commit messages with neutral one-line subjects.
It changes source identifiers to MIT and preserves existing copyright lines.
ADP and MAAP test blobs retain only core cases. Shared harness labels are removed.
Pre-conversion ADP test blobs without separable core test cases are omitted.

The export examined 3628 source commits and retained 26 commits.
The filtered head is `21d132baa148f4731a1622b425e4327c1ac7a44f`.
A second export produced the identical head.
The branch merges this history with the initial MIT repository commit using
`git merge --allow-unrelated-histories --no-ff`.

## File map

| Original path | Exported path |
|---|---|
| [sw/firmware/ctrl/adp/adp.c](https://github.com/kebag-logic/milan-fpga/blob/6aa25dec977c6ad78bf4ff6275de47fb81d0c246/sw/firmware/ctrl/adp/adp.c) | [src/adp.c](../src/adp.c) |
| [sw/firmware/ctrl/adp/adp.h](https://github.com/kebag-logic/milan-fpga/blob/6aa25dec977c6ad78bf4ff6275de47fb81d0c246/sw/firmware/ctrl/adp/adp.h) | [include/adp.h](../include/adp.h) |
| [sw/firmware/ctrl/acmp/acmp.c](https://github.com/kebag-logic/milan-fpga/blob/6aa25dec977c6ad78bf4ff6275de47fb81d0c246/sw/firmware/ctrl/acmp/acmp.c) | [src/acmp.c](../src/acmp.c) |
| [sw/firmware/ctrl/acmp/acmp.h](https://github.com/kebag-logic/milan-fpga/blob/6aa25dec977c6ad78bf4ff6275de47fb81d0c246/sw/firmware/ctrl/acmp/acmp.h) | [include/acmp.h](../include/acmp.h) |
| [sw/firmware/ctrl/maap/maap.c](https://github.com/kebag-logic/milan-fpga/blob/6aa25dec977c6ad78bf4ff6275de47fb81d0c246/sw/firmware/ctrl/maap/maap.c) | [src/maap.c](../src/maap.c) |
| [sw/firmware/ctrl/maap/maap.h](https://github.com/kebag-logic/milan-fpga/blob/6aa25dec977c6ad78bf4ff6275de47fb81d0c246/sw/firmware/ctrl/maap/maap.h) | [include/maap.h](../include/maap.h) |
| [sw/firmware/ctrl/wire/wire.h](https://github.com/kebag-logic/milan-fpga/blob/6aa25dec977c6ad78bf4ff6275de47fb81d0c246/sw/firmware/ctrl/wire/wire.h) | [include/wire.h](../include/wire.h) |
| [sw/firmware/ctrl/test/test_adp.cpp](https://github.com/kebag-logic/milan-fpga/blob/6aa25dec977c6ad78bf4ff6275de47fb81d0c246/sw/firmware/ctrl/test/test_adp.cpp) | [tests/test_adp.cpp](../tests/test_adp.cpp) |
| [sw/firmware/ctrl/test/test_adp_reentry.cpp](https://github.com/kebag-logic/milan-fpga/blob/6aa25dec977c6ad78bf4ff6275de47fb81d0c246/sw/firmware/ctrl/test/test_adp_reentry.cpp) | [tests/test_adp_reentry.cpp](../tests/test_adp_reentry.cpp) |
| [sw/firmware/ctrl/test/test_acmp.cpp](https://github.com/kebag-logic/milan-fpga/blob/6aa25dec977c6ad78bf4ff6275de47fb81d0c246/sw/firmware/ctrl/test/test_acmp.cpp) | [tests/test_acmp.cpp](../tests/test_acmp.cpp) |
| [sw/firmware/ctrl/test/acmp_fake.hpp](https://github.com/kebag-logic/milan-fpga/blob/6aa25dec977c6ad78bf4ff6275de47fb81d0c246/sw/firmware/ctrl/test/acmp_fake.hpp) | [tests/acmp_fake.hpp](../tests/acmp_fake.hpp) |
| [sw/firmware/ctrl/test/test_maap.cpp](https://github.com/kebag-logic/milan-fpga/blob/6aa25dec977c6ad78bf4ff6275de47fb81d0c246/sw/firmware/ctrl/test/test_maap.cpp) | [tests/test_maap.cpp](../tests/test_maap.cpp) |
| [sw/firmware/ctrl/test/test_maap_debug.cpp](https://github.com/kebag-logic/milan-fpga/blob/6aa25dec977c6ad78bf4ff6275de47fb81d0c246/sw/firmware/ctrl/test/test_maap_debug.cpp) | [tests/test_maap_debug.cpp](../tests/test_maap_debug.cpp) |

## Kept outside the export

The saved-state adapter depends on an external state interface, so
[acmp_nvm](https://github.com/kebag-logic/milan-fpga/blob/6aa25dec977c6ad78bf4ff6275de47fb81d0c246/sw/firmware/ctrl/acmp/acmp_nvm.h)
is not portable-core material. ACMP binding serialization remains in the core.
Mailbox adapters, host models, composition, register contracts and linked images
stay in the source repository. No source repository files or submodule pins change.

Tests that require processor-generated expectations or mailbox fixtures remain
with their integration harness. Core cases and their plants are retained here.
The coverage reader and exact unreachable-state exclusions derive from the
[source coverage harness](https://github.com/kebag-logic/milan-fpga/tree/6aa25dec977c6ad78bf4ff6275de47fb81d0c246/sw/firmware/gtest).
The 311 substitutions derive from the
[source mutation tables](https://github.com/kebag-logic/milan-fpga/tree/6aa25dec977c6ad78bf4ff6275de47fb81d0c246/sw/firmware/ctrl/test).
The [test inventory](TESTS.md) shows the core assertions that replace adapter killers.

Production C and header bytes match the pinned source after the SPDX replacement.
No protocol behavior is changed. The consumer submodule and firmware-image checks
are a later change under [issue 697](https://github.com/kebag-logic/milan-fpga/issues/697).
