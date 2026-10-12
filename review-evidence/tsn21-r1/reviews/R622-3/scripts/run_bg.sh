#!/bin/sh
# SPDX-License-Identifier: MIT
# Run one command detached, keeping log and exit status. Usage: run_bg.sh <log> <rc> <command...>
log=$1 rc=$2; shift 2
rm -f "$rc"
( "$@" > "$log" 2>&1; echo $? > "$rc" ) &
