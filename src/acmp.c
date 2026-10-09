// SPDX-FileCopyrightText: 2026 Kebag Logic
// SPDX-License-Identifier: MIT
// Milan v1.2 Table 5.29























#include "acmp.h"

#include <string.h>

#include "wire.h"

#ifdef CTRL_REENTRY_ASSERT
#define REENTRY_TRAP() ctrl_reentry_assert("acmp")
#else
#define REENTRY_TRAP() ((void)0)
#endif

// IEEE 1722.1-2021 Figure 8-1

#define PDU ACMP_HEADER_BYTES
#define O_MSG (PDU + 1u)
#define O_STATUS (PDU + 2u)
#define O_STREAM_ID (PDU + 4u)
#define O_CONTROLLER (PDU + 12u)
#define O_TALKER (PDU + 20u)
#define O_LISTENER (PDU + 28u)
#define O_TALKER_UID (PDU + 36u)
#define O_LISTENER_UID (PDU + 38u)
#define O_DEST_MAC (PDU + 40u)
#define O_COUNT (PDU + 46u)
#define O_SEQ (PDU + 48u)
#define O_FLAGS (PDU + 50u)
#define O_VLAN (PDU + 52u)
#define AVTP_VERSION(frame) (((frame)[O_MSG] >> 4) & 0x07u)   // IEEE 1722-2016 Figure 5

// IEEE 1722.1-2021 Figure 6-1; IEEE 1722.1-2021 6.2.2
#define A_VALID_TIME (PDU + 2u)
#define A_ENTITY_ID (PDU + 4u)
#define A_AVAILABLE_INDEX (PDU + 36u)
#define A_GM (PDU + 40u)
#define A_DOMAIN (PDU + 48u)
#define A_INTERFACE_INDEX (PDU + 54u)


#define BIND_VALID 0x01u
#define BIND_STARTED 0x02u
#define BIND_STREAMING_WAIT 0x04u


struct pdu {
	uint8_t msg;
	uint8_t status;
	uint64_t stream_id;
	uint64_t controller;
	uint64_t talker;
	uint64_t listener;
	uint16_t talker_uid;
	uint16_t listener_uid;
	uint64_t dest_mac;
	uint16_t count;
	uint16_t seq;
	uint16_t flags;
	uint16_t vlan;
};



static bool enter(struct acmp *a)
{
	if (a->in_port) {
		a->reentries++;
		REENTRY_TRAP();
		return false;
	}
	a->now_read = false;
	return true;
}

static bool p_send(struct acmp *a, unsigned interface, const uint8_t *frame)
{
	a->in_port = true;
	bool ok = a->ports->send(a->ports->ctx, interface, frame, ACMP_FRAME_BYTES);
	a->in_port = false;
	return ok;
}



static uint32_t now(struct acmp *a)
{
	if (!a->now_read) {
		a->in_port = true;
		a->now = a->ports->now_ms(a->ports->ctx);
		a->in_port = false;
		a->now_read = true;
	}
	return a->now;
}

static void p_timer(struct acmp *a, unsigned interface, bool armed, uint32_t deadline_ms)
{
	a->in_port = true;
	a->ports->timer(a->ports->ctx, interface, armed, deadline_ms);
	a->in_port = false;
}

static void p_gptp(struct acmp *a, unsigned interface, uint64_t *gm, uint8_t *domain)
{
	a->in_port = true;
	a->ports->gptp(a->ports->ctx, interface, gm, domain);
	a->in_port = false;
}

static uint32_t p_seed(struct acmp *a)
{
	a->in_port = true;
	uint32_t seed = a->ports->seed(a->ports->ctx);
	a->in_port = false;
	return seed;
}

static bool p_locked(struct acmp *a, uint64_t *controller)
{
	a->in_port = true;
	bool locked = a->env->locked(a->env->ctx, controller);
	a->in_port = false;
	return locked;
}

static void p_source(struct acmp *a, unsigned index, struct acmp_source_state *out)
{
	a->in_port = true;
	a->env->source(a->env->ctx, index, out);
	a->in_port = false;
}

static void p_srp(struct acmp *a, unsigned sink, const struct acmp_stream *stream)
{
	a->in_port = true;
	a->env->srp(a->env->ctx, sink, stream);
	a->in_port = false;
}

static void p_persist(struct acmp *a, unsigned sink)
{
	a->in_port = true;
	a->env->persist(a->env->ctx, sink);
	a->in_port = false;
}

static void p_changed(struct acmp *a, unsigned sink)
{
	a->in_port = true;
	a->env->changed(a->env->ctx, sink);
	a->in_port = false;
}

static void p_admit(struct acmp *a, unsigned interface, unsigned sink, bool bound, uint64_t talker)
{
	a->in_port = true;
	a->ports->admit(a->ports->ctx, interface, sink, bound, talker);
	a->in_port = false;
}



static void decode(const uint8_t *frame, struct pdu *p)
{
	p->msg = frame[O_MSG] & 0x0Fu;
	p->status = (uint8_t)(frame[O_STATUS] >> 3);
	p->stream_id = wire_be64(frame + O_STREAM_ID);
	p->controller = wire_be64(frame + O_CONTROLLER);
	p->talker = wire_be64(frame + O_TALKER);
	p->listener = wire_be64(frame + O_LISTENER);
	p->talker_uid = wire_be16(frame + O_TALKER_UID);
	p->listener_uid = wire_be16(frame + O_LISTENER_UID);
	p->dest_mac = ((uint64_t)wire_be16(frame + O_DEST_MAC) << 32) | wire_be32(frame + O_DEST_MAC + 2u);
	p->count = wire_be16(frame + O_COUNT);
	p->seq = wire_be16(frame + O_SEQ);
	p->flags = wire_be16(frame + O_FLAGS);
	p->vlan = wire_be16(frame + O_VLAN);
}

