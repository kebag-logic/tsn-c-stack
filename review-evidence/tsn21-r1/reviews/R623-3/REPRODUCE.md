Use a clean detached checkout of `f3dc2ae5bad02aa05a504b43c207e8b304d2bed5` and a separate output packet. Disposable source copies and builds stay below the packet `scratch/`; that directory is not publishable.

Supply GCC/G++, Python 3.12 or later, CMake, GoogleTest/GMock 1.14.0, Clang 18 for lexical checks, RV32 GCC and the RISC-V emulator. Set `PKG_CONFIG_PATH`, `CMAKE_PREFIX_PATH` and, for shared libraries, `LD_LIBRARY_PATH` to the pinned GoogleTest installation. Set `TSN_CLANG` to the Clang 18 executable. The run used native GCC 16.2.1, RV32 GCC 16.2.0 and Clang 18.1.3. No dependency installation or private source tree is needed. Public reference fetches use authenticated read-only repository API access.

With `SOURCE` and `PACKET` set to those two directories, execute each command in the foreground:

```sh
python3 "$PACKET/scripts/prepare.py" "$SOURCE" "$PACKET"
python3 "$PACKET/scripts/run_checks.py" "$SOURCE" "$PACKET"
python3 "$PACKET/scripts/cache_probes.py" "$SOURCE" "$PACKET"
python3 "$PACKET/scripts/rv32_cache_controls.py" "$SOURCE" "$PACKET"
python3 "$PACKET/scripts/identity.py" "$SOURCE" "$PACKET"
```

`run_checks.py` joins independent campaigns in one foreground process: mutation 8 jobs, RV32 2 per configuration, metadata/registration 2 jobs and one object comparison. Their combined maximum is 15. RV32 fault controls run at most two campaigns, each with two 4-job builds: maximum 16. Each campaign has its own log and return-code receipt. No detached process is launched. Override `REVIEW_RV32_CC` if the RV32 compiler has another executable name; the repository toolchain also needs to find its supported RV32 compiler.

The first run checks all 340 mutations, both RV32 configurations, the generated documents, named assertion messages, comment policy, port contracts and all six object flag sets. Its mutation baseline executes 380 test instances across seven binaries. It creates the stock test objects used by `cache_probes.py`.

The cache script compiles each isolated restore omission and runs both the stock ACMP suite and independently extended witnesses. Expected results at this head: stock head/bound/started 77 tests pass; stock stream fails the repository stream-withdrawal assertion. The 80-test witness suite passes on the head and fails one field-specific witness on each field plant (the stream plant also fails the repository assertion). RV32 fault controls catch bound and pass started/stream; those limitations are evidence, not a claim that the faults are harmless.

`object_compare.sh` is unchanged from the public R622-1 executable artifact at evidence commit `3412290309887cbe686d673380820e88021989bc`. Its own exit status checks equality after stripping debug data. Review `receipts/local/objects.log` as well: this round requires and obtains raw equality for all six pairs. `public-evidence-audit.json` records its original blob/hash and verifies the downloaded public receipts and hosted archive digests.

`public_reconcile.py` requires the independently recorded verdict/hash before it will read PR comments. It emits only manager bodies and finding IDs, discarding all other bodies. Do not use it before writing an independent verdict and five-lens ledger.

Published execution logs preserve test/compile outcomes, messages, counts and return codes. Absolute local working-directory prefixes are normalized to `$SOURCE`, `$REVIEW_PACKET` and `$DEPENDENCIES`; pre-normalization hashes are recorded in `receipts/path-normalization.json`. Public downloaded evidence is retained unchanged. No binaries, dependency extractions, disposable source trees or builds are published.
