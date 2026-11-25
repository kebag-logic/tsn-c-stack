// SPDX-FileCopyrightText: 2026 Kebag Logic
// SPDX-License-Identifier: MIT

#include <gtest/gtest.h>
#include <gmock/gmock.h>

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <tuple>
#include <vector>

#include <sys/mman.h>
#include <unistd.h>

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
    uint8_t msg[16];
    uint32_t index[16];
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
    wire_put_be(f + 16, 56u, 2);
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
    const uint32_t draws = a.draws;
    adp_gm_change(&a);
    EXPECT_TRUE(a.state == ADP_STATE_DELAY && a.draws == draws + 1u && a.last_draw == ADP_DRAW_DELAY &&
                fk.last_delay == a.last_draw_ms && fk.last_delay <= 4000u)
        << "A2 GM_CHANGE in WAITING: DELAY with a 0..4 s draw (5.6.3.5.7)";
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

// IEEE 1722.1-2021 6.2.2.15
// IEEE 1722.1-2021 Figure 6-2 and 6-3
// IEEE 1722.1-2021 6.2.5.2.2

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

bool took(unsigned k, uint8_t msg, uint32_t index) {
    return k < fk.sends && k < 16u && fk.msg[k] == msg && fk.index[k] == index;
}

void advertise_then_depart_owed(struct adp* a) {
    fresh(a, true);
    adp_set_enable(a, true);
    adp_timer_expired(a);
    fk.room = false;
    adp_set_enable(a, false);
    adp_set_enable(a, true);
}

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

// Milan v1.2 Table 5.51

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

uint32_t seed_value;
unsigned seed_calls;

uint32_t chosen_seed(void* ctx) {
    static_cast<void>(ctx);
    ++seed_calls;
    return seed_value;
}

const adp_ports chosen = {nullptr, fake_send, fake_start, fake_stop, fake_gptp, fake_link, chosen_seed};

struct Boot {
    adp_entity e = entity;
    unsigned interface = 0;
    uint32_t sample = 0;
    bool startup = false;
};

adp first_draw(const Boot& b) {
    adp a;
    fresh(&a, b.startup);
    adp_init(&a, &b.e, &chosen, b.interface, 0);
    seed_value = b.sample;
    adp_set_enable(&a, true);
    if (!b.startup) {
        adp_link_change(&a, true);
    }
    return a;
}

uint32_t chi_square_x16(const std::vector<uint32_t>& draws, uint32_t max_ms) {
    uint32_t bins[16] = {};
    for (const auto ms : draws) {
        const uint32_t bin = (ms * 16u) / (max_ms + 1u);
        ++bins[bin < 16u ? bin : 15u];
    }
    const auto expected = static_cast<uint32_t>(draws.size() / 16u);
    uint32_t sum = 0;
    for (const auto n : bins) {
        const uint32_t d = n > expected ? n - expected : expected - n;
        sum += d * d;
    }
    return (sum * 16u) / expected;
}

constexpr uint32_t kChiSquareX16 = 490;
constexpr uint32_t kHosts = 4096;

void core_rng_never_zero(void) {
    Boot b;
    b.startup = true;
    b.sample = 0xDE81995Cu;
    const adp a = first_draw(b);
    EXPECT_EQ(a.rng, 0x42021u) << "A22 a seed that mixes to zero starts the generator at 1";
    EXPECT_TRUE(a.state == ADP_STATE_DELAY && a.draws == 1u) << "A22 and the startup draw is made";
}

void core_uniform_over_samples(void) {
    for (const bool startup : {false, true}) {
        const uint32_t max_ms = startup ? 2000u : 4000u;
        for (const uint32_t step : {1u, 1000u}) {
            std::vector<uint32_t> draws;
            for (uint32_t k = 0; k < kHosts; ++k) {
                Boot b;
                b.startup = startup;
                b.sample = 40000u + k * step;
                draws.push_back(first_draw(b).last_draw_ms);
            }
            EXPECT_LE(chi_square_x16(draws, max_ms), kChiSquareX16)
                << "A25 one host's first draws over neighbouring samples are uniform (6.2.4.2.2)";
        }
    }
}