// IEEE 1722.1-2021 8.2.1
// IEEE 1722.1-2021 8.2.1.2
// IEEE 1722.1-2021 8.2.1.3
// Milan v1.2 5.5.2.2
static void build(const struct acmp *a, unsigned interface, const struct pdu *p, uint8_t *frame)
{
	memset(frame, 0, ACMP_FRAME_BYTES);
	wire_put_be(frame, ACMP_MULTICAST_MAC, 6);
	wire_put_be(frame + 6, a->cfg.mac[interface], 6);
	wire_put_be(frame + 12, ACMP_ETHERTYPE, 2);
	frame[PDU] = ACMP_SUBTYPE;
	frame[O_MSG] = p->msg & 0x0Fu;
	wire_put_be(frame + O_STATUS, ((uint32_t)p->status << 11) | ACMP_CONTROL_DATA_LENGTH, 2);
	wire_put_be(frame + O_STREAM_ID, p->stream_id, 8);
	wire_put_be(frame + O_CONTROLLER, p->controller, 8);
	wire_put_be(frame + O_TALKER, p->talker, 8);
	wire_put_be(frame + O_LISTENER, p->listener, 8);
	wire_put_be(frame + O_TALKER_UID, p->talker_uid, 2);
	wire_put_be(frame + O_LISTENER_UID, p->listener_uid, 2);
	wire_put_be(frame + O_DEST_MAC, p->dest_mac, 6);
	wire_put_be(frame + O_COUNT, p->count, 2);
	wire_put_be(frame + O_SEQ, p->seq, 2);
	wire_put_be(frame + O_FLAGS, p->flags, 2);
	wire_put_be(frame + O_VLAN, p->vlan, 2);
}




static struct pdu echo(const struct pdu *cmd, uint8_t status)
{
	struct pdu r;
	memset(&r, 0, sizeof r);
	r.msg = (uint8_t)(cmd->msg + 1u);
	r.status = status;
	r.controller = cmd->controller;
	r.talker = cmd->talker;
	r.listener = cmd->listener;
	r.talker_uid = cmd->talker_uid;
	r.listener_uid = cmd->listener_uid;
	r.seq = cmd->seq;
	return r;
}



enum sent { SENT, OWED, LOST };





static enum sent transmit(struct acmp *a, unsigned interface, const uint8_t *frame, uint32_t release,
			  unsigned probe_of)
{
	if (a->owed_count == 0u && p_send(a, interface, frame)) {
		return SENT;
	}
	if (a->owed_count >= ACMP_OWED_MAX) {
		return LOST;
	}
	struct acmp_owed *o = &a->owed[(a->owed_head + a->owed_count) % ACMP_OWED_MAX];
	o->interface = (uint8_t)interface;
	o->probe_of = (uint8_t)probe_of;
	o->release = release;
	memcpy(o->frame, frame, ACMP_FRAME_BYTES);
	a->owed_count++;
	a->deferred_sends++;
	for (unsigned k = 0; k < a->cfg.n_sinks; ++k) {
		a->sinks[k].change_owed = (uint8_t)(a->sinks[k].change_owed + ((release >> k) & 1u));
	}
	return OWED;
}


static void respond(struct acmp *a, unsigned interface, const struct pdu *r, uint32_t release)
{
	uint8_t frame[ACMP_FRAME_BYTES];
	build(a, interface, r, frame);
	(void)transmit(a, interface, frame, release, 0u);
}



static bool room(struct acmp *a)
{
	if (a->owed_count < ACMP_OWED_MAX) {
		return true;
	}
	a->busy_drops++;
	return false;
}



static bool due(uint32_t deadline, uint32_t at)
{
	return (int32_t)(deadline - at) <= 0;
}

static void sm_timer(struct acmp *a, struct acmp_sink *s, enum acmp_timer kind, uint32_t delay_ms)
{
	s->timer = kind;
	s->timer_deadline = now(a) + delay_ms;
	s->timer_held = false;
}

static void sm_stop(struct acmp_sink *s)
{
	s->timer = ACMP_TIMER_NONE;
	s->timer_held = false;
}


static bool sm_running(const struct acmp_sink *s)
{
	return s->timer != ACMP_TIMER_NONE && !s->timer_held;
}



static uint32_t draw_ms(struct acmp *a)
{
	if (!a->seeded) {
		a->rng ^= p_seed(a);
		a->seeded = true;
		if (a->rng == 0u) {
			a->rng = 1u;
		}
	}
	uint32_t x = a->rng;
	x ^= x << 13;
	x ^= x >> 17;
	x ^= x << 5;
	a->rng = x;
	uint32_t ms = ((x >> 16) * (ACMP_TMR_DELAY_MAX_MS + 1u)) >> 16;
	a->draws++;
	a->last_draw_ms = ms;
	return ms;
}


static void earliest(bool *any, uint32_t *at, bool armed, uint32_t deadline)
{
	if (armed && (!*any || (int32_t)(deadline - *at) < 0)) {
		*at = deadline;
		*any = true;
	}
}



