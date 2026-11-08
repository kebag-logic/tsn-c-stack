// SPDX-FileCopyrightText: 2026 Kebag Logic
// SPDX-License-Identifier: MIT
// Milan v1.2 5.5.3
// Milan v1.2 Table 5.30
// Milan v1.2 5.5.4
// Milan v1.2 5.6.4

#include <gtest/gtest.h>

#include <algorithm>
#include <array>
#include <cstdint>
#include <cstring>
#include <functional>
#include <vector>

#include "acmp.h"
#include "acmp_fake.hpp"
#include "wire.h"

using namespace acmp_test;

namespace {
unsigned reentry_traps;
}

extern "C" void ctrl_reentry_assert(const char* module) {
    static_cast<void>(module);
    reentry_traps++;
}

namespace {

class AcmpCore : public ::testing::Test {
 protected:
    void SetUp() override {
        fk = Fake{};
        reentry_traps = 0;
        cfg = acmp_config{};
        cfg.entity_id = kOwn;
        cfg.n_interfaces = 2;
        cfg.mac[0] = kMac0;
        cfg.mac[1] = kMac1;
        cfg.n_sinks = 3;
        cfg.sink_interface[0] = 0;
        cfg.sink_interface[1] = 0;
        cfg.sink_interface[2] = 1;
        cfg.n_sources = 2;
        cfg.source_interface[0] = 0;
        cfg.source_interface[1] = 1;
        for (unsigned i = 0; i < ACMP_MAX_SOURCES; ++i) {
            fk.source[i] = acmp_source_state{true, {kSid + i, kDa + i, 2u}, false};
        }
        ASSERT_TRUE(acmp_init(&a, &cfg, &kPorts, &kEnv));
    }

    void rx(const Pdu& p, unsigned interface = 0) {
        auto f = acmpdu(p);
        acmp_rx(&a, interface, f.data(), f.size());
    }
    void adp(const Adp& d, unsigned interface = 0) {
        auto f = adpdu(d);
        acmp_adp_rx(&a, interface, f.data(), f.size());
    }
    static Pdu command(std::uint8_t msg, unsigned sink, std::uint64_t talker = kTkA, std::uint16_t uid = 1,
                       std::uint64_t ctlr = kCtl1, std::uint16_t flags = 0, std::uint16_t seq = 0x4100) {
        Pdu p;
        p.msg = msg;
        p.controller = ctlr;
        p.talker = talker;
        p.listener = kOwn;
        p.talker_uid = uid;
        p.listener_uid = static_cast<std::uint16_t>(sink);
        p.flags = flags;
        p.seq = seq;
        return p;
    }
    void bind(unsigned sink, std::uint64_t talker = kTkA, std::uint16_t uid = 1, std::uint64_t ctlr = kCtl1,
              bool sw = false) {
        rx(command(spec::MSG_BIND_RX_COMMAND, sink, talker, uid, ctlr, sw ? spec::FLAG_STREAMING_WAIT : 0u),
           a.sinks[sink].interface);
    }

    Pdu probe_answer(unsigned k, std::uint8_t status = spec::STATUS_SUCCESS) const {
        const acmp_sink& s = a.sinks[k];
        Pdu p;
        p.msg = spec::MSG_PROBE_TX_RESPONSE;
        p.status = status;
        p.controller = s.probe_controller;
        p.talker = s.probe_talker;
        p.listener = kOwn;
        p.talker_uid = s.probe_talker_uid;
        p.listener_uid = static_cast<std::uint16_t>(k);
        p.seq = s.probe_seq;
        p.stream_id = kSid + k;
        p.dest_mac = kDa + k;
        p.vlan = 2;
        return p;
    }

    void fire(unsigned k) {
        fk.now = a.sinks[k].timer_deadline;
        acmp_timer_expired(&a, a.sinks[k].interface);
    }
    void fire_adp(unsigned k) {
        fk.now = a.sinks[k].adp_deadline;
        acmp_timer_expired(&a, a.sinks[k].interface);
    }

    void to_state(unsigned k, acmp_sink_state st) {
        if (st == ACMP_UNBOUND) {
            return;
        }
        if (st == ACMP_PRB_W_AVAIL || st == ACMP_PRB_W_DELAY) {
            bind(k);
            adp(Adp{}, a.sinks[k].interface);
            Adp gone;
            gone.msg = spec::ADPDU_ENTITY_DEPARTING;
            adp(gone, a.sinks[k].interface);            // Milan v1.2 5.5.3.5.22
            if (st == ACMP_PRB_W_DELAY) {
                Adp back;
                back.index = 2;
                adp(back, a.sinks[k].interface);        // Milan v1.2 5.5.3.5.9
            }
            return;
        }
        bind(k);
        if (st == ACMP_PRB_W_RESP2) {
            fire(k);
        } else if (st == ACMP_PRB_W_RETRY) {
            rx(probe_answer(k, 5u), a.sinks[k].interface);
        } else if (st == ACMP_SETTLED_NO_RSV || st == ACMP_SETTLED_RSV_OK) {
            rx(probe_answer(k), a.sinks[k].interface);
            if (st == ACMP_SETTLED_RSV_OK) {
                acmp_tk_registered(&a, k, false);
            }
        }
    }
    Pdu last() const { return read(fk.sent.back().bytes.data()); }
    acmp_sink_view view(unsigned k) const {
        acmp_sink_view v{};
        static_cast<void>(acmp_view(&a, k, &v));
        return v;
    }

    // Milan v1.2 5.5.1.2; Milan v1.2 5.5.2.6
    // Milan v1.2 5.6.4.5.3; Milan v1.2 5.6.4.5.4
    void peer_loss_recovery(bool expired) {
        bind(0);
        ASSERT_EQ(fk.sent.size(), 2u) << "peer loss setup sends a bind response and initial probe";
        const auto first_sequence = last().seq;
        adp(Adp{});
        ASSERT_TRUE(a.sinks[0].discovered && a.sinks[0].adp_armed)
            << "peer loss setup discovers the bound talker and arms aging";
        fk.clear();
        if (expired) {
            fire_adp(0);
        } else {
            Adp gone;
            gone.msg = spec::ADPDU_ENTITY_DEPARTING;
            adp(gone);
        }
        const auto retained = view(0);
        EXPECT_TRUE(retained.bound && retained.binding.talker_entity_id == kTkA &&
                    retained.binding.talker_unique_id == 1u && retained.binding.controller_entity_id == kCtl1)
            << "peer loss retains the binding and its talker, stream and controller";
        EXPECT_TRUE(!a.sinks[0].discovered && !a.sinks[0].adp_armed &&
                    retained.state == ACMP_PRB_W_AVAIL)
            << "peer loss waits for a new advertisement with aging stopped";
        EXPECT_TRUE(fk.sent.empty()) << "peer loss sends no stale probe before rediscovery";
        Adp back;
        back.index = 2;
        adp(back);
        ASSERT_TRUE(a.sinks[0].discovered && a.sinks[0].state == ACMP_PRB_W_DELAY &&
                    a.sinks[0].timer == ACMP_TIMER_DELAY)
            << "returning talker remains discoverable and starts a fresh probe delay";
        fire(0);
        ASSERT_EQ(fk.sent.size(), 1u) << "rediscovery sends exactly one fresh probe";
        const auto probe = last();
        EXPECT_TRUE(probe.msg == spec::MSG_PROBE_TX_COMMAND && probe.talker == kTkA &&
                    probe.talker_uid == 1u && probe.listener == kOwn && probe.listener_uid == 0u &&
                    probe.controller == kCtl1 && probe.seq != first_sequence)
            << "rediscovery probes the retained binding with a new sequence";
        EXPECT_TRUE(view(0).bound && view(0).state == ACMP_PRB_W_RESP)
            << "rediscovery keeps the sink bound while awaiting the new response";
    }

