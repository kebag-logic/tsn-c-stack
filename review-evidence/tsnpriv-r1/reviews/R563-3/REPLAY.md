Use Python 3 and Git. SOURCE is a clean detached checkout at b7c6b7ba0007aaa5791df68d30296423127b003e; PACKET is this packet's directory. No build dependencies are needed for focused probes.

```sh
python3 scripts/focused_review.py "$SOURCE" "$PACKET"
python3 scripts/verify_checkout.py "$SOURCE" "$PACKET"
```

The foreground driver joins independent campaigns with at most four workers. Mutation copies and fixtures stay under scratch/. These scripts read the source checkout without editing it or creating commits. Results appear in receipts/focused/; every CLI/mutant subprocess has a log and return-code file. Original R562-1 fault transformations are unchanged; the wrapper omits the old-head checkout and synthetic-commit operations.

validator-fixtures.json records mocked dispatch: 24 gates without graphs, 25 with graphs, and fail-fast handling. These fixtures do not execute a compiler bank.

Refresh selected hosted archives with authenticated read-only repository access:

```sh
python3 scripts/inspect_hosted.py "$PACKET"
```

Archive SHA-256 digests are verified against the API. Archives stay under scratch/; selected text receipts are retained. Hosted checkout paths become <checkout>; original and published hashes are recorded. Metadata, body/settings snapshots, discussion inventory and job excerpts describe review-time state and may change later.

```sh
sha256sum -c MANIFEST.sha256
```

The manifest authenticates the delivered packet, not a later replay. Only listed files and REPORT.md are publishable. Never publish scratch/.
