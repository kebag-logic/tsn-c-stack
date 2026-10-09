// SPDX-FileCopyrightText: 2026 Kebag Logic
// SPDX-License-Identifier: MIT
// Milan v1.2 Table 5.51











#include "adp.h"

#include <assert.h>
#include <string.h>

#include "wire.h"



static bool port_active;
static uint32_t reentry_count;

static bool reject_reentry(void)
{
	assert(!port_active);
	if (port_active) {
		reentry_count++;
		return true;
	}
	return false;
}

uint32_t adp_reentry_count(void)
{
	(void)reject_reentry();
	return reentry_count;
}

static uint32_t rng_next(struct adp *a)
{
	uint32_t x = a->rng;
	x ^= x << 13;
	x ^= x >> 17;
	x ^= x << 5;
	a->rng = x;
	return x;
}

static uint32_t draw_ms(struct adp *a, enum adp_draw kind)
{
	uint32_t max_ms = kind == ADP_DRAW_STARTUP ? ADP_DELAY_STARTUP_MAX_MS : ADP_DELAY_MAX_MS;
	uint32_t r16 = rng_next(a) >> 16;
	uint32_t ms = (r16 * (max_ms + 1u)) >> 16;
	a->draws++;
	a->last_draw_ms = ms;
	a->last_draw = kind;
	return ms;
}

static void timer_start(struct adp *a, enum adp_timer kind, uint32_t delay_ms)
{
	a->timer = kind;
	port_active = true;
	a->ports->timer_start(a->ports->ctx, a->interface, delay_ms);
	port_active = false;
}

static void timer_stop(struct adp *a)
{
	a->timer = ADP_TIMER_NONE;
	port_active = true;
	a->ports->timer_stop(a->ports->ctx, a->interface);
	port_active = false;
}


static void enter_delay(struct adp *a, enum adp_draw kind)
{
	timer_start(a, ADP_TIMER_DELAY, draw_ms(a, kind));
	a->state = ADP_STATE_DELAY;
}

void adp_build(const struct adp *a, uint8_t message_type, uint32_t available_index, uint8_t *frame)
{
	if (reject_reentry()) {
		return;
	}
	const struct adp_entity *e = a->entity;
	uint64_t gm = 0;
	uint8_t domain = 0;
	port_active = true;
	a->ports->gptp(a->ports->ctx, a->interface, &gm, &domain);
	port_active = false;
	uint8_t valid_time = message_type == ADP_MSG_ENTITY_AVAILABLE ? ADP_VALID_TIME : 0u;
	uint8_t *pdu = frame + ADP_HEADER_BYTES;

	memset(frame, 0, ADP_FRAME_BYTES);
	wire_put_be(frame, ADP_MULTICAST_MAC, 6);
	wire_put_be(frame + 6, e->mac, 6);
	wire_put_be(frame + 12, ADP_ETHERTYPE, 2);
	pdu[0] = ADP_SUBTYPE;                                           // IEEE 1722.1-2021 6.2.2.1
	pdu[1] = message_type & 0x0Fu;                                  // IEEE 1722.1-2021 6.2.2.2-4
	wire_put_be(pdu + 2, ((uint32_t)valid_time << 11) | ADP_CONTROL_DATA_LENGTH, 2);   // IEEE 1722.1-2021 6.2.2.5-6
	wire_put_be(pdu + 4, e->entity_id, 8);                          // IEEE 1722.1-2021 6.2.2.7
	wire_put_be(pdu + 12, e->entity_model_id, 8);                   // IEEE 1722.1-2021 6.2.2.8
	wire_put_be(pdu + 20, e->entity_capabilities, 4);               // IEEE 1722.1-2021 6.2.2.9; Milan v1.2 5.6.2
	wire_put_be(pdu + 24, e->talker_stream_sources, 2);             // IEEE 1722.1-2021 6.2.2.10; Milan v1.2 5.6.2
	wire_put_be(pdu + 26, e->talker_capabilities, 2);               // IEEE 1722.1-2021 6.2.2.11
	wire_put_be(pdu + 28, e->listener_stream_sinks, 2);             // IEEE 1722.1-2021 6.2.2.12; Milan v1.2 5.6.2
	wire_put_be(pdu + 30, e->listener_capabilities, 2);             // IEEE 1722.1-2021 6.2.2.13
	wire_put_be(pdu + 32, 0u, 4);                                   // IEEE 1722.1-2021 6.2.2.14
	wire_put_be(pdu + 36, available_index, 4);                      // IEEE 1722.1-2021 6.2.2.15
	wire_put_be(pdu + 40, gm, 8);                                   // IEEE 1722.1-2021 6.2.2.16
	pdu[48] = domain;                                               // IEEE 1722.1-2021 6.2.2.17
	wire_put_be(pdu + 50, a->current_configuration_index, 2);      // IEEE 1722.1-2021 6.2.2.18
	wire_put_be(pdu + 52, e->identify_control_index, 2);           // IEEE 1722.1-2021 6.2.2.19
	wire_put_be(pdu + 54, a->interface, 2);                         // IEEE 1722.1-2021 6.2.2.20
	// IEEE 1722.1-2021 6.2.2.21
}



