Use an isolated, clean checkout of `db950cfa959f501932a47d4113733a671f882a83` and a separate packet directory. The scripts accept locations as arguments. They do not modify tracked source or write to GitHub.

The host needs Python, GitHub read access, CMake, GCC/G++, pkg-config, tar/bsdtar, cppcheck, a RISC-V bare-metal compiler, QEMU and the Mermaid renderer. The setup script fetches GoogleTest/GMock at `f8d7d77c06936315286eb55f8de22cd23c188571` and extracts Clang 18.1.8 and its dependencies only beneath scratch. Package versions and hashes are retained in the [setup receipt](receipts/sdk-setup.log). No shared installation is used.

```sh
python3 scripts/fetch-authorities.py PACKET
python3 scripts/prepare-sdk.py PACKET/scratch
python3 scripts/audit-source.py CHECKOUT PACKET/scratch/authorities
python3 scripts/run-gates.py CHECKOUT PACKET
python3 scripts/check-mutation-receipts.py PACKET/scratch/validate-compatible/mutations
```

The target runner remains attached until both commands finish. It passes `--jobs 4` to both campaign drivers. Their internal independent work runs concurrently. The observed review service peak was below its 12 GiB cap. SDK builds use `-j16`.

The first local run exposed an environment mismatch: Clang 18 selected the host's libstdc++ 16 headers. The [failed build receipt](receipts/initial-environment/clang-sanitizers-build.log) is retained. The final runner explicitly supplies libstdc++ 13 headers to Clang++, while retaining project warnings, sanitizers and the exact GoogleTest package. It clears ambient include/library path variables. The complete validation then passes. GCC and RV32 use the installed 16.2.0 compilers. No source workaround was made.

The [gate-count script](scripts/gate-count.py) compares saved PR metadata, the local gate JSON and the exact-head hosted log. Its [receipt](receipts/gate-count.txt) records the open validation-count finding. It expects the captured API/log inputs under scratch, which are not part of the publication; retrieve PR #18 and job 113850082778 read-only to repeat that comparison.

The published execution receipts retain return codes, results, XML assertion failures and gate output. The [normalization record](receipts/NORMALIZATION.json) gives original and published hashes. Only source, packet and user-home locations were replaced by neutral placeholders. Hosted log extracts retain checkout identity and validation output. Full standards PDFs, SDK packages, executables and disposable mutation trees stay under scratch and are not published.
