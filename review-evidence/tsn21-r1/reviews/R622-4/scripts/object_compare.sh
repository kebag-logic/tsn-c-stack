#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# usage: object_compare.sh <repo-tree> <ref-acmp.c> <ref-acmp.h> <work>
# Builds each acmp.c/acmp.h pair at the same path with identical RV32 freestanding flags; compares raw objects.
set -u
tree=$1 refc=$2 refh=$3 work=$4
cc=${RV32_CC:-riscv64-elf-gcc}
base="-march=rv32i -mabi=ilp32 -ffreestanding -fno-builtin -nostdinc -isystem $($cc -print-file-name=include) -std=c11 -Wall -Wextra -Werror"
mkdir -p "$work/src" "$work/include" "$work/out"
cp "$tree/include/"*.h "$work/include/"; mkdir -p "$work/port"; cp "$tree/examples/rv32/include/"*.h "$work/port/"
rc=0
while IFS='|' read -r name flags; do
  for side in repo ref; do
    if [ $side = repo ]; then cp "$tree/src/acmp.c" "$work/src/acmp.c"; cp "$tree/include/acmp.h" "$work/include/acmp.h";
    else cp "$refc" "$work/src/acmp.c"; cp "$refh" "$work/include/acmp.h"; fi
    (cd "$work" && $cc $base $flags -Iinclude -Iport -c src/acmp.c -o "out/$name-$side.o") || rc=1
  done
  if cmp -s "$work/out/$name-repo.o" "$work/out/$name-ref.o"; then r=EQUAL; else r=DIFFER; rc=1; fi
  echo "$name [$flags]: raw $r $(sha256sum < "$work/out/$name-repo.o" | cut -c1-16) $(sha256sum < "$work/out/$name-ref.o" | cut -c1-16) $(stat -c %s "$work/out/$name-repo.o")B"
done <<'LIST'
debug-g0|-DCTRL_REENTRY_ASSERT -g0
debug|-DCTRL_REENTRY_ASSERT -g
release|-DCTRL_REENTRY_ASSERT -O3 -DNDEBUG
os|-DCTRL_REENTRY_ASSERT -Os
o2-noassert|-O2
os-g3|-Os -g3
LIST
exit $rc
