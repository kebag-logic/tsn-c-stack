#!/bin/sh
# SPDX-License-Identifier: MIT
# Usage: baseline.sh <clone> <scratch root> <receipt dir>
# Exports the clone's HEAD tree and runs, concurrently, the full entity selftest,
# the documented mapper-plant subset, a no-match selection and the example drift check.
set -u
clone=$1 root=$2 out=$3
rm -rf "$root/head" && mkdir -p "$root/head" "$out"
git -C "$clone" archive HEAD | tar -x -C "$root/head"
cd "$root/head" || exit 99
export PYTHONDONTWRITEBYTECODE=1
( python3 scripts/entity_selftest.py --work "$root/b-full" > "$out/selftest-full.txt" 2>&1; echo $? > "$out/selftest-full.rc" ) &
( python3 scripts/entity_selftest.py --work "$root/b-plants" --select mapper_plant > "$out/selftest-mapper-plants.txt" 2>&1; echo $? > "$out/selftest-mapper-plants.rc" ) &
( python3 scripts/entity_selftest.py --work "$root/b-none" --select no_such_test_name > "$out/selftest-nomatch.txt" 2>&1; echo $? > "$out/selftest-nomatch.rc" ) &
( python3 scripts/entity_selftest.py --work "$root/b-fw" --select firmware > "$out/selftest-firmware.txt" 2>&1; echo $? > "$out/selftest-firmware.rc" ) &
( python3 scripts/entity_yaml.py --examples --check > "$out/examples-check.txt" 2>&1; echo $? > "$out/examples-check.rc" ) &
wait
for f in selftest-full selftest-mapper-plants selftest-nomatch selftest-firmware examples-check; do
  echo "$f rc=$(cat "$out/$f.rc") $(tail -n 3 "$out/$f.txt" | tr '\n' ' ')"
done