static bool send(struct adp *a, uint8_t message_type, uint32_t available_index)
{
	uint8_t frame[ADP_FRAME_BYTES];
	adp_build(a, message_type, available_index, frame);
	port_active = true;
	bool sent = a->ports->send(a->ports->ctx, a->interface, frame, ADP_FRAME_BYTES);
	port_active = false;
	if (sent) {
		return true;
	}
	a->deferred_sends++;
	return false;
}


static void depart(struct adp *a)
{
	if (!send(a, ADP_MSG_ENTITY_DEPARTING, a->departing_index)) {
		return;
	}
	a->departing_owed--;
	a->departing_index = 0;
}

// Milan v1.2 5.6.3.5.9



static void advertise(struct adp *a)
{
	a->available_owed = true;
	if (a->departing_owed != 0u || !send(a, ADP_MSG_ENTITY_AVAILABLE, a->available_index)) {
		return;
	}
	a->available_owed = false;
	a->available_index++;                                           // IEEE 1722.1-2021 6.2.2.15
	timer_start(a, ADP_TIMER_ADVERTISE, ADP_ADVERTISE_MS);
	a->state = ADP_STATE_WAITING;
}

void adp_init(struct adp *a, const struct adp_entity *entity, const struct adp_ports *ports,
	      unsigned interface, uint16_t current_configuration_index)
{
	if (reject_reentry()) {
		return;
	}
	memset(a, 0, sizeof *a);
	a->entity = entity;
	a->ports = ports;
	a->interface = (uint8_t)interface;
	a->state = ADP_STATE_DOWN;
	a->current_configuration_index = current_configuration_index;
	a->rng = (uint32_t)entity->entity_id ^ (uint32_t)(entity->entity_id >> 32) ^ 0x9E3779B9u;
	if (a->rng == 0u) {
		a->rng = 1u;
	}
}

void adp_set_current_configuration(struct adp *a, uint16_t index)
{
	if (reject_reentry()) {
		return;
	}
	a->current_configuration_index = index;
}

// Milan v1.2 5.6.3.5.8; Milan v1.2 5.6.3.5.11
static void shutdown(struct adp *a)
{
	if (a->state == ADP_STATE_DOWN) {
		return;
	}
	timer_stop(a);
	// IEEE 1722.1-2021 Figure 6-3
	// IEEE 1722.1-2021 6.2.5.2.2; IEEE 1722.1-2021 6.2.2.15
	uint32_t index = a->available_index;
	a->available_index = 0;
	a->available_owed = false;
	a->state = ADP_STATE_DOWN;
	if (a->departing_owed == 0u) {
		a->departing_index = index;
		a->departing_owed = 1u;
		depart(a);
	} else if (a->departing_owed < ADP_DEPARTING_OWED_MAX) {
		a->departing_owed++;
	} else {
		a->departing_coalesced++;
	}
}

