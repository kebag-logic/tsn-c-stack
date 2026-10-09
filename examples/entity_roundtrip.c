// SPDX-License-Identifier: MIT
#include "entity_roundtrip.h"
#include "adp.h"
#include "acmp.h"
#include "maap.h"
#include "wire.h"
#include "entities/listener/entity_config.h"
#include "entities/talker/entity_config.h"
#include "entities/duplex/entity_config.h"
#include "entities/ax7101/entity_config.h"
#include <string.h>

#define CHECK(expression, code) do { if (!(expression)) return (code); } while (0)

struct port {
    uint8_t frame[ADP_FRAME_BYTES];
    size_t length;
    unsigned sends, starts, stops, admissions;
    unsigned last_interface;
    unsigned admitted[4];
    uint32_t delay;
    bool room, valid;
};

static bool send_frame(void *ctx, unsigned interface, const uint8_t *frame, size_t length)
{
    struct port *p = ctx;
    p->last_interface = interface;
    if (!p->room || length > sizeof p->frame) return false;
    memcpy(p->frame, frame, length);
    p->length = length;
    ++p->sends;
    return true;
}

static void start(void *ctx, unsigned interface, uint32_t delay)
{
    struct port *p = ctx;
    (void)interface;
    p->delay = delay;
    ++p->starts;
}

static void stop(void *ctx, unsigned interface)
{
    (void)interface;
    ++((struct port *)ctx)->stops;
}

static void gptp(void *ctx, unsigned interface, uint64_t *gm, uint8_t *domain)
{
    (void)ctx;
    (void)interface;
    *gm = UINT64_C(0x0102030405060708);
    *domain = 0;
}

static bool link_up(void *ctx, unsigned interface)
{
    (void)ctx;
    (void)interface;
    return true;
}

static uint32_t clock_ms(void *ctx)
{
    (void)ctx;
    return 123;
}

static void timer(void *ctx, unsigned interface, bool armed, uint32_t deadline)
{
    if (armed) start(ctx, interface, deadline);
    else stop(ctx, interface);
}

static void admit(void *ctx, unsigned interface, unsigned sink, bool bound, uint64_t talker)
{
    (void)interface;
    (void)sink;
    (void)talker;
    if (bound) {
        struct port *p = ctx;
        ++p->admissions;
        if (interface < 4) ++p->admitted[interface];
    }
}

static bool locked(void *ctx, uint64_t *controller)
{
    (void)ctx;
    *controller = 0;
    return false;
}

static void source(void *ctx, unsigned index, struct acmp_source_state *out)
{
    (void)ctx;
    (void)index;
    memset(out, 0, sizeof *out);
}

static void srp(void *ctx, unsigned sink, const struct acmp_stream *stream)
{
    (void)ctx;
    (void)sink;
    (void)stream;
}

static void notify(void *ctx, unsigned sink)
{
    (void)ctx;
    (void)sink;
}

static void range(void *ctx, unsigned interface, uint64_t base, uint16_t count, bool valid)
{
    (void)interface;
    (void)base;
    ((struct port *)ctx)->valid = valid && count != 0;
}

struct entity_case {
    const struct adp_entity *adp;
    const struct acmp_config *acmp;
    unsigned interfaces, sinks, sources;
    uint16_t listener_caps, talker_caps;
    uint64_t model;
    uint8_t sink_interface[2], source_interface[2];
};

static const struct entity_case cases[] = {
    {listener_adp, &listener_acmp, 1, 1, 0, 0x4001, 0, UINT64_C(0x001bc50000000001), {0, 0}, {0, 0}},
    {talker_adp, &talker_acmp, 1, 0, 1, 0, 0x4001, UINT64_C(0x001bc50000000002), {0, 0}, {0, 0}},
    {duplex_adp, &duplex_acmp, 2, 2, 2, 0x4801, 0x4801, UINT64_C(0x001bc50000000003), {1, 0}, {0, 1}},
    {ax7101_adp, &ax7101_acmp, 1, 2, 2, 0x4801, 0x4801, UINT64_C(0x001bc5c1935893e1), {0, 0}, {0, 0}},
};