static void rearm(struct acmp *a)
{
	for (unsigned i = 0; i < a->cfg.n_interfaces; ++i) {
		bool any = false;
		uint32_t at = 0;
		for (unsigned k = 0; k < a->cfg.n_sinks; ++k) {
			const struct acmp_sink *s = &a->sinks[k];
			if (s->interface == i) {
				earliest(&any, &at, sm_running(s), s->timer_deadline);
				earliest(&any, &at, s->adp_armed, s->adp_deadline);
			}
		}
		if (any && (!a->timer_armed[i] || a->timer_at[i] != at)) {
			a->timer_armed[i] = true;
			a->timer_at[i] = at;
			p_timer(a, i, true, at);
		} else if (!any && a->timer_armed[i]) {
			a->timer_armed[i] = false;
			p_timer(a, i, false, 0u);
		}
	}
}



static void view_of(const struct acmp_sink *s, struct acmp_sink_view *v)
{
	memset(v, 0, sizeof *v);
	v->state = s->state;
	v->bound = s->bound;
	v->binding = s->binding;
	v->started = s->started;
	v->probing_status = s->probing;
	v->acmp_status = s->acmp_status;
	v->settled = s->state == ACMP_SETTLED_NO_RSV || s->state == ACMP_SETTLED_RSV_OK;
	if (v->settled) {
		v->stream = s->stream;
	}
	v->talker_registered = s->state == ACMP_SETTLED_RSV_OK;
	v->registering_failed = v->talker_registered && s->tk_failed;
	v->talker_discovered = s->discovered;
}

// Milan v1.2 Table 5.22




static bool view_equal(const struct acmp_sink_view *x, const struct acmp_sink_view *y)
{
	uint64_t diff = (x->stream.stream_id ^ y->stream.stream_id) | (x->stream.dest_mac ^ y->stream.dest_mac) |
			(uint64_t)(x->stream.vlan_id ^ y->stream.vlan_id) |
			(uint64_t)((unsigned)x->probing_status ^ (unsigned)y->probing_status) |
			(uint64_t)(x->acmp_status ^ y->acmp_status) | (uint64_t)(x->bound != y->bound) |
			(uint64_t)(x->started != y->started) | (uint64_t)(x->talker_registered != y->talker_registered) |
			(uint64_t)(x->registering_failed != y->registering_failed);
	return diff == 0u;
}

// Milan v1.2 5.5.3.5.8

static void record_of(const struct acmp_sink *s, uint8_t payload[ACMP_BINDING_BYTES])
{
	memset(payload, 0, ACMP_BINDING_BYTES);
	if (s->bound) {
		payload[0] = (uint8_t)(BIND_VALID | (s->started ? BIND_STARTED : 0u) |
				       (s->binding.streaming_wait ? BIND_STREAMING_WAIT : 0u));
		wire_put_be(payload + 2, s->binding.talker_unique_id, 2);
		wire_put_be(payload + 4, s->binding.talker_entity_id, 8);
		wire_put_be(payload + 12, s->binding.controller_entity_id, 8);
	}
}



static bool same_record(const uint8_t *x, const uint8_t *y)
{
	uint8_t diff = 0;
	for (unsigned i = 0; i < ACMP_BINDING_BYTES; ++i) {
		diff |= (uint8_t)(x[i] ^ y[i]);
	}
	return diff == 0u;
}

// Milan v1.2 5.6.4.1


static void admit(struct acmp *a)
{
	for (unsigned k = 0; k < a->cfg.n_sinks; ++k) {
		struct acmp_sink *s = &a->sinks[k];
		uint64_t talker = s->binding.talker_entity_id;
		if (s->bound != s->admitted || (s->bound && talker != s->admitted_talker)) {
			s->admitted = s->bound;
			s->admitted_talker = talker;
			p_admit(a, s->interface, k, s->bound, talker);
		}
	}
}


static void finish(struct acmp *a)
{
	rearm(a);
	admit(a);
	for (unsigned k = 0; k < a->cfg.n_sinks; ++k) {
		struct acmp_sink *s = &a->sinks[k];
		uint8_t record[ACMP_BINDING_BYTES];
		record_of(s, record);
		if (!same_record(record, s->saved)) {
			memcpy(s->saved, record, ACMP_BINDING_BYTES);
			p_persist(a, k);
		}
		struct acmp_sink_view v;
		view_of(s, &v);
		if (s->change_owed == 0u && !view_equal(&v, &s->reported)) {
			s->reported = v;
			p_changed(a, k);
		}
	}
}

// Milan v1.2 5.5.3.5.1


static void sink_reset(struct acmp *a, unsigned k)
{
	struct acmp_sink *s = &a->sinks[k];
	bool admitted = s->admitted;
	uint64_t admitted_talker = s->admitted_talker;
	memset(s, 0, sizeof *s);
	s->admitted = admitted;
	s->admitted_talker = admitted_talker;
	s->interface = a->cfg.sink_interface[k];
	s->state = ACMP_UNBOUND;
	s->probing = ACMP_PROBING_DISABLED;
}



static void sink_settle(struct acmp_sink *s)
{
	record_of(s, s->saved);
	view_of(s, &s->reported);
}

// Milan v1.2 5.6.4

static void disc_start(struct acmp_sink *s)
{
	s->disc_running = true;
	s->discovered = false;
	s->adp_armed = false;
}

static void disc_stop(struct acmp_sink *s)
{
	s->disc_running = false;
	s->discovered = false;
	s->adp_armed = false;
}


static void delay(struct acmp *a, struct acmp_sink *s)
{
	sm_timer(a, s, ACMP_TIMER_DELAY, draw_ms(a));
	s->state = ACMP_PRB_W_DELAY;
}

// Milan v1.2 5.5.3.5.15

static void passive(struct acmp_sink *s)
{
	s->probing = ACMP_PROBING_PASSIVE;
	s->acmp_status = ACMP_STATUS_SUCCESS;
	s->state = ACMP_PRB_W_AVAIL;
}

