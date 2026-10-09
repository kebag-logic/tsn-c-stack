# Replay the focused review checks

Use Python 3 and a detached clone at `b7c6b7ba0007aaa5791df68d30296423127b003e`.
Set `SOURCE` to that clone and `PACKET` to this packet. All commands run in the
foreground. No source edits, commits or public writes are needed.

```sh
python3 "$PACKET/scripts/independent_probes.py" "$SOURCE" "$PACKET/receipts/probes"
python3 "$PACKET/scripts/replay_mutants.py" "$SOURCE" \
  "$PACKET/scripts/published-mutant_probes.py" \
  "$PACKET/scratch/mutants" "$PACKET/receipts/mutants"
python3 "$PACKET/scripts/check_integrity.py" "$SOURCE" \
  "$PACKET/receipts/initial-index.txt" "$PACKET/receipts/checkout-integrity.json"
```

The first script exercises the real CLI plus controlled repository-response
fixtures for the per-commit checks and their invocation from `main()`.
The fixtures create no commit objects. Expected and actual results are preserved
in `receipts/probes/independent-probes.json`.

The original [published mutation script](https://github.com/kebag-logic/tsn-c-stack/blob/5f9b951b14fa8c22b03ea9b5cde49ed57033279b/review-evidence/tsnpriv-r1/reviews/R562-1/scripts/mutant_probes.py)
is retained byte for byte as `scripts/published-mutant_probes.py`.
Run it through the replay wrapper above. The wrapper evaluates its unchanged
declarations and uses all nine exact substitutions, with unique-anchor checks.
It runs the actual `--selftest` subprocess for each disposable source copy, in
normal and optimized Python. The unmutated control must return zero; every
fault must return nonzero and print a failed selftest case.

The original script's old-head checkout and synthetic commit creation are omitted
to obey this round's exact-head and no-commit restrictions. Its real-history and
synthetic-history detector columns are therefore not claimed as replayed.
The required selftest detector and every published fault substitution are replayed.

The hosted evidence collector uses authenticated read-only repository access:

```sh
python3 "$PACKET/scripts/collect_hosted.py" "$PACKET"
```

It downloads exact-head artifacts concurrently, checks the API's SHA-256 digest
for each archive, and keeps downloads and extracted trees under `scratch/`.
Selected unmodified hosted receipts are copied for publication. Job-log excerpts
retain their timestamps, with terminal color escapes removed. Public hosted
workspace paths in raw receipts are not local reviewer paths.

Full native and RV32 campaigns were inspected through published author and
exact-head hosted receipts; they were not run locally in this round. The local
execution consists of the focused scripts above. No heavy build or RTL simulator
was run. The current-dev merge candidate remains a manager duty.

`MANIFEST.sha256` lists the publishable files using paths relative to this packet.
`scratch/` is disposable and must never be published.
