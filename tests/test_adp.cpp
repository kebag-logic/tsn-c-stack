// SPDX-FileCopyrightText: 2026 Kebag Logic
// SPDX-License-Identifier: MIT
//
// ADP core cases over fake ports.

#include <gtest/gtest.h>

#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <tuple>

#include "adp.h"
#include "wire.h"


namespace {

const struct adp_entity entity = {
    .entity_id = 0x1122334455667788ull,
    .entity_model_id = 0x99AABBCCDDEEFF01ull,
    .mac = 0x001B921122AAull,
    .entity_capabilities = 0xC588u,
    .talker_stream_sources = 8u,
    .talker_capabilities = 0x4801u,
    .listener_stream_sinks = 8u,
    .listener_capabilities = 0x4801u,
    .identify_control_index = 5u,
};

struct fake {
    bool room;
    bool link;
    unsigned sends;
    uint8_t last[ADP_FRAME_BYTES];
    uint8_t msg[16];     // message_type of each frame taken, in order
    uint32_t index[16];  // and its available_index
    unsigned starts;
    uint32_t last_delay;
    unsigned stops;
    uint64_t gm;
    uint8_t domain;
};

struct fake fk;

bool fake_send(void* ctx, unsigned interface, const uint8_t* frame, size_t len) {
    static_cast<void>(ctx);
    static_cast<void>(interface);
    if (!fk.room || len != ADP_FRAME_BYTES) {
        return false;
    }
    std::memcpy(fk.last, frame, len);
    if (fk.sends < 16u) {
        fk.msg[fk.sends] = frame[15] & 0x0Fu;
        fk.index[fk.sends] = wire_be32(frame + 50);
    }
    fk.sends++;
    return true;
}

void fake_start(void* ctx, unsigned interface, uint32_t delay_ms) {
    static_cast<void>(ctx);
    static_cast<void>(interface);
    fk.starts++;
    fk.last_delay = delay_ms;
}

void fake_stop(void* ctx, unsigned interface) {
    static_cast<void>(ctx);
    static_cast<void>(interface);
    fk.stops++;
}

void fake_gptp(void* ctx, unsigned interface, uint64_t* gm, uint8_t* domain) {
    static_cast<void>(ctx);
    static_cast<void>(interface);
    *gm = fk.gm;
    *domain = fk.domain;
}

bool fake_link(void* ctx, unsigned interface) {
    static_cast<void>(ctx);
    static_cast<void>(interface);
    return fk.link;
}

uint32_t fake_seed(void* ctx) {
    static_cast<void>(ctx);
    return 0x5EEDu;
}

const struct adp_ports ports = {nullptr, fake_send, fake_start, fake_stop, fake_gptp, fake_link, fake_seed};

void discover(uint8_t* f, uint8_t msg, uint64_t eid) {
    std::memset(f, 0, ADP_FRAME_BYTES);
    wire_put_be(f, 0x91E0F0010000ull, 6);
    wire_put_be(f + 12, ADP_ETHERTYPE, 2);
    f[14] = ADP_SUBTYPE;
    f[15] = msg;
    wire_put_be(f + 18, eid, 8);
}

void fresh(struct adp* a, bool link) {
    std::memset(&fk, 0, sizeof fk);
    fk.room = true;
    fk.link = link;
    fk.gm = 0xA1A2A3A4A5A6A7A8ull;
    adp_init(a, &entity, &ports, 0, 2);
}

void core_schedule(void) {
    struct adp a;
    fresh(&a, false);
    adp_set_enable(&a, true);
    EXPECT_EQ(a.state, ADP_STATE_DOWN) << "A0 enabled with the link down: DOWN (5.6.3.5.1)";
    EXPECT_EQ(fk.starts, 0) << "A0 and no timer";
    adp_link_change(&a, true);
    EXPECT_TRUE(a.state == ADP_STATE_DELAY && a.last_draw == ADP_DRAW_DELAY && fk.last_delay == a.last_draw_ms &&
                fk.last_delay <= ADP_DELAY_MAX_MS)
        << "A0 LINK_UP: DELAY with a 0..4 s draw (5.6.3.5.3)";
    adp_timer_expired(&a);
    EXPECT_TRUE(fk.sends == 1u && fk.last[15] == ADP_MSG_ENTITY_AVAILABLE && a.state == ADP_STATE_WAITING &&
                fk.last_delay == ADP_ADVERTISE_MS)
        << "A1 TMR_DELAY: ENTITY_AVAILABLE, WAITING, TMR_ADVERTISE 5 s (5.6.3.5.9)";
    EXPECT_EQ(wire_be16(fk.last + 16), (10u << 11) | 56u) << "A1 valid_time 10, control_data_length 56";
    EXPECT_EQ(wire_be32(fk.last + 50), 0) << "A1 the first available_index is 0";
    EXPECT_EQ(a.available_index, 1) << "A1 available_index is incremented after the send (6.2.2.15)";
    fk.gm = 0x0102030405060708ull;
    fk.domain = 3;
    adp_timer_expired(&a);
    adp_timer_expired(&a);
    EXPECT_TRUE(fk.sends == 2u && wire_be32(fk.last + 50) == 1u && wire_be64(fk.last + 54) == 0x0102030405060708ull &&
                fk.last[62] == 3u)
        << "A2 the next cycle carries index 1 and the grandmaster sampled at build";
    adp_set_current_configuration(&a, 0x0103);
    adp_gm_change(&a);
    adp_timer_expired(&a);
    EXPECT_EQ(fk.sends, 3) << "A2 GM_CHANGE in WAITING re-advertises (5.6.3.5.7)";
    EXPECT_EQ(wire_be16(fk.last + 64), 0x0103) << "A2 with the new current_configuration_index (6.2.2.18)";
    EXPECT_EQ(wire_be16(fk.last + 66), 5) << "A2 and the entity's identify_control_index (6.2.2.19)";
}

void core_discard(void) {
    struct adp a;
    uint8_t f[ADP_FRAME_BYTES];
    fresh(&a, true);
    adp_set_enable(&a, true);
    EXPECT_TRUE(a.state == ADP_STATE_DELAY && a.last_draw == ADP_DRAW_STARTUP &&
                a.last_draw_ms <= ADP_DELAY_STARTUP_MAX_MS)
        << "A3 enabled with the link up: DELAY with a 0..2 s draw (5.6.3.5.2)";
    discover(f, ADP_MSG_ENTITY_DISCOVER, 0);
    unsigned starts = fk.starts;
    adp_rx(&a, f, sizeof f);
    EXPECT_TRUE(fk.starts == starts && a.discarded == 0u) << "A3 RCV_ADP_DISCOVER in DELAY is ignored (Table 5.51)";
    adp_timer_expired(&a);
    discover(f, ADP_MSG_ENTITY_DISCOVER, 0x7766554433221100ull);
    adp_rx(&a, f, sizeof f);
    discover(f, ADP_MSG_ENTITY_AVAILABLE, 0);
    adp_rx(&a, f, sizeof f);
    adp_rx(&a, f, 25u);
    EXPECT_EQ(a.discarded, 3) << "A4 a foreign DISCOVER, an AVAILABLE and a truncated ADPDU are discarded (5.6.3.1)";
    EXPECT_EQ(a.state, ADP_STATE_WAITING) << "A4 and leave WAITING alone";
    discover(f, ADP_MSG_ENTITY_DISCOVER, entity.entity_id);
    unsigned stops = fk.stops;
    adp_rx(&a, f, sizeof f);
    EXPECT_TRUE(fk.stops == stops + 1u && a.state == ADP_STATE_DELAY && a.last_draw == ADP_DRAW_DELAY)
        << "A4 a DISCOVER for this entity stops TMR_ADVERTISE and enters DELAY (5.6.3.5.4)";
    adp_timer_expired(&a);
    unsigned sends = fk.sends;
    a.timer = ADP_TIMER_NONE;
    adp_timer_expired(&a);
    EXPECT_EQ(a.stray_expiries, 1) << "A5 an expiry with no timer running is a stray, counted";
    EXPECT_EQ(fk.sends, sends) << "A5 and sends nothing";
}

void core_deferred(void) {
    struct adp a;
    fresh(&a, true);
    adp_set_enable(&a, true);
    fk.room = false;
    adp_timer_expired(&a);
    EXPECT_TRUE(a.available_owed && a.state == ADP_STATE_DELAY && a.deferred_sends == 1u)
        << "A6 a refused send keeps ENTITY_AVAILABLE owed in DELAY";
    adp_poll(&a);
    EXPECT_EQ(a.deferred_sends, 2) << "A6 a poll without room retries and keeps it";
    fk.room = true;
    adp_poll(&a);
    EXPECT_TRUE(fk.sends == 1u && a.state == ADP_STATE_WAITING && !a.available_owed &&
                fk.last_delay == ADP_ADVERTISE_MS)
        << "A6 a poll with room sends it and completes 5.6.3.5.9";
    adp_timer_expired(&a);
    fk.room = false;
    adp_timer_expired(&a);
    adp_link_change(&a, false);
    fk.room = true;
    adp_poll(&a);
    EXPECT_TRUE(fk.sends == 1u && a.state == ADP_STATE_DOWN && !a.available_owed && a.departing_owed == 0u)
        << "A7 a link loss drops an owed ENTITY_AVAILABLE and departs nothing (5.6.3.5.10)";
    adp_link_change(&a, true);
    adp_timer_expired(&a);
    uint32_t index = a.available_index;
    fk.room = false;
    adp_set_enable(&a, false);
    EXPECT_TRUE(a.departing_owed == 1u && a.available_index == 0u && a.state == ADP_STATE_DOWN)
        << "A8 SHUTDOWN with no room keeps ENTITY_DEPARTING owed, index reset";
    adp_link_change(&a, false);
    fk.room = true;
    adp_poll(&a);
    EXPECT_TRUE(fk.last[15] == ADP_MSG_ENTITY_DEPARTING && wire_be32(fk.last + 50) == index &&
                wire_be16(fk.last + 16) == 56u)
        << "A8 a link loss does not drop it; the next poll sends it with the index current at SHUTDOWN";
    unsigned sends = fk.sends;
    fk.link = false;
    adp_set_enable(&a, true);
    adp_set_enable(&a, false);
    EXPECT_EQ(fk.sends, sends) << "A8 SHUTDOWN in DOWN sends nothing (Table 5.51)";
}

// IEEE 1722.1-2021 6.2.2.15 with Figures 6-2 and 6-3 and 6.2.5.2.2 (the
// ruling on PR #668, comment 5994972330): ENTITY_DEPARTING carries the
// CURRENT available_index, and the first ENTITY_AVAILABLE after a restart
// carries 0. Every value below is read off the frame the port was given.
uint32_t wire_index(void) {
    return wire_be32(fk.last + 50);
}

bool wire_is(uint8_t msg, uint32_t index) {
    return (fk.last[15] & 0x0Fu) == msg && wire_index() == index;
}

void core_departing_index(void) {
    struct adp a;
    fresh(&a, true);
    adp_set_enable(&a, true);
    adp_timer_expired(&a);
    EXPECT_TRUE(wire_is(ADP_MSG_ENTITY_AVAILABLE, 0)) << "A10 the first ENTITY_AVAILABLE carries 0";
    adp_timer_expired(&a);
    adp_timer_expired(&a);
    EXPECT_TRUE(wire_is(ADP_MSG_ENTITY_AVAILABLE, 1)) << "A10 the second carries 1";
    EXPECT_EQ(a.state, ADP_STATE_WAITING) << "A10 SHUTDOWN is taken in WAITING";
    adp_set_enable(&a, false);
    EXPECT_TRUE(wire_is(ADP_MSG_ENTITY_DEPARTING, 2))
        << "A10 SHUTDOWN in WAITING, sent at once: ENTITY_DEPARTING carries the current index, 2";
    adp_set_enable(&a, true);
    adp_timer_expired(&a);
    EXPECT_TRUE(wire_is(ADP_MSG_ENTITY_AVAILABLE, 0)) << "A11 the first ENTITY_AVAILABLE after a restart carries 0";
    adp_timer_expired(&a);
    EXPECT_EQ(a.state, ADP_STATE_DELAY) << "A12 SHUTDOWN is taken in DELAY";
    adp_set_enable(&a, false);
    EXPECT_TRUE(wire_is(ADP_MSG_ENTITY_DEPARTING, 1))
        << "A12 SHUTDOWN in DELAY, sent at once: ENTITY_DEPARTING carries the current index, 1";
    adp_set_enable(&a, true);
    adp_timer_expired(&a);
    adp_timer_expired(&a);
    adp_timer_expired(&a);
    fk.room = false;
    adp_set_enable(&a, false);
    EXPECT_TRUE(a.departing_owed == 1u) << "A13 SHUTDOWN with no room leaves ENTITY_DEPARTING owed";
    fk.room = true;
    adp_poll(&a);
    EXPECT_TRUE(wire_is(ADP_MSG_ENTITY_DEPARTING, 2))
        << "A13 sent from a later poll, it carries the index current at SHUTDOWN, 2";
    adp_set_enable(&a, true);
    adp_timer_expired(&a);
    EXPECT_TRUE(wire_is(ADP_MSG_ENTITY_AVAILABLE, 0)) << "A13 and the restart's first ENTITY_AVAILABLE carries 0";
    adp_timer_expired(&a);
    a.available_index = 0xFFFFFFFFu;
    adp_timer_expired(&a);
    EXPECT_TRUE(wire_is(ADP_MSG_ENTITY_AVAILABLE, 0xFFFFFFFFu)) << "A14 available_index 0xFFFFFFFF goes on the wire";
    adp_timer_expired(&a);
    adp_timer_expired(&a);
    EXPECT_TRUE(wire_is(ADP_MSG_ENTITY_AVAILABLE, 0)) << "A14 the next ENTITY_AVAILABLE carries 0, modulo 2^32";
    adp_set_enable(&a, false);
    EXPECT_TRUE(wire_is(ADP_MSG_ENTITY_DEPARTING, 1))
        << "A14 SHUTDOWN after the wrap: ENTITY_DEPARTING carries the current index, 1";
}

// The frame the fake took k-th is `msg` carrying `index`.
bool took(unsigned k, uint8_t msg, uint32_t index) {
    return k < fk.sends && k < 16u && fk.msg[k] == msg && fk.index[k] == index;
}

// One ENTITY_AVAILABLE sent (index 0, so 1 is current), then SHUTDOWN behind
// a full transmit path: ENTITY_DEPARTING owed with index 1. Then a restart.
void advertise_then_depart_owed(struct adp* a) {
    fresh(a, true);
    adp_set_enable(a, true);
    adp_timer_expired(a);
    fk.room = false;
    adp_set_enable(a, false);
    adp_set_enable(a, true);
}

// R497-2-F1: an owed ENTITY_DEPARTING is never lost to a restart. It keeps
// its SHUTDOWN index and leaves before the restart's ENTITY_AVAILABLE.
void core_owed_departing(void) {
    struct adp a;
    advertise_then_depart_owed(&a);
    EXPECT_TRUE(took(0, ADP_MSG_ENTITY_AVAILABLE, 0) && fk.sends == 1u && a.departing_owed == 1u &&
                a.departing_index == 1u)
        << "A15 advertised once, SHUTDOWN behind a full ring: ENTITY_DEPARTING owed with index 1";
    EXPECT_TRUE(a.state == ADP_STATE_DELAY && a.timer == ADP_TIMER_DELAY && a.last_draw == ADP_DRAW_STARTUP)
        << "A15 the restart runs while it is owed: DELAY, the startup TMR_DELAY armed";
    unsigned starts = fk.starts;
    adp_timer_expired(&a);
    EXPECT_TRUE(a.available_owed && a.departing_owed == 1u && a.departing_index == 1u && a.state == ADP_STATE_DELAY &&
                a.timer == ADP_TIMER_NONE && fk.starts == starts && fk.sends == 1u)
        << "A15 that TMR_DELAY expires before the ring has room: ENTITY_AVAILABLE owed behind it, no timer";
    EXPECT_TRUE(adp_poll(&a) && a.available_owed && a.departing_owed == 1u && fk.sends == 1u)
        << "A15 a poll without room keeps both owed";
    fk.room = true;
    EXPECT_TRUE(adp_poll(&a) && fk.sends == 2u && took(1, ADP_MSG_ENTITY_DEPARTING, 1))
        << "A15 with room, the next poll sends the owed ENTITY_DEPARTING first, with its SHUTDOWN index 1";
    EXPECT_TRUE(!adp_poll(&a) && fk.sends == 3u && took(2, ADP_MSG_ENTITY_AVAILABLE, 0))
        << "A15 and the one after it the restart's ENTITY_AVAILABLE, with index 0";
    EXPECT_TRUE(a.state == ADP_STATE_WAITING && a.timer == ADP_TIMER_ADVERTISE && fk.starts == starts + 1u &&
                fk.last_delay == ADP_ADVERTISE_MS && a.available_index == 1u)
        << "A15 then WAITING with TMR_ADVERTISE armed 5 s, available_index 1";
    EXPECT_TRUE(!a.available_owed && a.departing_owed == 0u && !adp_poll(&a) && fk.sends == 3u)
        << "A15 and nothing stranded: nothing owed, a further poll sends nothing";
    adp_timer_expired(&a);
    adp_timer_expired(&a);
    EXPECT_TRUE(fk.sends == 4u && took(3, ADP_MSG_ENTITY_AVAILABLE, 1))
        << "A15 the schedule runs on: the next ENTITY_AVAILABLE carries 1";
}

// A second SHUTDOWN while the first DEPARTING is owed queues its own.
void core_owed_second_shutdown(void) {
    struct adp a;
    advertise_then_depart_owed(&a);
    adp_timer_expired(&a);
    adp_set_enable(&a, false);
    EXPECT_TRUE(a.departing_owed == 2u && a.departing_index == 1u && !a.available_owed && a.state == ADP_STATE_DOWN)
        << "A16 a SHUTDOWN while one is owed queues its own ENTITY_DEPARTING and drops the owed AVAILABLE";
    adp_set_enable(&a, true);
    fk.room = true;
    static_cast<void>(adp_poll(&a));
    bool owed = adp_poll(&a);
    EXPECT_TRUE(fk.sends == 3u && took(1, ADP_MSG_ENTITY_DEPARTING, 1) && took(2, ADP_MSG_ENTITY_DEPARTING, 0) && !owed)
        << "A16 each leaves in order with its SHUTDOWN's index: 1, then 0 (that run sent nothing)";
    EXPECT_TRUE(a.state == ADP_STATE_DELAY && a.timer == ADP_TIMER_DELAY && !a.available_owed)
        << "A16 the restart running meanwhile is untouched: DELAY, its TMR_DELAY armed";
    adp_timer_expired(&a);
    EXPECT_TRUE(fk.sends == 4u && took(3, ADP_MSG_ENTITY_AVAILABLE, 0) && a.state == ADP_STATE_WAITING)
        << "A16 its ENTITY_AVAILABLE, with index 0, leaves at its TMR_DELAY expiry; WAITING";
}

// Room returns, and the restart's TMR_DELAY expires before any poll.
void core_owed_room_first(void) {
    struct adp a;
    advertise_then_depart_owed(&a);
    fk.room = true;
    adp_timer_expired(&a);
    EXPECT_TRUE(fk.sends == 1u && a.available_owed && a.departing_owed == 1u && a.state == ADP_STATE_DELAY)
        << "A17 room back and TMR_DELAY expiring before a poll: the ENTITY_AVAILABLE does not pass the owed DEPARTING";
    static_cast<void>(adp_poll(&a));
    bool owed = adp_poll(&a);
    EXPECT_TRUE(fk.sends == 3u && took(1, ADP_MSG_ENTITY_DEPARTING, 1) && took(2, ADP_MSG_ENTITY_AVAILABLE, 0) &&
                !owed && a.state == ADP_STATE_WAITING)
        << "A17 the polls then send DEPARTING with index 1 and AVAILABLE with index 0, in that order";
}

// R496-3-F2: the legs of the owed-frame rule (adp.h) A15 to A17 leave open.
// A link loss while the restart runs, before and after its TMR_DELAY expiry.
void core_owed_link_loss(void) {
    struct adp a;
    advertise_then_depart_owed(&a);
    adp_link_change(&a, false);
    EXPECT_TRUE(a.state == ADP_STATE_DOWN && a.timer == ADP_TIMER_NONE && a.departing_owed == 1u &&
                a.departing_index == 1u && fk.sends == 1u)
        << "A18 a link loss during the restart stops it and keeps the owed ENTITY_DEPARTING, index 1";
    adp_link_change(&a, true);
    EXPECT_TRUE(a.state == ADP_STATE_DELAY && a.timer == ADP_TIMER_DELAY && a.last_draw == ADP_DRAW_DELAY &&
                a.departing_owed == 1u && a.departing_index == 1u)
        << "A18 the link's return starts a new run with the ENTITY_DEPARTING still owed (5.6.3.5.3)";
    adp_timer_expired(&a);
    adp_link_change(&a, false);
    EXPECT_TRUE(a.state == ADP_STATE_DOWN && !a.available_owed && a.departing_owed == 1u && a.departing_index == 1u &&
                fk.sends == 1u)
        << "A18 a link loss with that run's ENTITY_AVAILABLE owed drops the AVAILABLE and keeps the DEPARTING";
    adp_link_change(&a, true);
    fk.room = true;
    bool owed = adp_poll(&a);
    EXPECT_TRUE(!owed && fk.sends == 2u && took(1, ADP_MSG_ENTITY_DEPARTING, 1))
        << "A18 with room the ENTITY_DEPARTING leaves, index 1";
    adp_timer_expired(&a);
    EXPECT_TRUE(fk.sends == 3u && took(2, ADP_MSG_ENTITY_AVAILABLE, 0) && a.state == ADP_STATE_WAITING)
        << "A18 then the new run's ENTITY_AVAILABLE, index 0, at its TMR_DELAY expiry; WAITING";
}

// Inputs that leave an owed ENTITY_AVAILABLE owed: Milan v1.2 Table 5.51
// ignores GM_CHANGE and RCV_ADP_DISCOVER in DELAY, and a stray is no input.
void core_owed_inputs_ignored(void) {
    struct adp a;
    uint8_t f[ADP_FRAME_BYTES];
    fresh(&a, true);
    adp_set_enable(&a, true);
    fk.room = false;
    adp_timer_expired(&a);
    unsigned starts = fk.starts;
    adp_gm_change(&a);
    EXPECT_TRUE(a.available_owed && a.state == ADP_STATE_DELAY && a.timer == ADP_TIMER_NONE && fk.starts == starts)
        << "A19 a GM change in DELAY leaves the owed ENTITY_AVAILABLE owed, no timer started";
    discover(f, ADP_MSG_ENTITY_DISCOVER, 0);
    adp_rx(&a, f, sizeof f);
    EXPECT_TRUE(a.available_owed && a.state == ADP_STATE_DELAY && a.timer == ADP_TIMER_NONE && fk.starts == starts)
        << "A19 so does an ENTITY_DISCOVER";
    adp_timer_expired(&a);
    EXPECT_TRUE(a.available_owed && a.stray_expiries == 1u && a.state == ADP_STATE_DELAY && fk.sends == 0u)
        << "A19 and a stray expiry, which is counted";
    fk.room = true;
    bool owed = adp_poll(&a);
    EXPECT_TRUE(!owed && fk.sends == 1u && took(0, ADP_MSG_ENTITY_AVAILABLE, 0) && a.state == ADP_STATE_WAITING &&
                a.timer == ADP_TIMER_ADVERTISE && fk.last_delay == ADP_ADVERTISE_MS)
        << "A19 the next poll with room sends it, index 0, then WAITING with TMR_ADVERTISE 5 s";
}

// A link loss itself drops an owed ENTITY_AVAILABLE, with no poll between.
void core_owed_link_loss_drops(void) {
    struct adp a;
    fresh(&a, true);
    adp_set_enable(&a, true);
    fk.room = false;
    adp_timer_expired(&a);
    adp_link_change(&a, false);
    EXPECT_TRUE(!a.available_owed && a.state == ADP_STATE_DOWN && a.departing_owed == 0u)
        << "A20 a link loss drops the owed ENTITY_AVAILABLE at once, before any poll (5.6.3.5.10)";
    adp_link_change(&a, true);
    fk.room = true;
    bool owed = adp_poll(&a);
    EXPECT_TRUE(!owed && fk.sends == 0u && a.state == ADP_STATE_DELAY && a.timer == ADP_TIMER_DELAY &&
                a.last_draw == ADP_DRAW_DELAY)
        << "A20 after the link's return a poll sends nothing: the new run waits for its TMR_DELAY (5.6.3.5.3)";
    adp_timer_expired(&a);
    EXPECT_TRUE(fk.sends == 1u && took(0, ADP_MSG_ENTITY_AVAILABLE, 0) && a.state == ADP_STATE_WAITING)
        << "A20 whose expiry sends the ENTITY_AVAILABLE, index 0; WAITING";
}

// R497-3-F1: at most ADP_DEPARTING_OWED_MAX DEPARTINGs are owed; a SHUTDOWN
// beyond them is coalesced into the queued one and counted (adp.h).
void core_departing_capacity(void) {
    struct adp a;
    advertise_then_depart_owed(&a);
    adp_timer_expired(&a);
    adp_set_enable(&a, false);
    EXPECT_TRUE(a.departing_owed == ADP_DEPARTING_OWED_MAX && a.departing_owed == 2u && a.departing_index == 1u &&
                a.departing_coalesced == 0u)
        << "A21 a second SHUTDOWN takes the last place: two owed, the oldest with index 1, none coalesced";
    adp_set_enable(&a, true);
    adp_timer_expired(&a);
    adp_set_enable(&a, false);
    EXPECT_TRUE(a.departing_owed == 2u && a.departing_index == 1u && a.departing_coalesced == 1u && !a.available_owed &&
                a.state == ADP_STATE_DOWN && fk.sends == 1u)
        << "A21 the next SHUTDOWN is coalesced into the queued one and counted; its run's owed AVAILABLE is dropped";
    for (unsigned k = 0; k < 100000u; ++k) {
        adp_set_enable(&a, true);
        adp_set_enable(&a, false);
    }
    EXPECT_TRUE(a.departing_owed == 2u && a.departing_index == 1u && a.departing_coalesced == 100001u && fk.sends == 1u)
        << "A21 and so are 100000 more, each counted, the two owed unchanged";
    adp_set_enable(&a, true);
    fk.room = true;
    static_cast<void>(adp_poll(&a));
    bool owed = adp_poll(&a);
    EXPECT_TRUE(fk.sends == 3u && took(1, ADP_MSG_ENTITY_DEPARTING, 1) && took(2, ADP_MSG_ENTITY_DEPARTING, 0) &&
                !owed && !adp_poll(&a) && fk.sends == 3u)
        << "A21 with room the wire carries DEPARTING 1, then one DEPARTING 0, and nothing more is owed";
    adp_timer_expired(&a);
    EXPECT_TRUE(fk.sends == 4u && took(3, ADP_MSG_ENTITY_AVAILABLE, 0) && a.state == ADP_STATE_WAITING)
        << "A21 then the running restart's ENTITY_AVAILABLE, index 0, at its TMR_DELAY expiry; WAITING";
}

void core_draws(void) {
    struct adp a;
    fresh(&a, true);
    uint32_t max_start = 0;
    uint32_t max_delay = 0;
    bool in_range = true;
    for (unsigned k = 0; k < 400u; ++k) {
        adp_set_enable(&a, true);
        in_range = in_range && a.last_draw == ADP_DRAW_STARTUP && a.last_draw_ms <= ADP_DELAY_STARTUP_MAX_MS;
        max_start = a.last_draw_ms > max_start ? a.last_draw_ms : max_start;
        adp_link_change(&a, false);
        adp_link_change(&a, true);
        in_range = in_range && a.last_draw == ADP_DRAW_DELAY && a.last_draw_ms <= ADP_DELAY_MAX_MS;
        max_delay = a.last_draw_ms > max_delay ? a.last_draw_ms : max_delay;
        adp_set_enable(&a, false);
    }
    EXPECT_TRUE(in_range) << "A9 every startup draw is 0..2 s and every other draw 0..4 s";
    EXPECT_TRUE(max_delay > ADP_DELAY_STARTUP_MAX_MS) << "A9 the two kinds are distinct: the 0..4 s draws pass 2 s";
    EXPECT_TRUE(max_start > 1800u && max_delay > 3600u) << "A9 and both reach near their maxima";
}

TEST(AdpCore, A0toA2Schedule) {
    core_schedule();
}
TEST(AdpCore, A3toA5DiscoverAndDiscard) {
    core_discard();
}
TEST(AdpCore, A6toA8DeferredSends) {
    core_deferred();
}
TEST(AdpCore, A9DrawKinds) {
    core_draws();
}
TEST(AdpCore, A10toA14DepartingIndex) {
    core_departing_index();
}
TEST(AdpCore, A15OwedDepartingAcrossARestart) {
    core_owed_departing();
}
TEST(AdpCore, A16SecondShutdownQueuesItsOwn) {
    core_owed_second_shutdown();
}
TEST(AdpCore, A17RoomBackBeforeAPoll) {
    core_owed_room_first();
}
TEST(AdpCore, A18LinkLossKeepsTheOwedDeparting) {
    core_owed_link_loss();
}
TEST(AdpCore, A19IgnoredInputsKeepTheOwedAvailable) {
    core_owed_inputs_ignored();
}
TEST(AdpCore, A20LinkLossDropsTheOwedAvailable) {
    core_owed_link_loss_drops();
}
TEST(AdpCore, A21DepartingCapacity) {
    core_departing_capacity();
}

} // namespace
