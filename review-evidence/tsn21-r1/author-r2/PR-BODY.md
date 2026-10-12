[A602]

Relates to #21

Carry milan-fpga F-INT's required ACMP `publish` callback from `09c7231eca343607c97c0d66abebb2553688712c`. Publish changed bound, started and settled stream-ID state before new frames and first at completion. Preserve the publication cache across reset and refuse callback re-entry. Integrators must supply the callback and apply its state before returning.

The six upstream cases and fake are ported, with publication plants, RV32 smoke checks and API documentation. The branch retains the assigned `1a9f651cdf7846b8e10ac246a6ef6916960fbb92` base.

## Round 2

- Add named assertions and mutations for publication after timers and loss of the stream cache during reset.
- Trace ACMP-10 to issue #21 and F-INT at `09c7231e`, including commits `5a50b2045` and `7c583daac`; link the exact Milan and IEEE clauses.
- Preserve upstream comment lines as blank lines. All 7,849 source tokens and 1,175 header tokens match F-INT, including their line positions. No core behavior changes in this round.

The unchanged reviewer probes and witnesses catch both required faults by the new named repository assertions; the unmodified witness suite passes.

All 25 Linux gates and both RV32 configurations pass. The hosted suite has 380 instances; adjusted coverage remains 100% in every measured file; all 340 mutations are caught, with zero escapes or errors. Clang 18 ASan/UBSan and leak checks pass locally with compatible C++ headers and matching runtime archives.

All six raw RV32 object pairs are byte-equal before stripping, using the same source directory, wire header, minimal port headers and RV32 GCC 16.2.0. Every comparison uses these common flags:

```sh
-Isrc -I"$PORT_INCLUDE" -march=rv32i -mabi=ilp32 -ffreestanding -fno-builtin -nostdinc -isystem "$(riscv64-elf-gcc -print-file-name=include)" -std=c11 -Wall -Wextra -Werror
```

`PORT_INCLUDE` names the minimal port headers. Append the exact flags below, then `-c src/acmp.c -o "$OUTPUT"`:

| Comparison | Additional flags | Raw objects |
|---|---|---|
| Default O0, no debug data | `-DCTRL_REENTRY_ASSERT -g0` | Equal |
| RV32 Debug, default O0 | `-DCTRL_REENTRY_ASSERT -g` | Equal |
| RV32 Release | `-DCTRL_REENTRY_ASSERT -O3 -DNDEBUG` | Equal |
| Size optimization | `-DCTRL_REENTRY_ASSERT -Os` | Equal |
| O2 without the re-entry hook | `-O2` | Equal |
| Size optimization with macro debug data | `-Os -g3` | Equal |

Validate with the pinned dependencies:

```sh
python3 scripts/validate.py --work build-validation --jobs 16 --graphs
python3 scripts/baremetal.py --work build-rv32 --jobs 16
```

The manager owns publication, hosted acceptance, the current-main merge candidate, two positive reviews and the consumer pin update. RV32 smoke execution does not establish hardware timing.
