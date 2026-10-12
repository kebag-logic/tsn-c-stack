# SPDX-License-Identifier: MIT
# Pinned dependency environment for the tsn-c-stack gates.
# TSN_GTEST: prefix of GoogleTest/GMock 1.14.0. TSN_CLANG18: directory holding a working `clang-18` (18.1.x).
: "${TSN_GTEST:?set TSN_GTEST to the GoogleTest 1.14.0 prefix}"
: "${TSN_CLANG18:?set TSN_CLANG18 to a directory containing clang-18}"
export PKG_CONFIG_PATH="$TSN_GTEST/lib/pkgconfig" CMAKE_PREFIX_PATH="$TSN_GTEST" LD_LIBRARY_PATH="$TSN_GTEST/lib"
export PATH="$TSN_CLANG18:$PATH"
