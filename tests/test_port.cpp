// SPDX-License-Identifier: MIT
#include <gtest/gtest.h>
extern "C" {
#include "adp_port.h"
}

// REQ: PORT-01
TEST(ExamplePort, DefersExpiryAndRetainsBlockedOutput) {
    example_adp_port p;
    adp_entity entity{};
    entity.entity_id = 1;
    entity.mac = 0x020000000001ULL;
    example_adp_init(&p, &entity);
    example_adp_link(&p, true);
    adp_set_enable(&p.core, true);
    EXPECT_FALSE(p.tx_ready);
    EXPECT_TRUE(p.armed);
    example_adp_service(&p, p.deadline_ms);
    ASSERT_TRUE(p.tx_ready);
    EXPECT_EQ(p.tx[15], 0u);
    adp_set_enable(&p.core, false);
    EXPECT_EQ(p.core.departing_owed, 1u);
    EXPECT_EQ(p.core.available_index, 0u) << "shutdown resets the next advertisement index";
    uint8_t frame[ADP_FRAME_BYTES];
    EXPECT_TRUE(example_adp_take_frame(&p, frame));
    example_adp_service(&p, p.now_ms);
    EXPECT_TRUE(example_adp_take_frame(&p, frame));
    EXPECT_EQ(frame[15], 1u);
    EXPECT_FALSE(example_adp_take_frame(&p, frame));
}
