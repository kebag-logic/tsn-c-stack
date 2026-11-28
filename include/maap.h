// SPDX-FileCopyrightText: 2026 Kebag Logic
// SPDX-License-Identifier: MIT
// IEEE 1722-2016 Annex B


#ifndef CTRL_MAAP_H
#define CTRL_MAAP_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define MAAP_POOL_BASE UINT64_C(0x91e0f0000000)
#define MAAP_POOL_SIZE 0xfe00u                  // IEEE 1722-2016 B.4; IEEE 1722-2016 Table B.9
#define MAAP_MULTICAST UINT64_C(0x91e0f000ff00) // IEEE 1722-2016 B.4; IEEE 1722-2016 Table B.10
#define MAAP_FRAME_BYTES 60u
#define MAAP_PROBE_RETRANSMITS 3u              // IEEE 1722-2016 B.3.3; IEEE 1722-2016 Table B.8
#define MAAP_PROBE_BASE_MS 500u
#define MAAP_PROBE_VARIATION_MS 100u
#define MAAP_ANNOUNCE_BASE_MS 30000u
#define MAAP_ANNOUNCE_VARIATION_MS 2000u
#define MAAP_SERVICE_MS 10u
#define MAAP_QUEUE_FRAMES 16u

enum maap_state { MAAP_INITIAL, MAAP_PROBE, MAAP_DEFEND };
enum maap_message { MAAP_MSG_PROBE = 1, MAAP_MSG_DEFEND = 2, MAAP_MSG_ANNOUNCE = 3 };

struct maap_ports {
	void *ctx;

	bool (*send)(void *ctx, unsigned interface, const uint8_t *frame, size_t len);
	void (*timer_start)(void *ctx, unsigned interface, uint32_t delay_ms);
	void (*timer_stop)(void *ctx, unsigned interface);


	void (*range)(void *ctx, unsigned interface, uint64_t base, uint16_t count, bool valid);
	// IEEE 1722-2016 B.3.6.1
	uint32_t (*clock)(void *ctx);
};

struct maap {
	const struct maap_ports *ports;
	uint64_t mac;
	uint64_t base;
	uint64_t preferred;
	uint16_t count;
	uint8_t interface;
	enum maap_state state;
	uint32_t rng;
	uint32_t last_delay_ms;
	uint8_t probe_count;
	bool enabled;
	bool operational;
	bool timer_running;
	bool expiry_owed;
	bool valid;
	bool in_call;
	uint8_t queue[MAAP_QUEUE_FRAMES][MAAP_FRAME_BYTES];
	unsigned queued;

	uint32_t conflicts;
	uint32_t discarded;
	uint32_t stale_expiries;
	uint32_t deferred;
	uint32_t overflow;
	uint32_t reentries;
};



bool maap_init(struct maap *m, const struct maap_ports *ports, unsigned interface,
	       uint64_t mac, uint16_t count);
// IEEE 1722-2016 Table B.7



bool maap_begin(struct maap *m, uint64_t preferred);
void maap_release(struct maap *m);


void maap_port_operational(struct maap *m, bool up);
void maap_rx(struct maap *m, const uint8_t *frame, size_t len);
void maap_timer_expired(struct maap *m);


bool maap_poll(struct maap *m);

#ifdef __cplusplus
}
#endif
#endif