    acmp_config cfg{};
    acmp a{};
};

std::uint32_t state_drawing(std::uint32_t ms) {
    for (std::uint32_t s = 1;; ++s) {
        std::uint32_t x = s;
        x ^= x << 13;
        x ^= x >> 17;
        x ^= x << 5;
        if ((((x >> 16) * (spec::TMR_DELAY_MAX_MS + 1u)) >> 16) == ms) {
            return s;
        }
    }
}

constexpr acmp_sink_state kStates[] = {ACMP_UNBOUND,     ACMP_PRB_W_AVAIL,    ACMP_PRB_W_DELAY,
                                       ACMP_PRB_W_RESP,  ACMP_PRB_W_RESP2,    ACMP_PRB_W_RETRY,
                                       ACMP_SETTLED_NO_RSV, ACMP_SETTLED_RSV_OK};

// REQ: ACMP-01
TEST_F(AcmpCore, A0InitRefusesWhatTheStaticSizesCannotHold) {

    acmp b{};
    acmp_config bad = cfg;
    bad.n_interfaces = 0;
    bad.n_sinks = 0;
    bad.n_sources = 0;
    EXPECT_FALSE(acmp_init(&b, &bad, &kPorts, &kEnv)) << "A0 no interface is refused";
    bad = cfg;
    bad.n_interfaces = ACMP_MAX_INTERFACES + 1u;
    EXPECT_FALSE(acmp_init(&b, &bad, &kPorts, &kEnv)) << "A0 more interfaces than ACMP_MAX_INTERFACES are refused";
    bad = cfg;
    bad.n_sinks = ACMP_MAX_SINKS + 1u;
    bad.n_sources = 0;
    for (std::uint8_t& i : bad.sink_interface) {
        i = 0;
    }
    EXPECT_FALSE(acmp_init(&b, &bad, &kPorts, &kEnv)) << "A0 more sinks than ACMP_MAX_SINKS are refused";

    struct SourceOverflow {
        acmp_config config;
        std::uint8_t extra[alignof(acmp_config)]{};
    } sources{cfg, {}};
    static_assert(offsetof(acmp_config, source_interface) + ACMP_MAX_SOURCES < sizeof(SourceOverflow));
    sources.config.n_sources = ACMP_MAX_SOURCES + 1u;
    auto* storage = reinterpret_cast<unsigned char*>(&sources);
    std::memset(storage + offsetof(acmp_config, source_interface), 0,
                sizeof(sources) - offsetof(acmp_config, source_interface));
    EXPECT_FALSE(acmp_init(&b, &sources.config, &kPorts, &kEnv))
        << "A0 more sources than ACMP_MAX_SOURCES are refused";
    bad = cfg;
    bad.sink_interface[2] = 2;
    EXPECT_FALSE(acmp_init(&b, &bad, &kPorts, &kEnv)) << "A0 a sink on an interface the entity lacks is refused";
    bad = cfg;
    bad.source_interface[1] = 2;
    EXPECT_FALSE(acmp_init(&b, &bad, &kPorts, &kEnv)) << "A0 a source on an interface the entity lacks is refused";
}

// REQ: ACMP-01
TEST_F(AcmpCore, A0EverySinkStartsUnboundAndNothingIsCalled) {
    for (unsigned k = 0; k < cfg.n_sinks; ++k) {
        acmp_sink_view v = view(k);
        EXPECT_TRUE(v.state == ACMP_UNBOUND && !v.bound && v.probing_status == ACMP_PROBING_DISABLED &&
                    v.acmp_status == 0u)
            << "A0 every sink starts UNBOUND, probing disabled, ACMP status 0 (5.5.3.5.1)";
    }
    EXPECT_TRUE(fk.calls.empty()) << "A0 init calls no port: nothing reads the mailbox before it is open";
    EXPECT_EQ(a.sinks[2].interface, 1u) << "A0 each sink keeps its descriptor's AVB interface";
    acmp_sink_view v{};
    EXPECT_FALSE(acmp_view(&a, cfg.n_sinks, &v)) << "A0 there is no view of a sink the configuration lacks";
    EXPECT_FALSE(acmp_change_pending(&a, cfg.n_sinks)) << "A0 nor a pending change";
}

// Milan v1.2 5.5.3.5.3

// REQ: ACMP-03, ACMP-02, MFCONN-01
TEST_F(AcmpCore, A1BindFromUnboundRespondsThenProbes) {
    rx(command(spec::MSG_BIND_RX_COMMAND, 0, kTkA, 1, kCtl1, spec::FLAG_STREAMING_WAIT | spec::FLAG_FAST_CONNECT, 0x4100));
    ASSERT_EQ(fk.sent.size(), 2u) << "A1 BIND_RX sends two frames: the response and the probe";
    Pdu r = read(fk.sent[0].bytes.data());
    Pdu want;
    want.msg = spec::MSG_BIND_RX_RESPONSE;
    want.status = spec::STATUS_SUCCESS;
    want.controller = kCtl1;
    want.talker = kTkA;
    want.listener = kOwn;
    want.talker_uid = 1;
    want.listener_uid = 0;
    want.seq = 0x4100;
    want.count = 1;
    want.flags = spec::FLAG_STREAMING_WAIT;
    EXPECT_TRUE(same(r, want)) << "A1 BIND_RX_RESPONSE is Table 5.32 field by field";
    Pdu p = read(fk.sent[1].bytes.data());
    Pdu probe;
    probe.msg = spec::MSG_PROBE_TX_COMMAND;
    probe.controller = kCtl1;
    probe.talker = kTkA;
    probe.listener = kOwn;
    probe.talker_uid = 1;
    probe.listener_uid = 0;
    probe.seq = 0;
    probe.flags = spec::FLAG_FAST_CONNECT;
    EXPECT_TRUE(same(p, probe)) << "A1 PROBE_TX_COMMAND is Table 5.33 field by field";
    EXPECT_EQ(fk.sent[1].interface, 0u) << "A1 the probe leaves on the sink's AVB interface";
    const uint8_t* b = fk.sent[0].bytes.data();
    EXPECT_TRUE(wire_be64(b) >> 16 == spec::MULTICAST_MAC && (wire_be64(b + 6) >> 16) == kMac0 &&
                wire_be16(b + 12) == spec::ETHERTYPE && b[14] == spec::SUBTYPE &&
                (wire_be16(b + 16) & 0x07FFu) == spec::CONTROL_DATA_LENGTH && wire_be16(b + 68) == 0u)
        << "A1 every frame goes to the ACMP multicast address from the interface's MAC, cdl 44 (8.2.1, 5.5.2.2)";
    const acmp_sink& s = a.sinks[0];
    EXPECT_TRUE(s.state == ACMP_PRB_W_RESP && s.probing == ACMP_PROBING_ACTIVE && s.acmp_status == 0u)
        << "A1 then PRB_W_RESP, PROBING_ACTIVE, ACMP status 0";
    EXPECT_TRUE(s.timer == ACMP_TIMER_NO_RESP && s.timer_deadline == fk.now + spec::TMR_NO_RESP_MS &&
                fk.armed[0] && fk.at[0] == fk.now + spec::TMR_NO_RESP_MS)
        << "A1 and TMR_NO_RESP armed 200 ms out on the interface's timer (Table 5.26)";
    EXPECT_TRUE(s.disc_running && !s.discovered) << "A1 the discovery machine starts, talker not discovered";
    EXPECT_TRUE(s.bound && s.binding.talker_entity_id == kTkA && s.binding.talker_unique_id == 1u &&
                s.binding.controller_entity_id == kCtl1 && s.binding.streaming_wait && !s.started)
        << "A1 the binding parameters are the command's; STREAMING_WAIT binds it stopped";
    EXPECT_TRUE(fk.count(Call::PERSIST) == 1u && fk.calls[static_cast<unsigned>(fk.position(Call::PERSIST))].index == 0u)
        << "A1 the binding is saved (5.5.2.4)";
    EXPECT_TRUE(fk.count(Call::CHANGED) == 1u && fk.position(Call::CHANGED) > fk.position(Call::SEND, 0))
        << "A1 the change is reported after the response was taken (#653)";
}

// REQ: ACMP-03, ACMP-02
TEST_F(AcmpCore, A1BindWithoutStreamingWaitBindsStarted) {
    bind(0, kTkA, 1, kCtl1, false);
    EXPECT_TRUE(a.sinks[0].started && !a.sinks[0].binding.streaming_wait && read(fk.sent[0].bytes.data()).flags == 0u)
        << "A1 a bind without STREAMING_WAIT lands started (IEEE 1722.1-2021 7.4.35)";
}

// Milan v1.2 Table 5.34; Milan v1.2 Table 5.37; Milan v1.2 Table 5.38; Milan v1.2 Table 5.39

// REQ: ACMP-03, ACMP-02, MFCONN-01
TEST_F(AcmpCore, A2GetRxStateInEveryState) {
    for (acmp_sink_state st : kStates) {
        SetUp();
        to_state(0, st);
        fk.clear();
        fk.source[0].dest_mac_valid = true;
        acmp_sink_state before = a.sinks[0].state;
        rx(command(spec::MSG_GET_RX_STATE_COMMAND, 0, 0, 0, kCtl2, 0, 0x4300));
        ASSERT_EQ(fk.sent.size(), 1u) << "A2 GET_RX_STATE is answered in state " << st;
        Pdu r = last();
        Pdu want;
        want.msg = spec::MSG_GET_RX_STATE_RESPONSE;
        want.controller = kCtl2;
        want.listener = kOwn;
        want.seq = 0x4300;
        if (st != ACMP_UNBOUND) {
            want.talker = kTkA;
            want.talker_uid = 1;
            want.count = 1;
            want.flags = spec::FLAG_FAST_CONNECT;
        }
        if (st == ACMP_SETTLED_NO_RSV || st == ACMP_SETTLED_RSV_OK) {
            want.stream_id = kSid;
            want.dest_mac = kDa;
            want.vlan = 2;
        }
        EXPECT_TRUE(same(r, want)) << "A2 GET_RX_STATE_RESPONSE is Table 5.34/5.37/5.38/5.39 in state " << st;
        EXPECT_TRUE(a.sinks[0].state == before && fk.count(Call::CHANGED) == 0u && fk.count(Call::PERSIST) == 0u)
            << "A2 and GET_RX_STATE changes nothing in state " << st;
    }
}

// REQ: ACMP-03, ACMP-02
TEST_F(AcmpCore, A2GetRxStateReportsStreamingWaitAndRegisteringFailed) {
    bind(0, kTkA, 1, kCtl1, true);
    rx(probe_answer(0));
    acmp_tk_registered(&a, 0, true);
    fk.clear();
    rx(command(spec::MSG_GET_RX_STATE_COMMAND, 0, 0, 0, kCtl2));
    EXPECT_EQ(last().flags, spec::FLAG_FAST_CONNECT | spec::FLAG_STREAMING_WAIT | spec::FLAG_REGISTERING_FAILED)
        << "A2 SETTLED_RSV_OK on a Talker Failed: STREAMING_WAIT saved, REGISTERING_FAILED 1 (Table 5.39)";
    EXPECT_TRUE(view(0).registering_failed && view(0).talker_registered) << "A2 and the view says so (5.3.8.8)";
}

// REQ: ACMP-03, ACMP-02
TEST_F(AcmpCore, A2UnknownSinkIsAnsweredListenerUnknownId) {
    for (std::uint8_t msg : {spec::MSG_BIND_RX_COMMAND, spec::MSG_UNBIND_RX_COMMAND, spec::MSG_GET_RX_STATE_COMMAND}) {
        fk.clear();
        rx(command(msg, cfg.n_sinks, kTkA, 7, kCtl1, spec::FLAG_STREAMING_WAIT, 0x77));
        ASSERT_EQ(fk.sent.size(), 1u) << "A2 a command for a sink the entity lacks is answered, msg " << unsigned(msg);
        Pdu want;
        want.msg = static_cast<std::uint8_t>(msg + 1u);
        want.status = spec::STATUS_LISTENER_UNKNOWN_ID;
        want.controller = kCtl1;
        want.talker = kTkA;
        want.listener = kOwn;
        want.talker_uid = 7;
        want.listener_uid = static_cast<std::uint16_t>(cfg.n_sinks);
        want.seq = 0x77;
        EXPECT_TRUE(same(last(), want)) << "A2 LISTENER_UNKNOWN_ID, the command's fields echoed (Table 5.27)";
    }
    EXPECT_TRUE(a.unknown_sink == 3u && fk.count(Call::PERSIST) == 0u && fk.count(Call::CHANGED) == 0u)
        << "A2 and nothing changes";
}

// Milan v1.2 Table 5.36

// REQ: ACMP-03, ACMP-02, MFCONN-01, MFSRP-01
TEST_F(AcmpCore, A3UnbindInEveryState) {
    for (acmp_sink_state st : kStates) {
        SetUp();
        to_state(0, st);
        fk.clear();
        rx(command(spec::MSG_UNBIND_RX_COMMAND, 0, kTkA, 1, kCtl1, 0, 0x4200));
        ASSERT_FALSE(fk.sent.empty()) << "A3 UNBIND_RX is answered in state " << st;
        Pdu want;
        want.msg = spec::MSG_UNBIND_RX_RESPONSE;
        want.controller = kCtl1;
        want.listener = kOwn;
        want.seq = 0x4200;
        EXPECT_TRUE(same(last(), want)) << "A3 UNBIND_RX_RESPONSE is Table 5.36: talker_entity_id and "
                                           "talker_unique_id 0, in state "
                                        << st;
        const acmp_sink& s = a.sinks[0];
        EXPECT_TRUE(s.state == ACMP_UNBOUND && !s.bound && s.probing == ACMP_PROBING_DISABLED && s.acmp_status == 0u &&
                    s.timer == ACMP_TIMER_NONE && !s.disc_running && !s.adp_armed && !s.started &&
                    s.binding.talker_entity_id == 0u && s.binding.controller_entity_id == 0u)
            << "A3 then UNBOUND, binding cleared, nothing running, in state " << st;
        EXPECT_EQ(fk.count(Call::PERSIST), st == ACMP_UNBOUND ? 0u : 1u)
            << "A3 the cleared binding is saved, unless there was none, in state " << st;
        bool settled = st == ACMP_SETTLED_NO_RSV || st == ACMP_SETTLED_RSV_OK;
        EXPECT_TRUE(!settled || (fk.count(Call::SRP) == 1u && !fk.calls[unsigned(fk.position(Call::SRP))].flag &&
                                 fk.position(Call::SRP) < fk.position(Call::SEND)))
            << "A3 a settled sink stops SRP before the response (5.5.3.5.39, .45)";
        EXPECT_TRUE(st == ACMP_UNBOUND ||
                    (fk.count(Call::CHANGED) == 1u && fk.position(Call::CHANGED) > fk.position(Call::SEND)))
            << "A3 the change is reported after the response (#653), in state " << st;
        EXPECT_TRUE(!fk.armed[0]) << "A3 and the interface's timer is stopped, in state " << st;
    }
}

// Milan v1.2 5.5.2.4; Milan v1.2 5.5.2.5

// REQ: ACMP-03, ACMP-02
TEST_F(AcmpCore, A4LockedByAnotherControllerRefusesBindAndUnbind) {
    for (acmp_sink_state st : {ACMP_UNBOUND, ACMP_PRB_W_RESP, ACMP_SETTLED_RSV_OK}) {
        for (std::uint8_t msg : {spec::MSG_BIND_RX_COMMAND, spec::MSG_UNBIND_RX_COMMAND}) {
            SetUp();
            to_state(0, st);
            fk.locked = true;
            fk.holder = kCtl2;
            fk.clear();
            acmp_sink before = a.sinks[0];
            rx(command(msg, 0, kTkB, 3, kCtl1, 0, 0x4400));
            ASSERT_EQ(fk.sent.size(), 1u) << "A4 one response";
            Pdu want;
            want.msg = static_cast<std::uint8_t>(msg + 1u);
            want.status = spec::STATUS_CONTROLLER_NOT_AUTHORIZED;
            want.controller = kCtl1;
            want.talker = kTkB;
            want.listener = kOwn;
            want.talker_uid = 3;
            want.listener_uid = 0;
            want.seq = 0x4400;
            EXPECT_TRUE(same(last(), want))
                << "A4 CONTROLLER_NOT_AUTHORIZED (16, IEEE 1722.1-2021 Table 8-3), fields echoed (Tables 5.31, 5.35)";
            EXPECT_TRUE(a.sinks[0].state == before.state && a.sinks[0].bound == before.bound &&
                        a.sinks[0].binding.talker_entity_id == before.binding.talker_entity_id &&
                        fk.count(Call::PERSIST) == 0u && fk.count(Call::CHANGED) == 0u && fk.count(Call::SRP) == 0u)
                << "A4 and nothing changes";
        }
    }
    EXPECT_EQ(a.refused_locked, 1u) << "A4 each refusal is counted";
}

// REQ: ACMP-03, ACMP-02
TEST_F(AcmpCore, A4TheLockingControllerPassesAndGetRxStateIsNotLocked) {
    fk.locked = true;
    fk.holder = kCtl1;
    bind(0);
    EXPECT_EQ(a.sinks[0].state, ACMP_PRB_W_RESP) << "A4 the locking controller binds";
    fk.holder = kCtl2;
    fk.clear();
    rx(command(spec::MSG_GET_RX_STATE_COMMAND, 0, 0, 0, kCtl1));
    EXPECT_TRUE(last().status == spec::STATUS_SUCCESS && fk.count(Call::LOCKED) == 0u)
        << "A4 GET_RX_STATE asks no lock (5.5.3.5.4)";
}

// REQ: ACMP-03, ACMP-02
TEST_F(AcmpCore, A5RebindTheSameSourceUpdatesAndExits) {
    for (acmp_sink_state st : kStates) {
        if (st == ACMP_UNBOUND) {
            continue;
        }
        SetUp();
        to_state(0, st);
        acmp_sink before = a.sinks[0];
        std::uint16_t seq = a.sequence_id;
        fk.clear();
        rx(command(spec::MSG_BIND_RX_COMMAND, 0, kTkA, 1, kCtl2, spec::FLAG_STREAMING_WAIT, 0x4500));
        ASSERT_EQ(fk.sent.size(), 1u) << "A5 a re-bind of the same source sends the response alone, state " << st;
        EXPECT_TRUE(last().msg == spec::MSG_BIND_RX_RESPONSE && last().status == spec::STATUS_SUCCESS &&
                    last().count == 1u && last().flags == spec::FLAG_STREAMING_WAIT)
            << "A5 Table 5.32";
        const acmp_sink& s = a.sinks[0];
        EXPECT_TRUE(s.binding.controller_entity_id == kCtl2 && s.binding.streaming_wait && !s.started)
            << "A5 the controller and STREAMING_WAIT are updated, state " << st;
        EXPECT_TRUE(s.state == before.state && s.timer == before.timer && s.timer_deadline == before.timer_deadline &&
                    s.disc_running == before.disc_running && s.discovered == before.discovered &&
                    a.sequence_id == seq && fk.count(Call::SRP) == 0u)
            << "A5 and nothing else moves: no probe, no timer, discovery kept, state " << st;
        EXPECT_EQ(fk.count(Call::PERSIST), 1u) << "A5 the updated binding is saved, state " << st;
    }
}

// REQ: ACMP-03, ACMP-02
TEST_F(AcmpCore, A6BindAnotherSourceRestartsTheSink) {
    for (acmp_sink_state st : kStates) {
        if (st == ACMP_UNBOUND) {
            continue;
        }
        SetUp();
        to_state(0, st);
        std::uint16_t seq = a.sequence_id;
        fk.clear();
        rx(command(spec::MSG_BIND_RX_COMMAND, 0, kTkB, 2, kCtl2, 0, 0x4600));
        ASSERT_EQ(fk.sent.size(), 2u) << "A6 response then probe, state " << st;
        Pdu p = read(fk.sent[1].bytes.data());
        EXPECT_TRUE(read(fk.sent[0].bytes.data()).msg == spec::MSG_BIND_RX_RESPONSE &&
                    p.msg == spec::MSG_PROBE_TX_COMMAND && p.talker == kTkB && p.talker_uid == 2u &&
                    p.controller == kCtl2 && p.seq == seq)
            << "A6 the new probe names the new source with the next sequence_id, state " << st;
        const acmp_sink& s = a.sinks[0];
        EXPECT_TRUE(s.state == ACMP_PRB_W_RESP && s.timer == ACMP_TIMER_NO_RESP && s.disc_running && !s.discovered &&
                    !s.adp_armed && s.probing == ACMP_PROBING_ACTIVE && s.acmp_status == 0u)
            << "A6 PRB_W_RESP, discovery restarted not discovered, TMR_NO_RESP, state " << st;
        bool settled = st == ACMP_SETTLED_NO_RSV || st == ACMP_SETTLED_RSV_OK;
        EXPECT_TRUE(settled ? (fk.count(Call::SRP) == 1u && !fk.calls[unsigned(fk.position(Call::SRP))].flag &&
                               view(0).stream.stream_id == 0u)
                            : fk.count(Call::SRP) == 0u)
            << "A6 SRP is stopped and its parameters cleared only when settled (5.5.3.5.37, .43), state " << st;
        EXPECT_EQ(fk.count(Call::PERSIST), 1u) << "A6 the new binding is saved, state " << st;
    }
}

// REQ: ACMP-03, ACMP-02
TEST_F(AcmpCore, A6TheSameTalkerAnotherSourceIsANewBinding) {
    bind(0, kTkA, 1);
    fk.clear();
    rx(command(spec::MSG_BIND_RX_COMMAND, 0, kTkA, 2, kCtl1));
    ASSERT_EQ(fk.sent.size(), 2u) << "A6 the same talker with another talker_unique_id is a new source: a new probe";
    EXPECT_TRUE(a.sinks[0].binding.talker_unique_id == 2u && read(fk.sent[1].bytes.data()).talker_uid == 2u)
        << "A6 the binding and the probe name the new source (step 2 compares both fields)";
}

// Milan v1.2 5.5.3.1; Milan v1.2 5.5.3.5.18

// REQ: ACMP-04
TEST_F(AcmpCore, A7ResponsesKeyOnTheListenerUniqueId) {
    bind(0, kTkA, 1);
    bind(1, kTkA, 1);
    Pdu to1 = probe_answer(1);
    rx(to1);
    EXPECT_TRUE(a.sinks[1].state == ACMP_SETTLED_NO_RSV && a.sinks[0].state == ACMP_PRB_W_RESP)
        << "A7 the response belongs to the sink its listener_unique_id names, not to every sink probing that source";
    rx(probe_answer(0));
    EXPECT_EQ(a.sinks[0].state, ACMP_SETTLED_NO_RSV) << "A7 and sink 0 settles on its own response";
}

// REQ: ACMP-04
TEST_F(AcmpCore, A7EachGuardTermIsChecked) {
    bind(0);
    Pdu good = probe_answer(0);
    Pdu bad = good;
    bad.controller = kCtl2;
    rx(bad);
    bad = good;
    bad.talker = kTkB;
    rx(bad);
    bad = good;
    bad.talker_uid = 9;
    rx(bad);
    bad = good;
    bad.seq = static_cast<std::uint16_t>(good.seq + 1u);
    rx(bad);
    EXPECT_TRUE(a.sinks[0].state == ACMP_PRB_W_RESP && a.probe_mismatch == 4u)
        << "A7 a response with another controller, talker, talker_unique_id or sequence_id is ignored (5.5.3.5.18 step 1)";
    rx(good);
    EXPECT_EQ(a.sinks[0].state, ACMP_SETTLED_NO_RSV) << "A7 and the right one settles, so no guard refuses everything";
}

// REQ: ACMP-04
TEST_F(AcmpCore, A7TheGuardReadsTheSentProbeNotTheBinding) {
    bind(0, kTkA, 1, kCtl1);
    Pdu answer = probe_answer(0);
    rx(command(spec::MSG_BIND_RX_COMMAND, 0, kTkA, 1, kCtl2));
    ASSERT_EQ(a.sinks[0].binding.controller_entity_id, kCtl2);
    rx(answer);
    EXPECT_EQ(a.sinks[0].state, ACMP_SETTLED_NO_RSV)
        << "A7 the answer to the probe sent before a re-bind still matches the probe that was sent";
}

// REQ: ACMP-04
TEST_F(AcmpCore, A7ResponsesOutsideProbingAreIgnored) {
    for (acmp_sink_state st : kStates) {
        if (st == ACMP_PRB_W_RESP || st == ACMP_PRB_W_RESP2) {
            continue;
        }
        SetUp();
        to_state(0, st);
        acmp_sink before = a.sinks[0];
        fk.clear();
        Pdu r = probe_answer(0);
        rx(r);
        EXPECT_TRUE(a.sinks[0].state == before.state && fk.calls.empty())
            << "A7 RCV_PROBE_TX_RESP is ignored outside PRB_W_RESP and PRB_W_RESP2 (Table 5.30 -), state " << st;
    }
    SetUp();
    Pdu r = probe_answer(0);
    r.listener_uid = static_cast<std::uint16_t>(cfg.n_sinks);
    rx(r);
    EXPECT_TRUE(fk.sent.empty() && a.unknown_sink == 1u)
        << "A7 a probe response for a sink the entity lacks is ignored, never answered (5.5.3.1)";
}

// Milan v1.2 5.5.3.5.18; Milan v1.2 5.5.3.5.25

// REQ: ACMP-04, MFSRP-01
TEST_F(AcmpCore, A8SuccessSettles) {
    for (acmp_sink_state st : {ACMP_PRB_W_RESP, ACMP_PRB_W_RESP2}) {
        SetUp();
        to_state(0, st);
        fk.clear();
        Pdu r = probe_answer(0);
        r.vlan = 0x1002;                                 // Milan v1.2 5.3.8.9
        rx(r);
        const acmp_sink& s = a.sinks[0];
        EXPECT_TRUE(s.state == ACMP_SETTLED_NO_RSV && s.probing == ACMP_PROBING_COMPLETED && s.acmp_status == 0u)
            << "A8 SUCCESS: SETTLED_NO_RSV, PROBING_COMPLETED, state " << st;
        EXPECT_TRUE(s.timer == ACMP_TIMER_NO_TK && s.timer_deadline == fk.now + spec::TMR_NO_TK_MS)
            << "A8 TMR_NO_RESP stopped and TMR_NO_TK 10 s started";
        ASSERT_EQ(fk.count(Call::SRP), 1u) << "A8 SRP is started";
        const Call& c = fk.calls[unsigned(fk.position(Call::SRP))];
        EXPECT_TRUE(c.flag && c.stream.stream_id == kSid && c.stream.dest_mac == kDa && c.stream.vlan_id == 0x1002u)
            << "A8 with the response's stream_id, stream_dest_mac and stream_vlan_id exactly";
        EXPECT_TRUE(view(0).settled && view(0).stream.vlan_id == 0x1002u) << "A8 and the view holds them";
        EXPECT_TRUE(fk.sent.empty()) << "A8 a response is not answered";
    }
}

// REQ: ACMP-04
TEST_F(AcmpCore, A9FailureWaitsForTheRetry) {
    for (acmp_sink_state st : {ACMP_PRB_W_RESP, ACMP_PRB_W_RESP2}) {
        SetUp();
        to_state(0, st);
        rx(probe_answer(0, spec::STATUS_TALKER_DEST_MAC_FAIL));
        const acmp_sink& s = a.sinks[0];
        EXPECT_TRUE(s.state == ACMP_PRB_W_RETRY && s.acmp_status == spec::STATUS_TALKER_DEST_MAC_FAIL &&
                    s.probing == ACMP_PROBING_ACTIVE)
            << "A9 a failed response: PRB_W_RETRY, the ACMP status is its status (5.5.3.5.18 step 3), state " << st;
        EXPECT_TRUE(s.timer == ACMP_TIMER_RETRY && s.timer_deadline == fk.now + spec::TMR_RETRY_MS)
            << "A9 and TMR_RETRY 4 s";
    }
}

// REQ: ACMP-04
TEST_F(AcmpCore, A10NoResponseSendsTheDuplicateThenGivesUp) {
    bind(0);
    auto first = fk.sent.back();
    std::uint16_t seq = a.sequence_id;
    fk.clear();
    fire(0);
    ASSERT_EQ(fk.sent.size(), 1u) << "A10 the first TMR_NO_RESP sends one frame";
    EXPECT_TRUE(fk.sent[0].bytes == first.bytes && fk.sent[0].interface == first.interface && a.sequence_id == seq)
        << "A10 an exact duplicate of the first probe, same sequence_id (5.5.3.5.16)";
    EXPECT_TRUE(a.sinks[0].state == ACMP_PRB_W_RESP2 && a.sinks[0].probe_retried &&
                a.sinks[0].timer == ACMP_TIMER_NO_RESP && a.sinks[0].timer_deadline == fk.now + spec::TMR_NO_RESP_MS)
        << "A10 PRB_W_RESP2 with TMR_NO_RESP 200 ms";
    fk.clear();
    fire(0);
    EXPECT_TRUE(fk.sent.empty() && a.sinks[0].state == ACMP_PRB_W_RETRY &&
                a.sinks[0].acmp_status == spec::STATUS_LISTENER_TALKER_TIMEOUT &&
                a.sinks[0].timer == ACMP_TIMER_RETRY && a.sinks[0].timer_deadline == fk.now + spec::TMR_RETRY_MS)
        << "A10 the second: no frame, LISTENER_TALKER_TIMEOUT, TMR_RETRY 4 s (5.5.3.5.23)";
}

// REQ: ACMP-04
TEST_F(AcmpCore, A11RetryWaitsForTheTalkerOrDelays) {
    to_state(0, ACMP_PRB_W_RETRY);
    fire(0);
    EXPECT_TRUE(a.sinks[0].state == ACMP_PRB_W_AVAIL && a.sinks[0].probing == ACMP_PROBING_PASSIVE &&
                a.sinks[0].acmp_status == 0u && a.sinks[0].timer == ACMP_TIMER_NONE)
        << "A11 TMR_RETRY, talker not discovered: PRB_W_AVAIL, PASSIVE, status 0 (5.5.3.5.30 step 1)";
    SetUp();
    bind(0);
    adp(Adp{});
    rx(probe_answer(0, spec::STATUS_TALKER_DEST_MAC_FAIL));
    fire(0);
    const acmp_sink& s = a.sinks[0];
    EXPECT_TRUE(s.state == ACMP_PRB_W_DELAY && s.timer == ACMP_TIMER_DELAY &&
                s.timer_deadline - fk.now <= spec::TMR_DELAY_MAX_MS && s.timer_deadline - fk.now == a.last_draw_ms)
        << "A11 TMR_RETRY, talker discovered: TMR_DELAY 0 to 1 s, PRB_W_DELAY (5.5.3.5.30 step 2)";
    EXPECT_TRUE(s.acmp_status == spec::STATUS_TALKER_DEST_MAC_FAIL && s.probing == ACMP_PROBING_ACTIVE)
        << "A11 and the ACMP status stays: step 2 sets none";
}

// REQ: ACMP-04
TEST_F(AcmpCore, A12DelaySendsANewProbe) {
    to_state(0, ACMP_PRB_W_DELAY);
    std::uint16_t seq = a.sequence_id;
    fk.clear();
    fire(0);
    ASSERT_EQ(fk.sent.size(), 1u) << "A12 TMR_DELAY sends the probe (5.5.3.5.10)";
    EXPECT_TRUE(last().msg == spec::MSG_PROBE_TX_COMMAND && last().seq == seq && a.sequence_id == seq + 1u &&
                a.sinks[0].probe_seq == seq)
        << "A12 a new PROBE_TX_COMMAND with the next sequence_id, its copy kept";
    EXPECT_TRUE(a.sinks[0].state == ACMP_PRB_W_RESP && a.sinks[0].timer == ACMP_TIMER_NO_RESP &&
                a.sinks[0].timer_deadline == fk.now + spec::TMR_NO_RESP_MS)
        << "A12 PRB_W_RESP, TMR_NO_RESP 200 ms";
}

// REQ: ACMP-04
TEST_F(AcmpCore, A13NoTalkerAttributeReprobes) {
    to_state(0, ACMP_SETTLED_NO_RSV);
    fk.clear();
    fire(0);
    EXPECT_TRUE(fk.count(Call::SRP) == 1u && !fk.calls[unsigned(fk.position(Call::SRP))].flag &&
                view(0).stream.stream_id == 0u)
        << "A13 TMR_NO_TK clears the SRP parameters and stops SRP (5.5.3.5.36 step 1)";
    EXPECT_TRUE(a.sinks[0].state == ACMP_PRB_W_AVAIL && a.sinks[0].probing == ACMP_PROBING_PASSIVE)
        << "A13 talker not discovered: PRB_W_AVAIL, PASSIVE (step 2)";
    SetUp();
    bind(0);
    adp(Adp{});
    rx(probe_answer(0));
    rx(probe_answer(0));
    a.sinks[0].acmp_status = 0;
    fire(0);
    EXPECT_TRUE(a.sinks[0].state == ACMP_PRB_W_DELAY && a.sinks[0].probing == ACMP_PROBING_ACTIVE &&
                a.sinks[0].acmp_status == 0u && a.sinks[0].timer == ACMP_TIMER_DELAY)
        << "A13 talker discovered: TMR_DELAY, PRB_W_DELAY, ACTIVE, status 0 (step 3)";
}

// REQ: ACMP-04, MFSRP-01
TEST_F(AcmpCore, A14RegisteredSettlesTheReservation) {
    to_state(0, ACMP_SETTLED_NO_RSV);
    fk.clear();
    acmp_tk_registered(&a, 0, false);
    EXPECT_TRUE(a.sinks[0].state == ACMP_SETTLED_RSV_OK && a.sinks[0].timer == ACMP_TIMER_NONE && !fk.armed[0])
        << "A14 EVT_TK_REGISTERED: TMR_NO_TK cleared, SETTLED_RSV_OK (5.5.3.5.42)";
    EXPECT_TRUE(fk.count(Call::CHANGED) == 1u && view(0).talker_registered && !view(0).registering_failed)
        << "A14 the registration state is a Table 5.22 item: reported";
    for (acmp_sink_state st : kStates) {
        if (st == ACMP_SETTLED_NO_RSV) {
            continue;
        }
        SetUp();
        to_state(0, st);
        acmp_sink before = a.sinks[0];
        acmp_tk_registered(&a, 0, true);
        EXPECT_TRUE(a.sinks[0].state == before.state && a.sinks[0].tk_failed == before.tk_failed &&
                    a.impossible == 1u)
            << "A14 EVT_TK_REGISTERED anywhere else is Table 5.30's x: counted, nothing changes, state " << st;
    }
    acmp_tk_registered(&a, cfg.n_sinks, false);
    EXPECT_EQ(a.impossible, 2u) << "A14 as is one for a sink the entity lacks";
}

// REQ: ACMP-04, MFSRP-01, MFRECOVERY-01
TEST_F(AcmpCore, A15UnregisteredReprobes) {
    to_state(0, ACMP_SETTLED_RSV_OK);
    fk.clear();
    acmp_tk_unregistered(&a, 0);
    EXPECT_TRUE(fk.count(Call::SRP) == 1u && !fk.calls[unsigned(fk.position(Call::SRP))].flag &&
                a.sinks[0].state == ACMP_PRB_W_AVAIL && a.sinks[0].probing == ACMP_PROBING_PASSIVE)
        << "A15 EVT_TK_UNREGISTERED, talker not discovered: SRP stopped, PRB_W_AVAIL (5.5.3.5.48 steps 1, 2)";
    SetUp();
    bind(0);
    adp(Adp{});
    rx(probe_answer(0));
    acmp_tk_registered(&a, 0, false);
    acmp_tk_unregistered(&a, 0);
    EXPECT_TRUE(a.sinks[0].state == ACMP_PRB_W_DELAY && a.sinks[0].probing == ACMP_PROBING_ACTIVE &&
                a.sinks[0].timer == ACMP_TIMER_DELAY)
        << "A15 talker discovered: TMR_DELAY, PRB_W_DELAY (step 3)";
    for (acmp_sink_state st : kStates) {
        if (st == ACMP_SETTLED_RSV_OK) {
            continue;
        }
        SetUp();
        to_state(0, st);
        acmp_sink before = a.sinks[0];
        fk.clear();
        acmp_tk_unregistered(&a, 0);
        EXPECT_TRUE(a.sinks[0].state == before.state && fk.calls.empty() && a.impossible == 1u)
            << "A15 EVT_TK_UNREGISTERED anywhere else is Table 5.30's x, state " << st;
    }
    acmp_tk_unregistered(&a, cfg.n_sinks);
    EXPECT_EQ(a.impossible, 2u) << "A15 as is one for a sink the entity lacks";
}

// REQ: ACMP-04, MFSRP-01
TEST_F(AcmpCore, KindChangesOnlyTheSettledView) {
    to_state(0, ACMP_SETTLED_RSV_OK);
    for (bool failed : {true, false}) {
        fk.clear();
        acmp_tk_kind_changed(&a, 0, failed);
        EXPECT_EQ(view(0).registering_failed, failed) << "kind updates the reported view";
        EXPECT_EQ(a.sinks[0].state, ACMP_SETTLED_RSV_OK) << "kind preserves settlement";
        EXPECT_EQ(fk.count(Call::CHANGED), 1u) << "kind change notifies once";
        EXPECT_EQ(fk.count(Call::SRP), 0u) << "kind does not reprobe";
        acmp_tk_kind_changed(&a, 0, failed);
        EXPECT_EQ(fk.count(Call::CHANGED), 1u) << "same kind is idempotent";
    }
    for (acmp_sink_state st : kStates) {
        if (st == ACMP_SETTLED_RSV_OK) { continue; }
        SetUp();
        to_state(0, st);
        fk.clear();
        const acmp_sink before = a.sinks[0];
        acmp_tk_kind_changed(&a, 0, true);
        EXPECT_EQ(a.impossible, 1u) << "kind refuses non-settled state";
        EXPECT_EQ(a.sinks[0].state, before.state);
        EXPECT_EQ(a.sinks[0].tk_failed, before.tk_failed);
        EXPECT_TRUE(fk.calls.empty());
    }
    acmp_tk_kind_changed(&a, cfg.n_sinks, false);
    EXPECT_EQ(a.impossible, 2u) << "kind refuses unknown sink";
}

// IEEE 1722.1-2021 8.2.1.15

// REQ: ACMP-04
TEST_F(AcmpCore, A16OneCounterForEveryNewProbe) {
    bind(0);
    bind(1, kTkB, 2);
    EXPECT_TRUE(a.sinks[0].probe_seq == 0u && a.sinks[1].probe_seq == 1u)
        << "A16 each new PROBE_TX_COMMAND takes the next sequence_id, across sinks";
    fire(0);
    EXPECT_EQ(a.sequence_id, 2u) << "A16 a duplicate takes none";
    a.sequence_id = 0xFFFFu;
    bind(2);
    bind(0, kTkB, 3);
    EXPECT_TRUE(a.sinks[2].probe_seq == 0xFFFFu && a.sinks[0].probe_seq == 0u) << "A16 the counter wraps at 2^16";
}

// REQ: ACMP-05
TEST_F(AcmpCore, A17EachInterfaceTimerHoldsItsEarliestDeadline) {
    bind(0);
    bind(2);
    fk.now += 50;
    bind(1, kTkB, 2);
    EXPECT_TRUE(fk.armed[0] && fk.at[0] == a.sinks[0].timer_deadline && fk.armed[1] &&
                fk.at[1] == a.sinks[2].timer_deadline)
        << "A17 each interface's timer is armed at the earliest deadline of its own sinks";
    fk.clear();
    fire(0);
    EXPECT_TRUE(a.sinks[0].state == ACMP_PRB_W_RESP2 && a.sinks[1].state == ACMP_PRB_W_RESP &&
                a.sinks[2].state == ACMP_PRB_W_RESP && fk.sent.size() == 1u)
        << "A17 an expiry takes the due timers only, of its own interface's sinks";
    EXPECT_TRUE(fk.armed[0] && fk.at[0] == a.sinks[1].timer_deadline) << "A17 and re-arms at the next deadline";
    EXPECT_EQ(fk.count(Call::TIMER), 1u) << "A17 the port is called only when the earliest deadline moves";
    fk.clear();
    rx(command(spec::MSG_UNBIND_RX_COMMAND, 2, kTkA, 1, kCtl1), 1);
    EXPECT_TRUE(!fk.armed[1] && fk.count(Call::TIMER) == 1u && fk.calls[unsigned(fk.position(Call::TIMER))].index == 1u)
        << "A17 an interface whose sinks hold no deadline has its timer stopped";
    fk.clear();
    acmp_timer_expired(&a, 0);
    EXPECT_TRUE(fk.sent.empty() && a.sinks[1].state == ACMP_PRB_W_RESP && fk.armed[0] && fk.count(Call::TIMER) == 1u)
        << "A17 an expiry with nothing due changes nothing and re-arms the timer it consumed";
    acmp_timer_expired(&a, cfg.n_interfaces);
    EXPECT_EQ(a.impossible, 1u) << "A17 an expiry of an interface the entity lacks is counted";
}

// REQ: ACMP-05
TEST_F(AcmpCore, A18AZeroDelayProbesInTheSameExpiry) {
    bind(0);
    adp(Adp{});
    rx(probe_answer(0, 5u));
    a.rng = state_drawing(spec::TMR_DELAY_MAX_MS);
    a.seeded = true;
    fire(0);
    EXPECT_TRUE(a.sinks[0].state == ACMP_PRB_W_DELAY && a.last_draw_ms == spec::TMR_DELAY_MAX_MS &&
                a.sinks[0].timer_deadline == fk.now + spec::TMR_DELAY_MAX_MS)
        << "A18 the longest draw is 1000 ms (Table 5.29)";
    SetUp();
    bind(0);
    adp(Adp{});
    rx(probe_answer(0, 5u));
    a.rng = state_drawing(0);
    a.seeded = true;
    fk.clear();
    fire(0);
    EXPECT_TRUE(a.last_draw_ms == 0u && a.sinks[0].state == ACMP_PRB_W_RESP && fk.sent.size() == 1u &&
                last().msg == spec::MSG_PROBE_TX_COMMAND)
        << "A18 TMR_RETRY drawing 0 ms sends its probe in the same expiry";
}

// REQ: ACMP-05
TEST_F(AcmpCore, A18TheSeedIsTakenAtTheFirstDraw) {
    to_state(0, ACMP_PRB_W_DELAY);
    EXPECT_EQ(fk.count(Call::SEED), 1u) << "A18 the seed port is read at the first draw";
    fire(0);
    rx(probe_answer(0, 5u));
    fire(0);
    adp(Adp{0, kTkA, 10, 9, kGm0, 0, 0});
    EXPECT_EQ(fk.count(Call::SEED), 1u) << "A18 and never again";
    SetUp();
    fk.seed = static_cast<std::uint32_t>(kOwn) ^ static_cast<std::uint32_t>(kOwn >> 32) ^ 0x7F4A7C15u;
    to_state(0, ACMP_PRB_W_DELAY);
    EXPECT_TRUE(a.rng != 0u && a.sinks[0].timer == ACMP_TIMER_DELAY)
        << "A18 a seed that cancels the state to 0 leaves it 1: xorshift never leaves 0";
}

// Milan v1.2 5.5.4

// REQ: ACMP-08, MFCONN-01
TEST_F(AcmpCore, A20ProbeTxIsAnsweredFromTheSource) {
    Pdu cmd;
    cmd.msg = spec::MSG_PROBE_TX_COMMAND;
    cmd.controller = kCtl1;
    cmd.talker = kOwn;
    cmd.listener = kTkB;
    cmd.talker_uid = 0;
    cmd.listener_uid = 5;
    cmd.seq = 0x1234;
    cmd.flags = 0xFFFFu;
    fk.source[0] = acmp_source_state{true, {kSid, kDa, 2u}, true};
    rx(cmd);
    ASSERT_EQ(fk.sent.size(), 1u);
    Pdu want;
    want.msg = spec::MSG_PROBE_TX_RESPONSE;
    want.controller = kCtl1;
    want.talker = kOwn;
    want.listener = kTkB;
    want.listener_uid = 5;
    want.seq = 0x1234;
    want.flags = spec::FLAG_FAST_CONNECT | spec::FLAG_STREAMING_WAIT;
    want.stream_id = kSid;
    want.dest_mac = kDa;
    want.vlan = 2;
    EXPECT_TRUE(same(last(), want))
        << "A20 PROBE_TX_RESPONSE is Table 5.43: cc 0, FAST_CONNECT and STREAMING_WAIT echoed, REGISTERING_FAILED 0";
    fk.source[0].dest_mac_valid = false;
    rx(cmd);
    want.status = spec::STATUS_TALKER_DEST_MAC_FAIL;
    want.flags = 0;
    want.stream_id = 0;
    want.dest_mac = 0;
    want.vlan = 0;
    EXPECT_TRUE(same(last(), want)) << "A20 no destination MAC: TALKER_DEST_MAC_FAILED (Table 5.42)";
    cmd.talker_uid = static_cast<std::uint16_t>(cfg.n_sources);
    rx(cmd);
    want.status = spec::STATUS_TALKER_UNKNOWN_ID;
    want.talker_uid = cmd.talker_uid;
    EXPECT_TRUE(same(last(), want)) << "A20 an unknown source: TALKER_UNKNOWN_ID (Table 5.40)";
    cmd.talker_uid = 1;
    rx(cmd, 0);
    want.status = spec::STATUS_INCOMPATIBLE_REQUEST;
    want.talker_uid = 1;
    EXPECT_TRUE(same(last(), want) && fk.sent.back().interface == 0u)
        << "A20 a probe from another interface than the source's: INCOMPATIBLE_REQUEST (5.5.4.1 step 2, Table 5.41)";
    fk.clear();
    rx(cmd, 1);
    EXPECT_TRUE(last().status == spec::STATUS_SUCCESS && fk.sent.back().interface == 1u &&
                last().stream_id == kSid + 1u)
        << "A20 on its own interface source 1 is answered there";
}

// REQ: ACMP-08, MFCONN-01
TEST_F(AcmpCore, A20DisconnectGetTxStateAndGetTxConnection) {
    Pdu cmd;
    cmd.controller = kCtl1;
    cmd.talker = kOwn;
    cmd.listener = kTkB;
    cmd.talker_uid = 0;
    cmd.listener_uid = 5;
    cmd.seq = 0x99;
    cmd.flags = 0xFFFFu;
    cmd.msg = spec::MSG_DISCONNECT_TX_COMMAND;
    rx(cmd);
    Pdu want;
    want.msg = spec::MSG_DISCONNECT_TX_RESPONSE;
    want.controller = kCtl1;
    want.talker = kOwn;
    want.listener = kTkB;
    want.listener_uid = 5;
    want.seq = 0x99;
    EXPECT_TRUE(same(last(), want)) << "A20 DISCONNECT_TX: SUCCESS, cc 0, flags 0, stream 0 (Table 5.45)";
    cmd.talker_uid = 9;
    rx(cmd);
    want.status = spec::STATUS_TALKER_UNKNOWN_ID;
    want.talker_uid = 9;
    EXPECT_TRUE(same(last(), want)) << "A20 DISCONNECT_TX of an unknown source: TALKER_UNKNOWN_ID (Table 5.44)";
    cmd.msg = spec::MSG_GET_TX_STATE_COMMAND;
    rx(cmd);
    want.msg = spec::MSG_GET_TX_STATE_RESPONSE;
    EXPECT_TRUE(same(last(), want)) << "A20 GET_TX_STATE of an unknown source: TALKER_UNKNOWN_ID (Table 5.46)";
    cmd.talker_uid = 0;
    fk.source[0] = acmp_source_state{true, {kSid, kDa, 2u}, true};
    rx(cmd);
    want.status = spec::STATUS_SUCCESS;
    want.talker_uid = 0;
    want.listener = 0;
    want.listener_uid = 0;
    want.flags = spec::FLAG_REGISTERING_FAILED;
    want.stream_id = kSid;
    want.dest_mac = kDa;
    want.vlan = 2;
    EXPECT_TRUE(same(last(), want))
        << "A20 GET_TX_STATE: listener fields 0, cc 0, REGISTERING_FAILED live, the stream (Table 5.47)";
    fk.source[0] = acmp_source_state{false, {kSid, kDa, 2u}, false};
    rx(cmd);
    want.flags = 0;
    want.dest_mac = 0;
    EXPECT_TRUE(same(last(), want)) << "A20 with no destination MAC held, none is reported";
    cmd.msg = spec::MSG_GET_TX_CONNECTION_COMMAND;
    cmd.talker_uid = 9;
    rx(cmd);
    want = Pdu{};
    want.msg = spec::MSG_GET_TX_CONNECTION_RESPONSE;
    want.status = spec::STATUS_NOT_SUPPORTED;
    want.controller = kCtl1;
    want.talker = kOwn;
    want.listener = kTkB;
    want.talker_uid = 9;
    want.listener_uid = 5;
    want.seq = 0x99;
    EXPECT_TRUE(same(last(), want)) << "A20 GET_TX_CONNECTION: NOT_SUPPORTED, fields echoed (5.5.4.4, Table 5.48)";
    EXPECT_TRUE(fk.count(Call::CHANGED) == 0u && fk.count(Call::PERSIST) == 0u)
        << "A20 the talker keeps no state (5.5.2.7)";
}

// REQ: ACMP-02
TEST_F(AcmpCore, A21MessagesNotForThisEntityAreIgnored) {
    Pdu p = command(spec::MSG_BIND_RX_COMMAND, 0);
    p.listener = kTkB;
    rx(p);
    Pdu t;
    t.msg = spec::MSG_PROBE_TX_COMMAND;
    t.talker = kTkB;
    t.listener = kOwn;
    rx(t);
    Pdu resp = command(spec::MSG_PROBE_TX_RESPONSE, 0);
    resp.listener = kTkB;
    rx(resp);
    for (std::uint8_t msg : {3, 5, 7, 9, 11, 13, 14, 15}) {
        rx(command(msg, 0));
    }
    EXPECT_TRUE(fk.sent.empty() && fk.calls.empty() && a.rx_ignored == 11u && a.sinks[0].state == ACMP_UNBOUND)
        << "A21 commands for another listener or talker, every response but PROBE_TX_RESPONSE and the reserved "
           "types are ignored (5.5.3.1, 8.2.1.9, 8.2.1.10)";
}

// REQ: ACMP-02
TEST_F(AcmpCore, A21MalformedFramesAreCounted) {
    auto f = acmpdu(command(spec::MSG_BIND_RX_COMMAND, 0));
    acmp_rx(&a, 0, f.data(), spec::FRAME_BYTES - 1u);
    auto g = f;
    g[12] = 0x81;
    acmp_rx(&a, 0, g.data(), g.size());
    g = f;
    g[14] = spec::ADPDU_SUBTYPE;
    acmp_rx(&a, 0, g.data(), g.size());
    acmp_rx(&a, cfg.n_interfaces, f.data(), f.size());
    EXPECT_TRUE(a.rx_malformed == 4u && fk.calls.empty() && a.sinks[0].state == ACMP_UNBOUND)
        << "A21 a frame shorter than the Milan ACMPDU, another EtherType or subtype, or an unknown interface is "
           "counted and not read (5.5.2.2)";
    std::array<std::uint8_t, spec::FRAME_BYTES + 26u> longer{};
    std::memcpy(longer.data(), f.data(), f.size());
    acmp_rx(&a, 0, longer.data(), longer.size());
    EXPECT_EQ(a.sinks[0].state, ACMP_PRB_W_RESP) << "A21 the longer IEEE 1722.1-2021 PDU is accepted (5.5.2.2)";
}

// REQ: ACMP-09
TEST_F(AcmpCore, A19AResponseWithoutRoomIsOwedAndItsChangeWaits) {
    fk.room = false;
    bind(0);
    EXPECT_TRUE(fk.sent.empty() && a.owed_count == 2u && a.deferred_sends == 2u)
        << "A19 no room: the response and the probe are owed, in order";
    EXPECT_TRUE(a.sinks[0].state == ACMP_PRB_W_RESP && fk.count(Call::PERSIST) == 1u)
        << "A19 the bind itself takes effect and is saved";
    EXPECT_TRUE(fk.count(Call::CHANGED) == 0u && acmp_change_pending(&a, 0))
        << "A19 but its change is not reported while its response waits (#653)";
    EXPECT_TRUE(acmp_poll(&a) && fk.sent.empty()) << "A19 a poll with no room sends nothing and says a frame is owed";
    fk.room = true;
    fk.clear();
    EXPECT_TRUE(acmp_poll(&a)) << "A19 one frame per poll: the probe is still owed after the response";
    ASSERT_EQ(fk.sent.size(), 1u);
    EXPECT_EQ(last().msg, spec::MSG_BIND_RX_RESPONSE) << "A19 the oldest first: the response";
    EXPECT_TRUE(fk.count(Call::CHANGED) == 1u && fk.position(Call::CHANGED) > fk.position(Call::SEND) &&
                !acmp_change_pending(&a, 0))
        << "A19 the change is reported once its response has left";
    EXPECT_FALSE(acmp_poll(&a)) << "A19 then the probe, and nothing is owed";
    EXPECT_EQ(last().msg, spec::MSG_PROBE_TX_COMMAND) << "A19 the probe left second";
    EXPECT_FALSE(acmp_poll(&a)) << "A19 a poll with nothing owed sends nothing";
}

// REQ: ACMP-09
TEST_F(AcmpCore, A19NothingPassesAnOwedFrame) {
    fk.room = false;
    rx(command(spec::MSG_GET_RX_STATE_COMMAND, 0, 0, 0, kCtl2, 0, 1));
    fk.room = true;
    rx(command(spec::MSG_GET_RX_STATE_COMMAND, 0, 0, 0, kCtl2, 0, 2));
    EXPECT_TRUE(fk.sent.empty() && a.owed_count == 2u) << "A19 a response does not pass one already owed";
    static_cast<void>(acmp_poll(&a));
    static_cast<void>(acmp_poll(&a));
    ASSERT_EQ(fk.sent.size(), 2u);
    EXPECT_TRUE(read(fk.sent[0].bytes.data()).seq == 1u && read(fk.sent[1].bytes.data()).seq == 2u)
        << "A19 they leave in the order they were made";
}

// REQ: ACMP-09, ACMP-12
TEST_F(AcmpCore, A19AFullQueueDeclinesTheCommandBeforeItActs) {
    fk.room = false;
    for (unsigned k = 0; k < ACMP_OWED_MAX; ++k) {
        rx(command(spec::MSG_GET_RX_STATE_COMMAND, 0, 0, 0, kCtl2, 0, static_cast<std::uint16_t>(k)));
    }
    ASSERT_EQ(a.owed_count, ACMP_OWED_MAX);
    fk.clear();
    auto b = acmpdu(command(spec::MSG_BIND_RX_COMMAND, 1));
    EXPECT_FALSE(acmp_rx(&a, 0, b.data(), b.size())) << "A19 a full queue declines a BIND_RX to its caller";
    Pdu t;
    t.msg = spec::MSG_GET_TX_STATE_COMMAND;
    t.talker = kOwn;
    auto g = acmpdu(t);
    EXPECT_FALSE(acmp_rx(&a, 0, g.data(), g.size())) << "A19 a full queue declines a GET_TX_STATE to its caller";
    EXPECT_TRUE(a.busy_declined == 2u && a.sinks[1].state == ACMP_UNBOUND && fk.calls.empty())
        << "A19 a command whose response would find the queue full is declined before it changes anything";
}

// REQ: ACMP-09
TEST_F(AcmpCore, A19AProbeWithoutRoomIsLostAndRecovered) {
    to_state(0, ACMP_PRB_W_DELAY);
    fk.room = false;
    for (unsigned k = 0; k < ACMP_OWED_MAX; ++k) {
        rx(command(spec::MSG_GET_RX_STATE_COMMAND, 1, 0, 0, kCtl2));
    }
    fire(0);
    EXPECT_TRUE(a.probes_lost == 1u && a.sinks[0].state == ACMP_PRB_W_RESP && a.sinks[0].timer == ACMP_TIMER_NO_RESP)
        << "A19 a probe the full queue cannot take is lost and counted; TMR_NO_RESP will send its duplicate";
    fk.room = true;
    for (unsigned k = 0; k < ACMP_OWED_MAX; ++k) {
        static_cast<void>(acmp_poll(&a));
    }
    fk.clear();
    fire(0);
    EXPECT_TRUE(fk.sent.size() == 1u && last().msg == spec::MSG_PROBE_TX_COMMAND && last().seq == a.sinks[0].probe_seq)
        << "A19 and it does";
}

// REQ: ACMP-09
TEST_F(AcmpCore, A19TwoOwedResponsesForOneSinkReleaseTogether) {
    fk.room = false;
    bind(0);
    rx(command(spec::MSG_UNBIND_RX_COMMAND, 0));
    fk.room = true;
    fk.clear();
    static_cast<void>(acmp_poll(&a));
    static_cast<void>(acmp_poll(&a));
    EXPECT_TRUE(fk.count(Call::CHANGED) == 0u && acmp_change_pending(&a, 0))
        << "A19 the bind's response left but the unbind's is still owed: the sink's change still waits";
    static_cast<void>(acmp_poll(&a));
    EXPECT_TRUE(fk.count(Call::CHANGED) == 0u && !acmp_change_pending(&a, 0))
        << "A19 once the unbind's response leaves nothing is reported: the sink is as it was (unbound)";
}

// Milan v1.2 5.6.4; Milan v1.2 Table 5.54

// REQ: ACMP-06
TEST_F(AcmpCore, A22AvailableDiscoversWhenTheGrandmasterMatches) {
    rx(command(spec::MSG_BIND_RX_COMMAND, 0));
    Adp d;
    d.gm = kGm0 + 1u;
    adp(d);
    EXPECT_TRUE(!a.sinks[0].discovered && !a.sinks[0].adp_armed)
        << "A22 TK_NOT_DISCOVERED: an AVAILABLE from another grandmaster is ignored (5.6.4.5.1 step 1)";
    d.gm = kGm0;
    d.domain = 1;
    adp(d);
    EXPECT_FALSE(a.sinks[0].discovered) << "A22 and from another domain";
    for (std::uint8_t vt : {1, 10, 31}) {
        SetUp();
        fk.now = 70000;
        bind(0);
        Adp v;
        v.valid_time = vt;
        v.index = 33;
        v.interface_index = 4;
        adp(v);
        const acmp_sink& s = a.sinks[0];
        EXPECT_TRUE(s.discovered && s.disc_interface_index == 4u && s.disc_available_index == 33u)
            << "A22 a matching AVAILABLE: TK_DISCOVERED, interface_index and available_index saved (5.6.4.5.1)";
        EXPECT_TRUE(s.adp_armed && s.adp_deadline == 70000u + vt * spec::VALID_TIME_UNIT_MS)
            << "A22 TMR_NO_ADP is the received valid_time in two-second units, valid_time " << unsigned(vt);
        EXPECT_TRUE(fk.armed[0] && fk.at[0] == 70000u + spec::TMR_NO_RESP_MS)
            << "A22 and the interface's timer keeps the earlier deadline";
    }
}

// REQ: ACMP-06
TEST_F(AcmpCore, A22DiscoveredStartsTheProbeFromPrbWAvail) {
    std::uint8_t record[spec::BINDING_BYTES] = {0x03, 0, 0, 1};
    wire_put_be(record + 4, kTkA, 8);
    wire_put_be(record + 12, kCtl1, 8);
    ASSERT_EQ(acmp_restore_binding(&a, 0, record, sizeof record), ACMP_RESTORE_APPLIED);
    fk.clear();
    adp(Adp{});
    const acmp_sink& s = a.sinks[0];
    EXPECT_TRUE(s.state == ACMP_PRB_W_DELAY && s.probing == ACMP_PROBING_ACTIVE && s.timer == ACMP_TIMER_DELAY &&
                s.timer_deadline - fk.now <= spec::TMR_DELAY_MAX_MS)
        << "A22 EVT_TK_DISCOVERED in PRB_W_AVAIL: TMR_DELAY 0 to 1 s, PRB_W_DELAY, ACTIVE (5.5.3.5.9)";
    EXPECT_EQ(fk.count(Call::GPTP), 1u) << "A22 the grandmaster is sampled once for the frame";
}

// REQ: ACMP-06, MFCONN-03, MFRECOVERY-01
TEST_F(AcmpCore, A22DiscoveredStateCells) {

    auto discovered = [this]() {
        SetUp();
        bind(0);
        Adp d;
        d.index = 700;
        d.interface_index = 2;
        adp(d);
        fk.clear();
    };
    discovered();
    Adp d;
    d.index = 701;
    d.interface_index = 3;
    adp(d);
    EXPECT_TRUE(a.sinks[0].disc_available_index == 700u && a.sinks[0].state == ACMP_PRB_W_RESP && fk.calls.empty())
        << "A22 TK_DISCOVERED: an AVAILABLE with another interface_index is ignored (5.6.4.5.2 step 1)";
    discovered();
    d.interface_index = 2;
    d.valid_time = 5;
    fk.now += 1000;
    adp(d);
    EXPECT_TRUE(a.sinks[0].disc_available_index == 701u && a.sinks[0].adp_deadline == fk.now + 5u * 2000u &&
                a.sinks[0].state == ACMP_PRB_W_RESP)
        << "A22 a rising available_index is noted and TMR_NO_ADP restarted, no event (step 3)";
    for (std::uint32_t index : {700u, 699u, 0u}) {
        discovered();
        d.index = index;
        d.valid_time = 10;
        adp(d);
        EXPECT_TRUE(a.sinks[0].state == ACMP_PRB_W_DELAY && a.sinks[0].discovered &&
                    a.sinks[0].disc_available_index == index && a.sinks[0].adp_deadline == fk.now + 20000u)
            << "A22 available_index " << index << " <= last: EVT_TK_DEPARTED then EVT_TK_DISCOVERED, the index noted "
            << "(5.6.4.5.2 steps 2a, 2c, 3)";
    }
    discovered();
    d.index = 600;
    d.gm = kGm0 + 1u;
    adp(d);
    EXPECT_TRUE(a.sinks[0].state == ACMP_PRB_W_AVAIL && !a.sinks[0].discovered && !a.sinks[0].adp_armed &&
                a.sinks[0].disc_available_index == 700u)
        << "A22 index <= last from another grandmaster: EVT_TK_DEPARTED, TMR_NO_ADP stopped, TK_NOT_DISCOVERED (2b)";
    discovered();
    d.gm = kGm0;
    d.domain = 7;
    adp(d);
    EXPECT_TRUE(a.sinks[0].state == ACMP_PRB_W_AVAIL && !a.sinks[0].discovered) << "A22 and from another domain";
    discovered();
    d.index = 800;
    d.domain = 7;
    adp(d);
    EXPECT_TRUE(a.sinks[0].discovered && a.sinks[0].disc_available_index == 800u)
        << "A22 a rising index reads no grandmaster: step 2 alone does";
}

// REQ: ACMP-06, MFCONN-03, MFRECOVERY-01
TEST_F(AcmpCore, A22DepartingAndAging) {
    bind(0);
    Adp gone;
    gone.msg = spec::ADPDU_ENTITY_DEPARTING;
    adp(gone);
    EXPECT_TRUE(a.sinks[0].state == ACMP_PRB_W_RESP && !a.sinks[0].discovered)
        << "A22 a DEPARTING in TK_NOT_DISCOVERED is ignored (Table 5.54 -)";
    adp(Adp{});
    gone.interface_index = 1;
    adp(gone);
    EXPECT_TRUE(a.sinks[0].discovered && a.sinks[0].adp_armed)
        << "A22 a DEPARTING with another interface_index is ignored (5.6.4.5.3 step 1)";
    gone.interface_index = 0;
    adp(gone);
    EXPECT_TRUE(!a.sinks[0].discovered && !a.sinks[0].adp_armed && a.sinks[0].state == ACMP_PRB_W_AVAIL)
        << "A22 a DEPARTING: TMR_NO_ADP stopped, TK_NOT_DISCOVERED, EVT_TK_DEPARTED (5.6.4.5.3)";
    SetUp();
    bind(0);
    Adp v;
    v.valid_time = 1;
    adp(v);
    fire_adp(0);
    EXPECT_TRUE(!a.sinks[0].discovered && !a.sinks[0].adp_armed && a.sinks[0].state == ACMP_PRB_W_AVAIL)
        << "A22 TMR_NO_ADP: TK_NOT_DISCOVERED and EVT_TK_DEPARTED (5.6.4.5.4)";
}

// REQ: ACMP-06, MFCONN-03, MFRECOVERY-01
TEST_F(AcmpCore, DepartingRetainsBindingAndReprobes) {
    peer_loss_recovery(false);
}

// REQ: ACMP-06, MFCONN-03, MFRECOVERY-01
TEST_F(AcmpCore, AdpTimeoutRetainsBindingAndReprobes) {
    peer_loss_recovery(true);
}

// REQ: ACMP-06
TEST_F(AcmpCore, A22OnlyBoundSinksOfThatTalkerOnThatInterface) {
    bind(0, kTkA);
    bind(1, kTkA, 2);
    bind(2, kTkA);
    fk.clear();
    adp(Adp{});
    EXPECT_TRUE(a.sinks[0].discovered && a.sinks[1].discovered && !a.sinks[2].discovered)
        << "A22 every bound sink of the talker processes it (5.6.4.1), only on the interface it arrived on";
    EXPECT_EQ(fk.count(Call::GPTP), 1u) << "A22 and the grandmaster is sampled once for the frame";
    Adp other;
    other.entity = kTkB;
    std::uint32_t ignored = a.adp_ignored;
    adp(other);
    EXPECT_EQ(a.adp_ignored, ignored + 1u) << "A22 an AVAILABLE no bound sink takes is counted";
    SetUp();
    Adp zero;
    zero.entity = 0;
    adp(zero);
    EXPECT_TRUE(!a.sinks[0].discovered && !a.sinks[0].adp_armed && a.adp_ignored == 1u)
        << "A22 an unbound sink runs no discovery";
}

// REQ: ACMP-06
TEST_F(AcmpCore, A22OtherAdpFramesAreIgnored) {
    bind(0);
    auto f = adpdu(Adp{});
    std::uint32_t n = a.adp_ignored;
    acmp_adp_rx(&a, 0, f.data(), spec::ADPDU_FRAME_BYTES - 1u);
    auto g = f;
    g[15] = 2;
    acmp_adp_rx(&a, 0, g.data(), g.size());
    g = f;
    g[14] = spec::SUBTYPE;
    acmp_adp_rx(&a, 0, g.data(), g.size());
    g = f;
    g[13] = 0xF1;
    acmp_adp_rx(&a, 0, g.data(), g.size());
    acmp_adp_rx(&a, cfg.n_interfaces, f.data(), f.size());
    EXPECT_TRUE(a.adp_ignored == n + 5u && !a.sinks[0].discovered)
        << "A22 a short ADPDU, a DISCOVER, another subtype or EtherType, or an unknown interface is not discovery's";
}

// REQ: PORT-01
TEST_F(AcmpCore, A23EveryEntryRefusesACallFromInsideAPort) {
    std::uint8_t record[spec::BINDING_BYTES] = {0x01};
    auto bindf = acmpdu(command(spec::MSG_BIND_RX_COMMAND, 1));
    auto adpf = adpdu(Adp{});
    const std::function<void()> calls[] = {
        [&] { acmp_rx(&a, 0, bindf.data(), bindf.size()); },
        [&] { acmp_adp_rx(&a, 0, adpf.data(), adpf.size()); },
        [&] { acmp_timer_expired(&a, 0); },
        [&] { acmp_tk_registered(&a, 0, false); },
        [&] { acmp_tk_kind_changed(&a, 0, false); },
        [&] { acmp_tk_unregistered(&a, 0); },
        [&] { EXPECT_FALSE(acmp_set_started(&a, 0, false)); },
        [&] { static_cast<void>(acmp_poll(&a)); },
        [&] { EXPECT_EQ(acmp_restore_binding(&a, 1, record, sizeof record), ACMP_RESTORE_REFUSED); },
        [&] { acmp_restore_rollback(&a); },
        [&] { acmp_open(&a); },
    };
    unsigned n = 0;
    for (const auto& call : calls) {
        SetUp();
        fk.room = false;
        fk.hook_kind = Call::SEND;
        fk.hook = call;
        bind(0);
        const acmp_sink& s = a.sinks[0];
        EXPECT_TRUE(a.reentries == 1u && reentry_traps == 1u)
            << "A23 a call made from inside the send port is refused, counted and trapped, entry " << n;
        EXPECT_TRUE(s.state == ACMP_PRB_W_RESP && s.timer == ACMP_TIMER_NO_RESP && s.timer_held && !fk.armed[0] &&
                    a.sinks[1].state == ACMP_UNBOUND && a.owed_count == 2u)
            << "A23 and the outer call completes as if it had not been made: TMR_NO_RESP held for the owed probe, entry "
            << n;
        n++;
    }
}

// REQ: PORT-01
TEST_F(AcmpCore, A23EveryPortIsGuarded) {
    const Call::Kind kinds[] = {Call::TIMER, Call::NOW, Call::GPTP, Call::SEED, Call::LOCKED,
                                Call::SOURCE, Call::SRP, Call::PERSIST, Call::CHANGED, Call::ADMIT};
    for (Call::Kind kind : kinds) {
        SetUp();
        fk.locked = true;
        fk.holder = kCtl1;
        fk.hook_kind = kind;
        fk.hook = [this] { acmp_timer_expired(&a, 0); };
        bind(0);
        Pdu t;
        t.msg = spec::MSG_GET_TX_STATE_COMMAND;
        t.talker = kOwn;
        rx(t);
        adp(Adp{});
        rx(probe_answer(0, 5u));
        fire(0);
        fire(0);
        rx(probe_answer(0));
        rx(command(spec::MSG_UNBIND_RX_COMMAND, 0));
        EXPECT_TRUE(a.reentries == 1u && reentry_traps == 1u) << "A23 the port kind " << kind << " is guarded";
    }
}

// REQ: ACMP-07, MFCONN-03
TEST_F(AcmpCore, A24ARestoredBindingFastConnects) {
    std::uint8_t record[spec::BINDING_BYTES] = {0x07, 0xAA, 0x12, 0x34};
    wire_put_be(record + 4, kTkB, 8);
    wire_put_be(record + 12, kCtl2, 8);
    EXPECT_EQ(acmp_restore_binding(&a, 1, record, sizeof record), ACMP_RESTORE_APPLIED) << "A24 a saved binding applies";
    const acmp_sink& s = a.sinks[1];
    EXPECT_TRUE(s.bound && s.started && s.binding.streaming_wait && s.binding.talker_unique_id == 0x1234u &&
                s.binding.talker_entity_id == kTkB && s.binding.controller_entity_id == kCtl2)
        << "A24 the record's flags and parameters, big-endian (the processor's BINDING payload)";
    EXPECT_TRUE(s.state == ACMP_PRB_W_AVAIL && s.probing == ACMP_PROBING_PASSIVE && s.acmp_status == 0u &&
                s.disc_running && !s.discovered && s.timer == ACMP_TIMER_NONE)
        << "A24 startup with a saved binding: discovery started, PROBING_PASSIVE, PRB_W_AVAIL (5.5.3.5.2)";
    EXPECT_TRUE(fk.calls.empty()) << "A24 a boot restore calls no port: nothing to save or report";
    std::uint8_t back[spec::BINDING_BYTES];
    ASSERT_TRUE(acmp_binding_latch(&a, 1, back));
    record[1] = 0;
    EXPECT_EQ(std::memcmp(back, record, sizeof back), 0) << "A24 the latch gives the same record back";
}

// REQ: ACMP-07
TEST_F(AcmpCore, A24UnboundRecordsRefusalsAndRollback) {
    std::uint8_t record[spec::BINDING_BYTES] = {0x06, 0, 0, 1};
    EXPECT_EQ(acmp_restore_binding(&a, 0, record, sizeof record), ACMP_RESTORE_APPLIED)
        << "A24 a record without the valid flag applies";
    EXPECT_TRUE(a.sinks[0].state == ACMP_UNBOUND && !a.sinks[0].bound) << "A24 and leaves the sink unbound (5.5.3.5.1)";
    record[0] = 0x01;
    EXPECT_EQ(acmp_restore_binding(&a, cfg.n_sinks, record, sizeof record), ACMP_RESTORE_REFUSED)
        << "A24 a record of a sink the configuration lacks is refused";
    EXPECT_EQ(acmp_restore_binding(&a, 0, record, sizeof record - 1u), ACMP_RESTORE_REFUSED)
        << "A24 a payload of another length is refused";
    for (unsigned len : {0u, spec::BINDING_BYTES + 1u, 0x100u + spec::BINDING_BYTES, 0xFFFFFFFFu}) {
        EXPECT_EQ(acmp_restore_binding(&a, 0, record, len), ACMP_RESTORE_REFUSED)
            << "A24 a payload of " << len << " bytes is refused, the longer ones too, before a byte is read";
    }
    ASSERT_EQ(acmp_restore_binding(&a, 0, record, sizeof record), ACMP_RESTORE_APPLIED);
    ASSERT_EQ(acmp_restore_binding(&a, 2, record, sizeof record), ACMP_RESTORE_APPLIED);
    acmp_restore_rollback(&a);
    EXPECT_TRUE(!a.sinks[0].bound && !a.sinks[2].bound && a.sinks[0].state == ACMP_UNBOUND && !a.sinks[2].disc_running &&
                a.sinks[2].interface == 1u && fk.calls.empty())
        << "A24 the roll-back drops every restored binding, keeps each sink's interface, calls no port";
    std::uint8_t back[spec::BINDING_BYTES];
    std::memset(back, 0xEE, sizeof back);
    ASSERT_TRUE(acmp_binding_latch(&a, 0, back));
    EXPECT_TRUE(std::all_of(back, back + sizeof back, [](std::uint8_t b) { return b == 0u; }))
        << "A24 an unbound sink's record is all zeros: how an unbind is saved";
    EXPECT_FALSE(acmp_binding_latch(&a, cfg.n_sinks, back)) << "A24 there is no record of a sink the entity lacks";
}

// REQ: ACMP-07
TEST_F(AcmpCore, A24StartedIsSavedAndReported) {
    EXPECT_FALSE(acmp_set_started(&a, 0, true)) << "A24 an unbound sink has no started state (5.3.8.7)";
    EXPECT_FALSE(acmp_set_started(&a, cfg.n_sinks, true)) << "A24 nor a sink the entity lacks";
    bind(0, kTkA, 1, kCtl1, true);
    fk.clear();
    EXPECT_TRUE(acmp_set_started(&a, 0, true)) << "A24 START_STREAMING of a bound sink";
    EXPECT_TRUE(a.sinks[0].started && fk.count(Call::PERSIST) == 1u && fk.count(Call::CHANGED) == 1u)
        << "A24 the started state is saved (5.3.8.7) and is a Table 5.22 item";
    fk.clear();
    EXPECT_TRUE(acmp_set_started(&a, 0, true));
    EXPECT_TRUE(fk.calls.empty()) << "A24 setting it again changes nothing";
}

constexpr std::uint8_t kRecValid = 0x01u;
constexpr std::uint8_t kRecStarted = 0x02u;
constexpr std::uint8_t kRecStreamingWait = 0x04u;

std::array<std::uint8_t, spec::BINDING_BYTES> payload(std::uint8_t flags, std::uint16_t uid, std::uint64_t talker,
                                                      std::uint64_t ctlr) {
    return {flags, 0x00, static_cast<std::uint8_t>(uid >> 8), static_cast<std::uint8_t>(uid),
            static_cast<std::uint8_t>(talker >> 56), static_cast<std::uint8_t>(talker >> 48),
            static_cast<std::uint8_t>(talker >> 40), static_cast<std::uint8_t>(talker >> 32),
            static_cast<std::uint8_t>(talker >> 24), static_cast<std::uint8_t>(talker >> 16),
            static_cast<std::uint8_t>(talker >> 8), static_cast<std::uint8_t>(talker),
            static_cast<std::uint8_t>(ctlr >> 56), static_cast<std::uint8_t>(ctlr >> 48),
            static_cast<std::uint8_t>(ctlr >> 40), static_cast<std::uint8_t>(ctlr >> 32),
            static_cast<std::uint8_t>(ctlr >> 24), static_cast<std::uint8_t>(ctlr >> 16),
            static_cast<std::uint8_t>(ctlr >> 8), static_cast<std::uint8_t>(ctlr)};
}

// REQ: ACMP-07
TEST_F(AcmpCore, A24TheRecordIsTheProcessorsPayloadOneFlagAtATime) {
    std::array<std::uint8_t, spec::BINDING_BYTES> back{};
    bind(0, kTkA, 0x1234u, kCtl1);
    ASSERT_TRUE(acmp_binding_latch(&a, 0, back.data()));
    EXPECT_EQ(back, payload(kRecValid | kRecStarted, 0x1234u, kTkA, kCtl1))
        << "A24 bound and started: flags 0x03, then the parameters, byte for byte";
    ASSERT_TRUE(acmp_set_started(&a, 0, false));
    ASSERT_TRUE(acmp_binding_latch(&a, 0, back.data()));
    EXPECT_EQ(back, payload(kRecValid, 0x1234u, kTkA, kCtl1)) << "A24 bound and stopped: the valid flag alone, 0x01";
    bind(1, kTkB, 0x0102u, kCtl2, true);
    ASSERT_TRUE(acmp_binding_latch(&a, 1, back.data()));
    EXPECT_EQ(back, payload(kRecValid | kRecStreamingWait, 0x0102u, kTkB, kCtl2))
        << "A24 bound with STREAMING_WAIT: flags 0x05";
    struct Case {
        std::uint8_t flags;
        bool started;
        bool sw;
    };
    for (const Case& c : {Case{kRecValid, false, false}, Case{kRecValid | kRecStarted, true, false},
                          Case{kRecValid | kRecStreamingWait, false, true}}) {
        SetUp();
        const auto rec = payload(c.flags, 0x0A0Bu, kTkB, kCtl2);
        ASSERT_EQ(acmp_restore_binding(&a, 0, rec.data(), static_cast<unsigned>(rec.size())), ACMP_RESTORE_APPLIED);
        const acmp_sink& s = a.sinks[0];
        EXPECT_TRUE(s.bound && s.started == c.started && s.binding.streaming_wait == c.sw &&
                    s.binding.talker_unique_id == 0x0A0Bu && s.binding.talker_entity_id == kTkB &&
                    s.binding.controller_entity_id == kCtl2)
            << "A24 the processor's flags 0x" << std::hex << unsigned(c.flags) << " restore that one flag";
    }
}

// Milan v1.2 Table 5.22

// REQ: ACMP-02
TEST_F(AcmpCore, A25OnlyTable522ItemsAreReported) {
    to_state(0, ACMP_SETTLED_NO_RSV);
    fk.clear();
    adp(Adp{});
    EXPECT_EQ(fk.count(Call::CHANGED), 0u) << "A25 discovery noted while settled moves no Table 5.22 item";
    SetUp();
    bind(0);
    fk.clear();
    fire(0);
    EXPECT_EQ(fk.count(Call::CHANGED), 0u) << "A25 the duplicate probe moves none: still PROBING_ACTIVE, status 0";
    fire(0);
    EXPECT_EQ(fk.count(Call::CHANGED), 1u) << "A25 the ACMP status LISTENER_TALKER_TIMEOUT does";
    fk.clear();
    rx(command(spec::MSG_BIND_RX_COMMAND, 0, kTkA, 1, kCtl1));
    EXPECT_TRUE(fk.count(Call::CHANGED) == 0u && fk.count(Call::PERSIST) == 0u)
        << "A25 a re-bind that changes nothing reports and saves nothing";
}

// IEEE 1722-2016 4.4.3.4

template <std::size_t N>
std::array<std::uint8_t, N> versioned(std::array<std::uint8_t, N> f, unsigned v) {
    f[15] = static_cast<std::uint8_t>((f[15] & 0x8Fu) | (v << 4));
    return f;
}

// REQ: ACMP-02
TEST_F(AcmpCore, A26AnotherAvtpVersionIsDiscardedBeforeItIsRead) {
    for (unsigned v = 1; v < 8u; ++v) {
        SetUp();
        auto bindf = versioned(acmpdu(command(spec::MSG_BIND_RX_COMMAND, 0)), v);
        acmp_rx(&a, 0, bindf.data(), bindf.size());
        EXPECT_TRUE(fk.calls.empty() && a.sinks[0].state == ACMP_UNBOUND && a.rx_malformed == 1u)
            << "A26 a BIND_RX of AVTP version " << v << " binds nothing, calls no port, counts as malformed";
        Pdu t;
        t.msg = spec::MSG_GET_TX_STATE_COMMAND;
        t.talker = kOwn;
        auto txf = versioned(acmpdu(t), v);
        acmp_rx(&a, 0, txf.data(), txf.size());
        EXPECT_TRUE(fk.calls.empty() && a.rx_malformed == 2u)
            << "A26 a talker command of version " << v << " is not answered";
        bind(0);
        ASSERT_EQ(a.sinks[0].state, ACMP_PRB_W_RESP) << "A26 the same BIND_RX at version 0 binds";
        fk.clear();
        auto resp = versioned(acmpdu(probe_answer(0)), v);
        acmp_rx(&a, 0, resp.data(), resp.size());
        EXPECT_TRUE(a.sinks[0].state == ACMP_PRB_W_RESP && fk.calls.empty() && a.rx_malformed == 3u)
            << "A26 the probe's own PROBE_TX_RESPONSE at version " << v << " is not taken";
        auto avail = versioned(adpdu(Adp{}), v);
        acmp_adp_rx(&a, 0, avail.data(), avail.size());
        EXPECT_TRUE(!a.sinks[0].discovered && fk.calls.empty() && a.adp_ignored == 1u)
            << "A26 an ENTITY_AVAILABLE of version " << v << " discovers nothing";
        adp(Adp{});
        ASSERT_TRUE(a.sinks[0].discovered) << "A26 the same AVAILABLE at version 0 discovers the talker";
        fk.clear();
        Adp gone;
        gone.msg = spec::ADPDU_ENTITY_DEPARTING;
        auto dep = versioned(adpdu(gone), v);
        acmp_adp_rx(&a, 0, dep.data(), dep.size());
        EXPECT_TRUE(a.sinks[0].discovered && fk.calls.empty() && a.adp_ignored == 2u)
            << "A26 an ENTITY_DEPARTING of version " << v << " departs nothing";
        rx(probe_answer(0));
        EXPECT_EQ(a.sinks[0].state, ACMP_SETTLED_NO_RSV) << "A26 the PROBE_TX_RESPONSE at version 0 settles";

        const auto rec = payload(kRecValid, 1u, kTkB, kCtl1);
        ASSERT_EQ(acmp_restore_binding(&a, 1, rec.data(), static_cast<unsigned>(rec.size())), ACMP_RESTORE_APPLIED);
        Adp tb;
        tb.entity = kTkB;
        auto availb = versioned(adpdu(tb), v);
        acmp_adp_rx(&a, 0, availb.data(), availb.size());
        EXPECT_TRUE(a.sinks[1].state == ACMP_PRB_W_AVAIL && !a.sinks[1].discovered)
            << "A26 a restored binding stays in PRB_W_AVAIL on an AVAILABLE of version " << v;
    }
}

// Milan v1.2 5.5.3.5.3; Milan v1.2 5.5.3.5.16

// REQ: ACMP-05
TEST_F(AcmpCore, A27AnOwedProbeStartsItsTimerWhenItLeaves) {
    const std::uint32_t t0 = fk.now;
    fk.room = false;
    bind(0);
    const acmp_sink& s = a.sinks[0];
    EXPECT_TRUE(s.state == ACMP_PRB_W_RESP && s.timer == ACMP_TIMER_NO_RESP && s.timer_held && !fk.armed[0] &&
                a.owed_count == 2u)
        << "A27 a probe with no transmit room: PRB_W_RESP, its TMR_NO_RESP held, no timer armed";
    fk.now = t0 + 5u;
    fk.room = true;
    fk.clear();
    EXPECT_TRUE(acmp_poll(&a));
    EXPECT_TRUE(fk.sent.size() == 1u && read(fk.sent[0].bytes.data()).msg == spec::MSG_BIND_RX_RESPONSE &&
                s.timer_held && !fk.armed[0])
        << "A27 the response leaves first, in command order, and the probe's timer still waits";
    EXPECT_FALSE(acmp_poll(&a));
    EXPECT_TRUE(fk.sent.size() == 2u && read(fk.sent[1].bytes.data()).msg == spec::MSG_PROBE_TX_COMMAND &&
                !s.timer_held && s.timer_deadline == t0 + 5u + spec::TMR_NO_RESP_MS && fk.armed[0] &&
                fk.at[0] == s.timer_deadline)
        << "A27 the probe leaves 5 ms late and TMR_NO_RESP runs 200 ms from that send";
    fk.now = s.timer_deadline - 1u;
    acmp_timer_expired(&a, 0);
    EXPECT_EQ(s.state, ACMP_PRB_W_RESP) << "A27 no expiry 199 ms after the send";
    fk.clear();
    fk.now = t0 + 5u + spec::TMR_NO_RESP_MS;
    acmp_timer_expired(&a, 0);
    EXPECT_TRUE(s.state == ACMP_PRB_W_RESP2 && fk.sent.size() == 1u) << "A27 the duplicate 200 ms after the send";
    SetUp();
    fk.room = false;
    bind(0);
    fk.now += spec::TMR_NO_RESP_MS + 50u;
    acmp_timer_expired(&a, 0);
    EXPECT_TRUE(a.sinks[0].state == ACMP_PRB_W_RESP && a.sinks[0].timer_held && a.owed_count == 2u)
        << "A27 an expiry of the interface while the probe is owed takes nothing: a held timer is never due";
}

// REQ: ACMP-05
TEST_F(AcmpCore, A27AStalledDuplicateGetsItsWholeInterval) {
    std::uint32_t t0 = fk.now;
    bind(0);
    const acmp_sink& s = a.sinks[0];
    const std::uint16_t seq = s.probe_seq;
    const auto first = fk.sent.back();
    fk.room = false;
    fk.now = t0 + spec::TMR_NO_RESP_MS;
    fk.clear();
    acmp_timer_expired(&a, 0);
    EXPECT_TRUE(s.state == ACMP_PRB_W_RESP2 && s.timer_held && fk.count(Call::TIMER) == 0u && !a.timer_armed[0] &&
                a.owed_count == 1u)
        << "A27 the first TMR_NO_RESP finds no room: the duplicate owed, PRB_W_RESP2, its timer held, none re-armed";
    fk.now = t0 + 205u;
    fk.room = true;
    fk.clear();
    EXPECT_FALSE(acmp_poll(&a));
    EXPECT_TRUE(fk.sent.size() == 1u && fk.sent[0].bytes == first.bytes && s.probe_seq == seq &&
                s.timer_deadline == t0 + 405u && fk.at[0] == t0 + 405u)
        << "A27 the duplicate, the first probe's exact copy and sequence_id, leaves at 205 ms: TMR_NO_RESP to 405 ms";
    fk.now = t0 + 402u;
    rx(probe_answer(0));
    EXPECT_EQ(s.state, ACMP_SETTLED_NO_RSV) << "A27 a response 197 ms after the duplicate left is taken (5.5.3.5.25)";
    SetUp();
    t0 = fk.now;
    bind(0);
    fk.room = false;
    fk.now = t0 + spec::TMR_NO_RESP_MS;
    acmp_timer_expired(&a, 0);
    fk.room = true;
    fk.now = t0 + 205u;
    static_cast<void>(acmp_poll(&a));
    fk.clear();
    fk.now = t0 + 404u;
    acmp_timer_expired(&a, 0);
    EXPECT_EQ(a.sinks[0].state, ACMP_PRB_W_RESP2) << "A27 no second expiry 199 ms after the duplicate left";
    fk.now = t0 + 405u;
    acmp_timer_expired(&a, 0);
    EXPECT_TRUE(a.sinks[0].state == ACMP_PRB_W_RETRY && fk.sent.empty() &&
                a.sinks[0].acmp_status == spec::STATUS_LISTENER_TALKER_TIMEOUT)
        << "A27 the second expiry at 200 ms: no third probe, LISTENER_TALKER_TIMEOUT (5.5.3.5.23)";
}

// REQ: ACMP-05
TEST_F(AcmpCore, A27AProbeOwedPastAnUnbindARebindOrASuccessStartsNothing) {
    fk.room = false;
    bind(0);
    rx(command(spec::MSG_UNBIND_RX_COMMAND, 0));
    const acmp_sink& s = a.sinks[0];
    EXPECT_TRUE(s.state == ACMP_UNBOUND && s.timer == ACMP_TIMER_NONE && !s.timer_held && a.owed_count == 3u)
        << "A27 an UNBIND_RX while the probe is owed stops its timer";
    fk.room = true;
    while (acmp_poll(&a)) {}
    EXPECT_TRUE(fk.sent.size() == 3u && read(fk.sent[1].bytes.data()).msg == spec::MSG_PROBE_TX_COMMAND &&
                s.timer == ACMP_TIMER_NONE && !fk.armed[0])
        << "A27 the probe still leaves, in order, and starts no timer";
    SetUp();
    fk.room = false;
    bind(0, kTkA);
    const std::uint16_t old_seq = a.sinks[0].probe_seq;
    bind(0, kTkB);
    EXPECT_TRUE(a.sinks[0].probe_seq != old_seq && a.sinks[0].timer_held && a.owed_count == 4u)
        << "A27 a BIND_RX of another source while the probe is owed: a new probe, a new sequence_id, held";
    fk.room = true;
    fk.now += 3u;
    static_cast<void>(acmp_poll(&a));
    static_cast<void>(acmp_poll(&a));
    EXPECT_TRUE(a.sinks[0].timer_held && !fk.armed[0]) << "A27 the old probe leaving starts no timer for the new one";
    static_cast<void>(acmp_poll(&a));
    fk.now += 2u;
    static_cast<void>(acmp_poll(&a));
    EXPECT_TRUE(!a.sinks[0].timer_held && a.sinks[0].timer_deadline == fk.now + spec::TMR_NO_RESP_MS && fk.armed[0])
        << "A27 the new probe's own send starts it";
    SetUp();
    bind(0);
    fk.room = false;
    fire(0);
    rx(probe_answer(0));
    const std::uint32_t no_tk = a.sinks[0].timer_deadline;
    EXPECT_TRUE(a.sinks[0].state == ACMP_SETTLED_NO_RSV && a.sinks[0].timer == ACMP_TIMER_NO_TK &&
                !a.sinks[0].timer_held)
        << "A27 a success while the duplicate is owed settles, TMR_NO_TK running";
    fk.room = true;
    fk.now += 7u;
    EXPECT_FALSE(acmp_poll(&a));
    EXPECT_TRUE(a.sinks[0].timer == ACMP_TIMER_NO_TK && a.sinks[0].timer_deadline == no_tk &&
                a.sinks[0].state == ACMP_SETTLED_NO_RSV)
        << "A27 and the duplicate leaving afterwards restarts nothing";
}

void expire_at(acmp* a, std::uint32_t at, unsigned interface = 0) {
    fk.now = at;
    acmp_timer_expired(a, interface);
}

constexpr std::uint32_t kWrap = 0xFFFFFFFFu;

// REQ: ACMP-05
TEST_F(AcmpCore, A28EveryTimerExpiresAtItsDeadlineAcrossTheWrap) {
    fk.now = kWrap - 99u;
    bind(0);
    const acmp_sink& s = a.sinks[0];
    EXPECT_EQ(s.timer_deadline, 100u) << "A28 TMR_NO_RESP armed 100 ms before the wrap ends 100 ms after it";
    expire_at(&a, kWrap);
    expire_at(&a, 99u);
    EXPECT_EQ(s.state, ACMP_PRB_W_RESP) << "A28 TMR_NO_RESP: nothing at the wrap or 1 ms before its deadline";
    expire_at(&a, 100u);
    EXPECT_EQ(s.state, ACMP_PRB_W_RESP2) << "A28 TMR_NO_RESP expires at its deadline across the wrap";
    SetUp();
    fk.now = kWrap - 1399u;
    bind(0);
    fire(0);
    fire(0);
    EXPECT_TRUE(a.sinks[0].state == ACMP_PRB_W_RETRY && a.sinks[0].timer_deadline == 3000u)
        << "A28 TMR_RETRY armed 999 ms before the wrap ends 3 s after it";
    expire_at(&a, kWrap);
    expire_at(&a, 2999u);
    EXPECT_EQ(a.sinks[0].state, ACMP_PRB_W_RETRY) << "A28 TMR_RETRY: nothing before its deadline";
    expire_at(&a, 3000u);
    EXPECT_EQ(a.sinks[0].state, ACMP_PRB_W_AVAIL) << "A28 TMR_RETRY expires at its deadline across the wrap";
    SetUp();
    fk.now = kWrap - 4999u;
    bind(0);
    rx(probe_answer(0));
    EXPECT_TRUE(a.sinks[0].state == ACMP_SETTLED_NO_RSV && a.sinks[0].timer_deadline == 5000u)
        << "A28 TMR_NO_TK armed 4999 ms before the wrap ends 5 s after it";
    expire_at(&a, kWrap);
    expire_at(&a, 4999u);
    EXPECT_EQ(a.sinks[0].state, ACMP_SETTLED_NO_RSV) << "A28 TMR_NO_TK: nothing before its deadline";
    adp(Adp{});
    expire_at(&a, 5000u);
    EXPECT_EQ(a.sinks[0].state, ACMP_PRB_W_DELAY) << "A28 TMR_NO_TK expires at its deadline across the wrap";
    const std::uint32_t delay = a.sinks[0].timer_deadline;
    EXPECT_TRUE(a.last_draw_ms > 0u && delay - 5000u == a.last_draw_ms) << "A28 TMR_DELAY is the draw after the expiry";
    SetUp();
    const std::uint8_t restored[spec::BINDING_BYTES] = {kRecValid, 0, 0, 1, 0x00, 0x22, 0x11, 0x00,
                                                         0xAA, 0xBB, 0xCC, 0xDD};
    ASSERT_EQ(acmp_restore_binding(&a, 0, restored, sizeof restored), ACMP_RESTORE_APPLIED);
    fk.now = kWrap;
    adp(Adp{});
    const std::uint32_t d = kWrap + a.last_draw_ms;
    EXPECT_TRUE(a.sinks[0].state == ACMP_PRB_W_DELAY && a.sinks[0].timer_deadline == d && a.last_draw_ms > 1u)
        << "A28 TMR_DELAY drawn at the last millisecond before the wrap ends after it";
    expire_at(&a, d - 1u);
    EXPECT_EQ(a.sinks[0].state, ACMP_PRB_W_DELAY) << "A28 TMR_DELAY: nothing before its deadline";
    expire_at(&a, d);
    EXPECT_EQ(a.sinks[0].state, ACMP_PRB_W_RESP) << "A28 TMR_DELAY expires at its deadline across the wrap";
    SetUp();
    bind(0);
    rx(probe_answer(0));
    fk.now = kWrap - 9999u;
    adp(Adp{});
    EXPECT_TRUE(a.sinks[0].adp_armed && a.sinks[0].adp_deadline == 10000u)
        << "A28 TMR_NO_ADP armed 9999 ms before the wrap ends 10 s after it";
    acmp_tk_registered(&a, 0, false);
    expire_at(&a, kWrap);
    expire_at(&a, 9999u);
    EXPECT_TRUE(a.sinks[0].discovered) << "A28 TMR_NO_ADP: nothing before its deadline";
    expire_at(&a, 10000u);
    EXPECT_FALSE(a.sinks[0].discovered) << "A28 TMR_NO_ADP expires at its deadline across the wrap (5.6.4.5.4)";
}

// REQ: ACMP-05
TEST_F(AcmpCore, A28TheEarliestDeadlineIsChosenAcrossTheWrap) {
    fk.now = kWrap - 255u;
    bind(0);
    fk.now = kWrap - 99u;
    bind(1);
    EXPECT_TRUE(a.sinks[0].timer_deadline == kWrap - 55u && a.sinks[1].timer_deadline == 100u)
        << "A28 one deadline before the wrap, one after it";
    EXPECT_TRUE(fk.armed[0] && fk.at[0] == kWrap - 55u)
        << "A28 the interface timer holds the earlier deadline, the numerically larger one before the wrap";
    expire_at(&a, kWrap - 55u);
    EXPECT_TRUE(a.sinks[0].state == ACMP_PRB_W_RESP2 && a.sinks[1].state == ACMP_PRB_W_RESP)
        << "A28 the first expiry takes sink 0 only: sink 1's deadline is after the wrap";
    EXPECT_TRUE(fk.armed[0] && fk.at[0] == 100u) << "A28 then the timer holds sink 1's deadline after the wrap";
}

std::vector<Call> admits() {
    std::vector<Call> v;
    for (const Call& c : fk.calls) {
        if (c.kind == Call::ADMIT) {
            v.push_back(c);
        }
    }
    return v;
}

// REQ: ACMP-06
TEST_F(AcmpCore, A29TheAdmitPortFollowsEachSinksBoundTalker) {
    bind(0, kTkA);
    auto v = admits();
    ASSERT_EQ(v.size(), 1u) << "A29 a BIND_RX admits its talker once";
    EXPECT_TRUE(v[0].index == 0u && v[0].value == 0u && v[0].flag && v[0].talker == kTkA)
        << "A29 for its sink, on the sink's interface, the bound talker";
    fk.clear();
    bind(0, kTkA, 1, kCtl2);
    bind(0, kTkA, 2);
    EXPECT_TRUE(admits().empty()) << "A29 a re-bind to the same talker, from any controller or source, admits nothing";
    bind(0, kTkB);
    v = admits();
    ASSERT_EQ(v.size(), 1u) << "A29 re-binding emits one admission";
    EXPECT_TRUE(v[0].flag && v[0].talker == kTkB && v[0].index == 0u) << "A29 a re-bind to another talker admits it";
    fk.clear();
    rx(command(spec::MSG_UNBIND_RX_COMMAND, 0));
    v = admits();
    ASSERT_EQ(v.size(), 1u) << "A29 an UNBIND_RX withdraws it";
    EXPECT_TRUE(!v[0].flag && v[0].index == 0u && v[0].value == 0u) << "A29 an UNBIND_RX withdraws it";
    fk.clear();
    rx(command(spec::MSG_UNBIND_RX_COMMAND, 0));
    EXPECT_TRUE(admits().empty()) << "A29 an UNBIND_RX of an unbound sink withdraws nothing";
    bind(2, kTkB);
    v = admits();
    ASSERT_EQ(v.size(), 1u) << "A29 sink 2 emits one admission";
    EXPECT_TRUE(v[0].index == 2u && v[0].value == 1u && v[0].flag) << "A29 sink 2's talker on interface 1";
    fk.clear();
    fk.locked = true;
    fk.holder = kCtl2;
    bind(1, kTkA);
    EXPECT_TRUE(admits().empty() && a.sinks[1].state == ACMP_UNBOUND) << "A29 a BIND_RX the lock refuses admits nothing";
}

// REQ: ACMP-07, MFCONN-03
TEST_F(AcmpCore, A29RestoredBindingsAreAdmittedWhenTheTransportOpens) {
    const auto bound = payload(kRecValid, 1u, kTkB, kCtl1);
    const auto none = payload(0u, 0u, 0u, 0u);
    ASSERT_EQ(acmp_restore_binding(&a, 1, bound.data(), spec::BINDING_BYTES), ACMP_RESTORE_APPLIED);
    ASSERT_EQ(acmp_restore_binding(&a, 2, none.data(), spec::BINDING_BYTES), ACMP_RESTORE_APPLIED);
    EXPECT_TRUE(fk.calls.empty()) << "A29 the boot restore admits nothing: the transport is not open";
    acmp_open(&a);
    auto v = admits();
    ASSERT_EQ(v.size(), 1u) << "A29 acmp_open admits each restored binding's talker, the unbound sinks nothing";
    EXPECT_TRUE(v[0].index == 1u && v[0].value == 0u && v[0].flag && v[0].talker == kTkB && fk.calls.size() == 1u)
        << "A29 sink 1's talker on its interface, and nothing else: no timer, nothing to save or report";
    fk.clear();
    acmp_open(&a);
    EXPECT_TRUE(fk.calls.empty()) << "A29 a second open changes nothing";
    SetUp();
    ASSERT_EQ(acmp_restore_binding(&a, 1, bound.data(), spec::BINDING_BYTES), ACMP_RESTORE_APPLIED);
    acmp_restore_rollback(&a);
    acmp_open(&a);
    EXPECT_TRUE(fk.calls.empty()) << "A29 a binding the roll-back dropped is never admitted";
    SetUp();
    bind(0, kTkA);
    fk.clear();
    ASSERT_EQ(acmp_restore_binding(&a, 0, none.data(), spec::BINDING_BYTES), ACMP_RESTORE_APPLIED);
    acmp_open(&a);
    v = admits();
    ASSERT_EQ(v.size(), 1u) << "A29 opening after reset emits one withdrawal";
    EXPECT_TRUE(!v[0].flag && v[0].index == 0u)
        << "A29 a sink the store resets is withdrawn at the next open: what the port holds outlives the reset";
}

// Milan v1.2 5.5.3.5.3
// Milan v1.2 5.5.3.5.16

// REQ: ACMP-05
TEST_F(AcmpCore, A30AProbeTakenAtOnceRunsFromTheClockAfterItsSend) {
    fk.send_ms = 5u;
    bind(0);
    const acmp_sink& s = a.sinks[0];
    ASSERT_TRUE(fk.sent.size() == 2u && read(fk.sent[1].bytes.data()).msg == spec::MSG_PROBE_TX_COMMAND)
        << "A30 BIND_RX sends the response and the probe at once";
    std::uint32_t taken = fk.sent[1].at;
    EXPECT_TRUE(s.timer_deadline == taken + spec::TMR_NO_RESP_MS && !s.timer_held && fk.armed[0] &&
                fk.at[0] == s.timer_deadline)
        << "A30 the probe taken at once: TMR_NO_RESP 200 ms from the clock after its send";
    fk.now = taken + spec::TMR_NO_RESP_MS - 1u;
    acmp_timer_expired(&a, 0);
    EXPECT_EQ(s.state, ACMP_PRB_W_RESP) << "A30 no expiry 199 ms after the probe was taken";
    rx(probe_answer(0));
    EXPECT_EQ(s.state, ACMP_SETTLED_NO_RSV) << "A30 a success 199 ms after the probe was taken settles";
    SetUp();
    fk.send_ms = 5u;
    bind(0);
    taken = fk.sent[1].at;
    fk.now = taken + spec::TMR_NO_RESP_MS;
    acmp_timer_expired(&a, 0);
    EXPECT_EQ(a.sinks[0].state, ACMP_PRB_W_RESP2) << "A30 the duplicate at the full 200 ms after the probe was taken";
    SetUp();
    fk.room = false;
    bind(0);
    fk.room = true;
    fk.send_ms = 5u;
    static_cast<void>(acmp_poll(&a));
    static_cast<void>(acmp_poll(&a));
    ASSERT_TRUE(fk.sent.size() == 2u && read(fk.sent[1].bytes.data()).msg == spec::MSG_PROBE_TX_COMMAND)
        << "A30 an owed probe leaves after its response";
    EXPECT_EQ(a.sinks[0].timer_deadline, fk.sent[1].at + spec::TMR_NO_RESP_MS)
        << "A30 an owed probe: TMR_NO_RESP 200 ms from the clock after the poll's send";
}

// REQ: ACMP-05
TEST_F(AcmpCore, A30ADuplicateTakenAtOnceRunsFromTheClockAfterItsSend) {
    bind(0);
    const acmp_sink& s = a.sinks[0];
    const auto first = fk.sent.back();
    const std::uint16_t seq = s.probe_seq;
    fk.send_ms = 5u;
    fk.clear();
    fire(0);
    ASSERT_TRUE(fk.sent.size() == 1u && fk.sent[0].bytes == first.bytes && s.probe_seq == seq &&
                s.state == ACMP_PRB_W_RESP2)
        << "A30 the first TMR_NO_RESP sends one duplicate, the first probe's exact copy and sequence_id";
    std::uint32_t taken = fk.sent[0].at;
    EXPECT_TRUE(s.timer_deadline == taken + spec::TMR_NO_RESP_MS && fk.at[0] == s.timer_deadline)
        << "A30 the duplicate taken at once: TMR_NO_RESP 200 ms from the clock after its send, not the expiry's";
    fk.now = taken + spec::TMR_NO_RESP_MS - 1u;
    acmp_timer_expired(&a, 0);
    EXPECT_EQ(s.state, ACMP_PRB_W_RESP2) << "A30 no second expiry 199 ms after the duplicate was taken";
    rx(probe_answer(0));
    EXPECT_EQ(s.state, ACMP_SETTLED_NO_RSV) << "A30 a success 199 ms after the duplicate was taken settles (5.5.3.5.25)";
    SetUp();
    bind(0);
    fk.send_ms = 5u;
    fire(0);
    taken = fk.sent.back().at;
    fk.clear();
    fk.now = taken + spec::TMR_NO_RESP_MS;
    acmp_timer_expired(&a, 0);
    EXPECT_TRUE(a.sinks[0].state == ACMP_PRB_W_RETRY && fk.sent.empty() &&
                a.sinks[0].acmp_status == spec::STATUS_LISTENER_TALKER_TIMEOUT)
        << "A30 the second expiry at the full 200 ms after the duplicate was taken: no third probe, the timeout";
}

// REQ: ACMP-05
TEST_F(AcmpCore, A30ATimerDueAfterAnEarlierSinksSendIsTakenInTheSameExpiry) {
    bind(1);
    adp(Adp{});
    rx(probe_answer(1, 5u));
    const std::uint32_t retry_at = a.sinks[1].timer_deadline;
    fk.now = retry_at - spec::TMR_NO_RESP_MS;
    bind(0);
    ASSERT_TRUE(a.sinks[0].timer_deadline == retry_at && a.sinks[1].state == ACMP_PRB_W_RETRY &&
                a.sinks[1].discovered)
        << "A30 two sinks of interface 0 due at one expiry";
    a.rng = state_drawing(0);
    a.seeded = true;
    fk.send_ms = 5u;
    fk.clear();
    fk.now = retry_at;
    acmp_timer_expired(&a, 0);
    EXPECT_TRUE(fk.sent.size() == 2u && a.sinks[0].state == ACMP_PRB_W_RESP2 && a.sinks[1].state == ACMP_PRB_W_RESP &&
                a.sinks[1].timer_deadline == fk.sent[1].at + spec::TMR_NO_RESP_MS)
        << "A30 sink 1's 0 ms TMR_DELAY, drawn after sink 0's duplicate moved the clock, probes in the same expiry";
}

// REQ: ACMP-06
TEST_F(AcmpCore, DepartingStopsEveryProbingTimer) {
    for (const auto state : {ACMP_PRB_W_DELAY, ACMP_PRB_W_RESP, ACMP_PRB_W_RESP2, ACMP_PRB_W_RETRY}) {
        SetUp();
        to_state(0, state);
        adp(Adp{});
        fk.clear();
        Adp departing;
        departing.msg = spec::ADPDU_ENTITY_DEPARTING;
        adp(departing);
        EXPECT_EQ(a.sinks[0].state, ACMP_PRB_W_AVAIL);
        EXPECT_EQ(a.sinks[0].timer, ACMP_TIMER_NONE);
        EXPECT_FALSE(a.sinks[0].discovered);
        EXPECT_EQ(a.sinks[0].probing, ACMP_PROBING_PASSIVE);
        EXPECT_EQ(fk.count(Call::CHANGED), 1u) << "departing publishes the passive probing status";
    }
}

// REQ: PORT-01
TEST_F(AcmpCore, CommandPortBudgets) {
    bind(0);
    EXPECT_EQ(fk.count(Call::NOW), 1u) << "BIND reads the clock after the accepted probe";
    fk.clear();
    rx(command(spec::MSG_GET_RX_STATE_COMMAND, 0));
    EXPECT_EQ(fk.count(Call::NOW), 0u) << "GET_RX_STATE needs no clock";
    fk.clear();
    rx(probe_answer(0));
    EXPECT_EQ(fk.count(Call::NOW), 1u) << "successful probe response starts one reservation timer";
    fk.clear();
    rx(command(spec::MSG_UNBIND_RX_COMMAND, 0));
    EXPECT_EQ(fk.count(Call::NOW), 0u) << "UNBIND needs no clock";
    fk.clear();
    Pdu p; p.msg = spec::MSG_GET_TX_STATE_COMMAND; p.talker = kOwn;
    rx(p);
    EXPECT_EQ(fk.count(Call::NOW), 0u) << "talker response needs no clock";
}

// REQ: PORT-01
TEST_F(AcmpCore, TimerPortBudgets) {
    for (const auto state : {ACMP_PRB_W_DELAY, ACMP_PRB_W_RESP, ACMP_PRB_W_RESP2,
                             ACMP_PRB_W_RETRY, ACMP_SETTLED_NO_RSV}) {
        SetUp();
        to_state(0, state);
        if (state == ACMP_PRB_W_RETRY) { adp(Adp{}); }
        fk.clear();
        fire(0);
        const char* label = state == ACMP_PRB_W_DELAY ? "PRB_W_DELAY" :
                            state == ACMP_PRB_W_RESP ? "PRB_W_RESP" :
                            state == ACMP_PRB_W_RESP2 ? "PRB_W_RESP2" :
                            state == ACMP_PRB_W_RETRY ? "PRB_W_RETRY" : "SETTLED_NO_RSV";
        const unsigned clocks = (state == ACMP_PRB_W_DELAY || state == ACMP_PRB_W_RESP) ? 2u : 1u;
        EXPECT_EQ(fk.count(Call::NOW), clocks) << "timer clock budget for state " << label;
        EXPECT_EQ(fk.count(Call::GPTP), 0u) << "timer expiry never samples the grandmaster in " << label;
    }
}

// REQ: PORT-01
TEST_F(AcmpCore, DiscoveryPortBudgets) {
    bind(0);
    fk.clear();
    adp(Adp{});
    EXPECT_EQ(fk.count(Call::NOW), 1u) << "AVAILABLE starts one discovery deadline";
    EXPECT_EQ(fk.count(Call::GPTP), 1u);
    fk.clear();
    Adp gone; gone.msg = spec::ADPDU_ENTITY_DEPARTING;
    adp(gone);
    EXPECT_EQ(fk.count(Call::GPTP), 0u) << "DEPARTING needs no grandmaster";
    adp(Adp{});
    fk.clear();
    fire_adp(0);
    EXPECT_EQ(fk.count(Call::GPTP), 0u) << "aging needs no grandmaster";
}

int send_at(unsigned n) { return fk.position(Call::SEND, n); }

bool published_before_send(unsigned m, unsigned n) {
    return m < fk.pubs.size() && send_at(n) >= 0 && fk.pubs[m].before <= static_cast<std::size_t>(send_at(n));
}

// REQ: ACMP-10
TEST_F(AcmpCore, A31TheBindingIsPublishedBeforeTheResponseThatPromisesIt) {
    bind(0);
    ASSERT_EQ(fk.pubs.size(), 1u) << "A31 a BIND_RX publishes the sink's binding once";
    EXPECT_TRUE(fk.pubs[0].interface == 0u && fk.pubs[0].sink == 0u && fk.pubs[0].bound && fk.pubs[0].stream == 0u)
        << "A31 bound, on the sink's interface, with no stream yet";
    EXPECT_TRUE(fk.pubs[0].started) << "A31 started: the command had no STREAMING_WAIT (5.3.8.7)";
    ASSERT_TRUE(fk.sent.size() == 2u && read(fk.sent[0].bytes.data()).msg == spec::MSG_BIND_RX_RESPONSE);
    EXPECT_TRUE(published_before_send(0, 0)) << "A31 the binding is published before the BIND_RX response";
    fk.clear();
    rx(probe_answer(0));
    ASSERT_EQ(fk.pubs.size(), 1u) << "A31 a PROBE_TX_RESPONSE that settles publishes the stream";
    EXPECT_TRUE(fk.pubs[0].bound && fk.pubs[0].stream == kSid && fk.pubs[0].sink == 0u && fk.pubs[0].moved)
        << "A31 the stream_id the response carried (5.5.3.5.18 step 4)";
    const int changed = fk.position(Call::CHANGED);
    EXPECT_TRUE(changed >= 0 && fk.pubs[0].before <= static_cast<std::size_t>(changed))
        << "A31 and before the notifier hears of the settled sink";
    fk.clear();
    rx(command(spec::MSG_GET_RX_STATE_COMMAND, 0));
    EXPECT_TRUE(fk.pubs.empty() && last().stream_id == kSid)
        << "A31 a GET_RX_STATE reports the stream already published, and publishes nothing";
    rx(command(spec::MSG_UNBIND_RX_COMMAND, 0));
    ASSERT_EQ(fk.pubs.size(), 1u) << "A31 an UNBIND_RX publishes the sink unbound";
    EXPECT_TRUE(!fk.pubs[0].bound && !fk.pubs[0].started && fk.pubs[0].stream == 0u)
        << "A31 unbound, not started, with no stream";
    ASSERT_EQ(read(fk.sent.back().bytes.data()).msg, spec::MSG_UNBIND_RX_RESPONSE);
    EXPECT_TRUE(published_before_send(0, static_cast<unsigned>(fk.sent.size() - 1u)))
        << "A31 the sink is published unbound before the UNBIND_RX response";
    fk.clear();
    rx(command(spec::MSG_UNBIND_RX_COMMAND, 0));
    EXPECT_TRUE(fk.pubs.empty()) << "A31 an UNBIND_RX of an unbound sink publishes nothing";
}

// REQ: ACMP-10
TEST_F(AcmpCore, A31LeavingSettlementTakesTheStreamOffTheDatapath) {
    to_state(0, ACMP_SETTLED_NO_RSV);
    fk.clear();
    bind(0, kTkB);
    ASSERT_EQ(fk.pubs.size(), 1u) << "A31 a re-bind of a settled sink to another talker publishes once";
    EXPECT_TRUE(fk.pubs[0].bound && fk.pubs[0].stream == 0u) << "A31 still bound, its old stream gone";
    EXPECT_TRUE(published_before_send(0, 0)) << "A31 before the BIND_RX response";
    to_state(1, ACMP_SETTLED_NO_RSV);
    adp(Adp{});
    fk.clear();
    fire(1);
    ASSERT_EQ(fk.pubs.size(), 1u) << "A31 TMR_NO_TK publishes the sink without its stream (5.5.3.5.36 step 1)";
    EXPECT_TRUE(fk.pubs[0].sink == 1u && fk.pubs[0].bound && fk.pubs[0].stream == 0u);
    to_state(2, ACMP_SETTLED_RSV_OK);
    fk.clear();
    acmp_tk_unregistered(&a, 2);
    ASSERT_EQ(fk.pubs.size(), 1u) << "A31 EVT_TK_UNREGISTERED publishes the sink without its stream (5.5.3.5.48)";
    EXPECT_TRUE(fk.pubs[0].sink == 2u && fk.pubs[0].interface == 1u && fk.pubs[0].bound && fk.pubs[0].stream == 0u)
        << "A31 sink 2, on interface 1";
}

// REQ: ACMP-10
TEST_F(AcmpCore, A31OnlyAMovedTripleIsPublished) {
    to_state(0, ACMP_SETTLED_NO_RSV);
    fk.clear();
    bind(0, kTkA, 1, kCtl2);
    acmp_tk_registered(&a, 0, false);
    EXPECT_TRUE(acmp_set_started(&a, 0, true));
    adp(Adp{});
    EXPECT_TRUE(fk.pubs.empty() && a.sinks[0].state == ACMP_SETTLED_RSV_OK)
        << "A31 a re-bind to the same talker, a registration, a start of a started sink and a discovery move "
           "neither bound, started nor stream";
    acmp_tk_kind_changed(&a, 0, true);
    EXPECT_TRUE(fk.pubs.empty()) << "A31 nor does a change of the registered kind";
}

// REQ: ACMP-10
TEST_F(AcmpCore, A31TheStartedLevelIsPublishedBeforeItIsPromised) {
    bind(0, kTkA, 1, kCtl1, true);
    ASSERT_EQ(fk.pubs.size(), 1u) << "A31 a BIND_RX with STREAMING_WAIT publishes once";
    EXPECT_TRUE(fk.pubs[0].bound && !fk.pubs[0].started)
        << "A31 a bind with STREAMING_WAIT is published bound and stopped";
    EXPECT_TRUE(published_before_send(0, 0)) << "A31 before the BIND_RX response that echoes STREAMING_WAIT";
    fk.clear();
    bind(0, kTkA, 1, kCtl2, false);
    ASSERT_EQ(fk.pubs.size(), 1u) << "A31 a re-bind to the same talker without STREAMING_WAIT publishes once";
    EXPECT_TRUE(fk.pubs[0].bound && fk.pubs[0].started && !fk.pubs[0].moved && fk.pubs[0].stream == 0u)
        << "A31 started now, the stream not moved";
    ASSERT_TRUE(!fk.sent.empty() && read(fk.sent[0].bytes.data()).msg == spec::MSG_BIND_RX_RESPONSE);
    EXPECT_TRUE(published_before_send(0, 0)) << "A31 the started move is published before the BIND_RX response";
    rx(probe_answer(0));
    ASSERT_EQ(a.sinks[0].state, ACMP_SETTLED_NO_RSV);
    fk.clear();
    ASSERT_TRUE(acmp_set_started(&a, 0, false));
    ASSERT_EQ(fk.pubs.size(), 1u) << "A31 a STOP_STREAMING publishes once";
    EXPECT_TRUE(fk.pubs[0].bound && !fk.pubs[0].started && fk.pubs[0].stream == kSid && !fk.pubs[0].moved)
        << "A31 stopped, the settled stream kept and not moved";
    int changed = fk.position(Call::CHANGED);
    EXPECT_TRUE(changed >= 0 && fk.pubs[0].before <= static_cast<std::size_t>(changed))
        << "A31 the stop is published before the notifier hears of it";
    fk.clear();
    EXPECT_TRUE(acmp_set_started(&a, 0, false));
    EXPECT_TRUE(fk.pubs.empty()) << "A31 a STOP_STREAMING of a stopped sink publishes nothing";
    ASSERT_TRUE(acmp_set_started(&a, 0, true));
    ASSERT_EQ(fk.pubs.size(), 1u) << "A31 a START_STREAMING publishes once";
    EXPECT_TRUE(fk.pubs[0].started && fk.pubs[0].stream == kSid && !fk.pubs[0].moved);
    changed = fk.position(Call::CHANGED);
    EXPECT_TRUE(changed >= 0 && fk.pubs[0].before <= static_cast<std::size_t>(changed))
        << "A31 the start is published before the notifier hears of it";
}

// REQ: ACMP-10, ACMP-07
TEST_F(AcmpCore, A31RestoredBindingsArePublishedWhenTheTransportOpens) {
    const auto bound = payload(kRecValid, 1u, kTkB, kCtl1);
    const auto none = payload(0u, 0u, 0u, 0u);
    ASSERT_EQ(acmp_restore_binding(&a, 2, bound.data(), spec::BINDING_BYTES), ACMP_RESTORE_APPLIED);
    EXPECT_TRUE(fk.pubs.empty()) << "A31 the boot restore publishes nothing: the transport is not open";
    acmp_open(&a);
    ASSERT_EQ(fk.pubs.size(), 1u) << "A31 acmp_open publishes each restored binding";
    EXPECT_TRUE(fk.pubs[0].sink == 2u && fk.pubs[0].interface == 1u && fk.pubs[0].bound && fk.pubs[0].stream == 0u)
        << "A31 sink 2, bound on interface 1, with no stream until it settles";
    EXPECT_FALSE(fk.pubs[0].started) << "A31 stopped, as its record saved it";
    fk.clear();
    acmp_open(&a);
    EXPECT_TRUE(fk.pubs.empty()) << "A31 a second open publishes nothing";
    SetUp();
    const auto started = payload(kRecValid | kRecStarted, 1u, kTkB, kCtl1);
    ASSERT_EQ(acmp_restore_binding(&a, 1, started.data(), spec::BINDING_BYTES), ACMP_RESTORE_APPLIED);
    acmp_open(&a);
    ASSERT_EQ(fk.pubs.size(), 1u);
    EXPECT_TRUE(fk.pubs[0].sink == 1u && fk.pubs[0].bound && fk.pubs[0].started)
        << "A31 a binding saved started is published started";
    SetUp();
    ASSERT_EQ(acmp_restore_binding(&a, 1, bound.data(), spec::BINDING_BYTES), ACMP_RESTORE_APPLIED);
    acmp_restore_rollback(&a);
    acmp_open(&a);
    EXPECT_TRUE(fk.pubs.empty()) << "A31 a binding the roll-back dropped is never published";
    SetUp();
    bind(0, kTkA);
    fk.clear();
    ASSERT_EQ(acmp_restore_binding(&a, 0, none.data(), spec::BINDING_BYTES), ACMP_RESTORE_APPLIED);
    EXPECT_TRUE(fk.pubs.empty()) << "A31 the store's reset of a sink is not published at once";
    acmp_open(&a);
    ASSERT_EQ(fk.pubs.size(), 1u) << "A31 a sink the store resets is published unbound at the next open";
    EXPECT_TRUE(!fk.pubs[0].bound && fk.pubs[0].sink == 0u)
        << "A31 what the port holds outlives the sink's reset, so the open publishes the change";
}

// REQ: ACMP-10, PORT-01
TEST_F(AcmpCore, A31ACallBackFromThePublishPortIsRefused) {
    fk.pub_hook = [this] {
        rx(command(spec::MSG_UNBIND_RX_COMMAND, 0));
        static_cast<void>(acmp_poll(&a));
    };
    bind(0);
    EXPECT_TRUE(a.reentries == 2u && reentry_traps == 2u && a.sinks[0].bound && a.sinks[0].state == ACMP_PRB_W_RESP)
        << "A31 an UNBIND_RX and a poll from inside the publish port are counted and change nothing (#678)";
}


// REQ: ACMP-10
TEST_F(AcmpCore, A31SettlementIsPublishedBeforeTheTimerPort) {
    bind(0);
    fk.clear();
    rx(probe_answer(0));
    ASSERT_EQ(fk.pubs.size(), 1u) << "A31 settlement publishes once before completion callbacks";
    const int timer = fk.position(Call::TIMER);
    ASSERT_GE(timer, 0) << "A31 settlement re-arms the interface timer";
    EXPECT_LE(fk.pubs[0].before, static_cast<std::size_t>(timer))
        << "A31 settlement publication precedes the timer port in finish";
}

// REQ: ACMP-10
TEST_F(AcmpCore, A31StoreResetOfASettledSinkPublishesAMovedStream) {
    to_state(0, ACMP_SETTLED_NO_RSV);
    ASSERT_NE(a.sinks[0].published_stream, 0u) << "A31 the settled stream was published before reset";
    const auto none = payload(0u, 0u, 0u, 0u);
    fk.clear();
    ASSERT_EQ(acmp_restore_binding(&a, 0, none.data(), spec::BINDING_BYTES), ACMP_RESTORE_APPLIED);
    EXPECT_TRUE(fk.pubs.empty()) << "A31 resetting a settled sink defers publication until open";
    acmp_open(&a);
    ASSERT_EQ(fk.pubs.size(), 1u) << "A31 the reset settled sink publishes once at the next open";
    EXPECT_TRUE(!fk.pubs[0].bound && fk.pubs[0].stream == 0u && fk.pubs[0].moved)
        << "A31 withdrawal after a store reset reports the settled stream moved";
}

// REQ: ACMP-10
TEST_F(AcmpCore, A31StoreResetOfABoundStoppedSinkPublishesItsWithdrawal) {
    bind(0, kTkA, 1, kCtl1, true);
    ASSERT_EQ(fk.pubs.size(), 1u) << "A31 the stopped binding publishes once before reset";
    ASSERT_TRUE(fk.pubs[0].bound && !fk.pubs[0].started && fk.pubs[0].stream == 0u)
        << "A31 only the bound cache is nonzero before reset";
    const auto none = payload(0u, 0u, 0u, 0u);
    fk.clear();
    ASSERT_EQ(acmp_restore_binding(&a, 0, none.data(), spec::BINDING_BYTES), ACMP_RESTORE_APPLIED);
    EXPECT_TRUE(fk.pubs.empty()) << "A31 resetting a stopped binding defers publication until open";
    acmp_open(&a);
    ASSERT_EQ(fk.pubs.size(), 1u)
        << "A31 the bound cache survives reset to publish the stopped binding withdrawal";
    EXPECT_TRUE(!fk.pubs[0].bound && !fk.pubs[0].started && fk.pubs[0].stream == 0u && !fk.pubs[0].moved)
        << "A31 the stopped binding is withdrawn without moving a stream";
}

// REQ: ACMP-10
TEST_F(AcmpCore, A31StoreRestoreOfAStoppedRecordPublishesTheStop) {
    bind(0);
    ASSERT_EQ(fk.pubs.size(), 1u) << "A31 the started binding publishes once before restore";
    ASSERT_TRUE(fk.pubs[0].bound && fk.pubs[0].started && fk.pubs[0].stream == 0u)
        << "A31 the binding is started without a settled stream before restore";
    const auto stopped = payload(kRecValid, 1u, kTkA, kCtl1);
    fk.clear();
    ASSERT_EQ(acmp_restore_binding(&a, 0, stopped.data(), spec::BINDING_BYTES), ACMP_RESTORE_APPLIED);
    EXPECT_TRUE(fk.pubs.empty()) << "A31 restoring a stopped record defers publication until open";
    acmp_open(&a);
    ASSERT_EQ(fk.pubs.size(), 1u)
        << "A31 the started cache survives reset to publish the restored stop";
    EXPECT_TRUE(fk.pubs[0].bound && !fk.pubs[0].started && fk.pubs[0].stream == 0u && !fk.pubs[0].moved)
        << "A31 the restored binding is published stopped without moving a stream";
}

class AcmpFresh : public AcmpCore {
 protected:
    void SetUp() override {
        AcmpCore::SetUp();
        cfg.da_fresh_ms = 15000u;
        ASSERT_TRUE(acmp_init(&a, &cfg, &kPorts, &kEnv));
    }
    void answer(unsigned source = 0, unsigned interface = 0,
                std::uint8_t message = spec::MSG_PROBE_TX_COMMAND) {
        Pdu p;
        p.msg = message;
        p.talker = kOwn;
        p.talker_uid = static_cast<std::uint16_t>(source);
        rx(p, interface);
    }
};

// REQ: ACMP-11
TEST_F(AcmpFresh, NoProbe) {
    fk.now = 0u;
    EXPECT_FALSE(acmp_declaring(&a, 0)) << "freshness requires an answered probe even at clock zero";
}

// REQ: ACMP-11
TEST_F(AcmpFresh, StaleProbe) {
    for (auto start : {50000u, UINT32_MAX - 999u}) {
        fk.now = start;
        answer();
        fk.now += 15001u;
        EXPECT_FALSE(acmp_declaring(&a, 0)) << "a probe older than the freshness window cannot declare";
        fk.now = start;
        EXPECT_FALSE(acmp_declaring(&a, 0)) << "an observed stale probe cannot resurrect on a later wrap";
    }
}

// REQ: ACMP-11
TEST_F(AcmpFresh, StaleProbeAfterListenerWrap) {
    const std::uint32_t start = 50000u;
    fk.now = start;
    answer();
    ASSERT_TRUE(acmp_listener_registered(&a, 0, 0, true));
    for (const std::uint64_t elapsed : {UINT64_C(15000), UINT64_C(1000000000),
            UINT64_C(2000000000), UINT64_C(3000000000), UINT64_C(4000000000),
            UINT64_C(0x100000064)}) {
        fk.now = start + static_cast<std::uint32_t>(elapsed);
        (void)acmp_declaring(&a, 0);
    }
    ASSERT_TRUE(acmp_listener_registered(&a, 0, 0, false));
    EXPECT_FALSE(acmp_declaring(&a, 0))
        << "Listener withdrawal after a serviced full wrap cannot revive an expired probe";
}

// REQ: ACMP-11
TEST_F(AcmpFresh, StaleProbeAfterInvalidAddressWrap) {
    const std::uint32_t start = 50000u;
    fk.now = start;
    answer();
    fk.source[0].dest_mac_valid = false;
    for (const std::uint64_t elapsed : {UINT64_C(15000), UINT64_C(1000000000),
            UINT64_C(2000000000), UINT64_C(3000000000), UINT64_C(4000000000),
            UINT64_C(0x100000064)}) {
        fk.now = start + static_cast<std::uint32_t>(elapsed);
        (void)acmp_declaring(&a, 0);
    }
    fk.source[0].dest_mac_valid = true;
    EXPECT_FALSE(acmp_declaring(&a, 0))
        << "destination recovery after a serviced full wrap cannot revive an expired probe";
}

// REQ: ACMP-11
TEST_F(AcmpFresh, WindowEdge) {
    for (auto start : {50000u, UINT32_MAX - 999u}) {
        fk.now = start;
        answer();
        fk.now += 15000u;
        EXPECT_FALSE(acmp_declaring(&a, 0)) << "the exact fifteen second boundary closes the declaration";
        answer();
        ASSERT_TRUE(acmp_listener_registered(&a, 0, 0, true));
        fk.now += 15000u;
        EXPECT_TRUE(acmp_declaring(&a, 0)) << "Listener demand keeps the gate open at exact probe expiry";
        ASSERT_TRUE(acmp_listener_registered(&a, 0, 0, false));
        EXPECT_FALSE(acmp_declaring(&a, 0)) << "Listener withdrawal exposes exact probe expiry immediately";
    }
}

// REQ: ACMP-11
TEST_F(AcmpFresh, WithinWindowAndRefresh) {
    fk.send_ms = 7u;
    answer();
    EXPECT_TRUE(acmp_declaring(&a, 0)) << "an accepted response opens the freshness window immediately";
    fk.now += 14999u;
    EXPECT_TRUE(acmp_declaring(&a, 0)) << "the final millisecond remains fresh from send acceptance";
    answer();
    fk.now += 14999u;
    EXPECT_TRUE(acmp_declaring(&a, 0)) << "another answer renews the complete freshness window";
}

// REQ: ACMP-11
TEST_F(AcmpFresh, ListenerWithoutProbe) {
    fk.source[0].asking_failed = true;
    ASSERT_TRUE(acmp_listener_registered(&a, 0, 0, true));
    EXPECT_TRUE(acmp_declaring(&a, 0)) << "a registered Listener declares without any answered probe";
    ASSERT_TRUE(acmp_listener_registered(&a, 0, 0, false));
    EXPECT_FALSE(acmp_declaring(&a, 0)) << "withdrawing the last Listener closes an unprobed source";
}

// REQ: ACMP-11
TEST_F(AcmpFresh, ListenerInterfaceMismatch) {
    EXPECT_FALSE(acmp_listener_registered(&a, 1, 0, true))
        << "a valid interface belonging to another source is refused";
    EXPECT_FALSE(acmp_declaring(&a, 0))
        << "a Listener on the wrong valid interface cannot open this source";
}

// REQ: ACMP-11
TEST_F(AcmpFresh, FreshProbeAfterListenerWithdrawal) {
    answer();
    ASSERT_TRUE(acmp_listener_registered(&a, 0, 0, true));
    fk.now += 100u;
    ASSERT_TRUE(acmp_listener_registered(&a, 0, 0, false));
    EXPECT_TRUE(acmp_declaring(&a, 0))
        << "a fresh answered probe survives Listener registration and withdrawal";
}

// REQ: ACMP-11
TEST_F(AcmpFresh, InitClearsListener) {
    ASSERT_TRUE(acmp_listener_registered(&a, 0, 0, true));
    ASSERT_TRUE(a.sources[0].listener_registered)
        << "Listener registration is still present immediately before initialization";
    ASSERT_TRUE(acmp_init(&a, &cfg, &kPorts, &kEnv));
    EXPECT_FALSE(acmp_declaring(&a, 0))
        << "initialization clears a Listener that was still registered";
}

// REQ: ACMP-11, PORT-01
TEST_F(AcmpFresh, QueryPorts) {
    answer();
    for (unsigned query = 0; query < 2u; ++query) {
        fk.now += 100u;
        fk.clear();
        (void)acmp_declaring(&a, 0);
        EXPECT_EQ(fk.count(Call::NOW), 1u)
            << "each answered declaration query samples the existing clock once";
        EXPECT_EQ(fk.count(Call::SOURCE), 1u)
            << "each declaration query samples the live source once";
        EXPECT_EQ(fk.calls.size(), 2u)
            << "declaration queries call only the existing clock and source ports";
        EXPECT_TRUE(fk.pubs.empty())
            << "declaration queries do not publish sink state";
    }
}

// REQ: ACMP-11
TEST_F(AcmpFresh, InvalidAddress) {
    answer();
    ASSERT_TRUE(acmp_listener_registered(&a, 0, 0, true));
    fk.source[0].dest_mac_valid = false;
    EXPECT_FALSE(acmp_declaring(&a, 0)) << "invalid destination blocks both fresh and registered demand";
    fk.source[0].dest_mac_valid = true;
    EXPECT_TRUE(acmp_declaring(&a, 0)) << "live destination validity is sampled on every declaration query";
}

// REQ: ACMP-11
TEST_F(AcmpFresh, ClockWrap) {
    fk.now = UINT32_MAX - 999u;
    answer();
    EXPECT_TRUE(acmp_declaring(&a, 0)) << "a pre-wrap answer is fresh before the clock rolls over";
    fk.now += 14999u;
    EXPECT_TRUE(acmp_declaring(&a, 0)) << "unsigned elapsed time keeps a probe fresh across clock wrap";
}

// REQ: ACMP-11
TEST_F(AcmpFresh, ConfiguredWindow) {
    cfg.da_fresh_ms = 30000u;
    ASSERT_TRUE(acmp_init(&a, &cfg, &kPorts, &kEnv));
    answer();
    fk.now += 20000u;
    EXPECT_TRUE(acmp_declaring(&a, 0)) << "the core uses the configured interval without a mirrored constant";
}

// REQ: ACMP-11
TEST_F(AcmpFresh, ZeroWindow) {
    cfg.da_fresh_ms = 0u;
    ASSERT_TRUE(acmp_init(&a, &cfg, &kPorts, &kEnv));
    fk.now = 50000u;
    answer();
    EXPECT_FALSE(acmp_declaring(&a, 0)) << "a zero interval disables probe demand even at answer acceptance";
    fk.now += 15001u;
    EXPECT_FALSE(acmp_declaring(&a, 0)) << "a zero interval cannot retain probe demand over time";
    ASSERT_TRUE(acmp_listener_registered(&a, 0, 0, true));
    EXPECT_TRUE(acmp_declaring(&a, 0)) << "a zero interval still allows a registered Listener to declare";
    ASSERT_TRUE(acmp_listener_registered(&a, 0, 0, false));
    EXPECT_FALSE(acmp_declaring(&a, 0)) << "a zero interval closes again when the Listener withdraws";
}

// REQ: ACMP-11, PORT-01
TEST_F(AcmpFresh, WindowRange) {
    cfg.da_fresh_ms = UINT32_C(0x7fffffff);
    ASSERT_TRUE(acmp_init(&a, &cfg, &kPorts, &kEnv))
        << "the largest interval below the clock half range remains valid";
    const auto before = a;
    for (auto interval : {UINT32_C(0x80000000), UINT32_MAX}) {
        cfg.da_fresh_ms = interval;
        EXPECT_FALSE(acmp_init(&a, &cfg, &kPorts, &kEnv))
            << "freshness intervals at or above the clock half range are refused";
        EXPECT_EQ(std::memcmp(&a, &before, sizeof a), 0)
            << "refusing a freshness interval leaves the instance unchanged";
    }
    EXPECT_TRUE(fk.calls.empty()) << "freshness interval validation calls no platform service";
}

// REQ: ACMP-11, ACMP-09
TEST_F(AcmpFresh, DeferredAnswer) {
    fk.room = false;
    answer();
    EXPECT_FALSE(acmp_declaring(&a, 0)) << "a queued response does not yet count as an answer";
    fk.now += 20000u;
    EXPECT_TRUE(acmp_poll(&a));
    EXPECT_FALSE(acmp_declaring(&a, 0)) << "a refused retry does not open the declaration";
    fk.room = true;
    EXPECT_FALSE(acmp_poll(&a));
    fk.now += 14999u;
    EXPECT_TRUE(acmp_declaring(&a, 0)) << "an owed answer starts freshness only after send acceptance";
}

// REQ: ACMP-11, ACMP-08
TEST_F(AcmpFresh, FailedAllocationAnswer) {
    fk.source[0].dest_mac_valid = false;
    answer();
    fk.source[0].dest_mac_valid = true;
    EXPECT_TRUE(acmp_declaring(&a, 0)) << "an answered allocation failure retains demand for later validity";
}

// REQ: ACMP-11, ACMP-08
TEST_F(AcmpFresh, OtherRepliesDoNotRefresh) {
    for (auto msg : {spec::MSG_GET_TX_STATE_COMMAND, spec::MSG_DISCONNECT_TX_COMMAND,
                     spec::MSG_GET_TX_CONNECTION_COMMAND}) {
        answer(0, 0, msg);
        EXPECT_FALSE(acmp_declaring(&a, 0)) << "other talker commands cannot supply probe freshness";
    }
    answer(0, 1);
    EXPECT_FALSE(acmp_declaring(&a, 0)) << "an incompatible interface answer cannot refresh a source";
    fk.clear();
    answer(cfg.n_sources, 0);
    EXPECT_EQ(fk.count(Call::NOW), 0u) << "unknown source replies do not timestamp probe demand";
    EXPECT_FALSE(acmp_declaring(&a, 0)) << "an unknown source answer cannot refresh a valid source";
}

// REQ: ACMP-11
TEST_F(AcmpFresh, SourceAndInterfaceIsolation) {
    answer(1, 1);
    EXPECT_FALSE(acmp_declaring(&a, 0)) << "a probe on the second source leaves the first source closed";
    EXPECT_TRUE(acmp_declaring(&a, 1)) << "the probed source declares on its configured interface";
    ASSERT_TRUE(acmp_listener_registered(&a, 1, 1, true));
    EXPECT_FALSE(acmp_declaring(&a, 0)) << "Listener demand does not leak into another source";
}

// REQ: ACMP-11, PORT-01
TEST_F(AcmpFresh, InputGuardsAndReentry) {
    EXPECT_FALSE(acmp_listener_registered(&a, 0, cfg.n_sources, true))
        << "unknown Listener source is refused without a state write";
    EXPECT_FALSE(acmp_listener_registered(&a, cfg.n_interfaces, 0, true))
        << "Listener interface must match the configured source interface";
    EXPECT_FALSE(acmp_declaring(&a, cfg.n_sources)) << "unknown declaration source returns false";
    ASSERT_TRUE(acmp_listener_registered(&a, 0, 0, true));
    ASSERT_TRUE(acmp_listener_registered(&a, 0, 0, false));
    EXPECT_TRUE(fk.calls.empty()) << "Listener input and invalid queries call no platform service";
    fk.hook_kind = Call::SOURCE;
    fk.hook = [&]() {
        EXPECT_FALSE(acmp_listener_registered(&a, 0, 0, true))
            << "Listener input refuses synchronous source callback reentry";
        EXPECT_FALSE(acmp_declaring(&a, 0)) << "declaration query refuses synchronous source callback reentry";
    };
    EXPECT_FALSE(acmp_declaring(&a, 0));
    EXPECT_EQ(a.reentries, 2u) << "both new entries account for refused callback recursion";
    EXPECT_EQ(reentry_traps, 2u) << "both new entries invoke the configured reentry hook";
}

// REQ: ACMP-11
TEST_F(AcmpFresh, ListenerWithdrawalAndReset) {
    answer();
    ASSERT_TRUE(acmp_listener_registered(&a, 0, 0, true));
    fk.now += 15000u;
    EXPECT_TRUE(acmp_declaring(&a, 0)) << "a Listener keeps a stale probe source declaring";
    ASSERT_TRUE(acmp_listener_registered(&a, 0, 0, false));
    fk.now += 15000u;
    EXPECT_FALSE(acmp_declaring(&a, 0)) << "Listener withdrawal cannot extend an expired freshness window";
    answer();
    EXPECT_TRUE(acmp_declaring(&a, 0));
    ASSERT_TRUE(acmp_init(&a, &cfg, &kPorts, &kEnv));
    EXPECT_FALSE(acmp_declaring(&a, 0)) << "initialization clears previous demand and probe timestamps";
    EXPECT_EQ(a.sources[0].answered_at, 0u) << "initialization clears the saved answer timestamp itself";
}

class AcmpOwed : public AcmpCore {
 protected:
    static constexpr std::uint32_t kCommandTimeoutMs = 200u;   // Milan v1.2 Table 5.26; IEEE 1722.1-2021 Table 8-1
    static constexpr std::uint32_t kHoldMs = 60u;

