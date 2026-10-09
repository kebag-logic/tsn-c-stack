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

## Validation changes

The validation commit adds `// REQ:` annotations and seven core cases to the imported tests:
[AdpCore.EntityFieldsUseIndependentCounts, AdpCore.LinkLevelsAndDisabledInputs and AdpCore.MockedPortOrder](../tests/test_adp.cpp),
[AcmpCore.DepartingStopsEveryProbingTimer, AcmpCore.CommandPortBudgets, AcmpCore.TimerPortBudgets and AcmpCore.DiscoveryPortBudgets](../tests/test_acmp.cpp).
No imported case body changes in that commit.

The review follow-up adds assertion messages to eight inherited MAAP controls and strengthens the added callback-budget tests.
It adds four parameterized ADP input controls for the [preserved receiver limit](DEVIATIONS.md).
All 311 imported source substitutions remain unchanged. Production files remain unchanged.

## Retained commit map

Each source commit links to its original record. Each exported commit links to the original import history.
The [owner decision](https://github.com/kebag-logic/milan-fpga/issues/697#issuecomment-6074811248) squash-merged that import as
[ae982af](https://github.com/kebag-logic/tsn-c-stack/commit/ae982af85ec97286bd35b39403926d8f0eaec81d).
Its tree equals the reviewed head. The map records export provenance; those commits are no longer ancestors of main.

| Original commit | Exported commit |
|---|---|
| [048cd2b32d5854a095491492fd556d6dd0083241](https://github.com/kebag-logic/milan-fpga/commit/048cd2b32d5854a095491492fd556d6dd0083241) | [3205c29e583e6f395ded7921674f59c119a07f9e](https://github.com/kebag-logic/tsn-c-stack/commit/3205c29e583e6f395ded7921674f59c119a07f9e) |
| [11e195bea81def13274ac6f424f974b3f4cfc0d7](https://github.com/kebag-logic/milan-fpga/commit/11e195bea81def13274ac6f424f974b3f4cfc0d7) | [6ad854091fa6e6fed5878f5be4215200a797d9ee](https://github.com/kebag-logic/tsn-c-stack/commit/6ad854091fa6e6fed5878f5be4215200a797d9ee) |
| [14f091be8f1ea9c6cb23159fb55bccfebcbc2766](https://github.com/kebag-logic/milan-fpga/commit/14f091be8f1ea9c6cb23159fb55bccfebcbc2766) | [21d132baa148f4731a1622b425e4327c1ac7a44f](https://github.com/kebag-logic/tsn-c-stack/commit/21d132baa148f4731a1622b425e4327c1ac7a44f) |
| [1a5d70faba6a9b01aab6bb868c12e4c7023e0c70](https://github.com/kebag-logic/milan-fpga/commit/1a5d70faba6a9b01aab6bb868c12e4c7023e0c70) | [590edd350f8b8790002b2ca7972b55ddea4d3c84](https://github.com/kebag-logic/tsn-c-stack/commit/590edd350f8b8790002b2ca7972b55ddea4d3c84) |
| [1b3cca0d0ae6c08dc32314dd9fc8d9fac34bfe3f](https://github.com/kebag-logic/milan-fpga/commit/1b3cca0d0ae6c08dc32314dd9fc8d9fac34bfe3f) | [e279a12585c918534846d8c4742f3ce5368c228a](https://github.com/kebag-logic/tsn-c-stack/commit/e279a12585c918534846d8c4742f3ce5368c228a) |
| [331455c95e424b33d3b299b85212603d06339e6b](https://github.com/kebag-logic/milan-fpga/commit/331455c95e424b33d3b299b85212603d06339e6b) | [53e6b06b7660876748cce9b6c6c9838cf0def922](https://github.com/kebag-logic/tsn-c-stack/commit/53e6b06b7660876748cce9b6c6c9838cf0def922) |
| [4a9fa9db61884bed6f7fe4b50fc178dbe76e119e](https://github.com/kebag-logic/milan-fpga/commit/4a9fa9db61884bed6f7fe4b50fc178dbe76e119e) | [3b0ad89f7ef09d05349b494c0abd539c76abe446](https://github.com/kebag-logic/tsn-c-stack/commit/3b0ad89f7ef09d05349b494c0abd539c76abe446) |
| [574911a2c8dcb98fb4619d6d2d237bbaa3b37f48](https://github.com/kebag-logic/milan-fpga/commit/574911a2c8dcb98fb4619d6d2d237bbaa3b37f48) | [53d4b4f171107808df5f053c74b27044d126ebcf](https://github.com/kebag-logic/tsn-c-stack/commit/53d4b4f171107808df5f053c74b27044d126ebcf) |
| [63ab3d6860b0137041e6cc95e0d7ff1ea7e65446](https://github.com/kebag-logic/milan-fpga/commit/63ab3d6860b0137041e6cc95e0d7ff1ea7e65446) | [31d1b2cbc12e3e112f454cb505dd0f425aa3c93c](https://github.com/kebag-logic/tsn-c-stack/commit/31d1b2cbc12e3e112f454cb505dd0f425aa3c93c) |
| [6c94e9f5f496ac25f8c4e31f9e3685c725de29f3](https://github.com/kebag-logic/milan-fpga/commit/6c94e9f5f496ac25f8c4e31f9e3685c725de29f3) | [42bb384d69cffc46b80c073c01d32edb78c51c19](https://github.com/kebag-logic/tsn-c-stack/commit/42bb384d69cffc46b80c073c01d32edb78c51c19) |
| [72597d223606ee9c3174dd7d68267921e40a8f3a](https://github.com/kebag-logic/milan-fpga/commit/72597d223606ee9c3174dd7d68267921e40a8f3a) | [bcc88a9325f43a2a4e40ac7d5771d6f059c67334](https://github.com/kebag-logic/tsn-c-stack/commit/bcc88a9325f43a2a4e40ac7d5771d6f059c67334) |
| [73df0cf13b69999815ff61506c31abe71af99433](https://github.com/kebag-logic/milan-fpga/commit/73df0cf13b69999815ff61506c31abe71af99433) | [fc80b724a5b347feb82293e81d81cd4e8b51cc7a](https://github.com/kebag-logic/tsn-c-stack/commit/fc80b724a5b347feb82293e81d81cd4e8b51cc7a) |
| [7ab3cd727225839ac17b26bdc9ae85b5d1b65b24](https://github.com/kebag-logic/milan-fpga/commit/7ab3cd727225839ac17b26bdc9ae85b5d1b65b24) | [7eec4a874bf68a00f5a134ef83314d9d78a9becd](https://github.com/kebag-logic/tsn-c-stack/commit/7eec4a874bf68a00f5a134ef83314d9d78a9becd) |
| [7c2df592ea6b7bedc535ae1dc3d346ed8927bbfa](https://github.com/kebag-logic/milan-fpga/commit/7c2df592ea6b7bedc535ae1dc3d346ed8927bbfa) | [dca441ce463702e231652d20e6c4adaeef4fe99e](https://github.com/kebag-logic/tsn-c-stack/commit/dca441ce463702e231652d20e6c4adaeef4fe99e) |
| [877c0b9d04078867e2bef481903745198527844c](https://github.com/kebag-logic/milan-fpga/commit/877c0b9d04078867e2bef481903745198527844c) | [45f901f73a04567cdf34447bc1fe7a597472b0c8](https://github.com/kebag-logic/tsn-c-stack/commit/45f901f73a04567cdf34447bc1fe7a597472b0c8) |
| [8b78a8fd36864246336c71c061ac4f21d629952f](https://github.com/kebag-logic/milan-fpga/commit/8b78a8fd36864246336c71c061ac4f21d629952f) | [8af735b2b498928699847a14ff0128e9920dc613](https://github.com/kebag-logic/tsn-c-stack/commit/8af735b2b498928699847a14ff0128e9920dc613) |
| [a71b8c8072c28c3511254484de5dda4e57e91d3f](https://github.com/kebag-logic/milan-fpga/commit/a71b8c8072c28c3511254484de5dda4e57e91d3f) | [c6a4168f361e5ed90d3430df11a1ed65421c64ca](https://github.com/kebag-logic/tsn-c-stack/commit/c6a4168f361e5ed90d3430df11a1ed65421c64ca) |
| [aa0fdd01efc946bad44036976acbc0acfe198bb1](https://github.com/kebag-logic/milan-fpga/commit/aa0fdd01efc946bad44036976acbc0acfe198bb1) | [7880839b74e962d71fcd0cc55fc392d091f5c036](https://github.com/kebag-logic/tsn-c-stack/commit/7880839b74e962d71fcd0cc55fc392d091f5c036) |
| [bd5c896957945a052149ff57c87ea33098124011](https://github.com/kebag-logic/milan-fpga/commit/bd5c896957945a052149ff57c87ea33098124011) | [578e1c608e8e896466b1b997f94cb567b972f279](https://github.com/kebag-logic/tsn-c-stack/commit/578e1c608e8e896466b1b997f94cb567b972f279) |
| [bf8bc6614f09ef2df5e87b67e8827fcc629fbcba](https://github.com/kebag-logic/milan-fpga/commit/bf8bc6614f09ef2df5e87b67e8827fcc629fbcba) | [724b6152b811eeb0ede28f425b3097bf294d5adb](https://github.com/kebag-logic/tsn-c-stack/commit/724b6152b811eeb0ede28f425b3097bf294d5adb) |
| [c11735c637ff05f605faf0be027e92037c84e273](https://github.com/kebag-logic/milan-fpga/commit/c11735c637ff05f605faf0be027e92037c84e273) | [9911f6586778abd8f9c5f81ffbc7c0343a9c9d7d](https://github.com/kebag-logic/tsn-c-stack/commit/9911f6586778abd8f9c5f81ffbc7c0343a9c9d7d) |
| [c28743c1a3ca95c6c5c62e5fa4f442c0b0d6d938](https://github.com/kebag-logic/milan-fpga/commit/c28743c1a3ca95c6c5c62e5fa4f442c0b0d6d938) | [ba5cf26d3e156d01d64eafed60a906e8162a56f2](https://github.com/kebag-logic/tsn-c-stack/commit/ba5cf26d3e156d01d64eafed60a906e8162a56f2) |
| [d4bc335c20ad764fdcda7ebef6a6cd64dc60af93](https://github.com/kebag-logic/milan-fpga/commit/d4bc335c20ad764fdcda7ebef6a6cd64dc60af93) | [03326a8f1a2c8180a8aa62b633c6cdc56b81598b](https://github.com/kebag-logic/tsn-c-stack/commit/03326a8f1a2c8180a8aa62b633c6cdc56b81598b) |
| [d8b355fe0f41d49dca6cae1cd8b3826e2edde364](https://github.com/kebag-logic/milan-fpga/commit/d8b355fe0f41d49dca6cae1cd8b3826e2edde364) | [04ef07dcd7a2bf91bbda88931023524d96f4e658](https://github.com/kebag-logic/tsn-c-stack/commit/04ef07dcd7a2bf91bbda88931023524d96f4e658) |
| [e21c1ca024d37ea188ad15b5c8f9c2dae18628df](https://github.com/kebag-logic/milan-fpga/commit/e21c1ca024d37ea188ad15b5c8f9c2dae18628df) | [537548433829e238e714eb752a2a3b3419b88be1](https://github.com/kebag-logic/tsn-c-stack/commit/537548433829e238e714eb752a2a3b3419b88be1) |
| [f42c2de88d033d9bcfe73c49b716dbc70bef26f2](https://github.com/kebag-logic/milan-fpga/commit/f42c2de88d033d9bcfe73c49b716dbc70bef26f2) | [c369add12886fba546683c340a19d1b94c6d2a11](https://github.com/kebag-logic/tsn-c-stack/commit/c369add12886fba546683c340a19d1b94c6d2a11) |

## Squash metadata

The owner-created [squash commit](https://github.com/kebag-logic/tsn-c-stack/commit/ae982af85ec97286bd35b39403926d8f0eaec81d)
uses hosted merge identities and a message body.
The [follow-up assignment](https://github.com/kebag-logic/milan-fpga/issues/697#issuecomment-6074811248) fixes it as the branch base.
The [privacy gate](../scripts/check_privacy.py) exempts only that exact commit from identity and one-line checks.
It still scans that commit's content and every reachable blob. Every new commit must use the configured holder identity and one-line subject.