// Milan v1.2 5.5.3.5.36 and 5.5.3.5.48
static void reprobe(struct acmp *a, struct acmp_sink *s)
{
	if (!s->discovered) {
		passive(s);
		return;
	}
	s->probing = ACMP_PROBING_ACTIVE;
	s->acmp_status = ACMP_STATUS_SUCCESS;
	delay(a, s);
}

// Milan v1.2 5.5.3.5.9
// Milan v1.2 5.5.3.5.14

static void tk_discovered(struct acmp *a, struct acmp_sink *s)
{
	s->discovered = true;
	if (s->state == ACMP_PRB_W_AVAIL) {
		s->probing = ACMP_PROBING_ACTIVE;
		s->acmp_status = ACMP_STATUS_SUCCESS;
		delay(a, s);
	}
}

// Milan v1.2 5.5.3.5.15
// Milan v1.2 5.5.3.5.41
// Milan v1.2 Table 5.30

static void tk_departed(struct acmp_sink *s)
{
	s->discovered = false;
	if (s->state == ACMP_PRB_W_DELAY || s->state == ACMP_PRB_W_RESP || s->state == ACMP_PRB_W_RESP2 ||
	    s->state == ACMP_PRB_W_RETRY) {
		sm_stop(s);
		passive(s);
	}
}

static void adp_arm(struct acmp *a, struct acmp_sink *s, uint32_t valid_ms)
{
	s->adp_armed = true;
	s->adp_deadline = now(a) + valid_ms;
}



struct adpdu {
	unsigned interface;
	uint16_t ifx;
	uint32_t index;
	uint32_t valid_ms;
	uint64_t gm;
	uint8_t domain;
	bool sampled;
	uint64_t local_gm;
	uint8_t local_domain;
};

// Milan v1.2 5.6.4.5.1
// Milan v1.2 5.6.4.5.2
static bool gm_matches(struct acmp *a, struct adpdu *d)
{
	if (!d->sampled) {
		p_gptp(a, d->interface, &d->local_gm, &d->local_domain);
		d->sampled = true;
	}
	return d->gm == d->local_gm && d->domain == d->local_domain;
}

// Milan v1.2 5.6.4.5.1; Milan v1.2 5.6.4.5.2
static void disc_available(struct acmp *a, struct acmp_sink *s, struct adpdu *d)
{
	uint16_t ifx = d->ifx;
	uint32_t index = d->index;
	uint32_t valid_ms = d->valid_ms;
	if (!s->discovered) {
		if (!gm_matches(a, d)) {
			return;                                 // Milan v1.2 5.6.4.5.1
		}
		s->disc_interface_index = ifx;
		s->disc_available_index = index;
		adp_arm(a, s, valid_ms);
		tk_discovered(a, s);
		return;
	}
	if (ifx != s->disc_interface_index) {
		return;                                         // Milan v1.2 5.6.4.5.2
	}
	if (index <= s->disc_available_index) {
		tk_departed(s);
		if (!gm_matches(a, d)) {
			s->adp_armed = false;
			return;
		}
		tk_discovered(a, s);
	}
	s->disc_available_index = index;
	adp_arm(a, s, valid_ms);
}

// Milan v1.2 Table 5.54
// Milan v1.2 5.6.4.5.3
static void disc_departing(struct acmp_sink *s, uint16_t ifx)
{
	if (!s->discovered || ifx != s->disc_interface_index) {
		return;
	}
	s->adp_armed = false;
	tk_departed(s);
}



// Milan v1.2 5.5.3.5.18

static void srp_stop(struct acmp *a, unsigned k)
{
	struct acmp_sink *s = &a->sinks[k];
	memset(&s->stream, 0, sizeof s->stream);
	s->tk_failed = false;
	p_srp(a, k, NULL);
}



static void no_resp_from_send(struct acmp *a, struct acmp_sink *s)
{
	a->now_read = false;
	sm_timer(a, s, ACMP_TIMER_NO_RESP, ACMP_TMR_NO_RESP_MS);
}

// Milan v1.2 Table 5.33
// Milan v1.2 5.5.3.5.3
// Milan v1.2 5.5.3.5.16



static void send_probe(struct acmp *a, unsigned k)
{
	struct acmp_sink *s = &a->sinks[k];
	struct pdu p;
	memset(&p, 0, sizeof p);
	p.msg = ACMP_MSG_PROBE_TX_COMMAND;
	p.controller = s->probe_controller;
	p.talker = s->probe_talker;
	p.listener = a->cfg.entity_id;
	p.talker_uid = s->probe_talker_uid;
	p.listener_uid = (uint16_t)k;
	p.seq = s->probe_seq;
	p.flags = ACMP_FLAG_FAST_CONNECT;
	uint8_t frame[ACMP_FRAME_BYTES];
	build(a, s->interface, &p, frame);
	enum sent sent = transmit(a, s->interface, frame, 0u, k + 1u);
	if (sent == SENT) {
		no_resp_from_send(a, s);
	} else if (sent == OWED) {
		s->timer = ACMP_TIMER_NO_RESP;
		s->timer_held = true;
	} else {
		sm_timer(a, s, ACMP_TIMER_NO_RESP, ACMP_TMR_NO_RESP_MS);
		a->probes_lost++;
	}
}

// Milan v1.2 5.5.3.5.3
// Milan v1.2 5.5.3.5.16

static void probe_left(struct acmp *a, const struct acmp_owed *o)
{
	if (o->probe_of == 0u) {
		return;
	}
	struct acmp_sink *s = &a->sinks[o->probe_of - 1u];
	if (s->timer_held && wire_be16(o->frame + O_SEQ) == s->probe_seq) {
		no_resp_from_send(a, s);
	}
}