    struct Held {
        unsigned interface;
        std::array<std::uint8_t, spec::FRAME_BYTES> bytes;
    };
    std::vector<Held> held;

    bool deliver(const Pdu& p, unsigned interface = 0) {
        auto f = acmpdu(p);
        if (held.empty() && acmp_rx(&a, interface, f.data(), f.size())) {
            return true;
        }
        held.push_back({interface, f});
        return false;
    }
    void pass() {
        fk.now += 1u;
        static_cast<void>(acmp_poll(&a));
        while (!held.empty() &&
               acmp_rx(&a, held.front().interface, held.front().bytes.data(), held.front().bytes.size())) {
            held.erase(held.begin());
        }
        for (unsigned i = 0; i < cfg.n_interfaces; ++i) {
            if (fk.armed[i] && static_cast<std::int32_t>(fk.now - fk.at[i]) >= 0) {
                acmp_timer_expired(&a, i);
            }
        }
    }
    void drain() {
        for (unsigned n = 0; n < 4u * ACMP_OWED_MAX && (a.owed_count != 0u || !held.empty()); ++n) {
            pass();
        }
    }
    void release_after_hold() {
        fk.now += kHoldMs;
        fk.room = true;
        drain();
    }
    unsigned position(const Sent* s) const { return static_cast<unsigned>(s - fk.sent.data()); }
    void fill(std::uint16_t first) {
        fk.room = false;
        for (unsigned k = 0; k < ACMP_OWED_MAX; ++k) {
            rx(command(spec::MSG_GET_RX_STATE_COMMAND, 0, 0, 0, kCtl2, 0, static_cast<std::uint16_t>(first + k)));
        }
    }
    const Sent* answer(std::uint8_t msg, std::uint16_t seq) const {
        for (const Sent& s : fk.sent) {
            Pdu p = read(s.bytes.data());
            if (p.msg == msg && p.seq == seq) {
                return &s;
            }
        }
        return nullptr;
    }
    bool unchanged_since(const acmp& before) const {
        acmp now_image;
        std::memcpy(&now_image, &a, sizeof a);
        now_image.busy_declined = before.busy_declined;
        now_image.now_read = before.now_read;
        return std::memcmp(&now_image, &before, sizeof a) == 0;
    }

