#!/bin/sh
# Run one gate driver in a checkout, keeping its log and exit status.
# Usage: run_gate.sh <checkout> <log> <rc> <command...>
dir=$1 log=$2 rc=$3; shift 3
cd "$dir" || exit 2
"$@" > "$log" 2>&1
echo $? > "$rc"
