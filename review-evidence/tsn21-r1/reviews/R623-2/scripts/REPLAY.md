Run from the exact detached source checkout. Set `PACKET` to a disposable packet directory, `GTEST_PREFIX` to a GoogleTest/GMock 1.14.0 installation, and `TSN_CLANG` to a working Clang 18 executable. Supply the compiler’s runtime library path if necessary. RV32 GCC, CMake, Python, and QEMU must be available. No shared installation is modified.

```sh
export CMAKE_PREFIX_PATH="$GTEST_PREFIX"
export PKG_CONFIG_PATH="$GTEST_PREFIX/lib/pkgconfig"
export PYTHONDONTWRITEBYTECODE=1
python3 "$PACKET/scripts/run_checks.py" "$PWD" "$PACKET" one
python3 "$PACKET/scripts/run_checks.py" "$PWD" "$PACKET" two
python3 "$PACKET/scripts/run_checks.py" "$PWD" "$PACKET" three
python3 "$PACKET/scripts/run_checks.py" "$PWD" "$PACKET" four
python3 "$PACKET/scripts/rv32_probe_check.py" "$PACKET"
python3 "$PACKET/scripts/compare_tokens.py" "$PWD" "$PACKET"
python3 "$PACKET/scripts/audit_mutations.py" "$PWD" "$PACKET/scratch/mutations" "$PACKET/receipts/local-mutation-audit.json"
python3 "$PACKET/scripts/integrity.py" "$PWD" "$PACKET/receipts/integrity.json"
```

Each phase is a foreground orchestrator that waits for its concurrent children. Phases must not overlap: the mutation/witness phase and the broader probe phase each budget at most 16 build jobs. The original external scripts are preserved under `receipts/public/reviews/R622-1/scripts/`; their byte identity to the published Git blobs is in `receipts/reused-script-identity.json`.

The source reference files are `receipts/authority-acmp.c`, `receipts/authority-acmp.h`, and the baseline files alongside them. `receipts/authority-index.json` records their repository and commit provenance. The exact public evidence revision is `3412290309887cbe686d673380820e88021989bc`, directory `review-evidence/tsn21-r1`, in `kebag-logic/tsn-c-stack`.

The saved hosted mutation receipts can be regraded without downloading or rebuilding:

```sh
python3 "$PACKET/scripts/audit_mutations.py" "$PWD" "$PACKET/receipts/hosted/quality/mutations" "$PACKET/receipts/hosted-mutation-audit.json"
```

For object comparison, the unchanged external script returns success on stripped equality. Inspect every raw result, or compare the six `scratch/objects/out/*-left.o` / `*-right.o` byte pairs explicitly. Do not infer raw equality from its return code.

For the witness script, its return code reports build viability; the raw test logs must show the head passing and each targeted fault failing the corresponding repository and witness assertion. For the broader probe script, independently check successful compilation and raw failure messages; its `failed_tests` extraction is incomplete.

Only paths in `MANIFEST.sha256` and `REPORT.md` are publishable. Scratch content is excluded. Exported command/XML receipts preserve diagnostics and numerical results, replacing only machine-specific path prefixes; hashes of original bytes are in `receipts/export-map.json`. The first metadata attempt’s compiler-launcher failure is retained as `*-initial.log` and `*-initial.rc`; phase four records the successful corrected environment.