// IEEE 1722.1-2021 8.2.1.15
// Milan v1.2 5.5.3.5.3
static void probe(struct acmp *a, unsigned k)
{
	struct acmp_sink *s = &a->sinks[k];
	s->probe_controller = s->binding.controller_entity_id;
	s->probe_talker = s->binding.talker_entity_id;
	s->probe_talker_uid = s->binding.talker_unique_id;
	s->probe_seq = a->sequence_id;
	a->sequence_id = (uint16_t)(a->sequence_id + 1u);
	s->probe_retried = false;
	send_probe(a, k);
}


static void sm_expired(struct acmp *a, unsigned k)
{
	struct acmp_sink *s = &a->sinks[k];
	enum acmp_timer kind = s->timer;
	sm_stop(s);
	if (kind == ACMP_TIMER_DELAY) {                         // Milan v1.2 5.5.3.5.10
		probe(a, k);
		s->state = ACMP_PRB_W_RESP;
	} else if (kind == ACMP_TIMER_NO_RESP && s->state == ACMP_PRB_W_RESP) {   // Milan v1.2 5.5.3.5.16
		s->probe_retried = true;
		send_probe(a, k);
		s->state = ACMP_PRB_W_RESP2;
	} else if (kind == ACMP_TIMER_NO_RESP) {                // Milan v1.2 5.5.3.5.23
		sm_timer(a, s, ACMP_TIMER_RETRY, ACMP_TMR_RETRY_MS);
		s->acmp_status = ACMP_STATUS_LISTENER_TALKER_TIMEOUT;
		s->state = ACMP_PRB_W_RETRY;
	} else if (kind == ACMP_TIMER_RETRY && !s->discovered) {   // Milan v1.2 5.5.3.5.30
		passive(s);
	} else if (kind == ACMP_TIMER_RETRY) {
		delay(a, s);
	} else {                                                // Milan v1.2 5.5.3.5.36
		srp_stop(a, k);
		reprobe(a, s);
	}
}

// Milan v1.2 5.5.3.1

static bool lock_refuses(struct acmp *a, const struct pdu *cmd)
{
	uint64_t holder = 0;
	if (p_locked(a, &holder) && holder != cmd->controller) {
		a->refused_locked++;
		return true;
	}
	return false;
}

static void bind_response(struct acmp *a, unsigned interface, unsigned k, const struct pdu *cmd)
{
	struct pdu r = echo(cmd, ACMP_STATUS_SUCCESS);             // Milan v1.2 Table 5.32
	r.count = 1u;
	r.flags = cmd->flags & ACMP_FLAG_STREAMING_WAIT;
	respond(a, interface, &r, 1u << k);
}

// Milan v1.2 5.5.3.5.3
static void bind(struct acmp *a, unsigned interface, unsigned k, const struct pdu *cmd)
{
	struct acmp_sink *s = &a->sinks[k];
	bool sw = (cmd->flags & ACMP_FLAG_STREAMING_WAIT) != 0u;
	if (s->bound && cmd->talker == s->binding.talker_entity_id && cmd->talker_uid == s->binding.talker_unique_id) {

		s->binding.controller_entity_id = cmd->controller;
		s->binding.streaming_wait = sw;
		s->started = !sw;
		bind_response(a, interface, k, cmd);
		return;
	}
	if (s->state == ACMP_SETTLED_NO_RSV || s->state == ACMP_SETTLED_RSV_OK) {
		srp_stop(a, k);                                 // Milan v1.2 5.5.3.5.37
	}
	disc_stop(s);
	sm_stop(s);
	s->bound = true;
	s->binding.talker_entity_id = cmd->talker;
	s->binding.talker_unique_id = cmd->talker_uid;
	s->binding.controller_entity_id = cmd->controller;
	s->binding.streaming_wait = sw;
	// Milan v1.2 5.3.8.7

	s->started = !sw;
	bind_response(a, interface, k, cmd);
	disc_start(s);
	probe(a, k);
	s->probing = ACMP_PROBING_ACTIVE;
	s->acmp_status = ACMP_STATUS_SUCCESS;
	s->state = ACMP_PRB_W_RESP;
}

// Milan v1.2 5.5.3.5.5

static void unbind(struct acmp *a, unsigned interface, unsigned k, const struct pdu *cmd)
{
	struct acmp_sink *s = &a->sinks[k];
	if (s->state == ACMP_SETTLED_NO_RSV || s->state == ACMP_SETTLED_RSV_OK) {
		srp_stop(a, k);
	}
	disc_stop(s);
	s->bound = false;
	memset(&s->binding, 0, sizeof s->binding);
	s->started = false;
	s->probing = ACMP_PROBING_DISABLED;
	s->acmp_status = ACMP_STATUS_SUCCESS;
	sm_stop(s);
	struct pdu r = echo(cmd, ACMP_STATUS_SUCCESS);             // Milan v1.2 Table 5.36
	r.talker = 0u;
	r.talker_uid = 0u;
	respond(a, interface, &r, 1u << k);
	s->state = ACMP_UNBOUND;
}