void core_uniform_over_hosts(void) {
    for (const bool startup : {false, true}) {
        const uint32_t max_ms = startup ? 2000u : 4000u;
        for (const uint32_t sample : {0u, 40000u}) {
            std::vector<uint32_t> draws;
            for (uint32_t k = 0; k < kHosts; ++k) {
                Boot b;
                b.startup = startup;
                b.sample = sample;
                b.e.mac = 0x001B92112000ull + k;
                b.e.entity_id = 0x001B92FFFE112000ull + k;
                draws.push_back(first_draw(b).last_draw_ms);
            }
            EXPECT_LE(chi_square_x16(draws, max_ms), kChiSquareX16)
                << "A26 neighbouring hosts started together draw uniformly (6.2.4.2.2)";
        }
    }
}

void core_seed_terms(void) {
    for (const bool startup : {false, true}) {
        Boot b;
        b.startup = startup;
        b.sample = 40000u;
        const uint32_t base = first_draw(b).rng;
        Boot other = b;
        other.interface = 1;
        EXPECT_NE(first_draw(other).rng, base) << "A27 two interfaces sampled together draw apart";
        other = b;
        other.e.entity_id ^= 1u;
        EXPECT_NE(first_draw(other).rng, base) << "A27 the low word of the entity ID is mixed in";
        other = b;
        other.e.entity_id ^= 1ull << 32;
        EXPECT_NE(first_draw(other).rng, base) << "A27 the high word of the entity ID is mixed in";
        other = b;
        other.e.mac += 1u;
        EXPECT_NE(first_draw(other).rng, base) << "A27 the MAC address is in the seed";
        other.sample -= 1u;
        EXPECT_EQ(first_draw(other).rng, base) << "A27 the seed is the sum of MAC address and clock (6.2.4.2.2)";
        Boot wrapped = b;
        wrapped.e.mac = 0xFFFFFFFFull;
        wrapped.sample = 5u;
        Boot carried = b;
        carried.e.mac = 0;
        carried.sample = 5u;
        EXPECT_EQ(first_draw(wrapped).rng, first_draw(carried).rng) << "A27 the sum carries end around (6.2.4.2.2)";
    }
}

void core_fresh_sample(void) {
    Boot b;
    b.sample = 40000u;
    seed_calls = 0;
    adp a = first_draw(b);
    EXPECT_EQ(seed_calls, 1u) << "A28 one sample is taken at LINK_UP and none with the link down";
    adp_timer_expired(&a);
    adp_gm_change(&a);
    adp_timer_expired(&a);
    adp_timer_expired(&a);
    EXPECT_EQ(a.state, ADP_STATE_DELAY);
    EXPECT_EQ(seed_calls, 1u) << "A28 a draw outside DOWN takes no sample";
    adp_link_change(&a, false);
    adp later = a;
    adp same = a;
    adp_link_change(&a, true);
    EXPECT_EQ(seed_calls, 2u) << "A28 the next LINK_UP takes a fresh sample";
    adp_link_change(&same, true);
    EXPECT_EQ(same.rng, a.rng);
    seed_value += 1u;
    adp_link_change(&later, true);
    EXPECT_NE(later.rng, a.rng) << "A28 the next LINK_UP mixes its sample in";
    b.startup = true;
    seed_calls = 0;
    adp on = first_draw(b);
    EXPECT_EQ(seed_calls, 1u) << "A28 one sample is taken at startup with the link up";
    const uint32_t first = on.rng;
    adp_link_change(&on, false);
    adp_link_change(&on, true);
    adp_link_change(&on, false);
    const uint32_t second = on.rng;
    adp_link_change(&on, true);
    EXPECT_TRUE(second != first && on.rng != second) << "A28 a stopped clock does not repeat the state";
}

