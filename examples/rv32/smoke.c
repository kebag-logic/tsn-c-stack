// SPDX-License-Identifier: MIT
#include "adp.h"
#include "acmp.h"
#include "maap.h"
#include "wire.h"
#include "entity_roundtrip.h"
#include <string.h>

#define CHECK(expression, code) do { if (!(expression)) return (code); } while (0)

struct port {
    uint8_t frame[ADP_FRAME_BYTES];
    size_t length;
    unsigned sends, starts, stops, admissions, calls;
    uint32_t delay;
    bool room, valid;
};

static bool send_frame(void *ctx, unsigned interface, const uint8_t *frame, size_t length)
{
    struct port *p = ctx;
    (void)interface;
    ++p->calls;
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
    ++p->calls;
    p->delay = delay;
    ++p->starts;
}

static void stop(void *ctx, unsigned interface)
{
    (void)interface;
    ++((struct port *)ctx)->calls;
    ++((struct port *)ctx)->stops;
}

static void gptp(void *ctx, unsigned interface, uint64_t *gm, uint8_t *domain)
{
    ++((struct port *)ctx)->calls;
    (void)interface;
    *gm = UINT64_C(0x0102030405060708);
    *domain = 0;
}

static bool link_up(void *ctx, unsigned interface)
{
    ++((struct port *)ctx)->calls;
    (void)interface;
    return true;
}