// Milan v1.2 Table 5.34; Milan v1.2 Table 5.37; Milan v1.2 Table 5.38 and 5.39
static void get_rx_state(struct acmp *a, unsigned interface, unsigned k, const struct pdu *cmd)
{
	const struct acmp_sink *s = &a->sinks[k];
	struct pdu r = echo(cmd, ACMP_STATUS_SUCCESS);
	r.talker = s->binding.talker_entity_id;
	r.talker_uid = s->binding.talker_unique_id;
	if (s->bound) {
		r.count = 1u;
		r.flags = (uint16_t)(ACMP_FLAG_FAST_CONNECT | (s->binding.streaming_wait ? ACMP_FLAG_STREAMING_WAIT : 0u));
	}
	if (s->state == ACMP_SETTLED_NO_RSV || s->state == ACMP_SETTLED_RSV_OK) {
		r.stream_id = s->stream.stream_id;
		r.dest_mac = s->stream.dest_mac;
		r.vlan = s->stream.vlan_id;
	}
	if (s->state == ACMP_SETTLED_RSV_OK && s->tk_failed) {
		r.flags |= ACMP_FLAG_REGISTERING_FAILED;
	}
	respond(a, interface, &r, 0u);
}

static void listener_command(struct acmp *a, unsigned interface, const struct pdu *cmd)
{
	if (!room(a)) {
		return;
	}
	unsigned k = cmd->listener_uid;
	if (k >= a->cfg.n_sinks) {
		a->unknown_sink++;
		struct pdu r = echo(cmd, ACMP_STATUS_LISTENER_UNKNOWN_ID);         // Milan v1.2 Table 5.27
		respond(a, interface, &r, 0u);
		return;
	}
	if (cmd->msg == ACMP_MSG_GET_RX_STATE_COMMAND) {
		get_rx_state(a, interface, k, cmd);
	} else if (lock_refuses(a, cmd)) {
		struct pdu r = echo(cmd, ACMP_STATUS_CONTROLLER_NOT_AUTHORIZED);   // Milan v1.2 Table 5.31; Milan v1.2 Table 5.35
		respond(a, interface, &r, 0u);
	} else if (cmd->msg == ACMP_MSG_BIND_RX_COMMAND) {
		bind(a, interface, k, cmd);
	} else {
		unbind(a, interface, k, cmd);
	}
}

// Milan v1.2 5.5.3.5.18
// Milan v1.2 5.5.3.5.25; Milan v1.2 Table 5.30
static void probe_response(struct acmp *a, const struct pdu *rsp)
{
	unsigned k = rsp->listener_uid;
	if (k >= a->cfg.n_sinks) {
		a->unknown_sink++;                              // Milan v1.2 5.5.3.1
		return;
	}
	struct acmp_sink *s = &a->sinks[k];
	if (s->state != ACMP_PRB_W_RESP && s->state != ACMP_PRB_W_RESP2) {
		a->rx_ignored++;
		return;
	}
	if (rsp->controller != s->probe_controller || rsp->talker != s->probe_talker ||
	    rsp->talker_uid != s->probe_talker_uid || rsp->seq != s->probe_seq) {
		a->probe_mismatch++;
		return;
	}
	sm_stop(s);
	if (rsp->status != ACMP_STATUS_SUCCESS) {
		sm_timer(a, s, ACMP_TIMER_RETRY, ACMP_TMR_RETRY_MS);
		s->acmp_status = rsp->status;
		s->state = ACMP_PRB_W_RETRY;
		return;
	}
	s->stream.stream_id = rsp->stream_id;                   // Milan v1.2 5.3.8.9
	s->stream.dest_mac = rsp->dest_mac;
	s->stream.vlan_id = rsp->vlan;
	p_srp(a, k, &s->stream);
	sm_timer(a, s, ACMP_TIMER_NO_TK, ACMP_TMR_NO_TK_MS);
	s->probing = ACMP_PROBING_COMPLETED;
	s->acmp_status = ACMP_STATUS_SUCCESS;
	s->state = ACMP_SETTLED_NO_RSV;
}

// Milan v1.2 5.5.4

static void talker_command(struct acmp *a, unsigned interface, const struct pdu *cmd)
{
	if (!room(a)) {
		return;
	}
	unsigned src = cmd->talker_uid;
	if (cmd->msg == ACMP_MSG_GET_TX_CONNECTION_COMMAND) {
		struct pdu r = echo(cmd, ACMP_STATUS_NOT_SUPPORTED);              // Milan v1.2 5.5.4.4; Milan v1.2 Table 5.48
		respond(a, interface, &r, 0u);
		return;
	}
	if (src >= a->cfg.n_sources) {
		struct pdu r = echo(cmd, ACMP_STATUS_TALKER_UNKNOWN_ID);          // Milan v1.2 Table 5.40; Milan v1.2 Table 5.44; Milan v1.2 Table 5.46
		respond(a, interface, &r, 0u);
		return;
	}
	if (cmd->msg == ACMP_MSG_DISCONNECT_TX_COMMAND) {
		struct pdu r = echo(cmd, ACMP_STATUS_SUCCESS);                    // Milan v1.2 5.5.4.2; Milan v1.2 Table 5.45
		respond(a, interface, &r, 0u);
		return;
	}
	if (cmd->msg == ACMP_MSG_PROBE_TX_COMMAND && interface != a->cfg.source_interface[src]) {
		struct pdu r = echo(cmd, ACMP_STATUS_INCOMPATIBLE_REQUEST);       // Milan v1.2 5.5.4.1; Milan v1.2 Table 5.41
		respond(a, interface, &r, 0u);
		return;
	}
	struct acmp_source_state st;
	memset(&st, 0, sizeof st);
	p_source(a, src, &st);
	if (cmd->msg == ACMP_MSG_PROBE_TX_COMMAND) {
		struct pdu r = echo(cmd, st.dest_mac_valid ? ACMP_STATUS_SUCCESS : ACMP_STATUS_TALKER_DEST_MAC_FAIL);
		if (st.dest_mac_valid) {                                         // Milan v1.2 Table 5.43; Milan v1.2 Table 5.42
			r.flags = cmd->flags & (ACMP_FLAG_FAST_CONNECT | ACMP_FLAG_STREAMING_WAIT);
			r.stream_id = st.stream.stream_id;
			r.dest_mac = st.stream.dest_mac;
			r.vlan = st.stream.vlan_id;
		}
		respond(a, interface, &r, 0u);
		return;
	}
	struct pdu r = echo(cmd, ACMP_STATUS_SUCCESS);                            // Milan v1.2 5.5.4.3; Milan v1.2 Table 5.47
	r.listener = 0u;
	r.listener_uid = 0u;
	r.flags = st.asking_failed ? ACMP_FLAG_REGISTERING_FAILED : 0u;
	r.stream_id = st.stream.stream_id;
	r.dest_mac = st.dest_mac_valid ? st.stream.dest_mac : 0u;
	r.vlan = st.stream.vlan_id;
	respond(a, interface, &r, 0u);
}



