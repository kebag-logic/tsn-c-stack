// SPDX-FileCopyrightText: 2026 Kebag Logic
// SPDX-License-Identifier: MIT
// Milan v1.2 5.5
// Milan v1.2 5.5.2.1
// Milan v1.2 5.6.4
// IEEE 1722.1-2021 8.2.1
// IEEE 1722.1-2021 8.2.1.3 and 6.2.2.3
// IEEE 1722-2016 4.4.3.4
// Milan v1.2 5.5.3
// Milan v1.2 Table 5.28
// Milan v1.2 Table 5.30
// Milan v1.2 5.5.3.5.1 to 5.5.3.5.48
// Milan v1.2 5.5.3.1
// Milan v1.2 Table 5.27
// Milan v1.2 5.5.3.5.18
// Milan v1.2 5.5.3.5.17
// Milan v1.2 5.5.3.5.3
// Milan v1.2 Table 5.29
// Milan v1.2 Table 5.26
// Milan v1.2 5.5.3.5.16
// Milan v1.2 5.5.3.5.23
// Milan v1.2 5.5.3.5.36
// IEEE 1722.1-2021 8.2.1.15
// Milan v1.2 5.5.2.4
// Milan v1.2 5.5.2.5
// IEEE 1722.1-2021 Table 8-3
// Milan v1.2 5.5.4
// Milan v1.2 5.5.2.7
// Milan v1.2 5.5.4.1
// Milan v1.2 Table 5.40 to 5.43
// Milan v1.2 5.5.4.2
// Milan v1.2 Table 5.44 and 5.45
// Milan v1.2 5.5.4.3
// Milan v1.2 Table 5.46 and 5.47
// Milan v1.2 5.5.4.4
// Milan v1.2 Table 5.48
// IEEE 1722.1-2021 8.2.1.9
// Milan v1.2 Table 5.40
// Milan v1.2 Table 5.44 and 5.46
// Milan v1.2 Table 5.41
// Milan v1.2 5.5.3.5.2
// Milan v1.2 5.6.4.1
// Milan v1.2 5.6.4.5.1
// IEEE 1722.1-2021 6.2.2.5
// Milan v1.2 Table 5.54
// Milan v1.2 5.6.4.5.1 to 5.6.4.5.4

















































































#ifndef ACMP_H
#define ACMP_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#ifndef ACMP_MAX_SINKS
#define ACMP_MAX_SINKS 16u
#endif
#ifndef ACMP_MAX_SOURCES
#define ACMP_MAX_SOURCES 16u
#endif
#define ACMP_MAX_INTERFACES 4u
#define ACMP_OWED_MAX 8u
#define ACMP_AVTP_VERSION 0u            // IEEE 1722.1-2021 8.2.1.3; IEEE 1722.1-2021 6.2.2.3

#define ACMP_ETHERTYPE 0x22F0u          // IEEE 1722-2016 Table 5
#define ACMP_SUBTYPE 0xFCu              // IEEE 1722.1-2021 8.2.1.1; IEEE 1722-2016 Table 6
#define ACMP_MULTICAST_MAC 0x91E0F0010000ull // IEEE 1722.1-2021 Table B.1; IEEE 1722.1-2021 8.2.1
#define ACMP_HEADER_BYTES 14u
#define ACMP_PDU_BYTES 56u              // Milan v1.2 5.5.2.2
#define ACMP_FRAME_BYTES 70u
#define ACMP_CONTROL_DATA_LENGTH 44u
#define ACMP_BINDING_BYTES 20u

// Milan v1.2 Table 5.26; Milan v1.2 Table 5.29
#define ACMP_TMR_NO_RESP_MS 200u
#define ACMP_TMR_RETRY_MS 4000u
#define ACMP_TMR_DELAY_MAX_MS 1000u
#define ACMP_TMR_NO_TK_MS 10000u
#define ACMP_VALID_TIME_UNIT_MS 2000u   // IEEE 1722.1-2021 6.2.2.5

// IEEE 1722.1-2021 Table 8-2; Milan v1.2 5.5.2.2
#define ACMP_MSG_PROBE_TX_COMMAND 0u
#define ACMP_MSG_PROBE_TX_RESPONSE 1u
#define ACMP_MSG_DISCONNECT_TX_COMMAND 2u
#define ACMP_MSG_DISCONNECT_TX_RESPONSE 3u
#define ACMP_MSG_GET_TX_STATE_COMMAND 4u
#define ACMP_MSG_GET_TX_STATE_RESPONSE 5u
#define ACMP_MSG_BIND_RX_COMMAND 6u
#define ACMP_MSG_BIND_RX_RESPONSE 7u
#define ACMP_MSG_UNBIND_RX_COMMAND 8u
#define ACMP_MSG_UNBIND_RX_RESPONSE 9u
#define ACMP_MSG_GET_RX_STATE_COMMAND 10u
#define ACMP_MSG_GET_RX_STATE_RESPONSE 11u
#define ACMP_MSG_GET_TX_CONNECTION_COMMAND 12u
#define ACMP_MSG_GET_TX_CONNECTION_RESPONSE 13u

