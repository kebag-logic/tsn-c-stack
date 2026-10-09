#!/bin/sh
# Re-run validate.py's clang-sanitizers build/test steps with Clang 18 and its own libc++,
# for hosts whose libstdc++ headers are newer than Clang 18 supports.
# Usage: run_clang18_libcxx.sh <vclone-at-exact-head> <scratch> <llvm18-prefix> <gtest-src> <receipts-dir>
set -u
SRC=$1; S=$2; LLVM=$3; GSRC=$4; OUT=$5
LIBDIR="$LLVM/lib/x86_64-unknown-linux-gnu"
FLAGS="-stdlib=libc++"; LFLAGS="-stdlib=libc++ -L$LIBDIR -Wl,-rpath,$LIBDIR"
rm -rf "$S/gtest-libcxx-build" "$S/gtest-libcxx-prefix" "$S/clang18-libcxx"
cmake -S "$GSRC" -B "$S/gtest-libcxx-build" -DCMAKE_BUILD_TYPE=Debug -DCMAKE_C_COMPILER="$LLVM/bin/clang" -DCMAKE_CXX_COMPILER="$LLVM/bin/clang++" \
  -DCMAKE_CXX_FLAGS="$FLAGS" -DCMAKE_EXE_LINKER_FLAGS="$LFLAGS" -DCMAKE_INSTALL_PREFIX="$S/gtest-libcxx-prefix" > "$OUT/clang18-gtest.log" 2>&1 \
 && cmake --build "$S/gtest-libcxx-build" -j16 >> "$OUT/clang18-gtest.log" 2>&1 && cmake --install "$S/gtest-libcxx-build" >> "$OUT/clang18-gtest.log" 2>&1 || { echo gtest-fail; exit 3; }
export CMAKE_PREFIX_PATH="$S/gtest-libcxx-prefix" PKG_CONFIG_PATH="$S/gtest-libcxx-prefix/lib/pkgconfig" TMPDIR="$S/clang18-tmp"
export ASAN_OPTIONS=detect_leaks=1:halt_on_error=1 UBSAN_OPTIONS=halt_on_error=1
mkdir -p "$TMPDIR"; unset $(env | sed -n 's/^\(GTEST_[A-Z_]*\)=.*/\1/p') 2>/dev/null
D="$S/clang18-libcxx"
cmake -S "$SRC" -B "$D" -DCMAKE_BUILD_TYPE=Debug -DCMAKE_C_COMPILER="$LLVM/bin/clang" -DCMAKE_CXX_COMPILER="$LLVM/bin/clang++" -DTSN_SANITIZERS=ON \
  -DCMAKE_CXX_FLAGS="$FLAGS" -DCMAKE_EXE_LINKER_FLAGS="$LFLAGS" > "$OUT/clang18-configure.log" 2>&1; echo "configure rc $?"
cmake --build "$D" -j16 > "$OUT/clang18-build.log" 2>&1; echo "build rc $?"
find "$D" -name '*.gcda' -delete
ctest --test-dir "$D" --output-on-failure -j16 > "$OUT/clang18-test.log" 2>&1; rc=$?; echo "test rc $rc"
grep -E 'tests passed|tests failed|Total Test' "$OUT/clang18-test.log"
grep -E 'CMAKE_C_COMPILER_VERSION|CMAKE_CXX_COMPILER_VERSION' "$D/CMakeFiles"/*/CMakeCXXCompiler.cmake "$D/CMakeFiles"/*/CMakeCCompiler.cmake | sed 's|.*/||'
grep -h 'GTest_VERSION\|PACKAGE_VERSION "' "$S/gtest-libcxx-prefix/lib/cmake/GTest/GTestConfigVersion.cmake" | head -1
exit $rc
