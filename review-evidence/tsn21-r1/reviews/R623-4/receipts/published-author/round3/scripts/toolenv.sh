# Source to select the pinned Clang 18 and GoogleTest 1.14.0 used by the review.
# Usage: TOOLS=<tools root> SCRATCH=<scratch dir> . toolenv.sh
: "${TOOLS:?}" "${SCRATCH:?}"
CL=$TOOLS/clang-18/root
mkdir -p "$SCRATCH/bin"
for n in clang clang-18 clang++ clang++-18; do
  t=clang; case $n in clang++*) t=clang++;; esac
  printf '#!/bin/sh\nexec env LD_LIBRARY_PATH=%s/usr/lib/x86_64-linux-gnu %s/usr/lib/llvm-18/bin/%s "$@"\n' "$CL" "$CL" "$t" > "$SCRATCH/bin/$n"
  chmod +x "$SCRATCH/bin/$n"
done
export PATH="$SCRATCH/bin:$PATH" TSN_CLANG="$SCRATCH/bin/clang-18"
export PKG_CONFIG_PATH=$TOOLS/gtest-1.14.0/lib/pkgconfig CMAKE_PREFIX_PATH=$TOOLS/gtest-1.14.0 LD_LIBRARY_PATH=$TOOLS/gtest-1.14.0/lib
