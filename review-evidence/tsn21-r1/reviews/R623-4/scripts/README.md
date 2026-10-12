Reproduce against a detached clone at bc68ad8f3577e8f3dc24c4336e9b80a933df6c79. These scripts locate the packet from their own location, accept the source clone as their sole argument, and write disposable trees only to the packet scratch directory. They do not modify the source clone.

Supply Python 3.10+, C/C++ compilers, CMake/make, exact GoogleTest/GMock 1.14.0, a Clang 18 executable for raw token extraction, an RV32 bare-metal compiler, and the RISC-V emulator. Set TSN_CLANG to the Clang 18 executable. Set PKG_CONFIG_PATH, CMAKE_PREFIX_PATH and any runtime library path required by the exact test-framework installation. Dependency paths are supplied through the environment rather than embedded host locations.

Run from any directory:

```sh
python3 packet/scripts/run_focused.py source-clone
python3 packet/scripts/cache_controls.py source-clone
python3 packet/scripts/identity.py source-clone
python3 packet/scripts/shared_assertion_probe.py source-clone
```

The last command reproduces R623-4-F1. Its cache and needle logs return zero despite two field mappings sharing one assertion; its five-plant campaign returns zero with both the bound and future plants failing that same assertion. Inspect the retained patch, JSON and XML. A corrected completeness gate should reject this control. The script currently records the observed return codes without interpreting acceptance as a correct gate result.

The main runner uses a foreground executor: a hosted make -j16 build runs alongside metadata checks, then an eight-worker hosted campaign runs concurrently with the two four-worker RV32 configurations. Every build/campaign command finishes in the foreground and has its own log and return-code receipt. No parent or hardware bank is invoked. The first metadata and suite phase is separate from the campaign phase, preserving the sixteen-worker compilation budget.

fetch_author.py reads immutable published author blobs using the stored tree index and verifies each Git blob hash. It requires read access through the repository CLI. The reference ACMP source/header are included in receipts/authorities for the identity script. No network write is made.

The independently frozen verdict is receipts/independent-verdict.md with its SHA-256 and timestamp in receipts/independent-verdict-seal.json. REPORT.md adds prior-finding reconciliation and final integrity. Its control-count prose corrects the frozen snapshot: the independent ordinary CLI campaign contains sixteen controls, not seventeen; the underlying JSON was unchanged. The initial empty-campaign invocation error for the finding probe is retained separately from the corrected successful campaign.

Raw logs are retained as execution receipts. Build directories, object files, downloaded archives, and source copies under scratch/ are never published. Only files named by MANIFEST.sha256 and REPORT.md are publishable.
