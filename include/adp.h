// SPDX-FileCopyrightText: 2026 Kebag Logic
// SPDX-License-Identifier: MIT
// Milan v1.2 5.6.3
// IEEE 1722.1-2021 6.2
// Milan v1.2 5.6.3.5.2
// Milan v1.2 5.6.3.5.3
// Milan v1.2 5.6.3.5.5
// Milan v1.2 5.6.3.5.9
// IEEE 1722.1-2021 6.2.2.15
// IEEE 1722.1-2021 Figure 6-2
// Milan v1.2 5.6.3.1
// Milan v1.2 5.6.3.5.4
// Milan v1.2 5.6.3.5.7
// Milan v1.2 5.6.3.5.8
// Milan v1.2 5.6.3.5.11
// Milan v1.2 5.6.3.5.6
// Milan v1.2 5.6.3.5.10
// IEEE 1722.1-2021 Figure 6-3
// IEEE 1722.1-2021 6.2.5.2.2
// Milan v1.2 Table 5.54
// IEEE 1722.1-2021 6.2.6.3.5
// Milan v1.2 5.6.4











































#ifndef ADP_H
#define ADP_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define ADP_ETHERTYPE 0x22F0u           // IEEE 1722-2016 Table 5
#define ADP_SUBTYPE 0xFAu               // IEEE 1722.1-2021 6.2.2.1
#define ADP_MULTICAST_MAC 0x91E0F0010000ull // IEEE 1722.1-2021 Table B.1
#define ADP_HEADER_BYTES 14u
#define ADP_PDU_BYTES 68u               // IEEE 1722.1-2021 Figure 6-1
#define ADP_FRAME_BYTES 82u
#define ADP_CONTROL_DATA_LENGTH 56u     // IEEE 1722.1-2021 6.2.2.6
#define ADP_VALID_TIME 10u              // Milan v1.2 5.6.2
#define ADP_ADVERTISE_MS 5000u          // Milan v1.2 Table 5.50
#define ADP_DELAY_MAX_MS 4000u          // Milan v1.2 Table 5.50
#define ADP_DELAY_STARTUP_MAX_MS 2000u  // Milan v1.2 5.6.3.5.2
#define ADP_DEPARTING_OWED_MAX 2u

// IEEE 1722.1-2021 Table 6-1
#define ADP_MSG_ENTITY_AVAILABLE 0u
#define ADP_MSG_ENTITY_DEPARTING 1u
#define ADP_MSG_ENTITY_DISCOVER 2u

// Milan v1.2 Table 5.49

enum adp_state {
	ADP_STATE_DOWN = 0,
	ADP_STATE_DELAY = 2,
	ADP_STATE_WAITING = 3,
};


enum adp_timer {
	ADP_TIMER_NONE = 0,
	ADP_TIMER_DELAY,
	ADP_TIMER_ADVERTISE,
};


enum adp_draw {
	ADP_DRAW_NONE = 0,
	ADP_DRAW_STARTUP,       // Milan v1.2 5.6.3.5.2
	ADP_DRAW_DELAY,
};


struct adp_entity {
	uint64_t entity_id;
	uint64_t entity_model_id;
	uint64_t mac;
	uint32_t entity_capabilities;
	uint16_t talker_stream_sources;
	uint16_t talker_capabilities;
	uint16_t listener_stream_sinks;
	uint16_t listener_capabilities;
	uint16_t identify_control_index;
};

















struct adp_ports {
	void *ctx;


	bool (*send)(void *ctx, unsigned interface, const uint8_t *frame, size_t len);



	void (*timer_start)(void *ctx, unsigned interface, uint32_t delay_ms);
	void (*timer_stop)(void *ctx, unsigned interface);

	void (*gptp)(void *ctx, unsigned interface, uint64_t *gm_id, uint8_t *domain);

	bool (*link_up)(void *ctx, unsigned interface);

	uint32_t (*seed)(void *ctx);
};

struct adp {
	const struct adp_entity *entity;
	const struct adp_ports *ports;
	uint8_t interface;
	enum adp_state state;
	bool enabled;                       // Milan v1.2 5.6.1
	bool link_up;
	uint32_t available_index;
	uint16_t current_configuration_index;
	enum adp_timer timer;
	uint32_t rng;

	bool available_owed;
	uint32_t departing_owed;
	uint32_t departing_index;

	uint32_t gm_changed;
	uint32_t draws;
	uint32_t last_draw_ms;
	enum adp_draw last_draw;
	uint32_t stray_expiries;
	uint32_t discarded;                 // Milan v1.2 5.6.3.1
	uint32_t deferred_sends;
	uint32_t departing_coalesced;
};

void adp_init(struct adp *a, const struct adp_entity *entity, const struct adp_ports *ports,
	      unsigned interface, uint16_t current_configuration_index);

// Milan v1.2 5.6.3.5.1; Milan v1.2 5.6.3.5.2
void adp_set_enable(struct adp *a, bool enable);

// IEEE 1722.1-2021 6.2.2.18
void adp_set_current_configuration(struct adp *a, uint16_t index);


void adp_rx(struct adp *a, const uint8_t *frame, size_t len);
void adp_timer_expired(struct adp *a);
void adp_link_change(struct adp *a, bool up);
void adp_gm_change(struct adp *a);



bool adp_poll(struct adp *a);


void adp_build(const struct adp *a, uint8_t message_type, uint32_t available_index, uint8_t *frame);



uint32_t adp_reentry_count(void);

#ifdef __cplusplus
}
#endif

#endif