void core_samples_per_rise(void) {
    adp a;
    adp other;
    fresh(&a, false);
    adp_init(&a, &entity, &chosen, 0, 0);
    adp_init(&other, &entity, &chosen, 1, 0);
    seed_value = 40000u;
    seed_calls = 0;
    adp_set_enable(&a, true);
    adp_set_enable(&other, true);
    EXPECT_EQ(seed_calls, 0u) << "A30 an enable with the link down takes no sample";
    for (unsigned rise = 1; rise <= 3u; ++rise) {
        const uint32_t draws = a.draws;
        adp_link_change(&a, true);
        EXPECT_TRUE(seed_calls == rise && a.draws == draws + 1u) << "A30 each qualified LINK_UP takes one sample";
        adp_link_change(&a, true);
        EXPECT_TRUE(seed_calls == rise && a.draws == draws + 1u) << "A30 a duplicate LINK_UP takes no sample";
        adp_link_change(&a, false);
    }
    const uint32_t untouched = other.rng;
    adp_link_change(&other, true);
    EXPECT_TRUE(seed_calls == 4u && other.rng != untouched && other.last_draw == ADP_DRAW_DELAY)
        << "A30 the other interface's LINK_UP takes its own sample";
    adp_set_enable(&a, false);
    adp_link_change(&a, true);
    adp_link_change(&a, false);
    EXPECT_EQ(seed_calls, 4u) << "A30 a LINK_UP while disabled takes no sample";
    adp_link_change(&a, true);
    fk.link = true;
    adp_set_enable(&a, true);
    EXPECT_TRUE(seed_calls == 5u && a.last_draw == ADP_DRAW_STARTUP) << "A30 the startup draw takes one sample";
}

void core_link_time_sample(void) {
    for (const bool startup : {false, true}) {
        std::vector<uint32_t> first;
        for (uint32_t k = 0; k < kHosts; ++k) {
            Boot b;
            b.startup = startup;
            b.sample = 40000u;
            adp a = first_draw(b);
            if (startup) {
                adp_link_change(&a, false);
            }
            seed_value = 90000u + k;
            adp_link_change(&a, startup);
            if (!startup) {
                adp_link_change(&a, false);
                adp_link_change(&a, true);
            }
            first.push_back(a.last_draw_ms);
        }
        std::vector<uint32_t> sorted = first;
        std::sort(sorted.begin(), sorted.end());
        const auto distinct = static_cast<uint32_t>(std::unique(sorted.begin(), sorted.end()) - sorted.begin());
        EXPECT_GE(distinct, 2400u) << "A31 boots that differ only in the sample at a LINK_UP draw apart";
        EXPECT_LE(chi_square_x16(first, 4000u), kChiSquareX16)
            << "A31 and draw uniformly from the sample taken at that LINK_UP";
    }
}

using Columns = std::vector<uint32_t>;

uint32_t times(const Columns& m, uint32_t x) {
    uint32_t y = 0;
    for (unsigned k = 0; k < 32u; ++k) {
        if ((x >> k & 1u) != 0u) {
            y ^= m[k];
        }
    }
    return y;
}

Columns power(Columns m, uint32_t n) {
    Columns r;
    for (unsigned k = 0; k < 32u; ++k) {
        r.push_back(1u << k);
    }
    for (; n != 0u; n >>= 1) {
        if ((n & 1u) != 0u) {
            for (auto& c : r) {
                c = times(m, c);
            }
        }
        Columns squared;
        for (const auto c : m) {
            squared.push_back(times(m, c));
        }
        m = squared;
    }
    return r;
}

uint32_t step_from(uint32_t state) {
    adp a;
    fresh(&a, true);
    adp_set_enable(&a, true);
    adp_timer_expired(&a);
    a.rng = state;
    adp_gm_change(&a);
    return a.rng;
}

