#!/usr/bin/env bash
set -u
repo=${1:?repository path}
packet=${2:?packet path}
gate=${3:?validate or baremetal}
# The caller supplies PATH, PKG_CONFIG_PATH, CMAKE_PREFIX_PATH and LD_LIBRARY_PATH
# for the pinned compiler and test dependency installations.
unset CPATH CPLUS_INCLUDE_PATH C_INCLUDE_PATH LIBRARY_PATH
cd "$repo"
if test "$gate" = validate; then
  python3 scripts/validate.py --graphs --jobs 2 --work "$packet/scratch/validation" > "$packet/receipts/validate.log" 2>&1
else
  python3 scripts/baremetal.py --jobs 2 --work "$packet/scratch/rv32" > "$packet/receipts/baremetal.log" 2>&1
fi
rc=$?
printf '%s\n' "$rc" > "$packet/receipts/$gate.rc"
cat "$packet/receipts/$gate.log"
exit "$rc"
