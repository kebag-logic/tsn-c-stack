# Pinned toolchain environment for the tsn-c-stack gates.
# Set TOOLS to the directory holding gtest-1.14.0 and clang-18 before sourcing.
: "${TOOLS:?set TOOLS to the pinned tool root}"
export PKG_CONFIG_PATH=$TOOLS/gtest-1.14.0/lib/pkgconfig
export CMAKE_PREFIX_PATH=$TOOLS/gtest-1.14.0
export LD_LIBRARY_PATH=$TOOLS/gtest-1.14.0/lib
export PATH=$TOOLS/clang-18/bin:$PATH