void core_period(void) {
    Columns m;
    for (unsigned k = 0; k < 32u; ++k) {
        m.push_back(step_from(1u << k));
    }
    EXPECT_EQ(step_from(0xC0000001u), step_from(0xC0000000u) ^ step_from(1u)) << "A29 one draw is one linear step";
    const Columns identity = power(m, 0);
    EXPECT_EQ(power(m, 0xFFFFFFFFu), identity) << "A29 the sequence returns after 2^32 - 1 draws";
    for (const uint32_t prime : {3u, 5u, 17u, 257u, 65537u}) {
        EXPECT_NE(power(m, 0xFFFFFFFFu / prime), identity) << "A29 and not before: its length is 2^32 - 1 (6.2.4.2.2)";
    }
}

void core_enable_idempotent(void) {
    struct adp a;
    fresh(&a, true);
    adp_set_enable(&a, false);
    EXPECT_TRUE(fk.sends == 0u && fk.stops == 0u && a.state == ADP_STATE_DOWN)
        << "A23 a disable while disabled sends and stops nothing";
    adp_set_enable(&a, true);
    const unsigned draws = a.draws;
    const unsigned starts = fk.starts;
    adp_set_enable(&a, true);
    EXPECT_TRUE(a.draws == draws && fk.starts == starts && a.state == ADP_STATE_DELAY)
        << "A23 an enable while enabled draws and arms nothing";
}

// Milan v1.2 5.6.3.1

void core_discard_kinds(void) {
    struct adp a;
    uint8_t f[ADP_FRAME_BYTES];
    fresh(&a, true);
    adp_set_enable(&a, true);
    adp_timer_expired(&a);
    discover(f, ADP_MSG_ENTITY_DISCOVER, 0);
    wire_put_be(f + 12, 0x88F5u, 2);
    adp_rx(&a, f, sizeof f);
    discover(f, ADP_MSG_ENTITY_DISCOVER, 0);
    f[ADP_HEADER_BYTES] = 0xFCu;
    adp_rx(&a, f, sizeof f);
    EXPECT_EQ(a.discarded, 2u) << "A24 a DISCOVER under another EtherType or subtype is discarded and counted";
    EXPECT_EQ(a.state, ADP_STATE_WAITING) << "A24 and leaves WAITING alone";
}

// REQ: ADP-02, PORT-01, MFDISC-01, MFDISC-04, MFRECOVERY-01
TEST(AdpCore, A0toA2Schedule) {
    core_schedule();
}
// REQ: ADP-01, ADP-02, MFDISC-02
TEST(AdpCore, A3toA5DiscoverAndDiscard) {
    core_discard();
}
// REQ: ADP-03, ADP-02
TEST(AdpCore, A6toA8DeferredSends) {
    core_deferred();
}
// REQ: ADP-02, PORT-01, MFDISC-01
TEST(AdpCore, A9DrawKinds) {
    core_draws();
}
// REQ: ADP-03, ADP-02, MFDISC-01, MFDISC-03
TEST(AdpCore, A10toA14DepartingIndex) {
    core_departing_index();
}
// REQ: ADP-03, ADP-02, MFDISC-03
TEST(AdpCore, A15OwedDepartingAcrossARestart) {
    core_owed_departing();
}
// REQ: ADP-03, ADP-02
TEST(AdpCore, A16SecondShutdownQueuesItsOwn) {
    core_owed_second_shutdown();
}
// REQ: ADP-03, ADP-02
TEST(AdpCore, A17RoomBackBeforeAPoll) {
    core_owed_room_first();
}
// REQ: ADP-03, ADP-02, MFDISC-03
TEST(AdpCore, A18LinkLossKeepsTheOwedDeparting) {
    core_owed_link_loss();
}
// REQ: ADP-03, ADP-02
TEST(AdpCore, A19IgnoredInputsKeepTheOwedAvailable) {
    core_owed_inputs_ignored();
}
// REQ: ADP-03, ADP-02, MFDISC-03
TEST(AdpCore, A20LinkLossDropsTheOwedAvailable) {
    core_owed_link_loss_drops();
}
// REQ: ADP-03, ADP-02
TEST(AdpCore, A21DepartingCapacity) {
    core_departing_capacity();
}
// REQ: ADP-02, PORT-01
TEST(AdpCore, A22GeneratorNeverStuckAtZero) { core_rng_never_zero(); }
// REQ: ADP-02, PORT-01
TEST(AdpCore, A23RepeatedEnableOrDisableChangesNothing) { core_enable_idempotent(); }
// REQ: ADP-01, ADP-02
TEST(AdpCore, A24OtherEtherTypeOrSubtypeDiscarded) { core_discard_kinds(); }
// REQ: ADP-02, PORT-01, MFDISC-01
TEST(AdpCore, A25FirstDrawsAreUniformOverSamples) { core_uniform_over_samples(); }
// REQ: ADP-02, PORT-01, MFDISC-01
TEST(AdpCore, A26NeighbouringHostsDrawUniformly) { core_uniform_over_hosts(); }
// REQ: ADP-02, PORT-01
TEST(AdpCore, A27EverySeedTermIsMixedIn) { core_seed_terms(); }
// REQ: ADP-02, PORT-01
TEST(AdpCore, A28EachLeaveOfDownTakesAFreshSample) { core_fresh_sample(); }
// REQ: ADP-02
TEST(AdpCore, A29SequenceIsOfMaximumLength) { core_period(); }
// REQ: ADP-02, PORT-01, MFDISC-01
TEST(AdpCore, A30EachQualifiedRiseTakesOneSample) { core_samples_per_rise(); }
// REQ: ADP-02, PORT-01, MFDISC-01
TEST(AdpCore, A31TheLinkUpsSampleSetsItsDraw) { core_link_time_sample(); }

