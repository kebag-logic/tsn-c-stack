// SPDX-License-Identifier: MIT
#ifndef EXAMPLE_ADP_PORT_H
#define EXAMPLE_ADP_PORT_H
#include "adp.h"

struct example_adp_port {
    struct adp core;
    struct adp_ports ports;
    struct adp_entity entity;
    uint32_t now_ms, deadline_ms;
    uint64_t grandmaster;
    uint8_t domain;
    bool link, armed, tx_ready;
    uint8_t tx[ADP_FRAME_BYTES];
};

void example_adp_init(struct example_adp_port *p, const struct adp_entity *entity);
void example_adp_link(struct example_adp_port *p, bool up);
void example_adp_service(struct example_adp_port *p, uint32_t now_ms);
bool example_adp_take_frame(struct example_adp_port *p, uint8_t frame[ADP_FRAME_BYTES]);
#endif
