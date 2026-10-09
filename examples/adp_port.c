// SPDX-License-Identifier: MIT
#include "adp_port.h"
#include <string.h>

static bool send_frame(void *ctx, unsigned interface, const uint8_t *frame, size_t len)
{
    struct example_adp_port *p = ctx;
    (void)interface;
    if (p->tx_ready || len != sizeof p->tx) {
        return false;
    }
    memcpy(p->tx, frame, len);
    p->tx_ready = true;
    return true;
}

static void start(void *ctx, unsigned interface, uint32_t delay_ms)
{
    struct example_adp_port *p = ctx;
    (void)interface;
    p->deadline_ms = p->now_ms + delay_ms;
    p->armed = true;
}

static void stop(void *ctx, unsigned interface)
{
    struct example_adp_port *p = ctx;
    (void)interface;
    p->armed = false;
}

static void gptp(void *ctx, unsigned interface, uint64_t *gm, uint8_t *domain)
{
    const struct example_adp_port *p = ctx;
    (void)interface;
    *gm = p->grandmaster;
    *domain = p->domain;
}

static bool link_up(void *ctx, unsigned interface)
{
    (void)interface;
    return ((const struct example_adp_port *)ctx)->link;
}

static uint32_t seed(void *ctx)
{
    const struct example_adp_port *p = ctx;
    return p->now_ms ^ (uint32_t)p->entity.mac;
}

void example_adp_init(struct example_adp_port *p, const struct adp_entity *entity)
{
    memset(p, 0, sizeof *p);
    p->entity = *entity;
    p->ports = (struct adp_ports){p, send_frame, start, stop, gptp, link_up, seed};
    adp_init(&p->core, &p->entity, &p->ports, 0, 0);
}

void example_adp_link(struct example_adp_port *p, bool up)
{
    p->link = up;
    adp_link_change(&p->core, up);
}

void example_adp_service(struct example_adp_port *p, uint32_t now_ms)
{
    p->now_ms = now_ms;
    if (p->armed && (int32_t)(now_ms - p->deadline_ms) >= 0) {
        p->armed = false;
        adp_timer_expired(&p->core);
    }
    (void)adp_poll(&p->core);
}

bool example_adp_take_frame(struct example_adp_port *p, uint8_t frame[ADP_FRAME_BYTES])
{
    if (!p->tx_ready) {
        return false;
    }
    memcpy(frame, p->tx, sizeof p->tx);
    p->tx_ready = false;
    return true;
}