// REQ: ADP-02, PORT-01, MFDISC-03, MFRECOVERY-01
TEST(AdpCore, LinkLevelsAndDisabledInputs) {
    adp a;
    uint8_t f[ADP_FRAME_BYTES];
    fresh(&a, true);
    discover(f, ADP_MSG_ENTITY_DISCOVER, 0);
    adp_rx(&a, f, sizeof f);
    adp_gm_change(&a);
    EXPECT_EQ(fk.sends, 0u);
    EXPECT_EQ(fk.starts, 0u);
    adp_set_enable(&a, true);
    const auto starts = fk.starts;
    adp_link_change(&a, true);
    EXPECT_EQ(fk.starts, starts) << "duplicate link level keeps the timer";
    adp_link_change(&a, false);
    EXPECT_EQ(a.state, ADP_STATE_DOWN);
    adp_rx(&a, f, sizeof f);
    EXPECT_EQ(a.state, ADP_STATE_DOWN) << "DOWN ignores discovery";
    adp_set_enable(&a, false);
    EXPECT_EQ(fk.sends, 0u) << "shutdown in DOWN sends nothing";
}

// REQ: ADP-01, ADP-02, MFDISC-04
TEST(AdpCore, EntityFieldsUseIndependentCounts) {
    auto e = entity;
    e.talker_stream_sources = 7;
    e.listener_stream_sinks = 3;
    adp a;
    fresh(&a, true);
    adp_init(&a, &e, a.ports, 2, 0x1234);
    uint8_t f[ADP_FRAME_BYTES];
    adp_build(&a, 0, 0x87654321, f);
    EXPECT_EQ(wire_be16(f + 38), 7u) << "talker count is independent of listener count";
    EXPECT_EQ(wire_be16(f + 42), 3u);
    EXPECT_EQ(wire_be16(f + 64), 0x1234u);
    EXPECT_EQ(wire_be16(f + 68), 2u);
}