static uint32_t clock_ms(void *ctx)
{
    ++((struct port *)ctx)->calls;
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
    if (bound) ++((struct port *)ctx)->admissions;
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

// REQ: ADP-01, ADP-02, ADP-03, PORT-01
static int adp_smoke(void)
{
    struct port p = {.room = true};
    const struct adp_ports ports = {&p, send_frame, start, stop, gptp, link_up, clock_ms};
    const struct adp_entity entity = {.entity_id = 1, .mac = UINT64_C(0x020000000001)};
    struct adp core;
    uint8_t frame[ADP_FRAME_BYTES];
    adp_init(&core, &entity, &ports, 0, 0);
    adp_set_enable(&core, true);
    CHECK(core.state == ADP_STATE_DELAY && p.sends == 0 && p.starts == 1, 1);
    adp_timer_expired(&core);
    CHECK(core.state == ADP_STATE_WAITING && p.sends == 1 && p.delay == 5000, 2);
    CHECK(p.length == ADP_FRAME_BYTES && p.frame[15] == 0 && wire_be64(p.frame + 18) == 1, 3);
    adp_build(&core, ADP_MSG_ENTITY_DISCOVER, 0, frame);
    adp_rx(&core, frame, sizeof frame);
    CHECK(core.state == ADP_STATE_DELAY && core.discarded == 0, 4);
    adp_timer_expired(&core);
    p.room = false;
    adp_set_enable(&core, false);
    CHECK(core.departing_owed == 1 && core.available_index == 0, 5);
    p.room = true;
    CHECK(!adp_poll(&core) && p.frame[15] == 1 && core.departing_owed == 0, 6);
    return 0;
}

// IEEE 1722.1-2021 Figure 6-1
// IEEE 1722.1-2021 6.2.2.3 and 6.2.2.6
// IEEE 1722-2016 4.4.3.4 and 4.4.5.4
// Milan v1.2 Table 5.51
// REQ: ADP-01, ADP-02
static int adp_discovery_smoke(void)
{
    for (unsigned state = 0; state < 5; ++state) {
        for (unsigned control = 0; control < 4; ++control) {
            struct port p = {.room = true};
            const struct adp_ports ports = {&p, send_frame, start, stop, gptp, link_up, clock_ms};
            const struct adp_entity entity = {.entity_id = 1};
            struct adp core, expected;
            uint8_t frame[82] = {0};
            adp_init(&core, &entity, &ports, 0, 0);
            if (state != 0) adp_set_enable(&core, true);
            if (state == 1) adp_link_change(&core, false);
            if (state == 3) p.room = false;
            if (state >= 3) adp_timer_expired(&core);
            wire_put_be(frame + 12, 0x22f0, 2);
            frame[14] = 0xfa;
            frame[15] = control == 1 ? 0x12 : 0x02;
            frame[17] = control == 3 ? 0 : 56;
            wire_put_be(frame + 18, 1, 8);
            memcpy(&expected, &core, sizeof expected);
            const unsigned calls = p.calls, sends = p.sends, starts = p.starts, stops = p.stops;
            adp_rx(&core, frame, control == 2 ? 26 : sizeof frame);
            if (control != 0) ++expected.discarded;
            if (control != 0 || state != 4) {
                const uint8_t *actual = (const uint8_t *)&core;
                const uint8_t *saved = (const uint8_t *)&expected;
                for (size_t i = 0; i < sizeof core; ++i) CHECK(actual[i] == saved[i], 40 + control);
                CHECK(p.calls == calls, 44 + control);
            } else {
                CHECK(core.state == ADP_STATE_DELAY && core.timer == ADP_TIMER_DELAY && core.discarded == 0, 48);
                CHECK(p.starts == starts + 1 && p.stops == stops + 1 && p.sends == sends, 49);
            }
        }
    }
    return 0;
}

// REQ: ACMP-01, ACMP-07, PORT-01
static int acmp_smoke(void)
{
    struct port p = {.room = true};
    const struct acmp_ports ports = {&p, send_frame, clock_ms, timer, gptp, clock_ms, admit};
    const struct acmp_env env = {&p, locked, source, srp, notify, notify};
    const struct acmp_config config = {.entity_id = 1, .n_interfaces = 1, .n_sinks = 1};
    struct acmp core;
    struct acmp_sink_view view;
    uint8_t record[ACMP_BINDING_BYTES] = {1, 0, 0x12, 0x34};
    uint8_t saved[ACMP_BINDING_BYTES];
    wire_put_be(record + 4, UINT64_C(0x0102030405060708), 8);
    wire_put_be(record + 12, UINT64_C(0x1112131415161718), 8);
    CHECK(acmp_init(&core, &config, &ports, &env), 10);
    CHECK(acmp_restore_binding(&core, 0, record, sizeof record) == ACMP_RESTORE_APPLIED, 11);
    CHECK(acmp_view(&core, 0, &view) && view.state == ACMP_PRB_W_AVAIL && view.bound, 12);
    CHECK(view.binding.talker_unique_id == 0x1234 && view.binding.talker_entity_id == wire_be64(record + 4), 13);
    acmp_open(&core);
    CHECK(p.admissions == 1 && acmp_binding_latch(&core, 0, saved), 14);
    for (unsigned i = 0; i < sizeof record; ++i) CHECK(saved[i] == record[i], 15);
    acmp_restore_rollback(&core);
    CHECK(acmp_view(&core, 0, &view) && !view.bound && view.state == ACMP_UNBOUND, 16);
    return 0;
}

// REQ: MAAP-02, MAAP-04, PORT-01
static int maap_smoke(void)
{
    struct port p = {.room = true};
    const struct maap_ports ports = {&p, send_frame, start, stop, range, clock_ms};
    struct maap core;
    CHECK(maap_init(&core, &ports, 0, UINT64_C(0x020000000001), 8), 20);
    maap_port_operational(&core, true);
    CHECK(!maap_begin(&core, MAAP_POOL_BASE + 0xfdf9), 21);
    CHECK(maap_begin(&core, MAAP_POOL_BASE + 0xfdf8), 22);
    CHECK(core.state == MAAP_PROBE && p.sends == 1 && !p.valid, 23);
    for (unsigned i = 0; i < MAAP_PROBE_RETRANSMITS; ++i) maap_timer_expired(&core);
    CHECK(core.state == MAAP_DEFEND && p.sends == 5 && p.valid, 24);
    CHECK(p.length == MAAP_FRAME_BYTES && p.frame[15] == MAAP_MSG_ANNOUNCE, 25);
    maap_release(&core);
    CHECK(!p.valid && !maap_poll(&core), 26);
    return 0;
}

int main(void)
{
    int result = adp_smoke();
    if (!result) result = adp_discovery_smoke();
    if (!result) result = acmp_smoke();
    if (!result) result = maap_smoke();
    if (!result) result = entity_check_adp();
    if (!result) result = entity_check_acmp();
    if (!result) result = entity_check_maap();
    return result;
}
