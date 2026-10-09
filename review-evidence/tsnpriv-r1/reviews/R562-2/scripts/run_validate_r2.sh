#!/bin/sh
# Full validate.py gate set at the exact head in a disposable clone.
# Usage: run_validate_r2.sh <review-clone> <scratch> <llvm18-prefix> <gtest-1.14.0-prefix> <receipts-dir> [head]  (adapted from R562-1)
set -u
SRC=$1; SCRATCH=$2; LLVM=$3; GTEST=$4; OUT=$5
HEAD=${6:-b7c6b7ba0007aaa5791df68d30296423127b003e}
[ -e "$SCRATCH/vclone" ] && { echo "vclone exists"; exit 2; }
git clone -q --no-local "$SRC" "$SCRATCH/vclone" && git -C "$SCRATCH/vclone" checkout -q --detach "$HEAD"
mkdir -p "$SCRATCH/vbin"; ln -sf "$LLVM/bin/clang" "$SCRATCH/vbin/clang-18"
export PATH="$SCRATCH/vbin:$LLVM/bin:$PATH"
export PKG_CONFIG_PATH="$GTEST/lib/pkgconfig" CMAKE_PREFIX_PATH="$GTEST"
{ git -C "$SCRATCH/vclone" rev-parse HEAD HEAD^{tree}; clang --version | head -1; clang-18 --version | head -1; clang-tidy --version | grep -i version; cppcheck --version; gcc --version | head -1; cmake --version | head -1; pkg-config --modversion gtest gmock; grep -h 'set(GTEST_VERSION\|GOOGLETEST_VERSION' "$GTEST"/lib/cmake/GTest/GTestConfigVersion.cmake | head -2; python3 --version; mmdc --version; } > "$OUT/validate-toolchain.txt" 2>&1
cd "$SCRATCH/vclone" && /usr/bin/time -v python3 scripts/validate.py --work "$SCRATCH/vwork" --jobs 16 --graphs > "$OUT/validate.log" 2> "$OUT/validate.time"
rc=$?
echo $rc > "$OUT/validate.rc"
cp "$SCRATCH/vwork/gates.json" "$OUT/validate-gates.json"
for g in privacy privacy-selftest; do cp "$SCRATCH/vwork/$g.log" "$OUT/validate-$g.log"; done
exit $rc
