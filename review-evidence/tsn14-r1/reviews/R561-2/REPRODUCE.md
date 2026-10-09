# Reproduction

Use an isolated checkout at `663f14de4a07bb1a777282fdfc83d30fd03843d4`. Supply the packet directory, the supplied compiler prefix, and the GoogleTest/GMock 1.14.0 prefix as arguments. All builds, extracted packages and mutation copies stay under `scratch/`.

```sh
python3 scripts/provision-sdk.py "$PACKET"
python3 scripts/with-sdk.py "$PACKET" "$COMPILER_PREFIX" "$TEST_PREFIX" python3 scripts/run-gates.py "$SOURCE" "$PACKET" --jobs 16
python3 scripts/with-sdk.py "$PACKET" "$COMPILER_PREFIX" "$TEST_PREFIX" python3 scripts/run-probes.py "$SOURCE" "$PACKET"
python3 scripts/anchor-audit.py "$SOURCE" "$PACKET"
python3 scripts/integrity.py "$SOURCE"
python3 scripts/collect-receipts.py "$SOURCE" "$PACKET" --dependency-root "$DEPENDENCY_ROOT"
```

Run these from the packet directory, using absolute arguments. The campaign runner invokes the checkout's unmodified `validate.py --graphs` and `baremetal.py` concurrently and stays attached until both finish. The published probe driver is unchanged; four copies build concurrently with four workers each. Probe failure assertions are expected. The baseline must pass, each probe must build, and the affected MF-tagged test must fail.

The supplied compiler prefix is first on PATH. Its `clang-18` launcher referenced an external scratch directory. It was not executed. `TSN_CLANG` selects a packet-local launcher for the compiler bytes in the supplied prefix. The generic `clang` and `clang++` launchers use those same bytes. No shared dependency is modified. Compatible C++ headers and sanitizer runtimes are extracted from public packages whose URLs and hashes are in `receipts/sdk-packages.json`. GoogleTest is selected using PKG_CONFIG_PATH, CMAKE_PREFIX_PATH and LD_LIBRARY_PATH. External test filters and ambient include paths are cleared by the campaign runner.

The source authorities are retrieved from the pinned public source revision. The unchanged probe driver came from `review-evidence/tsn14-r1/reviews/R560-1/scripts/claim_probe.py` at evidence commit `8623919ec00c5ac91e66d1c6eda0dbca8963ed83`, blob `4651d3b185945a1ae9cc2d57c71f2c6717e115b5`. The three `receipts/prior-probes/*.json` records supply its exact substitutions.

`receipts/NORMALIZATION.json` records original and published hashes for copied execution receipts. Only locations and terminal control sequences are normalized; assertions, counts, statuses and return codes are retained. Hosted extracts preserve the exact-head checkout and executed gate lines. Hosted job summaries distinguish successful steps from skips. Files under scratch are never published.

Technical reproduction cannot repair the review-order failure recorded in REPORT.md. A new cleared-context review is needed for the independent approval requirement.
