The scripts operate on a clean checkout at the reviewed head. They place disposable sources, extracted dependencies, builds and binaries under this packet's `scratch/` directory. Nothing there belongs in the publication manifest. All runners stay in the foreground and join their children.

Dependencies: Python 3.12 or newer, Git, authenticated read access through the GitHub CLI, CMake/Make, a C/C++ compiler, GoogleTest/GMock exactly 1.14.0, the RV32 cross compiler and QEMU, and Clang 18 with its runtime dependencies. No installation or privileged command is required by these scripts. Supply a pre-existing GoogleTest prefix and a directory containing the Clang 18 dependency packages. The recorded run extracted available Ubuntu 18.1.3 packages and used the installed RV32 compiler identified in the comparison receipt.

Run these from this packet directory, replacing the two argument paths:

```sh
python3 scripts/prepare_dependencies.py --clang-packages /path/to/packages
python3 scripts/fetch_authorities.py
python3 scripts/fetch_evidence.py
python3 scripts/run_checks.py /path/to/checkout --gtest /path/to/gtest-1.14.0 --phase build
python3 scripts/run_checks.py /path/to/checkout --gtest /path/to/gtest-1.14.0 --phase checks
python3 scripts/compare.py /path/to/checkout
python3 scripts/probe.py /path/to/checkout --gtest /path/to/gtest-1.14.0
python3 scripts/audit_evidence.py /path/to/checkout
python3 scripts/sanitizer_limit.py /path/to/checkout --gtest /path/to/gtest-1.14.0
python3 scripts/integrity.py /path/to/checkout
```

`run_checks.py --phase checks` runs independent work concurrently: six mutation workers, up to eight RV32 compile workers, one source-control worker and one test worker. The initial hosted build uses `make -j16`. The comparison and probe runners use four workers. Do not run multiple such runners concurrently without reducing their combined worker limit.

The comparison uses the repository's pinned compiler lexer and explicitly compares token spelling/kind after removing only comment and whitespace tokens. Baseline preservation checks exact line bytes, not normalized text. Object builds use identical source basenames, include paths and flags, with debug metadata disabled on both sides; no object postprocessing occurs. The assertion-enabled/disabled cases retain the re-entry hook.

The probe runner compiles a disposable copy of the shipped ACMP test translation unit with three appended tests. It then compiles the unmodified core and three independently changed core copies. Expected results are rc 0 for the original and rc 1 for each negative control. XML records show the actual failing assertions. These are review evidence, not committed source changes.

`audit_evidence.py` compares the hosted XML selection against executable registration from the locally built mutation baselines, keeps separate build arms distinct, and checks the declared streamed message needles. It also verifies artifact digests and the run's 25 gate return codes. The ZIP files are original hosted downloads, retained to make receipt regrading possible after remote artifacts expire.

`sanitizer_limit.py` reproduces the recorded host-header failure with two syntax checks carrying sanitizer flags; it is not a sanitizer execution suite. On a host with compatible headers it may succeed and therefore reject the expected limitation. Hosted sanitizer evidence remains separate.

`MANIFEST.sha256` lists publishable files, relative to this directory. REPORT.md is also published. Unlisted material, especially `scratch/`, must not be published.