// IEEE 1722.1-2021 Table 8-3
#define ACMP_STATUS_SUCCESS 0u
#define ACMP_STATUS_LISTENER_UNKNOWN_ID 1u
#define ACMP_STATUS_TALKER_UNKNOWN_ID 2u
#define ACMP_STATUS_TALKER_DEST_MAC_FAIL 3u
#define ACMP_STATUS_LISTENER_TALKER_TIMEOUT 7u
#define ACMP_STATUS_CONTROLLER_NOT_AUTHORIZED 16u
#define ACMP_STATUS_INCOMPATIBLE_REQUEST 17u
#define ACMP_STATUS_NOT_SUPPORTED 31u

// IEEE 1722.1-2021 Table 8-4
// Milan v1.2 Table 5.23
#define ACMP_FLAG_FAST_CONNECT 0x0002u
#define ACMP_FLAG_STREAMING_WAIT 0x0008u
#define ACMP_FLAG_REGISTERING_FAILED 0x0040u

// IEEE 1722.1-2021 Figure 6-1; IEEE 1722.1-2021 6.2.2
#define ACMP_ADP_SUBTYPE 0xFAu
#define ACMP_ADP_FRAME_BYTES 82u
#define ACMP_ADP_MSG_ENTITY_AVAILABLE 0u
#define ACMP_ADP_MSG_ENTITY_DEPARTING 1u

// Milan v1.2 Table 5.28

enum acmp_sink_state {
	ACMP_UNBOUND = 0,
	ACMP_PRB_W_AVAIL = 1,
	ACMP_PRB_W_DELAY = 2,
	ACMP_PRB_W_RESP = 3,
	ACMP_PRB_W_RESP2 = 4,
	ACMP_PRB_W_RETRY = 5,
	ACMP_SETTLED_NO_RSV = 6,
	ACMP_SETTLED_RSV_OK = 7,
};

// Milan v1.2 5.3.8.6
enum acmp_probing {
	ACMP_PROBING_DISABLED = 0,
	ACMP_PROBING_PASSIVE = 1,
	ACMP_PROBING_ACTIVE = 2,
	ACMP_PROBING_COMPLETED = 3,
};

// Milan v1.2 Table 5.29

enum acmp_timer {
	ACMP_TIMER_NONE = 0,
	ACMP_TIMER_NO_RESP,
	ACMP_TIMER_RETRY,
	ACMP_TIMER_DELAY,
	ACMP_TIMER_NO_TK,
};

// Milan v1.2 5.5.2.4
struct acmp_binding {
	uint64_t talker_entity_id;
	uint64_t controller_entity_id;
	uint16_t talker_unique_id;
	bool streaming_wait;
};

// Milan v1.2 5.5.1.3
struct acmp_stream {
	uint64_t stream_id;
	uint64_t dest_mac;
	uint16_t vlan_id;
};

// Milan v1.2 5.5.4.1; Milan v1.2 5.5.4.3
struct acmp_source_state {
	bool dest_mac_valid;                    // Milan v1.2 5.5.4.1
	struct acmp_stream stream;
	bool asking_failed;                     // Milan v1.2 Table 5.47
};

// Milan v1.2 5.3.8.2 to 5.3.8.9
// Milan v1.2 Table 5.22


struct acmp_sink_view {
	enum acmp_sink_state state;
	bool bound;                             // Milan v1.2 5.3.8.2
	struct acmp_binding binding;            // Milan v1.2 5.3.8.3
	bool started;                           // Milan v1.2 5.3.8.7
	enum acmp_probing probing_status;       // Milan v1.2 5.3.8.6
	uint8_t acmp_status;
	bool settled;                           // Milan v1.2 5.3.8.5
	struct acmp_stream stream;              // Milan v1.2 5.3.8.9
	bool talker_registered;                 // Milan v1.2 5.3.8.8
	bool registering_failed;
	bool talker_discovered;                 // Milan v1.2 5.3.8.4
};

struct acmp_config {
	uint64_t entity_id;
	unsigned n_interfaces;
	uint64_t mac[ACMP_MAX_INTERFACES];
	unsigned n_sinks;
	uint8_t sink_interface[ACMP_MAX_SINKS];
	unsigned n_sources;
	uint8_t source_interface[ACMP_MAX_SOURCES];
};



struct acmp_ports {
	void *ctx;


	bool (*send)(void *ctx, unsigned interface, const uint8_t *frame, size_t len);

	uint32_t (*now_ms)(void *ctx);


	void (*timer)(void *ctx, unsigned interface, bool armed, uint32_t deadline_ms);

	void (*gptp)(void *ctx, unsigned interface, uint64_t *gm_id, uint8_t *domain);

