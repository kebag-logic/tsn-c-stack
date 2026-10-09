Reproduction uses a detached checkout at 66b3a75746fbbca3cffdfc7d89f013ab14aa1cc0. Set SOURCE to that checkout, PACKET to this packet, DEPENDENCIES to the pinned dependency 1.14.0 prefix, and COMPILER_PACKAGES to the directory containing the pinned version-18 package archives. Supply the RISC-V compiler, simulator and diagram renderer in PATH. No system installation is performed.

```sh
python3 "$PACKET/scripts/prepare_sdk.py" "$COMPILER_PACKAGES"
python3 "$PACKET/scripts/run_gates.py" "$SOURCE" --dependencies "$DEPENDENCIES" --compiler-bin "$PACKET/scratch/bin" --jobs 2
python3 "$PACKET/scripts/run_probes.py" "$SOURCE" --cc gcc --jobs 2
python3 "$PACKET/scripts/run_probes.py" "$SOURCE" --cc gcc --jobs 2 --select review-control-mask-removed
python3 "$PACKET/scripts/verify_source.py" "$SOURCE" --output "$PACKET/receipts/source-final.json"
```

Each parent remains in the foreground and joins all children. Gate output has separate logs and return-code files. The source is never mutated; plants are made only in packet scratch. The SDK helper extracts packages with ar/tar and verifies the downloaded package digests against the published author package manifest. Its local command wrappers select compiler/analyzer version 18.1.3 and compatible version-13 C++ headers without changing the runtime library.

To regrade the published campaign without compiling or network access:

```sh
python3 "$PACKET/scripts/regrade.py" "$PACKET/receipts/mutation-plants.json" "$PACKET/receipts/local/mutations" --output "$PACKET/scratch/regraded.json"
```

The regrader checks XML completeness, execution status, absence of skips/errors, and owned assertion-message delimiters. Exact named killers must match; a registered prefix killer requires a matching member, as specified by the campaign format. All five state-specific killers for each new ADP plant are exact names.

`fetch_public.py` retrieves public records using read-only requests. Record an independent verdict before inspecting earlier review content. `collect_receipts.py SOURCE --tools-prefix DEPENDENCIES_PARENT` exports execution receipts, public observations and raw/published digest provenance after a local run. It substitutes only host-location prefixes. Standards files and SDK/build trees are deliberately not published.

The initial local run selected ambient unversioned compiler/analyzer commands. It passed but was superseded by the complete pinned rerun. `initial-gate-run.json` identifies that preliminary run; `gate-run.json` and `receipts/local/` identify the qualifying run. Independent probes used GCC with address and undefined-behavior instrumentation.