// REQ: ADP-01, MFDISC-04
TEST(AdpCore, AdvertisementFieldsMatchCaller) {
    auto e = entity;
    e.talker_stream_sources = 7;
    e.talker_capabilities = 0x1357;
    e.listener_stream_sinks = 3;
    e.listener_capabilities = 0x2468;
    adp a;
    fresh(&a, true);
    fk.domain = 7;
    adp_init(&a, &e, &ports, 2, 0x1234);
    uint8_t frame[ADP_FRAME_BYTES];
    adp_build(&a, 0, 0x87654321, frame);
    const uint8_t expected[] = {
        0x91, 0xe0, 0xf0, 0x01, 0x00, 0x00,
        0x00, 0x1b, 0x92, 0x11, 0x22, 0xaa,
        0x22, 0xf0, 0xfa, 0x00, 0x50, 0x38,
        0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88,
        0x99, 0xaa, 0xbb, 0xcc, 0xdd, 0xee, 0xff, 0x01,
        0x00, 0x00, 0xc5, 0x88,
        0x00, 0x07, 0x13, 0x57, 0x00, 0x03, 0x24, 0x68,
        0x00, 0x00, 0x00, 0x00,
        0x87, 0x65, 0x43, 0x21,
        0xa1, 0xa2, 0xa3, 0xa4, 0xa5, 0xa6, 0xa7, 0xa8,
        0x07, 0x00, 0x12, 0x34, 0x00, 0x05, 0x00, 0x02,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00,
    };
    ASSERT_EQ(sizeof frame, sizeof expected) << "advertisement vector covers the complete frame";
    EXPECT_EQ(std::memcmp(frame, expected, sizeof expected), 0)
        << "advertisement bytes match the independent entity vector";
}

class AdpPortMock {
 public:
    MOCK_METHOD(bool, Send, (const uint8_t*, size_t));
    MOCK_METHOD(void, Start, (uint32_t));
    MOCK_METHOD(void, Stop, ());
    MOCK_METHOD(void, Gptp, (uint64_t*, uint8_t*));
    MOCK_METHOD(bool, Link, ());
    MOCK_METHOD(uint32_t, Seed, ());
};

// REQ: ADP-02, PORT-01
TEST(AdpCore, MockedPortOrder) {
    using namespace testing;
    StrictMock<AdpPortMock> mock;
    adp_ports ports = {
        &mock,
        [](void* c, unsigned, const uint8_t* f, size_t n) { return static_cast<AdpPortMock*>(c)->Send(f, n); },
        [](void* c, unsigned, uint32_t ms) { static_cast<AdpPortMock*>(c)->Start(ms); },
        [](void* c, unsigned) { static_cast<AdpPortMock*>(c)->Stop(); },
        [](void* c, unsigned, uint64_t* gm, uint8_t* d) { static_cast<AdpPortMock*>(c)->Gptp(gm, d); },
        [](void* c, unsigned) { return static_cast<AdpPortMock*>(c)->Link(); },
        [](void* c) { return static_cast<AdpPortMock*>(c)->Seed(); }
    };
    adp a;
    adp_init(&a, &entity, &ports, 0, 0);
    InSequence sequence;
    EXPECT_CALL(mock, Link()).WillOnce(Return(true));
    EXPECT_CALL(mock, Seed()).WillOnce(Return(1u));
    EXPECT_CALL(mock, Start(Le(2000u)));
    adp_set_enable(&a, true);
    EXPECT_CALL(mock, Gptp(_, _)).WillOnce(DoAll(SetArgPointee<0>(1u), SetArgPointee<1>(0u)));
    EXPECT_CALL(mock, Send(_, 82u)).WillOnce(Return(true));
    EXPECT_CALL(mock, Start(_)).WillOnce([](uint32_t ms) {
        EXPECT_EQ(ms, 5000u) << "A1 TMR_DELAY starts the advertisement period";
    });
    adp_timer_expired(&a);
    EXPECT_EQ(a.state, ADP_STATE_WAITING);
}

class AdpInputControl : public ::testing::TestWithParam<unsigned> {};

void discovery_state(adp* a, unsigned state) {
    fresh(a, state != 1u);
    if (state != 0u) adp_set_enable(a, true);
    if (state == 3u) fk.room = false;
    if (state >= 3u) adp_timer_expired(a);
}

