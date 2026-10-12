#!/bin/sh
# SPDX-License-Identifier: MIT
# Run the repository's RV32 gate on probe trees produced by probes.sh.
# Usage: rv32_probe.sh <probes work dir> <out dir> <variant...>
set -u
probes=$1 out=$2; shift 2
mkdir -p "$out"
for v in "$@"; do
  ( cd "$probes/$v" && python3 scripts/baremetal.py --work "$out/rv32-probe-$v" --jobs 8 > "$out/rv32-probe-$v.log" 2>&1
    echo $? > "$out/rv32-probe-$v.rc" ) &
done
wait
for v in "$@"; do echo "$v: baremetal rc $(cat "$out/rv32-probe-$v.rc")"; done
