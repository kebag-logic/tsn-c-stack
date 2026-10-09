#!/bin/bash
# Usage: TOOLS=<pinned tool root> run_gates.sh <clone> <packet>; runs both target gates concurrently
set -u
C=$1; P=$2
. "$P/scripts/env.sh"
cd "$C"
rm -f "$P/receipts/validate.rc" "$P/receipts/baremetal.rc"
(python3 scripts/validate.py --work "$P/scratch/build-validation" --jobs 16 --graphs > "$P/receipts/validate.log" 2>&1; echo $? > "$P/receipts/validate.rc") &
(python3 scripts/baremetal.py --work "$P/scratch/build-rv32" --jobs 16 > "$P/receipts/baremetal.log" 2>&1; echo $? > "$P/receipts/baremetal.rc") &
wait
