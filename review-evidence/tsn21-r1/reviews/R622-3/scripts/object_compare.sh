#!/bin/sh
# SPDX-License-Identifier: MIT
# Build acmp.c from two source copies into RV32 freestanding objects with the same
# flags in the same absolute directory; compare raw and debug-stripped objects.
# Usage: object_compare.sh <rv32-gcc> <wire.h dir> <port include dir> <left dir> <right dir> <work>
set -u
cc=$1 wire=$2 port=$3 left=$4 right=$5 work=$6
pre=$(dirname "$(command -v "$cc")")/$(basename "$cc" | sed 's/gcc$//')
mkdir -p "$work/build" "$work/out"
base="-march=rv32i -mabi=ilp32 -ffreestanding -fno-builtin -nostdinc -isystem $($cc -print-file-name=include) -std=c11 -Wall -Wextra -Werror"
status=0
for set in "debug-g0:-DCTRL_REENTRY_ASSERT -g0" "debug:-DCTRL_REENTRY_ASSERT -g" "release:-DCTRL_REENTRY_ASSERT -O3 -DNDEBUG" \
           "os:-DCTRL_REENTRY_ASSERT -Os" "o2-noassert:-O2" "os-g3:-Os -g3"; do
  name=${set%%:*} extra=${set#*:}
  for side in left right; do
    eval src=\$$side
    rm -rf "$work/build/src"; mkdir -p "$work/build/src"
    cp "$src/acmp.c" "$src/acmp.h" "$wire/wire.h" "$work/build/src/"
    (cd "$work/build" && $cc -Isrc -I"$port" $base $extra -c src/acmp.c -o "$work/out/$name-$side.o") || exit 2
    "${pre}objcopy" --strip-debug "$work/out/$name-$side.o" "$work/out/$name-$side.nodebug.o"
  done
  raw=DIFFER; cmp -s "$work/out/$name-left.o" "$work/out/$name-right.o" && raw=EQUAL
  nd=DIFFER; cmp -s "$work/out/$name-left.nodebug.o" "$work/out/$name-right.nodebug.o" && nd=EQUAL
  echo "$name [$extra]: raw $raw ($(sha256sum < "$work/out/$name-left.o" | cut -c1-16) $(sha256sum < "$work/out/$name-right.o" | cut -c1-16)); strip-debug $nd"
  [ $raw = EQUAL ] || status=1
done
exit $status