void adp_set_enable(struct adp *a, bool enable)
{
	if (reject_reentry()) {
		return;
	}
	if (enable == a->enabled) {
		return;
	}
	if (!enable) {
		shutdown(a);
		a->enabled = false;
		return;
	}
	a->enabled = true;
	port_active = true;
	a->rng ^= a->ports->seed(a->ports->ctx);
	port_active = false;
	if (a->rng == 0u) {
		a->rng = 1u;
	}
	port_active = true;
	a->link_up = a->ports->link_up(a->ports->ctx, a->interface);
	port_active = false;
	if (a->link_up) {
		enter_delay(a, ADP_DRAW_STARTUP);                       // Milan v1.2 5.6.3.5.2
	} else {
		a->state = ADP_STATE_DOWN;                              // Milan v1.2 5.6.3.5.1
	}
}

void adp_link_change(struct adp *a, bool up)
{
	if (reject_reentry()) {
		return;
	}
	bool was = a->link_up;
	a->link_up = up;
	if (!a->enabled || up == was) {
		return;
	}
	if (up) {
		if (a->state == ADP_STATE_DOWN) {
			enter_delay(a, ADP_DRAW_DELAY);                 // Milan v1.2 5.6.3.5.3
		}
		return;
	}
	if (a->state != ADP_STATE_DOWN) {
		timer_stop(a);                                          // Milan v1.2 5.6.3.5.6 / 5.6.3.5.10
		a->available_owed = false;
		a->state = ADP_STATE_DOWN;
	}
}

void adp_gm_change(struct adp *a)
{
	if (reject_reentry()) {
		return;
	}
	a->gm_changed++;
	if (a->enabled && a->state == ADP_STATE_WAITING) {
		enter_delay(a, ADP_DRAW_DELAY);                         // Milan v1.2 5.6.3.5.7
	}
}

void adp_timer_expired(struct adp *a)
{
	if (reject_reentry()) {
		return;
	}
	enum adp_timer kind = a->timer;
	if (kind == ADP_TIMER_NONE) {
		a->stray_expiries++;
		return;
	}
	a->timer = ADP_TIMER_NONE;
	if (a->state == ADP_STATE_DELAY && kind == ADP_TIMER_DELAY) {
		advertise(a);                                           // Milan v1.2 5.6.3.5.9
	} else if (a->state == ADP_STATE_WAITING && kind == ADP_TIMER_ADVERTISE) {
		enter_delay(a, ADP_DRAW_DELAY);                         // Milan v1.2 5.6.3.5.5
	} else {
		a->stray_expiries++;
	}
}

void adp_rx(struct adp *a, const uint8_t *frame, size_t len)
{
	if (reject_reentry()) {
		return;
	}
	// Milan v1.2 5.6.3.1

	if (len < ADP_HEADER_BYTES + 12u || wire_be16(frame + 12) != ADP_ETHERTYPE ||
	    frame[ADP_HEADER_BYTES] != ADP_SUBTYPE ||
	    (frame[ADP_HEADER_BYTES + 1u] & 0x0Fu) != ADP_MSG_ENTITY_DISCOVER) {
		a->discarded++;
		return;
	}
	uint64_t target = wire_be64(frame + ADP_HEADER_BYTES + 4u);
	if (target != 0u && target != a->entity->entity_id) {
		a->discarded++;
		return;
	}
	if (!a->enabled || a->state != ADP_STATE_WAITING) {             // Milan v1.2 Table 5.51
		return;
	}
	timer_stop(a);                                                  // Milan v1.2 5.6.3.5.4
	enter_delay(a, ADP_DRAW_DELAY);
}



bool adp_poll(struct adp *a)
{
	if (reject_reentry()) {
		return false;
	}
	if (a->departing_owed != 0u) {
		depart(a);
	} else if (a->available_owed) {
		if (a->enabled && a->state == ADP_STATE_DELAY) {
			advertise(a);
		} else {
			a->available_owed = false;
		}
	}
	return a->departing_owed != 0u || a->available_owed;
}
