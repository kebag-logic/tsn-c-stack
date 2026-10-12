#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# usage: run_gates.sh <tree> <expected-head> <outdir> <validate-jobs> <rv32-jobs>
# Runs the repository's own Linux kit and RV32 gate at an exact head; records rc files.
set -u
tree=$1 head=$2 out=$3 vj=$4 rj=$5
. "$(dirname "$0")/env.sh"
mkdir -p "$out"
cd "$tree"
[ "$(git rev-parse HEAD)" = "$head" ] || { echo "head mismatch" > "$out/head.err"; exit 2; }
git status --porcelain > "$out/status-before.txt"
( python3 scripts/validate.py --work "$out/build-validation" --jobs "$vj" --graphs > "$out/linux.log" 2>&1; echo $? > "$out/linux.rc" ) &
( python3 scripts/baremetal.py --work "$out/build-rv32" --jobs "$rj" > "$out/rv32.log" 2>&1; echo $? > "$out/rv32.rc" ) &
wait
git status --porcelain --ignored > "$out/status-after.txt"
echo done > "$out/DONE"
