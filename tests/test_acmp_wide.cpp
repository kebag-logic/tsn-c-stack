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
constexpr unsigned kWordEnd = kLast - 1u;

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

    bool command(std::uint8_t msg, unsigned sink) {
        Pdu p;
        p.msg = msg;
        p.controller = kCtl1;
        p.talker = kTkA;
        p.listener = kOwn;
        p.talker_uid = 1;
        p.listener_uid = static_cast<std::uint16_t>(sink);
        p.seq = 0x4100;
        auto f = acmpdu(p);
        return acmp_rx(&a, a.sinks[sink].interface, f.data(), f.size());
    }

    void bind(unsigned sink) {
        static_cast<void>(command(spec::MSG_BIND_RX_COMMAND, sink));
    }

    unsigned changed_sink(unsigned n) const {
        return fk.calls[static_cast<std::size_t>(fk.position(Call::CHANGED, n))].index;
    }

    unsigned owed_changes() const {
        unsigned n = 0;
        for (unsigned k = 0; k < ACMP_MAX_SINKS; ++k) {
            n += a.sinks[k].change_owed;
        }
        return n;
    }

    unsigned probe_in_the_slot_of(unsigned sink) {
        const unsigned slot = (a.owed_head + a.owed_count) % ACMP_OWED_MAX;
        fk.room = false;
        bind(sink);
        fk.room = true;
        static_cast<void>(acmp_poll(&a));
        static_cast<void>(acmp_poll(&a));
        fk.room = false;
        static_cast<void>(command(spec::MSG_GET_RX_STATE_COMMAND, 0u));
        for (unsigned k = 1; k <= 3u; ++k) {
            bind(k);
        }
        return slot;
    }

    void drain() {
        fk.room = true;
        for (unsigned k = 0; k < ACMP_OWED_MAX; ++k) {
            static_cast<void>(acmp_poll(&a));
        }
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

// REQ: ACMP-09
TEST_F(AcmpWide, SinksThirtyOneAndThirtyTwoWaitOnlyForTheirOwnResponses) {
    fk.room = false;
    bind(kWordEnd);
    EXPECT_TRUE(acmp_change_pending(&a, kWordEnd) && a.sinks[kWordEnd].change_owed == 1u && owed_changes() == 1u)
        << "W3 sink 31's change waits behind its own owed response, and no other sink's does";
    bind(kLast);
    EXPECT_TRUE(a.sinks[kWordEnd].change_owed == 1u && a.sinks[kLast].change_owed == 1u && owed_changes() == 2u)
        << "W3 with both bound, sinks 31 and 32 each wait behind one owed response, their own";
    fk.room = true;
    fk.clear();
    EXPECT_TRUE(acmp_poll(&a)) << "W3 the first poll sends sink 31's response and more is owed";
    ASSERT_EQ(fk.count(Call::CHANGED), 1u) << "W3 sink 31's response left: one change is reported";
    EXPECT_TRUE(changed_sink(0) == kWordEnd && !acmp_change_pending(&a, kWordEnd) && acmp_change_pending(&a, kLast))
        << "W3 it releases sink 31 alone: sink 32 still waits for its own response";
    EXPECT_TRUE(acmp_poll(&a)) << "W3 the second poll sends sink 31's probe";
    EXPECT_TRUE(command(spec::MSG_UNBIND_RX_COMMAND, kWordEnd) && a.sinks[kWordEnd].change_owed == 1u &&
                a.sinks[kLast].change_owed == 1u)
        << "W3 sink 31's unbind response is owed behind sink 32's frames and holds sink 31 alone";
    EXPECT_TRUE(acmp_poll(&a)) << "W3 the third poll sends sink 32's response";
    ASSERT_EQ(fk.count(Call::CHANGED), 2u) << "W3 sink 32's response left: a second change is reported";
    EXPECT_TRUE(changed_sink(1) == kLast && !acmp_change_pending(&a, kLast) && acmp_change_pending(&a, kWordEnd))
        << "W3 it releases sink 32 alone: sink 31 still waits for its unbind response";
    EXPECT_TRUE(acmp_poll(&a)) << "W3 the fourth poll sends sink 32's probe";
    EXPECT_FALSE(acmp_poll(&a)) << "W3 the fifth poll sends sink 31's unbind response and nothing is owed";
    ASSERT_EQ(fk.count(Call::CHANGED), 3u) << "W3 sink 31's unbind response left: a third change is reported";
    EXPECT_TRUE(changed_sink(2) == kWordEnd && owed_changes() == 0u)
        << "W3 the third change is sink 31's, and no sink is held";
}

// REQ: ACMP-09
TEST_F(AcmpWide, ProbeInTheSlotOfSinkThirtyOnesResponseHoldsNoSink) {
    const unsigned slot = probe_in_the_slot_of(kWordEnd);
    ASSERT_TRUE(a.owed_count == 7u && a.owed[slot].probe_of == 4u)
        << "W4 sink 3's probe is owed in the slot that held sink 31's response, which left";
    EXPECT_TRUE(!acmp_change_pending(&a, kWordEnd) && owed_changes() == 3u)
        << "W4 the probe in that slot holds no sink: sink 31 is free, and sinks 1 to 3 each wait for their own response";
    fk.clear();
    EXPECT_TRUE(acmp_set_started(&a, kWordEnd, false) && fk.count(Call::CHANGED) == 1u && changed_sink(0) == kWordEnd)
        << "W4 a change of sink 31 is reported at once";
    drain();
    EXPECT_TRUE(a.owed_count == 0u && owed_changes() == 0u)
        << "W4 once every owed frame left, no sink is held: " << owed_changes();
}

// REQ: ACMP-09
TEST_F(AcmpWide, ProbeInTheSlotOfSinkThirtyTwosResponseHoldsNoSink) {
    const unsigned slot = probe_in_the_slot_of(kLast);
    ASSERT_TRUE(a.owed_count == 7u && a.owed[slot].probe_of == 4u)
        << "W5 sink 3's probe is owed in the slot that held sink 32's response, which left";
    EXPECT_TRUE(!acmp_change_pending(&a, kLast) && owed_changes() == 3u)
        << "W5 the probe in that slot holds no sink: sink 32 is free, and sinks 1 to 3 each wait for their own response";
    fk.clear();
    EXPECT_TRUE(acmp_set_started(&a, kLast, false) && fk.count(Call::CHANGED) == 1u && changed_sink(0) == kLast)
        << "W5 a change of sink 32 is reported at once";
    drain();
    EXPECT_TRUE(a.owed_count == 0u && owed_changes() == 0u)
        << "W5 once every owed frame left, no sink is held: " << owed_changes();
}

}
