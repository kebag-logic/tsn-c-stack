Use an isolated checkout at `663f14de4a07bb1a777282fdfc83d30fd03843d4` and this packet. Keep generated files beneath packet `scratch/`. Set `CHECKOUT`, `PACKET`, `DEPENDENCY_PREFIX` and `LEXER_BIN` to the checkout, packet, GoogleTest/GMock 1.14.0 prefix and supplied Clang 18 executable directory.

The first run used the prescribed package/build/runtime paths and placed the supplied lexer directory first on PATH. That directory contains only the versioned lexer launcher; the unversioned sanitizer compiler selected host Clang 23. The second full run additionally selects the supplied Clang 18 compiler with compatible public headers/runtime extracted only under scratch. Both runs' receipts are retained separately.

```sh
python3 "$PACKET/scripts/integrity.py" "$CHECKOUT"
python3 "$PACKET/scripts/run_gates.py" "$CHECKOUT" "$PACKET" \
  --dependency-prefix "$DEPENDENCY_PREFIX" --lexer-bin "$LEXER_BIN" --jobs 3
python3 "$PACKET/scripts/provision_compat.py" "$PACKET" --lexer "$LEXER_BIN/clang-18"
python3 "$PACKET/scripts/run_gates.py" "$CHECKOUT" "$PACKET" \
  --dependency-prefix "$DEPENDENCY_PREFIX" --lexer-bin "$LEXER_BIN" \
  --driver-bin "$PACKET/scratch/compat/bin" --work-name gates-clang18 --jobs 3
python3 "$PACKET/scripts/run_claims.py" "$CHECKOUT" "$PACKET" \
  --dependency-prefix "$DEPENDENCY_PREFIX"
python3 "$PACKET/scripts/audit_sources.py" "$CHECKOUT" "$PACKET/receipts"
python3 "$PACKET/scripts/integrity.py" "$CHECKOUT"
```

The gate runner holds both subprocesses in the foreground and joins them. Each native driver uses three workers, while the independent RV32 driver uses two. The published claim script is unchanged and builds each of four copies with four workers: at most sixteen build jobs. Do not overlap that probe runner with another campaign. No direct make invocation is needed; the drivers supply their parallel limits to CMake.

`claim_probe.py` was downloaded from the published R560-1 script at evidence commit `06a9908b3d0a8cd691adfc793f61ba2dbb4e1cb4`, with SHA-256 `8ac24479992f96b1246e7916454d507926d818a1ffa388c7733602f979f9f1d4`. Its four original inputs are in receipts/prior-probe-inputs. The wrapper additionally checks all seven result files, 372 completed instances, no disabled/skipped cases, and the required MF tags on failed tests. Compilation errors do not count as kills.

The source audit consumes source-FR_NFR.md and source-REQUIREMENTS.md downloaded from milan-fpga at `5603c353137e90c1fa95429f6d00ef7a2298d9ee`. Their canonical paths are docs/reference/FR_NFR.md and REQUIREMENTS.md. It parses the upstream ID/line pairs independently and compares them with the local map and catalog, then plants a moved anchor.

`receipts/initial` and `receipts/clang18` contain complete gate logs/return codes, mutation XML/results and both-target summaries. `receipts/claims` contains the four probe copies' raw test reports and logs. Execution locations are normalized for publication; NORMALIZATION.json records the raw and published hashes. Original unmodified logs, copied source trees, SDK files and binaries stay in unpublished scratch.

`receipts/hosted` was downloaded read-only from pull-request run 37944235910. Run/job metadata also captures push run 37944216211. Both identify the exact head. Public author evidence and this review's runs are separate from future manager candidate validation.