bool acmp_init(struct acmp *a, const struct acmp_config *cfg, const struct acmp_ports *ports,
	       const struct acmp_env *env)
{
	if (cfg->n_interfaces == 0u || cfg->n_interfaces > ACMP_MAX_INTERFACES || cfg->n_sinks > ACMP_MAX_SINKS ||
	    cfg->n_sources > ACMP_MAX_SOURCES) {
		return false;
	}
	for (unsigned k = 0; k < cfg->n_sinks; ++k) {
		if (cfg->sink_interface[k] >= cfg->n_interfaces) {
			return false;
		}
	}
	for (unsigned k = 0; k < cfg->n_sources; ++k) {
		if (cfg->source_interface[k] >= cfg->n_interfaces) {
			return false;
		}
	}
	memset(a, 0, sizeof *a);
	a->cfg = *cfg;
	a->ports = ports;
	a->env = env;
	for (unsigned k = 0; k < cfg->n_sinks; ++k) {
		sink_reset(a, k);
		sink_settle(&a->sinks[k]);
	}
	a->rng = (uint32_t)cfg->entity_id ^ (uint32_t)(cfg->entity_id >> 32) ^ 0x7F4A7C15u;
	return true;
}

void acmp_rx(struct acmp *a, unsigned interface, const uint8_t *frame, size_t len)
{
	if (!enter(a)) {
		return;
	}
	if (interface >= a->cfg.n_interfaces || len < ACMP_FRAME_BYTES || wire_be16(frame + 12) != ACMP_ETHERTYPE ||
	    frame[PDU] != ACMP_SUBTYPE || AVTP_VERSION(frame) != ACMP_AVTP_VERSION) {
		a->rx_malformed++;
		return;
	}
	struct pdu cmd;
	decode(frame, &cmd);
	bool talker = cmd.talker == a->cfg.entity_id;
	bool listener = cmd.listener == a->cfg.entity_id;
	switch (cmd.msg) {
	case ACMP_MSG_PROBE_TX_COMMAND:
	case ACMP_MSG_DISCONNECT_TX_COMMAND:
	case ACMP_MSG_GET_TX_STATE_COMMAND:
	case ACMP_MSG_GET_TX_CONNECTION_COMMAND:
		if (talker) {
			talker_command(a, interface, &cmd);
		} else {
			a->rx_ignored++;
		}
		break;
	case ACMP_MSG_BIND_RX_COMMAND:
	case ACMP_MSG_UNBIND_RX_COMMAND:
	case ACMP_MSG_GET_RX_STATE_COMMAND:
		if (listener) {
			listener_command(a, interface, &cmd);
		} else {
			a->rx_ignored++;
		}
		break;
	case ACMP_MSG_PROBE_TX_RESPONSE:
		if (listener) {
			probe_response(a, &cmd);
		} else {
			a->rx_ignored++;
		}
		break;
	default:
		a->rx_ignored++;                                // Milan v1.2 5.5.3.1
		break;
	}
	finish(a);
}

void acmp_adp_rx(struct acmp *a, unsigned interface, const uint8_t *frame, size_t len)
{
	if (!enter(a)) {
		return;
	}
	if (interface >= a->cfg.n_interfaces || len < ACMP_ADP_FRAME_BYTES || wire_be16(frame + 12) != ACMP_ETHERTYPE ||
	    frame[PDU] != ACMP_ADP_SUBTYPE || AVTP_VERSION(frame) != ACMP_AVTP_VERSION ||
	    (frame[O_MSG] & 0x0Fu) > ACMP_ADP_MSG_ENTITY_DEPARTING) {
		a->adp_ignored++;
		return;
	}
	uint8_t msg = frame[O_MSG] & 0x0Fu;
	uint64_t entity = wire_be64(frame + A_ENTITY_ID);
	struct adpdu d;
	memset(&d, 0, sizeof d);
	d.interface = interface;
	d.valid_ms = (uint32_t)(frame[A_VALID_TIME] >> 3) * ACMP_VALID_TIME_UNIT_MS;   // IEEE 1722.1-2021 6.2.2.5
	d.index = wire_be32(frame + A_AVAILABLE_INDEX);
	d.gm = wire_be64(frame + A_GM);
	d.domain = frame[A_DOMAIN];
	d.ifx = wire_be16(frame + A_INTERFACE_INDEX);
	unsigned taken = 0;
	for (unsigned k = 0; k < a->cfg.n_sinks; ++k) {        // Milan v1.2 5.6.4.1
		struct acmp_sink *s = &a->sinks[k];
		if (!s->disc_running || s->interface != interface || s->binding.talker_entity_id != entity) {
			continue;
		}
		taken++;
		if (msg == ACMP_ADP_MSG_ENTITY_DEPARTING) {
			disc_departing(s, d.ifx);
		} else {
			disc_available(a, s, &d);
		}
	}
	if (taken == 0u) {
		a->adp_ignored++;
	}
	finish(a);
}