// REQ: ENTITY-01, ADP-01
int entity_check_adp(void)
{
    for (unsigned k = 0; k < sizeof cases / sizeof cases[0]; ++k) {
        const struct entity_case *e = &cases[k];
        for (unsigned i = 0; i < e->interfaces; ++i) {
            struct port p = {.room = true};
            const struct adp_ports ports = {&p, send_frame, start, stop, gptp, link_up, clock_ms};
            struct adp core;
            adp_init(&core, &e->adp[i], &ports, i, 0);
            adp_set_enable(&core, true);
            adp_timer_expired(&core);
            CHECK(p.sends == 1 && p.length == 82 && p.last_interface == i, 31);
            CHECK(wire_be64(p.frame + 18) == UINT64_C(0x020000fffe000001), 32);
            CHECK(wire_be64(p.frame + 26) == e->model, 33);
            CHECK(wire_be16(p.frame + 6) == 0x0200 && wire_be32(p.frame + 8) == i + 1, 34);
            CHECK(wire_be32(p.frame + 34) == 0xc588, 35);
            CHECK(wire_be16(p.frame + 38) == e->sources && wire_be16(p.frame + 40) == e->talker_caps, 36);
            CHECK(wire_be16(p.frame + 42) == e->sinks && wire_be16(p.frame + 44) == e->listener_caps, 37);
            CHECK(wire_be16(p.frame + 66) == 0 && wire_be16(p.frame + 68) == i, 38);
        }
    }
    CHECK(ax7101_identity.name[0] == 'M' && ax7101_identity.serial_number[10] == '1', 39);
    return 0;
}

// REQ: ENTITY-01, ACMP-01, ACMP-07
int entity_check_acmp(void)
{
    for (unsigned k = 0; k < sizeof cases / sizeof cases[0]; ++k) {
        const struct entity_case *e = &cases[k];
        struct port p = {.room = true};
        const struct acmp_ports ports = {&p, send_frame, clock_ms, timer, gptp, clock_ms, admit};
        const struct acmp_env env = {&p, locked, source, srp, notify, notify};
        struct acmp core;
        CHECK(acmp_init(&core, e->acmp, &ports, &env), 40);
        CHECK(core.cfg.entity_id == UINT64_C(0x020000fffe000001), 41);
        CHECK(core.cfg.n_interfaces == e->interfaces && core.cfg.n_sinks == e->sinks && core.cfg.n_sources == e->sources, 42);
        for (unsigned i = 0; i < e->interfaces; ++i) CHECK(core.cfg.mac[i] == UINT64_C(0x020000000001) + i, 43);
        for (unsigned s = 0; s < e->sinks; ++s) {
            uint8_t record[20] = {1, 0, 0, 7};
            record[11] = 42;
            CHECK(core.sinks[s].interface == e->sink_interface[s], 44);
            CHECK(acmp_restore_binding(&core, s, record, sizeof record) == ACMP_RESTORE_APPLIED, 45);
        }
        for (unsigned s = 0; s < e->sources; ++s) CHECK(core.cfg.source_interface[s] == e->source_interface[s], 46);
        acmp_open(&core);
        CHECK(p.admissions == e->sinks, 47);
        for (unsigned i = 0; i < e->interfaces; ++i) {
            unsigned expected = 0;
            for (unsigned s = 0; s < e->sinks; ++s) if (e->sink_interface[s] == i) ++expected;
            CHECK(p.admitted[i] == expected, 48);
        }
    }
    return 0;
}

static int check_range(unsigned interface, uint64_t mac, uint16_t count, uint64_t preferred,
                       unsigned expected_interface, unsigned expected_count, uint64_t expected_base)
{
    struct port p = {.room = true};
    const struct maap_ports ports = {&p, send_frame, start, stop, range, clock_ms};
    struct maap core;
    CHECK(interface == expected_interface && count == expected_count, 50);
    CHECK(mac == UINT64_C(0x020000000001) + expected_interface, 51);
    CHECK(maap_init(&core, &ports, interface, mac, count), 52);
    maap_port_operational(&core, true);
    CHECK(maap_begin(&core, preferred), 53);
    CHECK(p.sends == 1 && p.last_interface == expected_interface && p.length == 60, 54);
    CHECK(wire_be16(p.frame + 32) == expected_count, 55);
    if (expected_base) CHECK(core.base == expected_base, 56);
    else CHECK(core.base >= UINT64_C(0x91e0f0000000) && core.base + count <= UINT64_C(0x91e0f000fe00), 57);
    for (unsigned i = 0; i < 3; ++i) maap_timer_expired(&core);
    CHECK(p.sends == 5 && p.valid && core.state == MAAP_DEFEND, 58);
    maap_release(&core);
    CHECK(!p.valid, 59);
    return 0;
}

// REQ: ENTITY-01, MAAP-02
int entity_check_maap(void)
{
    CHECK(listener_maap[0].count == 0, 60);
    int result = check_range(talker_maap[0].interface, talker_maap[0].mac, talker_maap[0].count,
                             talker_maap[0].preferred, 0, 1, UINT64_C(0x91e0f0000010));
    if (result) return result;
    for (unsigned i = 0; i < 2; ++i) {
        result = check_range(duplex_maap[i].interface, duplex_maap[i].mac, duplex_maap[i].count,
                             duplex_maap[i].preferred, i, 1, UINT64_C(0x91e0f0000010) + i * UINT64_C(16));
        if (result) return result;
    }
    return check_range(ax7101_maap[0].interface, ax7101_maap[0].mac, ax7101_maap[0].count,
                       ax7101_maap[0].preferred, 0, 2, 0);
}
