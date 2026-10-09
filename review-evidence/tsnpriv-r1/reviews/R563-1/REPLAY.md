Run from the packet root, replacing CHECKOUT with a clean checkout of commit 61fb7c9a523b89cb96d493c5baf9f7f866ebed85:

```sh
python3 scripts/review_probes.py --repo CHECKOUT --work scratch/replay-probes
python3 scripts/validator_wiring.py --repo CHECKOUT --work scratch/replay-validator
python3 scripts/check_integrity.py --repo CHECKOUT --initial-index receipts/initial-index.txt
sha256sum -c MANIFEST.sha256
```

These scripts read the checkout and create only designated scratch fixtures. They create no commits and change no tracked source. Privacy integration fixtures supply controlled repository responses. Validation fixtures intercept command execution and establish dispatch/failure behavior only.

The base gate implementation is run against the head checkout's history and tree, not against a separate base checkout. No full validation bank is executed by these scripts.

receipts/published contains verbatim author-packet files checked against receipts/published-manifest.json. Hosted ZIP archives are original downloads checked against receipts/hosted-artifacts.json; selected files are also extracted under receipts/hosted. Raw public job logs retain their original hosted paths.

Only files enumerated by MANIFEST.sha256 and REPORT.md are for publication. scratch is never published.
