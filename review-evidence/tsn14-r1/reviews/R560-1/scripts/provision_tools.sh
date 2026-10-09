#!/bin/sh
# SPDX-License-Identifier: MIT
# Reproduce the reviewer toolchain without shared installs: Ubuntu 24.04 Clang 18, clang-tidy 18,
# cppcheck 2.13, libstdc++-13 headers and the RV32 cross toolchain, plus GoogleTest 1.14.0 from its tag commit.
# Usage: provision_tools.sh WORKDIR   (then: . WORKDIR/shim/env.sh)
set -eu
W=$(cd "$1" && pwd); H=$(cd "$(dirname "$0")" && pwd); R=$W/noble-root; B=$W/shim/bin
python3 -I "$H/fetch_noble.py" "$W/debs" clang-18 libclang-cpp18 libllvm18 libclang-common-18-dev libclang-rt-18-dev \
  clang-tidy-18 llvm-18 llvm-18-linker-tools gcc-riscv64-unknown-elf binutils-riscv64-unknown-elf cppcheck \
  libedit2 libxml2 libicu74 libtinyxml2-10 libbsd0 libmd0 libstdc++-13-dev libgcc-13-dev libstdc++6 libgcc-s1 gcc-13-base
mkdir -p "$R" "$B" "$W/shim/cppcheck/bin"
for d in "$W"/debs/*.deb; do x=$(mktemp -d); (cd "$x" && ar x "$d" && tar -C "$R" -xf data.tar.*); rm -rf "$x"; done
cp "$R/usr/bin/cppcheck" "$W/shim/cppcheck/bin/"; cp -r "$R/usr/lib/x86_64-linux-gnu/cppcheck/"* "$W/shim/cppcheck/"
LP="$R/usr/lib/x86_64-linux-gnu:$R/usr/lib/llvm-18/lib"
wrap() { # name target [gcc13]
  { echo '#!/bin/sh'; echo "LD_LIBRARY_PATH=$LP\${LD_LIBRARY_PATH:+:\$LD_LIBRARY_PATH}; export LD_LIBRARY_PATH"
    if [ "${3:-}" = gcc13 ]; then echo "case \"\$1\" in -cc1*) exec $2 \"\$@\";; esac"; echo "exec $2 --gcc-toolchain=$R/usr \"\$@\"";
    else echo "exec $2 \"\$@\""; fi; } > "$B/$1"; chmod +x "$B/$1"; }
for n in clang clang-18; do wrap $n "$R/usr/lib/llvm-18/bin/clang" gcc13; done
for n in clang++ clang++-18; do wrap $n "$R/usr/lib/llvm-18/bin/clang++" gcc13; done
wrap clang-tidy "$R/usr/lib/llvm-18/bin/clang-tidy"; wrap llvm-symbolizer "$R/usr/lib/llvm-18/bin/llvm-symbolizer"
wrap cppcheck "$W/shim/cppcheck/bin/cppcheck"
for t in "$R"/usr/bin/riscv64-unknown-elf-*; do ln -sf "$t" "$B/"; done
git clone -q --no-checkout https://github.com/google/googletest.git "$W/gtest-src"
git -C "$W/gtest-src" checkout -q f8d7d77c06936315286eb55f8de22cd23c188571
cmake -S "$W/gtest-src" -B "$W/gtest-build" -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX="$W/gtest-1.14.0" \
  -DCMAKE_C_COMPILER="$B/clang" -DCMAKE_CXX_COMPILER="$B/clang++" -DCMAKE_POSITION_INDEPENDENT_CODE=ON
cmake --build "$W/gtest-build" -j16 && cmake --install "$W/gtest-build"
cat > "$W/shim/env.sh" <<E2
export PATH=$B:\$PATH
export PKG_CONFIG_PATH=$W/gtest-1.14.0/lib/pkgconfig
export CMAKE_PREFIX_PATH=$W/gtest-1.14.0
export TSN_CLANG=$B/clang-18
E2
