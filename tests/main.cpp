// SPDX-FileCopyrightText: 2026 Kebag Logic
// SPDX-License-Identifier: MIT
#include <gmock/gmock.h>
#include <gtest/gtest.h>

int main(int argc, char** argv) {
    ::testing::InitGoogleMock(&argc, argv);
    const int result = RUN_ALL_TESTS();
    const auto* tests = ::testing::UnitTest::GetInstance();
    return result != 0 || tests->test_to_run_count() == 0 ||
           tests->skipped_test_count() != 0 || tests->disabled_test_count() != 0;
}