void refused_discovery(adp* a, const uint8_t* frame, size_t length) {
    testing::StrictMock<AdpPortMock> mock;
    const adp_ports silent = {
        &mock,
        [](void* c, unsigned, const uint8_t* f, size_t n) { return static_cast<AdpPortMock*>(c)->Send(f, n); },
        [](void* c, unsigned, uint32_t ms) { static_cast<AdpPortMock*>(c)->Start(ms); },
        [](void* c, unsigned) { static_cast<AdpPortMock*>(c)->Stop(); },
        [](void* c, unsigned, uint64_t* gm, uint8_t* d) { static_cast<AdpPortMock*>(c)->Gptp(gm, d); },
        [](void* c, unsigned) { return static_cast<AdpPortMock*>(c)->Link(); },
        [](void* c) { return static_cast<AdpPortMock*>(c)->Seed(); }
    };
    const adp_ports* saved_ports = a->ports;
    a->ports = &silent;
    adp expected;
    std::memcpy(&expected, a, sizeof expected);
    ++expected.discarded;
    adp_rx(a, frame, length);
    EXPECT_EQ(a->discarded, expected.discarded) << "malformed discovery increments discarded exactly once";
    EXPECT_EQ(std::memcmp(a, &expected, sizeof expected), 0)
        << "malformed discovery preserves all other core storage";
    a->ports = saved_ports;
}

void accepted_discovery(unsigned state, const uint8_t* frame, size_t length) {
    adp a;
    discovery_state(&a, state);
    adp before;
    fake port_before;
    std::memcpy(&before, &a, sizeof a);
    std::memcpy(&port_before, &fk, sizeof fk);
    adp_rx(&a, frame, length);
    EXPECT_EQ(a.discarded, 0u) << "valid discovery is never discarded";
    EXPECT_EQ(fk.sends, port_before.sends) << "valid discovery defers transmission until expiry";
    if (state == 4u) {
        EXPECT_EQ(a.state, ADP_STATE_DELAY) << "valid discovery enters DELAY from WAITING";
        EXPECT_EQ(fk.starts, port_before.starts + 1u) << "valid discovery starts one delay timer";
        EXPECT_EQ(fk.stops, port_before.stops + 1u) << "valid discovery stops the advertisement timer";
        EXPECT_EQ(a.timer, ADP_TIMER_DELAY) << "valid discovery selects the delay timer";
        EXPECT_EQ(a.draws, before.draws + 1u) << "valid discovery draws one delay";
        EXPECT_EQ(a.last_draw, ADP_DRAW_DELAY) << "valid discovery uses the normal delay range";
    } else {
        EXPECT_EQ(std::memcmp(&a, &before, sizeof a), 0) << "valid discovery preserves inactive or delaying state";
        EXPECT_EQ(std::memcmp(&fk, &port_before, sizeof fk), 0) << "valid discovery preserves inactive or delaying ports";
    }
}