void acmp_timer_expired(struct acmp *a, unsigned interface)
{
	if (!enter(a)) {
		return;
	}
	if (interface >= a->cfg.n_interfaces) {
		a->impossible++;
		return;
	}
	a->timer_armed[interface] = false;
	for (unsigned k = 0; k < a->cfg.n_sinks; ++k) {
		struct acmp_sink *s = &a->sinks[k];
		if (s->interface != interface) {
			continue;
		}
		if (s->adp_armed && due(s->adp_deadline, now(a))) {      // Milan v1.2 5.6.4.5.4
			s->adp_armed = false;
			tk_departed(s);
		}
		while (sm_running(s) && due(s->timer_deadline, now(a))) {
			sm_expired(a, k);
		}
	}
	finish(a);
}

void acmp_tk_registered(struct acmp *a, unsigned sink, bool failed)
{
	if (!enter(a)) {
		return;
	}
	if (sink >= a->cfg.n_sinks || a->sinks[sink].state != ACMP_SETTLED_NO_RSV) {
		a->impossible++;                                // Milan v1.2 Table 5.30
		return;
	}
	struct acmp_sink *s = &a->sinks[sink];                  // Milan v1.2 5.5.3.5.42
	sm_stop(s);
	s->tk_failed = failed;
	s->state = ACMP_SETTLED_RSV_OK;
	finish(a);
}

void acmp_tk_kind_changed(struct acmp *a, unsigned sink, bool failed)
{
	if (!enter(a)) {
		return;
	}
	if (sink >= a->cfg.n_sinks || a->sinks[sink].state != ACMP_SETTLED_RSV_OK) {
		a->impossible++;
		return;
	}
	a->sinks[sink].tk_failed = failed;
	finish(a);
}

void acmp_tk_unregistered(struct acmp *a, unsigned sink)
{
	if (!enter(a)) {
		return;
	}
	if (sink >= a->cfg.n_sinks || a->sinks[sink].state != ACMP_SETTLED_RSV_OK) {
		a->impossible++;                                // Milan v1.2 Table 5.30
		return;
	}
	srp_stop(a, sink);                                      // Milan v1.2 5.5.3.5.48
	reprobe(a, &a->sinks[sink]);
	finish(a);
}

bool acmp_set_started(struct acmp *a, unsigned sink, bool started)
{
	if (!enter(a)) {
		return false;
	}
	if (sink >= a->cfg.n_sinks || !a->sinks[sink].bound) {
		return false;
	}
	a->sinks[sink].started = started;
	finish(a);
	return true;
}

bool acmp_poll(struct acmp *a)
{
	if (!enter(a)) {
		return a->owed_count != 0u;
	}
	if (a->owed_count != 0u) {
		const struct acmp_owed *o = &a->owed[a->owed_head];
		if (p_send(a, o->interface, o->frame)) {
			for (unsigned k = 0; k < a->cfg.n_sinks; ++k) {
				a->sinks[k].change_owed = (uint8_t)(a->sinks[k].change_owed - ((o->release >> k) & 1u));
			}
			probe_left(a, o);
			a->owed_head = (a->owed_head + 1u) % ACMP_OWED_MAX;
			a->owed_count--;
			finish(a);
		}
	}
	return a->owed_count != 0u;
}

enum acmp_restore acmp_restore_binding(struct acmp *a, unsigned sink, const uint8_t *payload, unsigned len)
{
	if (!enter(a)) {
		return ACMP_RESTORE_REFUSED;
	}
	if (sink >= a->cfg.n_sinks || len != ACMP_BINDING_BYTES) {
		return ACMP_RESTORE_REFUSED;
	}
	sink_reset(a, sink);
	struct acmp_sink *s = &a->sinks[sink];
	if ((payload[0] & BIND_VALID) != 0u) {                  // Milan v1.2 5.5.3.5.2
		s->bound = true;
		s->started = (payload[0] & BIND_STARTED) != 0u;
		s->binding.streaming_wait = (payload[0] & BIND_STREAMING_WAIT) != 0u;
		s->binding.talker_unique_id = wire_be16(payload + 2);
		s->binding.talker_entity_id = wire_be64(payload + 4);
		s->binding.controller_entity_id = wire_be64(payload + 12);
		disc_start(s);
		s->probing = ACMP_PROBING_PASSIVE;
		s->state = ACMP_PRB_W_AVAIL;
	}
	sink_settle(s);
	return ACMP_RESTORE_APPLIED;
}

void acmp_restore_rollback(struct acmp *a)
{
	if (!enter(a)) {
		return;
	}
	for (unsigned k = 0; k < a->cfg.n_sinks; ++k) {
		sink_reset(a, k);
		sink_settle(&a->sinks[k]);
	}
}

void acmp_open(struct acmp *a)
{
	if (!enter(a)) {
		return;
	}
	finish(a);
}

bool acmp_binding_latch(const struct acmp *a, unsigned sink, uint8_t payload[ACMP_BINDING_BYTES])
{
	if (sink >= a->cfg.n_sinks) {
		return false;
	}
	record_of(&a->sinks[sink], payload);
	return true;
}

bool acmp_view(const struct acmp *a, unsigned sink, struct acmp_sink_view *view)
{
	if (sink >= a->cfg.n_sinks) {
		return false;
	}
	view_of(&a->sinks[sink], view);
	return true;
}

bool acmp_change_pending(const struct acmp *a, unsigned sink)
{
	return sink < a->cfg.n_sinks && a->sinks[sink].change_owed != 0u;
}
