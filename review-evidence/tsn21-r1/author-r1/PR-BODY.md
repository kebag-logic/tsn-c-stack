[A602]

Relates to #21

Carry F-INT's ACMP publish port from `09c7231eca343607c97c0d66abebb2553688712c` onto `1a9f651cdf7846b8e10ac246a6ef6916960fbb92`. Publish each changed bound, started and settled stream-ID triple before new frames and first at completion; retain its cache across reset and guard callback re-entry. Integrators must provide the new callback and apply publication before returning.

Port all six publication regression cases, add fourteen assertion-specific mutation plants and extend the minimal RV32 smoke checks. Document the published-before-promised ordering in `docs/PORTING.md` and trace it through ACMP-10.

The two core files have exactly the reference's non-comment tokens: 7849 and 1175 respectively. The baseline bytes remain intact around the added port. Comments follow the repository contract. Same-flag RV32 objects are byte-identical at both tested optimization levels.

Validate with:

```sh
python3 scripts/validate.py --work build-validation --jobs 16 --graphs
python3 scripts/baremetal.py --work build-rv32 --jobs 16
```

Hosted tests, complete adjusted coverage, all 338 mutation plants and the source/metadata gates pass. RV32 Debug and Release pass. The local sanitizer build reproduces the baseline host-header failure; per the acceptance amendment, the hosted sanitizer job must pass after publication. The manager still owns publication, two reviews and the merge commit.
