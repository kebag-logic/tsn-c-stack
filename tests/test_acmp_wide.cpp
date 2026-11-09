// SPDX-FileCopyrightText: 2026 Kebag Logic
// SPDX-License-Identifier: MIT
// Milan v1.2 5.5.3.5

#include <gtest/gtest.h>

#include <cstdint>

#include "acmp.h"
#include "acmp_fake.hpp"

using namespace acmp_test;

extern "C" void ctrl_reentry_assert(const char* module) {
    static_cast<void>(module);
}

namespace {

constexpr unsigned kLast = ACMP_MAX_SINKS - 1u;

class AcmpWide : public ::testing::Test {
 protected:
    void SetUp() override {
        ASSERT_EQ(kLast, 32u) << "W0 the binary builds 33 sinks: the last is the first of the second release word";
        fk = Fake{};
        cfg = acmp_config{};
        cfg.entity_id = kOwn;
        cfg.n_interfaces = 2;
        cfg.mac[0] = kMac0;
        cfg.mac[1] = kMac1;
        cfg.n_sinks = ACMP_MAX_SINKS;
        for (unsigned k = 0; k < ACMP_MAX_SINKS; ++k) {
            cfg.sink_interface[k] = static_cast<std::uint8_t>(k % 2u);
        }
        cfg.n_sources = 2;
        cfg.source_interface[0] = 0;
        cfg.source_interface[1] = 1;
        for (unsigned i = 0; i < ACMP_MAX_SOURCES; ++i) {
            fk.source[i] = acmp_source_state{true, {kSid + i, kDa + i, 2u}, false};
        }
        ASSERT_TRUE(acmp_init(&a, &cfg, &kPorts, &kEnv));
    }

    void bind(unsigned sink) {
        Pdu p;
        p.msg = spec::MSG_BIND_RX_COMMAND;
        p.controller = kCtl1;
        p.talker = kTkA;
        p.listener = kOwn;
        p.talker_uid = 1;
        p.listener_uid = static_cast<std::uint16_t>(sink);
        p.seq = 0x4100;
        auto f = acmpdu(p);
        acmp_rx(&a, a.sinks[sink].interface, f.data(), f.size());
    }

    unsigned changed_sink(unsigned n) const {
        return fk.calls[static_cast<std::size_t>(fk.position(Call::CHANGED, n))].index;
    }

    acmp a{};
    acmp_config cfg{};
};

// REQ: ACMP-09
TEST_F(AcmpWide, OwedResponsesHoldOnlyTheirOwnSinksChanges) {
    fk.room = false;
    bind(kLast);
    EXPECT_TRUE(acmp_change_pending(&a, kLast) && a.sinks[kLast].change_owed == 1u)
        << "W1 sink 32's change waits behind its owed response (#653)";
    EXPECT_FALSE(acmp_change_pending(&a, 0)) << "W1 sink 0, which owes nothing, is not held by sink 32's response";
    bind(0);
    EXPECT_TRUE(a.owed_count == 4u && a.sinks[0].change_owed == 1u && a.sinks[kLast].change_owed == 1u)
        << "W1 with both bound, each sink waits behind one owed response, its own";
    fk.room = true;
    fk.clear();
    EXPECT_TRUE(acmp_poll(&a)) << "W1 the first poll sends sink 32's response and more is owed";
    ASSERT_EQ(fk.count(Call::CHANGED), 1u) << "W1 sink 32's response left: one change is reported";
    EXPECT_TRUE(changed_sink(0) == kLast && !acmp_change_pending(&a, kLast) && acmp_change_pending(&a, 0))
        << "W1 the change reported is sink 32's, and sink 0's still waits for its own response";
    EXPECT_TRUE(acmp_poll(&a)) << "W1 the second poll sends sink 32's probe";
    EXPECT_TRUE(fk.count(Call::CHANGED) == 1u && acmp_change_pending(&a, 0))
        << "W1 a probe releases no change: sink 0 still waits";
    EXPECT_TRUE(acmp_poll(&a)) << "W1 the third poll sends sink 0's response";
    ASSERT_EQ(fk.count(Call::CHANGED), 2u) << "W1 sink 0's response left: a second change is reported";
    EXPECT_TRUE(changed_sink(1) == 0u && !acmp_change_pending(&a, 0) && a.sinks[kLast].change_owed == 0u)
        << "W1 then sink 0's change is reported, and sink 32 owes nothing";
}

// REQ: ACMP-09
TEST_F(AcmpWide, SinkZerosOwedResponseLeavesSinkThirtyTwoFree) {
    fk.room = false;
    bind(0);
    EXPECT_TRUE(acmp_change_pending(&a, 0) && !acmp_change_pending(&a, kLast))
        << "W2 sink 0's owed response holds sink 0 and not sink 32";
    fk.room = true;
    fk.clear();
    EXPECT_TRUE(acmp_poll(&a)) << "W2 the poll sends sink 0's response and its probe is still owed";
    EXPECT_TRUE(!acmp_change_pending(&a, 0) && a.sinks[0].change_owed == 0u && a.sinks[kLast].change_owed == 0u)
        << "W2 its acceptance releases sink 0 and leaves sink 32's count at zero";
}

}