    // Milan v1.2 5.5.3.5.10; Milan v1.2 5.5.3.5.16
    std::vector<unsigned> others;
    std::vector<std::uint32_t> due_in;
    std::vector<std::uint32_t> owed_in;
    std::uint32_t arrival = 0;
    std::uint32_t released = 0;
    std::uint32_t taken_in = 0;
    void sinks_on_one_interface(unsigned n) {
        held.clear();
        others.clear();
        cfg.n_sinks = n;
        for (unsigned k = 0; k < n; ++k) {
            cfg.sink_interface[k] = 0;
        }
        ASSERT_TRUE(acmp_init(&a, &cfg, &kPorts, &kEnv));
        fk.room = true;
    }
    void retries_due(unsigned first, unsigned count, std::uint32_t step_ms) {
        for (unsigned k = first; k < first + count; ++k) {
            fk.now += step_ms;
            bind(k, kTkB, static_cast<std::uint16_t>(k));
            others.push_back(k);
        }
    }
    void bind_behind_the_owed_set_with_probes_due(std::uint32_t hold_ms) {
        std::uint32_t first_due = a.sinks[others.front()].timer_deadline;
        for (unsigned k : others) {
            first_due = static_cast<std::int32_t>(a.sinks[k].timer_deadline - first_due) < 0 ? a.sinks[k].timer_deadline
                                                                                               : first_due;
        }
        fk.now = first_due - hold_ms - 1u;
        fill(0x7A00);
        fk.clear();
        arrival = fk.now;
        EXPECT_FALSE(deliver(command(spec::MSG_BIND_RX_COMMAND, 1, kTkA, 1, kCtl1, 0, 0x7A08)))
            << "a BIND_RX behind the full owed set is declined while other probes are about to fall due";
        std::vector<acmp_sink_state> from;
        due_in.clear();
        owed_in.assign(others.size(), 0u);
        for (unsigned k : others) {
            from.push_back(a.sinks[k].state);
            due_in.push_back(a.sinks[k].timer_deadline - (first_due - 1u));
        }
        fk.now += hold_ms;
        fk.room = true;
        released = fk.now;
        taken_in = 0;
        for (std::uint32_t n = 1; n <= 4u * ACMP_OWED_MAX && (a.owed_count != 0u || !held.empty()); ++n) {
            pass();
            taken_in = taken_in == 0u && held.empty() ? n : taken_in;
            for (unsigned j = 0; j < others.size(); ++j) {
                owed_in[j] = owed_in[j] == 0u && a.sinks[others[j]].state != from[j] ? n : owed_in[j];
            }
        }
    }
};

// REQ: ACMP-12, ACMP-09
TEST_F(AcmpOwed, HeldEgressDefersTheCommandBehindTheOwedSet) {
    fill(0x7380);
    ASSERT_EQ(a.owed_count, ACMP_OWED_MAX);
    fk.clear();
    const std::uint32_t arrival = fk.now;
    EXPECT_FALSE(deliver(command(spec::MSG_GET_RX_STATE_COMMAND, 0, 0, 0, kCtl2, 0, 0x7388)))
        << "a GET_RX_STATE behind the full owed set is declined to the port, not taken";
    EXPECT_TRUE(fk.calls.empty() && a.busy_declined == 1u && a.owed_count == ACMP_OWED_MAX)
        << "the declined GET_RX_STATE makes no port call and is counted once";
    release_after_hold();
    ASSERT_TRUE(held.empty() && a.owed_count == 0u) << "the held command was taken and every owed frame left";
    const Sent* s = answer(spec::MSG_GET_RX_STATE_RESPONSE, 0x7388);
    ASSERT_TRUE(s != nullptr) << "the command behind the owed set is answered after the egress returns";
    Pdu r = read(s->bytes.data());
    EXPECT_TRUE(r.status == spec::STATUS_SUCCESS && r.controller == kCtl2 && r.listener == kOwn &&
                r.listener_uid == 0u && r.talker == 0u && r.talker_uid == 0u && r.count == 0u && r.flags == 0u &&
                r.stream_id == 0u)
        << "its answer is the Milan Table 5.34 response, not an error status";
    EXPECT_LE(s->at - arrival, kCommandTimeoutMs) << "the deferred answer leaves within its 200 ms command timeout";
    ASSERT_EQ(fk.sent.size(), ACMP_OWED_MAX + 1u);
    for (unsigned k = 0; k <= ACMP_OWED_MAX; ++k) {
        EXPECT_EQ(static_cast<unsigned>(read(fk.sent[k].bytes.data()).seq), 0x7380u + k)
            << "the answers leave in command order, none lost";
    }
    EXPECT_EQ(s->at - arrival, kHoldMs + ACMP_OWED_MAX + 1u)
        << "the deferred answer leaves in the pass after the eight frames owed ahead of it";
}

// REQ: ACMP-12, ACMP-08
TEST_F(AcmpOwed, TalkerCommandsBehindTheOwedSetAreAnsweredInTime) {
    fill(0x7400);
    fk.clear();
    Pdu p;
    p.controller = kCtl2;
    p.talker = kOwn;
    p.listener = kTkB;
    p.listener_uid = 3u;
    p.flags = spec::FLAG_FAST_CONNECT;
    const std::uint32_t arrival = fk.now;
    p.msg = spec::MSG_PROBE_TX_COMMAND;
    p.seq = 0x7408;
    EXPECT_FALSE(deliver(p)) << "a PROBE_TX behind the full owed set is declined to the port";
    EXPECT_TRUE(fk.calls.empty() && a.busy_declined == 1u)
        << "the declined PROBE_TX reads no source state and is counted";
    p.msg = spec::MSG_DISCONNECT_TX_COMMAND;
    p.seq = 0x7409;
    EXPECT_FALSE(deliver(p)) << "a DISCONNECT_TX waits in the port behind the declined command";
    p.msg = spec::MSG_GET_TX_CONNECTION_COMMAND;
    p.seq = 0x740A;
    EXPECT_FALSE(deliver(p)) << "a GET_TX_CONNECTION waits in the port behind the declined commands";
    release_after_hold();
    ASSERT_TRUE(held.empty() && a.owed_count == 0u) << "the held talker commands were all taken";
    const Sent* probe = answer(spec::MSG_PROBE_TX_RESPONSE, 0x7408);
    ASSERT_TRUE(probe != nullptr) << "the PROBE_TX behind the owed set is answered";
    Pdu r = read(probe->bytes.data());
    EXPECT_TRUE(r.status == spec::STATUS_SUCCESS && r.stream_id == kSid && r.dest_mac == kDa && r.vlan == 2u &&
                r.flags == spec::FLAG_FAST_CONNECT && r.listener == kTkB && r.listener_uid == 3u)
        << "the PROBE_TX answer carries the Milan Table 5.43 fields";
    const Sent* disconnect = answer(spec::MSG_DISCONNECT_TX_RESPONSE, 0x7409);
    ASSERT_TRUE(disconnect != nullptr) << "the DISCONNECT_TX behind the owed set is answered";
    EXPECT_TRUE(read(disconnect->bytes.data()).status == spec::STATUS_SUCCESS)
        << "the DISCONNECT_TX answer is the Milan Table 5.45 success";
    const Sent* connection = answer(spec::MSG_GET_TX_CONNECTION_RESPONSE, 0x740A);
    ASSERT_TRUE(connection != nullptr) << "the GET_TX_CONNECTION behind the owed set is answered";
    EXPECT_TRUE(read(connection->bytes.data()).status == spec::STATUS_NOT_SUPPORTED)
        << "the GET_TX_CONNECTION answer is the Milan Table 5.48 refusal";
    for (const Sent* s : {probe, disconnect, connection}) {
        EXPECT_LE(s->at - arrival, kCommandTimeoutMs) << "each talker answer leaves within its 200 ms command timeout";
    }
    EXPECT_TRUE(probe->at < disconnect->at && disconnect->at < connection->at)
        << "the held talker answers leave in arrival order";
}

// REQ: ACMP-12, ACMP-03
TEST_F(AcmpOwed, DeclinedUnbindChangesNothingUntilItIsTaken) {
    bind(1);
    ASSERT_TRUE(a.sinks[1].bound);
    fill(0x7500);
    fk.clear();
    acmp before;
    std::memcpy(&before, &a, sizeof a);
    const std::uint32_t arrival = fk.now;
    EXPECT_FALSE(deliver(command(spec::MSG_UNBIND_RX_COMMAND, 1, kTkA, 1, kCtl1, 0, 0x7508)))
        << "an UNBIND_RX behind the full owed set is declined";
    EXPECT_TRUE(fk.calls.empty() && fk.pubs.empty())
        << "the declined UNBIND_RX calls no port or environment service";
    EXPECT_TRUE(unchanged_since(before)) << "the declined UNBIND_RX changes no instance state but its counter";
    EXPECT_EQ(a.busy_declined, before.busy_declined + 1u) << "the declined UNBIND_RX is counted once";
    release_after_hold();
    const Sent* s = answer(spec::MSG_UNBIND_RX_RESPONSE, 0x7508);
    ASSERT_TRUE(s != nullptr) << "the UNBIND_RX behind the owed set is answered once it is taken";
    Pdu r = read(s->bytes.data());
    EXPECT_TRUE(r.status == spec::STATUS_SUCCESS && r.talker == 0u && r.talker_uid == 0u && r.listener_uid == 1u)
        << "the UNBIND_RX answer is the Milan Table 5.36 success";
    EXPECT_LE(s->at - arrival, kCommandTimeoutMs) << "the UNBIND_RX answer leaves within its 200 ms command timeout";
    EXPECT_TRUE(!a.sinks[1].bound && a.sinks[1].state == ACMP_UNBOUND)
        << "the unbinding takes effect only when the command is taken";
}

// REQ: ACMP-12, PORT-01
TEST_F(AcmpOwed, ReadyPredicateMatchesTheOwedBound) {
    fk.room = false;
    for (unsigned k = 0; k + 2u < ACMP_OWED_MAX; ++k) {
        rx(command(spec::MSG_GET_RX_STATE_COMMAND, 0, 0, 0, kCtl2, 0, static_cast<std::uint16_t>(k)));
    }
    EXPECT_TRUE(acmp_rx_ready(&a)) << "two free owed slots keep the core ready";
    rx(command(spec::MSG_GET_RX_STATE_COMMAND, 0, 0, 0, kCtl2, 0, 6u));
    ASSERT_EQ(a.owed_count, ACMP_OWED_MAX - 1u);
    EXPECT_FALSE(acmp_rx_ready(&a)) << "one free owed slot is not ready, since a BIND_RX needs two";
    auto bind_rx = acmpdu(command(spec::MSG_BIND_RX_COMMAND, 1, kTkA, 1, kCtl1, 0, 0x77u));
    EXPECT_FALSE(acmp_rx(&a, 0, bind_rx.data(), bind_rx.size()))
        << "a BIND_RX with one free owed slot is declined";
    EXPECT_TRUE(a.busy_declined == 1u && !a.sinks[1].bound) << "the BIND_RX declined at one free slot binds nothing";
    auto last_slot = acmpdu(command(spec::MSG_GET_RX_STATE_COMMAND, 0, 0, 0, kCtl2, 0, 7u));
    EXPECT_TRUE(acmp_rx(&a, 0, last_slot.data(), last_slot.size()))
        << "the command that takes the last owed slot is taken";
    EXPECT_EQ(a.owed_count, ACMP_OWED_MAX) << "the last owed slot holds that answer";
    EXPECT_FALSE(acmp_rx_ready(&a)) << "a full owed set is not ready";
    fk.room = true;
    EXPECT_TRUE(acmp_poll(&a));
    EXPECT_FALSE(acmp_rx_ready(&a)) << "one accepted owed frame leaves one free slot, still not ready";
    EXPECT_TRUE(acmp_poll(&a));
    EXPECT_TRUE(acmp_rx_ready(&a)) << "a second accepted owed frame makes the core ready again";
    auto f = acmpdu(command(spec::MSG_GET_RX_STATE_COMMAND, 0, 0, 0, kCtl2, 0, 9u));
    fk.hook_kind = Call::SEND;
    fk.hook = [&]() {
        EXPECT_FALSE(acmp_rx_ready(&a)) << "the core is not ready inside a port callback";
        EXPECT_FALSE(acmp_rx(&a, 0, f.data(), f.size())) << "a frame offered by callback re-entry is declined";
    };
    EXPECT_TRUE(acmp_poll(&a));
    EXPECT_TRUE(a.reentries == 1u && reentry_traps == 1u && a.busy_declined == 1u)
        << "the re-entered frame counts as re-entry, not as a full owed set";
}

// REQ: ACMP-12, ACMP-02
TEST_F(AcmpOwed, OnlyOwnCommandsAreDeclined) {
    fill(0x7600);
    fk.clear();
    auto f = acmpdu(command(spec::MSG_GET_RX_STATE_COMMAND, 0));
    EXPECT_TRUE(acmp_rx(&a, 0, f.data(), spec::FRAME_BYTES - 1u))
        << "a malformed frame is taken and counted while the owed set is full";
    auto take = [&](const Pdu& p) {
        auto g = acmpdu(p);
        return acmp_rx(&a, 0, g.data(), g.size());
    };
    Pdu other_listener = command(spec::MSG_GET_RX_STATE_COMMAND, 0);
    other_listener.listener = kTkB;
    EXPECT_TRUE(take(other_listener)) << "a listener command for another entity is taken and ignored";
    Pdu other_talker;
    other_talker.msg = spec::MSG_GET_TX_STATE_COMMAND;
    other_talker.talker = kTkB;
    EXPECT_TRUE(take(other_talker)) << "a talker command for another entity is taken and ignored";
    EXPECT_TRUE(take(probe_answer(0))) << "a probe response needs no owed slot and is taken";
    EXPECT_TRUE(a.busy_declined == 0u && a.rx_malformed == 1u && a.rx_ignored == 3u)
        << "frames without an owed answer are never declined";
}

// REQ: ACMP-12, ACMP-03
TEST_F(AcmpOwed, DeclinedBindIsAnsweredAfterTheHold) {
    fill(0x7700);
    fk.clear();
    const std::uint32_t arrival = fk.now;
    EXPECT_FALSE(deliver(command(spec::MSG_BIND_RX_COMMAND, 1, kTkA, 1, kCtl1, spec::FLAG_STREAMING_WAIT, 0x7708)))
        << "a BIND_RX behind the full owed set is declined to the port";
    EXPECT_TRUE(fk.calls.empty() && a.busy_declined == 1u && !a.sinks[1].bound && a.sinks[1].state == ACMP_UNBOUND)
        << "the declined BIND_RX binds nothing and makes no port call";
    EXPECT_FALSE(deliver(command(spec::MSG_GET_RX_STATE_COMMAND, 1, 0, 0, kCtl2, 0, 0x7709)))
        << "a GET_RX_STATE waits in the port behind the declined BIND_RX";
    release_after_hold();
    ASSERT_TRUE(held.empty() && a.owed_count == 0u) << "the held BIND_RX and the command behind it were taken";
    const Sent* s = answer(spec::MSG_BIND_RX_RESPONSE, 0x7708);
    ASSERT_TRUE(s != nullptr) << "the BIND_RX behind the owed set is answered after the egress returns";
    Pdu r = read(s->bytes.data());
    EXPECT_TRUE(r.status == spec::STATUS_SUCCESS && r.controller == kCtl1 && r.talker == kTkA && r.talker_uid == 1u &&
                r.listener == kOwn && r.listener_uid == 1u && r.count == 1u && r.flags == spec::FLAG_STREAMING_WAIT &&
                r.stream_id == 0u && r.dest_mac == 0u && r.vlan == 0u)
        << "the BIND_RX answer carries the Milan Table 5.32 fields";
    EXPECT_LE(s->at - arrival, kCommandTimeoutMs) << "the BIND_RX answer leaves within its 200 ms command timeout";
    EXPECT_EQ(position(s), ACMP_OWED_MAX) << "the BIND_RX answer leaves right after the eight frames owed ahead of it";
    for (unsigned k = 0; k < ACMP_OWED_MAX; ++k) {
        EXPECT_EQ(static_cast<unsigned>(read(fk.sent[k].bytes.data()).seq), 0x7700u + k)
            << "the frames owed ahead of the BIND_RX leave first, in order";
    }
    const Sent* behind = answer(spec::MSG_GET_RX_STATE_RESPONSE, 0x7709);
    ASSERT_TRUE(behind != nullptr) << "the command held behind the BIND_RX is answered too";
    EXPECT_TRUE(behind->at > s->at && read(behind->bytes.data()).count == 1u)
        << "the command held behind the BIND_RX is answered after it and sees the new binding";
    EXPECT_LE(behind->at - arrival, kCommandTimeoutMs) << "the command behind the BIND_RX is answered within 200 ms";
    EXPECT_TRUE(a.sinks[1].bound && a.sinks[1].binding.talker_entity_id == kTkA && a.sinks[1].binding.streaming_wait)
        << "the binding takes effect when the BIND_RX is taken";
}

// REQ: ACMP-12, ACMP-08
TEST_F(AcmpOwed, DeclinedGetTxStateIsAnsweredAfterTheHold) {
    fill(0x7800);
    fk.clear();
    Pdu p;
    p.controller = kCtl2;
    p.talker = kOwn;
    p.talker_uid = 1u;
    p.listener = kTkB;
    p.listener_uid = 3u;
    p.msg = spec::MSG_GET_TX_STATE_COMMAND;
    p.seq = 0x7808;
    const std::uint32_t arrival = fk.now;
    EXPECT_FALSE(deliver(p)) << "a GET_TX_STATE behind the full owed set is declined to the port";
    EXPECT_TRUE(fk.calls.empty() && a.busy_declined == 1u)
        << "the declined GET_TX_STATE reads no source state and is counted";
    p.msg = spec::MSG_GET_TX_CONNECTION_COMMAND;
    p.seq = 0x7809;
    EXPECT_FALSE(deliver(p)) << "a GET_TX_CONNECTION waits in the port behind the declined GET_TX_STATE";
    fk.source[1] = acmp_source_state{true, {kSid + 7u, kDa + 7u, 3u}, true};
    release_after_hold();
    ASSERT_TRUE(held.empty() && a.owed_count == 0u) << "the held GET_TX_STATE and the command behind it were taken";
    const Sent* s = answer(spec::MSG_GET_TX_STATE_RESPONSE, 0x7808);
    ASSERT_TRUE(s != nullptr) << "the GET_TX_STATE behind the owed set is answered after the egress returns";
    Pdu r = read(s->bytes.data());
    EXPECT_TRUE(r.status == spec::STATUS_SUCCESS && r.controller == kCtl2 && r.talker == kOwn && r.talker_uid == 1u &&
                r.listener == 0u && r.listener_uid == 0u && r.flags == spec::FLAG_REGISTERING_FAILED &&
                r.stream_id == kSid + 7u && r.dest_mac == kDa + 7u && r.vlan == 3u)
        << "the GET_TX_STATE answer carries the Milan Table 5.47 fields from the source state when taken";
    EXPECT_LE(s->at - arrival, kCommandTimeoutMs) << "the GET_TX_STATE answer leaves within its 200 ms command timeout";
    EXPECT_EQ(position(s), ACMP_OWED_MAX)
        << "the GET_TX_STATE answer leaves right after the eight frames owed ahead of it";
    const Sent* behind = answer(spec::MSG_GET_TX_CONNECTION_RESPONSE, 0x7809);
    ASSERT_TRUE(behind != nullptr) << "the command held behind the GET_TX_STATE is answered too";
    EXPECT_EQ(position(behind), ACMP_OWED_MAX + 1u) << "the command held behind the GET_TX_STATE is answered next";
    EXPECT_LE(behind->at - arrival, kCommandTimeoutMs) << "the command behind the GET_TX_STATE is answered within 200 ms";
}

// REQ: ACMP-12, ACMP-09
TEST_F(AcmpOwed, DeferredBindWaitsForTwoSlotsAndLosesNoProbe) {
    fill(0x7900);
    fk.clear();
    const std::uint32_t arrival = fk.now;
    EXPECT_FALSE(deliver(command(spec::MSG_BIND_RX_COMMAND, 1, kTkA, 1, kCtl1, 0, 0x7908)))
        << "a new binding behind the full owed set is declined";
    fk.now += kHoldMs;
    fk.room = true;
    pass();
    EXPECT_TRUE(held.size() == 1u && a.owed_count == ACMP_OWED_MAX - 1u && a.busy_declined == 2u && !a.sinks[1].bound)
        << "with one free owed slot the BIND_RX is declined again";
    pass();
    EXPECT_TRUE(held.empty() && a.owed_count == ACMP_OWED_MAX && a.sinks[1].bound)
        << "with two free owed slots the BIND_RX is taken, and its answer and probe are both owed";
    drain();
    EXPECT_EQ(a.probes_lost, 0u) << "a deferred binding loses no probe";
    const Sent* s = answer(spec::MSG_BIND_RX_RESPONSE, 0x7908);
    ASSERT_TRUE(s != nullptr) << "the deferred BIND_RX is answered";
    EXPECT_LE(s->at - arrival, kCommandTimeoutMs) << "the deferred BIND_RX answer leaves within 200 ms";
    ASSERT_EQ(fk.sent.size(), ACMP_OWED_MAX + 2u) << "the owed frames, the BIND_RX answer and one probe leave";
    const Sent& probe = fk.sent.back();
    Pdu q = read(probe.bytes.data());
    EXPECT_TRUE(q.msg == spec::MSG_PROBE_TX_COMMAND && q.talker == kTkA && q.listener_uid == 1u &&
                q.seq == a.sinks[1].probe_seq && probe.at == s->at + 1u)
        << "the first probe leaves at once, in the pass after the BIND_RX answer";
    EXPECT_TRUE(a.sinks[1].state == ACMP_PRB_W_RESP && !a.sinks[1].probe_retried &&
                a.sinks[1].timer == ACMP_TIMER_NO_RESP && a.sinks[1].timer_deadline == probe.at + spec::TMR_NO_RESP_MS)
        << "the probe's timeout runs from when it left, with its retry still unused";
}

// REQ: ACMP-12, ACMP-09
TEST_F(AcmpOwed, ProbesFallingDueInTheDrainWaitForTheDeferredBind) {
    struct Case {
        unsigned retries;
        std::uint32_t step_ms;
        bool delay;
    };
    for (const Case& c : {Case{1u, 1u, false}, Case{0u, 0u, true}, Case{4u, 1u, false}, Case{4u, 0u, false}}) {
        SetUp();
        sinks_on_one_interface(2u + c.retries + (c.delay ? 1u : 0u));
        retries_due(2u, c.retries, c.step_ms);
        if (c.delay) {
            to_state(2u + c.retries, ACMP_PRB_W_DELAY);
            others.push_back(2u + c.retries);
        }
        bind_behind_the_owed_set_with_probes_due(kHoldMs);
        ASSERT_TRUE(held.empty() && a.owed_count == 0u) << "the deferred BIND_RX was taken and every owed frame left";
        EXPECT_EQ(taken_in, 2u) << "the deferred BIND_RX is declined once more at one free slot and taken in pass two";
        EXPECT_EQ(a.busy_declined, 2u) << "no probe makes the deferred BIND_RX wait another pass";
        const Sent* s = answer(spec::MSG_BIND_RX_RESPONSE, 0x7A08);
        ASSERT_TRUE(s != nullptr) << "the deferred BIND_RX is answered while other probes fall due";
        EXPECT_EQ(s->at - released, ACMP_OWED_MAX + 1u)
            << "the deferred BIND_RX is answered in pass ACMP_OWED_MAX + 1 though other probes fall due";
        EXPECT_EQ(position(s), ACMP_OWED_MAX) << "no held probe leaves ahead of the deferred BIND_RX answer";
        EXPECT_LE(s->at - arrival, kCommandTimeoutMs) << "the BIND_RX answer still leaves within 200 ms";
        EXPECT_EQ(a.probes_lost, 0u) << "no probe held for the deferred BIND_RX is lost";
        ASSERT_EQ(fk.sent.size(), ACMP_OWED_MAX + 2u + others.size())
            << "the owed frames, the BIND_RX answer and its probe, and every held probe leave";
        Pdu own = read(fk.sent[ACMP_OWED_MAX + 1u].bytes.data());
        EXPECT_TRUE(own.msg == spec::MSG_PROBE_TX_COMMAND && own.listener_uid == 1u && own.talker == kTkA)
            << "the deferred binding's own probe leaves right after its answer";
        std::uint32_t holds = 0;
        for (unsigned j = 0; j < others.size(); ++j) {
            const Sent& left = fk.sent[ACMP_OWED_MAX + 2u + j];
            Pdu q = read(left.bytes.data());
            const acmp_sink& sink = a.sinks[others[j]];
            EXPECT_TRUE(q.msg == spec::MSG_PROBE_TX_COMMAND && q.listener_uid == others[j] && q.seq == sink.probe_seq)
                << "each held probe leaves after the deferred binding's frames, in sink order";
            EXPECT_EQ(owed_in[j], taken_in + 1u + j)
                << "each held probe is owed in the pass after the BIND_RX is taken, one pass per probe before it";
            EXPECT_TRUE(sink.timer == ACMP_TIMER_NO_RESP && !sink.timer_held && !sink.probe_held &&
                        sink.timer_deadline == left.at + spec::TMR_NO_RESP_MS)
                << "each held probe was sent, and its timeout runs from when it left";
            EXPECT_TRUE(sink.state == (c.delay && j + 1u == others.size() ? ACMP_PRB_W_RESP : ACMP_PRB_W_RESP2))
                << "a held delay expiry sends the first probe and a held retry the duplicate";
            holds += owed_in[j] - due_in[j];
        }
        EXPECT_EQ(a.probes_held, holds) << "each pass that holds a probe counts once";
    }
}

// REQ: ACMP-12, ACMP-09
TEST_F(AcmpOwed, DeferredBindAtTheDocumentedMarginMeetsItsTimeout) {
    const std::uint32_t margin = kCommandTimeoutMs - (ACMP_OWED_MAX + 1u);
    for (unsigned retries : {1u, 4u}) {
        SetUp();
        sinks_on_one_interface(2u + retries);
        retries_due(2u, retries, 1u);
        bind_behind_the_owed_set_with_probes_due(margin);
        const Sent* s = answer(spec::MSG_BIND_RX_RESPONSE, 0x7A08);
        ASSERT_TRUE(s != nullptr) << "the BIND_RX deferred for the margin hold is answered";
        EXPECT_EQ(s->at - arrival, kCommandTimeoutMs)
            << "a 191 ms hold leaves the deferred BIND_RX exactly the documented passes of its 200 ms timeout";
        EXPECT_TRUE(a.probes_lost == 0u && a.probes_held != 0u && fk.sent.size() == ACMP_OWED_MAX + 2u + retries)
            << "at the margin every probe falling due is held and sent, none lost";
    }
}

// REQ: ACMP-12, ACMP-09
TEST_F(AcmpOwed, HoldEndsWithTheLastHeldProbe) {
    sinks_on_one_interface(3u);
    retries_due(2u, 1u, 1u);
    Adp here;
    here.entity = kTkB;
    adp(here);
    ASSERT_TRUE(a.sinks[2].discovered && a.sinks[2].state == ACMP_PRB_W_RESP) << "the probing sink knows its talker";
    fk.now = a.sinks[2].timer_deadline - kHoldMs - 1u;
    fill(0x7B00);
    fk.clear();
    EXPECT_FALSE(deliver(command(spec::MSG_BIND_RX_COMMAND, 1, kTkA, 1, kCtl1, 0, 0x7B08)))
        << "a BIND_RX is declined behind the full owed set before the retry falls due";
    fk.now += kHoldMs;
    fk.room = true;
    pass();
    ASSERT_TRUE(a.sinks[2].probe_held && a.probes_held == 1u && a.owed_count == ACMP_OWED_MAX - 1u)
        << "the retry falling due beside the deferred BIND_RX is held, not owed";
    Adp gone = here;
    gone.msg = spec::ADPDU_ENTITY_DEPARTING;
    adp(gone);
    EXPECT_TRUE(!a.sinks[2].probe_held && a.sinks[2].state == ACMP_PRB_W_AVAIL && a.sinks[2].timer == ACMP_TIMER_NONE)
        << "a held probe whose talker departs is dropped with the probing it belonged to";
    drain();
    ASSERT_TRUE(held.empty() && a.owed_count == 0u && a.sinks[1].bound) << "the deferred BIND_RX was taken";
    ASSERT_TRUE(a.sinks[1].state == ACMP_PRB_W_RESP && a.probes_lost == 0u) << "the new binding's first probe left";
    fill(0x7C00);
    fk.now = a.sinks[1].timer_deadline;
    acmp_timer_expired(&a, 0);
    EXPECT_TRUE(a.probes_lost == 1u && a.probes_held == 1u && !a.sinks[1].probe_held &&
                a.sinks[1].state == ACMP_PRB_W_RESP2)
        << "with no probe held and no BIND_RX waiting, a retry that finds every slot owed is lost and counted";
}

}

// REQ: ACMP-02
TEST(Wire, W1PutBeWritesTheLowBytesMostSignificantFirst) {
    for (std::uint64_t value : {0x0102030405060708ull, 0x8899AABBCCDDEEFFull, 0xF0E1D2C3B4A59687ull,
                                0x00000000FFFFFFFFull, 0xFFFFFFFF00000000ull}) {
        for (unsigned k = 0; k < 4; ++k) {
            ASSERT_NE(static_cast<std::uint8_t>(value >> (32u + 8u * k)), static_cast<std::uint8_t>(value >> (8u * k)))
                << "W1 oracle halves differ in every crossing byte";
        }
        for (unsigned bytes = 1; bytes <= 8; ++bytes) {
            std::array<std::uint8_t, 10> got{};
            got.fill(0x5A);
            std::array<std::uint8_t, 10> want = got;
            for (unsigned i = 0; i < bytes; ++i) {
                want[1u + i] = static_cast<std::uint8_t>(value >> (8u * (bytes - 1u - i)));
            }
            wire_put_be(got.data() + 1, value, bytes);
            EXPECT_EQ(got, want) << "W1 wire_put_be writes the low bytes most significant first and nothing past them";
        }
    }
}
