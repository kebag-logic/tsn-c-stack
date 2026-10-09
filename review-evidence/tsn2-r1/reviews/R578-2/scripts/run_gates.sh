#!/bin/sh
# SPDX-License-Identifier: MIT
# Usage: run_gates.sh <clone> <validate|baremetal> <jobs> <receipt-dir>
# Runs one tsn-c-stack gate driver with the pinned toolchain environment.
# Set TSN_TOOLS to the directory holding gtest-1.14.0 and clang-18.
set -u
: "${TSN_TOOLS:?set TSN_TOOLS to the pinned toolchain directory}"
clone=$1 kind=$2 jobs=$3 out=$4
export PKG_CONFIG_PATH=$TSN_TOOLS/gtest-1.14.0/lib/pkgconfig
export CMAKE_PREFIX_PATH=$TSN_TOOLS/gtest-1.14.0
export LD_LIBRARY_PATH=$TSN_TOOLS/gtest-1.14.0/lib
export PATH=$TSN_TOOLS/clang-18/bin:$PATH
cd "$clone" || exit 99
{
  echo "head $(git rev-parse HEAD) tree $(git rev-parse 'HEAD^{tree}')"
  echo "clang-18: $(clang-18 --version | head -1)"; echo "clang: $(command -v clang) $(clang --version | head -1)"
  echo "gcc: $(gcc --version | head -1)"; echo "cmake: $(cmake --version | head -1)"; echo "python: $(python3 --version)"
  echo "riscv: $(riscv64-elf-gcc --version | head -1)"; echo "qemu: $(qemu-system-riscv32 --version | head -1)"
  echo "gtest pkg-config: $(pkg-config --modversion gtest)"; echo "start $(date -u +%FT%TZ)"
} > "$out/$kind.env"
if [ "$kind" = validate ]; then
  python3 scripts/validate.py --work build-validation --jobs "$jobs" --graphs > "$out/$kind.log" 2>&1
else
  python3 scripts/baremetal.py --work build-rv32 --jobs "$jobs" > "$out/$kind.log" 2>&1
fi
rc=$?
echo "end $(date -u +%FT%TZ)" >> "$out/$kind.env"
echo $rc > "$out/$kind.rc"