[[noreturn]] void read_up_to_a_protected_page(unsigned state) {
    const auto page = static_cast<size_t>(sysconf(_SC_PAGESIZE));
    void* pages = mmap(nullptr, 2 * page, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (pages == MAP_FAILED || mprotect(static_cast<uint8_t*>(pages) + page, page, PROT_NONE) != 0) std::_Exit(2);
    uint8_t* frame = static_cast<uint8_t*>(pages) + page - 82;
    for (uint64_t target : {UINT64_C(0), entity.entity_id, entity.entity_id ^ UINT64_C(1)}) {
        for (unsigned valid_time : {0u, 31u}) {
            for (unsigned length = 0; length < 2048; ++length) {
                adp a;
                discovery_state(&a, state);
                discover(frame, 2u, target);
                wire_put_be(frame + 16, (valid_time << 11) | length, 2);
                adp_rx(&a, frame, 82u);
            }
        }
    }
    std::_Exit(0);
}

// IEEE 1722.1-2021 6.2.2.3
// IEEE 1722-2016 4.4.3.4
// REQ: ADP-01
TEST_P(AdpInputControl, RejectsUnsupportedVersion) {
    adp a;
    discovery_state(&a, GetParam());
    for (uint64_t target : {UINT64_C(0), entity.entity_id}) {
        for (unsigned version = 1; version < 8; ++version) {
            uint8_t frame[82];
            discover(frame, 2u, target);
            frame[15] |= static_cast<uint8_t>(version << 4);
            refused_discovery(&a, frame, sizeof frame);
            if (HasFailure()) return;
        }
    }
}

// IEEE 1722.1-2021 Figure 6-1
// IEEE 1722.1-2021 6.2.2.6
// REQ: ADP-01
TEST_P(AdpInputControl, RejectsShortFrame) {
    adp a;
    discovery_state(&a, GetParam());
    for (uint64_t target : {UINT64_C(0), entity.entity_id}) {
        uint8_t frame[82];
        discover(frame, 2u, target);
        for (size_t length = 0; length < sizeof frame; ++length) {
            const std::vector<uint8_t> short_frame(frame, frame + length);
            refused_discovery(&a, short_frame.data(), short_frame.size());
            if (HasFailure()) return;
        }
    }
}

// IEEE 1722.1-2021 6.2.2.6
// IEEE 1722-2016 4.4.5.4
// REQ: ADP-01
TEST_P(AdpInputControl, RejectsShortControlDataLength) {
    adp a;
    discovery_state(&a, GetParam());
    for (uint64_t target : {UINT64_C(0), entity.entity_id}) {
        uint8_t frame[82];
        discover(frame, 2u, target);
        for (unsigned valid_time : {0u, 31u}) {
            for (unsigned length = 0; length < 56; ++length) {
                wire_put_be(frame + 16, (valid_time << 11) | length, 2);
                refused_discovery(&a, frame, sizeof frame);
                if (HasFailure()) return;
            }
        }
    }
}

// IEEE 1722.1-2021 6.2.2.6 and 6.2.7.1.3
// IEEE 1722-2016 4.4.5.4
// Milan v1.2 5.6.3.1
// REQ: ADP-01
TEST_P(AdpInputControl, AcceptsLongControlDataLength) {
    for (uint64_t target : {UINT64_C(0), entity.entity_id}) {
        for (unsigned valid_time : {0u, 31u}) {
            for (unsigned length = 57; length < 2048; ++length) {
                std::vector<uint8_t> bare(82);
                discover(bare.data(), 2u, target);
                wire_put_be(bare.data() + 16, (valid_time << 11) | length, 2);
                accepted_discovery(GetParam(), bare.data(), bare.size());
                if (HasFailure()) return;
            }
            for (unsigned length : {57u, 84u, 2047u}) {
                std::vector<uint8_t> whole(26u + length, 0xFF);
                discover(whole.data(), 2u, target);
                wire_put_be(whole.data() + 16, (valid_time << 11) | length, 2);
                accepted_discovery(GetParam(), whole.data(), whole.size());
                if (HasFailure()) return;
            }
        }
    }
}

// IEEE 1722.1-2021 Figure 6-1
// IEEE 1722.1-2021 6.2.2.6
// REQ: ADP-01
TEST_P(AdpInputControl, ReadsNoOctetPastTheFrame) {
    EXPECT_EXIT(read_up_to_a_protected_page(GetParam()), ::testing::ExitedWithCode(0), "")
        << "discovery of every length is read within its 82 octets";
}

// Milan v1.2 5.6.3.1
// Milan v1.2 Table 5.51
// REQ: ADP-01, ADP-02, MFDISC-02
TEST_P(AdpInputControl, ValidDiscovery) {
    for (uint64_t target : {UINT64_C(0), entity.entity_id}) {
        for (size_t length : {82u, 83u, 128u}) {
            uint8_t frame[128] = {};
            discover(frame, 2u, target);
            accepted_discovery(GetParam(), frame, length);
        }
    }
}

INSTANTIATE_TEST_SUITE_P(AllStates, AdpInputControl, ::testing::Values(0u, 1u, 2u, 3u, 4u));

}
