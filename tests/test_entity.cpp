// SPDX-License-Identifier: MIT
#include <gtest/gtest.h>
#include "entity_roundtrip.h"

extern "C" void ctrl_reentry_assert(const char *module)
{
    (void)module;
    EXPECT_TRUE(false) << "entity round trip never reenters a port";
}

// REQ: ENTITY-01, ADP-01
TEST(EntityYaml, AdpRoundTrip)
{
    EXPECT_EQ(entity_check_adp(), 0) << "generated ADP fields match the independent entity oracle";
}

// REQ: ENTITY-01, ACMP-01, ACMP-07
TEST(EntityYaml, AcmpRoundTrip)
{
    EXPECT_EQ(entity_check_acmp(), 0) << "generated ACMP interfaces preserve binding admission routes";
}

// REQ: ENTITY-01, MAAP-02
TEST(EntityYaml, MaapRoundTrip)
{
    EXPECT_EQ(entity_check_maap(), 0) << "generated MAAP arguments preserve range and interface ownership";
}
