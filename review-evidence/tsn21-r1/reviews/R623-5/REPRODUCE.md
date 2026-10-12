The scripts accept a detached source checkout as their first argument. Use the pinned test dependencies described by the repository: GoogleTest/GMock 1.14.0, Clang 18 for lexical checks, a hosted C/C++ compiler, the freestanding RV32 compiler and QEMU. Set PATH, TSN_CLANG, CMAKE_PREFIX_PATH, PKG_CONFIG_PATH and LD_LIBRARY_PATH for the local installation. Do not use an ambient test-library version in place of the pin.

Run from this packet directory, substituting the source checkout path:

```sh
export PYTHONDONTWRITEBYTECODE=1
python3 scripts/prepare.py "$REVIEW_SOURCE"
python3 scripts/focused_checks.py "$REVIEW_SOURCE" --phase build
python3 scripts/focused_checks.py "$REVIEW_SOURCE" --phase checks
python3 scripts/identity_and_merge.py "$REVIEW_SOURCE" --cc riscv64-elf-gcc
python3 scripts/regenerate_and_collect.py
python3 scripts/prior_shared_assertion_probe.py "$REVIEW_SOURCE"
python3 scripts/integrity.py "$REVIEW_SOURCE"
```

All disposable trees and builds are below scratch. The foreground runner waits for every subprocess and records a separate log/return code. Builds use make -j16; independent focused campaigns run concurrently with four workers each. The portable runner limits each of the two concurrent RV32 configurations to two workers. The recorded RV32 run used four per configuration; the reproduction runner uses two per configuration to bound configured concurrency across all four task families. The original prior probe retains its eight-job setting and runs separately.

The source and integration publication campaigns each select 18 plants. Shared and separate future-field campaigns each select five restore-loss plants. The shared cache gate is expected to return 1 specifically for shared ownership; it is not a failing review check. Mutant executable return code 1 denotes a caught, assertion-matched defect when the campaign result is CAUGHT. Generation operates only on the disposable integration copy and requires identical output bytes.

The unchanged prior probe was fetched from the immutable public evidence commit 380d86e7d936f35d05dfb558a3b5cbc17da6e340, path review-evidence/tsn21-r1/reviews/R623-4/scripts/shared_assertion_probe.py, after the independent verdict was recorded. Published author receipts under receipts/published-r4 are selected files from that commit's author-r4/round4 directory. They are author evidence, distinct from reviewer execution and from manager merge-turn duties.

Receipt text preserves command results, diagnostics, streamed assertion markers, counts and return codes. Public copies normalize host path prefixes to symbolic roots and omit unrelated account metadata from API snapshots; the normalization ledger records original and publication SHA-256 values. Original execution bytes remain only in scratch/raw-receipts and are not published. Object/token hashes and equality decisions were computed on original bytes before any receipt-text normalization. No production file was normalized or edited.

MANIFEST.sha256 lists all publishable files. Scratch is deliberately excluded.