	uint32_t (*seed)(void *ctx);





	void (*admit)(void *ctx, unsigned interface, unsigned sink, bool bound, uint64_t talker_entity_id);
};



struct acmp_env {
	void *ctx;
	// Milan v1.2 5.3.4.1

	bool (*locked)(void *ctx, uint64_t *controller_entity_id);

	void (*source)(void *ctx, unsigned index, struct acmp_source_state *out);
	// Milan v1.2 5.5.3.5.18
	// Milan v1.2 5.5.3.5.36

	void (*srp)(void *ctx, unsigned sink, const struct acmp_stream *stream);

	void (*persist)(void *ctx, unsigned sink);

	void (*changed)(void *ctx, unsigned sink);
};

struct acmp_sink {
	enum acmp_sink_state state;
	uint8_t interface;
	bool bound;
	bool started;
	struct acmp_binding binding;
	enum acmp_probing probing;
	uint8_t acmp_status;
	// Milan v1.2 5.5.3.5.3
	uint64_t probe_controller;
	uint64_t probe_talker;
	uint16_t probe_talker_uid;
	uint16_t probe_seq;
	bool probe_retried;                     // Milan v1.2 5.5.3.5.16

	struct acmp_stream stream;
	bool tk_failed;
	// Milan v1.2 5.6.4
	bool disc_running;
	bool discovered;
	uint16_t disc_interface_index;
	uint32_t disc_available_index;

	enum acmp_timer timer;
	uint32_t timer_deadline;
	bool timer_held;
	bool adp_armed;
	uint32_t adp_deadline;

	bool admitted;
	uint64_t admitted_talker;

	uint8_t change_owed;
	struct acmp_sink_view reported;
	uint8_t saved[ACMP_BINDING_BYTES];
};


struct acmp_owed {
	uint8_t interface;
	uint8_t probe_of;
	uint32_t release;
	uint8_t frame[ACMP_FRAME_BYTES];
};

struct acmp {
	struct acmp_config cfg;
	const struct acmp_ports *ports;
	const struct acmp_env *env;
	struct acmp_sink sinks[ACMP_MAX_SINKS];
	uint16_t sequence_id;                   // IEEE 1722.1-2021 8.2.1.15
	uint32_t rng;
	bool seeded;
	bool in_port;
	bool now_read;
	uint32_t now;
	bool timer_armed[ACMP_MAX_INTERFACES];
	uint32_t timer_at[ACMP_MAX_INTERFACES];
	struct acmp_owed owed[ACMP_OWED_MAX];
	unsigned owed_head;
	unsigned owed_count;

	uint32_t rx_ignored;
	uint32_t rx_malformed;
	uint32_t unknown_sink;
	uint32_t probe_mismatch;
	uint32_t refused_locked;
	uint32_t adp_ignored;
	uint32_t impossible;                    // Milan v1.2 Table 5.30; Milan v1.2 Table 5.54
	uint32_t busy_drops;
	uint32_t probes_lost;
	uint32_t deferred_sends;
	uint32_t reentries;
	uint32_t draws;
	uint32_t last_draw_ms;
};

// Milan v1.2 5.5.3.5.1


bool acmp_init(struct acmp *a, const struct acmp_config *cfg, const struct acmp_ports *ports,
	       const struct acmp_env *env);


void acmp_rx(struct acmp *a, unsigned interface, const uint8_t *frame, size_t len);
void acmp_adp_rx(struct acmp *a, unsigned interface, const uint8_t *frame, size_t len);
void acmp_timer_expired(struct acmp *a, unsigned interface);

// Milan v1.2 Table 5.29


void acmp_tk_registered(struct acmp *a, unsigned sink, bool failed);
void acmp_tk_unregistered(struct acmp *a, unsigned sink);
// Milan v1.2 Table 5.23
// Milan v1.2 Table 5.30


void acmp_tk_kind_changed(struct acmp *a, unsigned sink, bool failed);

// Milan v1.2 5.3.8.7

bool acmp_set_started(struct acmp *a, unsigned sink, bool started);



bool acmp_poll(struct acmp *a);



enum acmp_restore {
	ACMP_RESTORE_APPLIED = 0,
	ACMP_RESTORE_REFUSED = 1,
};
enum acmp_restore acmp_restore_binding(struct acmp *a, unsigned sink, const uint8_t *payload, unsigned len);
void acmp_restore_rollback(struct acmp *a);



void acmp_open(struct acmp *a);

bool acmp_binding_latch(const struct acmp *a, unsigned sink, uint8_t payload[ACMP_BINDING_BYTES]);


bool acmp_view(const struct acmp *a, unsigned sink, struct acmp_sink_view *view);

bool acmp_change_pending(const struct acmp *a, unsigned sink);

#ifdef CTRL_REENTRY_ASSERT


void ctrl_reentry_assert(const char *module);
#endif

#ifdef __cplusplus
}
#endif

#endif
