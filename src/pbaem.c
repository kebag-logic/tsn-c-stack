// SPDX-License-Identifier: MIT
#include "pbaem.h"
#include "wire.h"
#include <string.h>

// REQ: AEM-01
// IEEE 1722.1-2021 Table 7-1
enum {
	ENTITY = 0x0000, CONFIGURATION = 0x0001, AUDIO_UNIT = 0x0002, STREAM_INPUT = 0x0005,
	STREAM_OUTPUT = 0x0006, AVB_INTERFACE = 0x0009, CLOCK_SOURCE = 0x000a, LOCALE = 0x000c,
	STRINGS = 0x000d, STREAM_PORT_INPUT = 0x000e, STREAM_PORT_OUTPUT = 0x000f,
	AUDIO_CLUSTER = 0x0014, AUDIO_MAP = 0x0017, CONTROL = 0x001a, CLOCK_DOMAIN = 0x0024
};

// Milan v1.2 6.2 and 6.4
#define AAF_BASE UINT64_C(0x0205022000006000)
#define AAF_FAMILY UINT64_C(0x0215022002006000)
#define AAF_CHANNEL_SHIFT 22u
#define AAF_CHANNEL_MASK UINT64_C(0x3ff)
// Milan v1.2 Table 7.1
#define CRF_FORMAT UINT64_C(0x041060010000bb80)

static const unsigned channels[PBAEM_AAF_STREAMS] = {8u, 8u, 4u, 4u};
static const unsigned cluster_base[PBAEM_AAF_STREAMS] = {0u, 8u, 16u, 20u};

static uint64_t aaf(unsigned count)
{
	return AAF_BASE | ((uint64_t)count << AAF_CHANNEL_SHIFT);
}

uint64_t pbaem_output_format(unsigned stream)
{
	if (stream >= PBAEM_STREAMS) {
		return 0;
	}
	return stream == PBAEM_AAF_STREAMS ? CRF_FORMAT : aaf(channels[stream]);
}

uint64_t pbaem_default_input_format(unsigned stream)
{
	return pbaem_output_format(stream);
}

// Milan v1.2 6.2 and 6.4; Milan v1.2 7.3.2
bool pbaem_input_format_supported(unsigned stream, uint64_t format)
{
	if (stream >= PBAEM_STREAMS) {
		return false;
	}
	if (stream == PBAEM_AAF_STREAMS) {
		return format == CRF_FORMAT;
	}
	uint64_t count = (format >> AAF_CHANNEL_SHIFT) & AAF_CHANNEL_MASK;
	return (format & ~(AAF_CHANNEL_MASK << AAF_CHANNEL_SHIFT)) == AAF_BASE && count >= 1u && count <= 8u;
}

void pbaem_init(struct pbaem *model, const struct pbaem_identity *identity)
{
	memset(model, 0, sizeof *model);
	model->identity = *identity;
	for (unsigned k = 0; k < PBAEM_STREAMS; ++k) {
		model->input_formats[k] = pbaem_default_input_format(k);
	}
}

bool pbaem_set_input_format(struct pbaem *model, unsigned stream, uint64_t format)
{
	if (!pbaem_input_format_supported(stream, format)) {
		return false;
	}
	model->input_formats[stream] = format;
	return true;
}

// IEEE 1722.1-2021 7.4.23
bool pbaem_set_clock_source(struct pbaem *model, unsigned source)
{
	if (source >= PBAEM_CLOCK_SOURCES) {
		return false;
	}
	model->clock_source = (uint16_t)source;
	return true;
}

// IEEE 1722.1-2021 7.2.2
unsigned pbaem_count(uint16_t type)
{
	switch (type) {
	case ENTITY: case CONFIGURATION: case AUDIO_UNIT: case AVB_INTERFACE: case LOCALE: case STRINGS:
	case CONTROL: case CLOCK_DOMAIN:
		return 1u;
	case STREAM_INPUT: case STREAM_OUTPUT:
		return PBAEM_STREAMS;
	case CLOCK_SOURCE:
		return PBAEM_CLOCK_SOURCES;
	case STREAM_PORT_INPUT: case STREAM_PORT_OUTPUT: case AUDIO_MAP:
		return PBAEM_AAF_STREAMS;
	case AUDIO_CLUSTER:
		return PBAEM_CLUSTERS;
	default:
		return 0u;
	}
}

static void put(uint8_t *d, unsigned at, uint64_t value, unsigned bytes)
{
	wire_put_be(d + at, value, bytes);
}

static void text(uint8_t *d, unsigned at, const char *s)
{
	for (unsigned k = 0; s[k] != 0; ++k) {
		d[at + k] = (uint8_t)s[k];
	}
}

static void number(uint8_t *d, unsigned at, unsigned n)
{
	if (n >= 10u) {
		d[at++] = (uint8_t)('0' + n / 10u);
	}
	d[at] = (uint8_t)('0' + n % 10u);
}

// IEEE 1722.1-2021 7.3.7
static void named(uint8_t *d, const char *name, unsigned suffix, bool numbered, uint16_t localized)
{
	text(d, 4u, name);
	if (numbered) {
		unsigned at = 4u;
		while (d[at] != 0) {
			++at;
		}
		number(d, at, suffix);
	}
	put(d, 68u, localized, 2u);
}

// IEEE 1722.1-2021 7.2.1
static size_t entity(const struct pbaem *m, uint8_t *d)
{
	const struct pbaem_identity *id = &m->identity;
	put(d, 4u, id->entity_id, 8u);
	put(d, 12u, id->model_id, 8u);
	put(d, 20u, 0xc588u, 4u);
	put(d, 24u, PBAEM_STREAMS, 2u);
	put(d, 26u, 0x4801u, 2u);
	put(d, 28u, PBAEM_STREAMS, 2u);
	put(d, 30u, 0x4801u, 2u);
	put(d, 36u, m->available_index, 4u);
	memcpy(d + 48u, id->name, 64u);
	put(d, 112u, 2u, 2u);
	put(d, 114u, 0u, 2u);
	memcpy(d + 116u, id->firmware, 64u);
	memcpy(d + 180u, id->group, 64u);
	memcpy(d + 244u, id->serial, 64u);
	put(d, 308u, 1u, 2u);
	return 312u;
}

// IEEE 1722.1-2021 7.2.2
static size_t configuration(uint8_t *d)
{
	static const uint16_t counts[8][2] = {
		{AUDIO_UNIT, 1u}, {STREAM_INPUT, PBAEM_STREAMS}, {STREAM_OUTPUT, PBAEM_STREAMS}, {AVB_INTERFACE, 1u},
		{CLOCK_DOMAIN, 1u}, {CLOCK_SOURCE, PBAEM_CLOCK_SOURCES}, {CONTROL, 1u}, {LOCALE, 1u}};
	named(d, "Default", 0u, false, 1u);
	put(d, 70u, 8u, 2u);
	put(d, 72u, 74u, 2u);
	for (unsigned k = 0; k < 8u; ++k) {
		put(d, 74u + 4u * k, counts[k][0], 2u);
		put(d, 76u + 4u * k, counts[k][1], 2u);
	}
	return 106u;
}

// IEEE 1722.1-2021 7.2.3
static size_t audio_unit(uint8_t *d)
{
	named(d, "Audio Unit", 0u, false, 0xffffu);
	put(d, 72u, PBAEM_AAF_STREAMS, 2u);
	put(d, 76u, PBAEM_AAF_STREAMS, 2u);
	put(d, 136u, 48000u, 4u);
	put(d, 140u, 144u, 2u);
	put(d, 142u, 1u, 2u);
	put(d, 144u, 48000u, 4u);
	return 148u;
}

// IEEE 1722.1-2021 7.2.6; Milan v1.2 5.3.3.4 and 6.4
static size_t stream(const struct pbaem *m, uint8_t *d, bool input, unsigned k)
{
	bool clock = k == PBAEM_AAF_STREAMS;
	unsigned formats = input && !clock ? 2u : 1u;
	size_t length = 138u + 8u * formats;
	if (clock) {
		named(d, "CRF", 0u, false, 0xffffu);
	} else {
		named(d, input ? "Stream In " : "Stream Out ", k, true, 0xffffu);
	}
	put(d, 72u, input || clock ? 3u : 2u, 2u);
	put(d, 74u, input ? m->input_formats[k] : pbaem_output_format(k), 8u);
	put(d, 82u, 138u, 2u);
	put(d, 84u, formats, 2u);
	put(d, 128u, input ? 2126000u : 0u, 4u);
	put(d, 132u, length, 2u);
	put(d, 138u, input ? pbaem_default_input_format(k) : pbaem_output_format(k), 8u);
	if (formats == 2u) {
		put(d, 146u, AAF_FAMILY, 8u);
	}
	return length;
}

// IEEE 1722.1-2021 7.2.8; Milan v1.2 5.3.3.5
static size_t avb_interface(const struct pbaem *m, uint8_t *d)
{
	named(d, "AVB Interface ", 0u, true, 0xffffu);
	put(d, 70u, m->identity.mac, 6u);
	put(d, 76u, 7u, 2u);
	put(d, 78u, m->identity.clock_identity, 8u);
	d[86] = 248u;
	d[87] = 248u;
	put(d, 88u, 0xffffu, 2u);
	d[90] = 0xfeu;
	d[91] = 248u;
	d[93] = 0xfdu;
	put(d, 96u, 1u, 2u);
	return 102u;
}

// IEEE 1722.1-2021 7.2.9; Milan v1.2 5.3.3.6
static size_t clock_source(uint8_t *d, unsigned k)
{
	if (k == 0u) {
		named(d, "Internal", 0u, false, 0xffffu);
	} else if (k == 1u) {
		named(d, "CRF Clock", 0u, false, 0xffffu);
	} else {
		named(d, "Stream Clock ", k - 2u, true, 0xffffu);
	}
	put(d, 70u, 2u, 2u);
	put(d, 72u, k == 0u ? 0u : 2u, 2u);
	put(d, 82u, k == 0u ? CLOCK_SOURCE : STREAM_INPUT, 2u);
	put(d, 84u, k == 0u ? 0u : k == 1u ? PBAEM_AAF_STREAMS : k - 2u, 2u);
	return 86u;
}

// IEEE 1722.1-2021 7.2.11 and 7.2.12
static size_t locale(uint8_t *d)
{
	text(d, 4u, "en-US");
	put(d, 68u, 1u, 2u);
	return 72u;
}

static size_t strings(uint8_t *d)
{
	text(d, 4u, "PocketBeagle 2 bridge");
	text(d, 68u, "48 kHz");
	text(d, 132u, "Kebag Logic");
	return 452u;
}

// IEEE 1722.1-2021 7.2.13; Milan v1.2 5.3.3.7 and 5.3.3.9
static size_t stream_port(uint8_t *d, bool input, unsigned k)
{
	put(d, 6u, input ? 1u : 0u, 2u);
	put(d, 12u, channels[k], 2u);
	put(d, 14u, (input ? 0u : 24u) + cluster_base[k], 2u);
	put(d, 16u, input ? 0u : 1u, 2u);
	put(d, 18u, input ? 0u : k, 2u);
	return 20u;
}

// IEEE 1722.1-2021 7.2.16
static size_t audio_cluster(uint8_t *d, unsigned k)
{
	bool output = k >= 24u;
	named(d, output ? "USB In " : "USB Out ", output ? k - 24u : k, true, 0xffffu);
	put(d, 70u, output ? AUDIO_UNIT : 0xffffu, 2u);
	put(d, 76u, 500u, 4u);
	put(d, 80u, 500u, 4u);
	put(d, 84u, 1u, 2u);
	d[86] = 0x40u;
	return 90u;
}

// IEEE 1722.1-2021 7.2.19
static size_t audio_map(uint8_t *d, unsigned k)
{
	put(d, 4u, 8u, 2u);
	put(d, 6u, channels[k], 2u);
	for (unsigned j = 0; j < channels[k]; ++j) {
		put(d, 8u + 8u * j, k, 2u);
		put(d, 10u + 8u * j, j, 2u);
		put(d, 12u + 8u * j, j, 2u);
	}
	return 8u + 8u * channels[k];
}

// IEEE 1722.1-2021 7.2.22 and 7.3.5; Milan v1.2 5.3.3.10 and 5.3.12
static size_t control(const struct pbaem *m, uint8_t *d)
{
	named(d, "Identify", 0u, false, 0xffffu);
	put(d, 70u, 500u, 4u);
	put(d, 74u, 500u, 4u);
	put(d, 80u, 1u, 2u);
	put(d, 82u, UINT64_C(0x90e0f00000000001), 8u);
	put(d, 94u, 104u, 2u);
	put(d, 96u, 1u, 2u);
	put(d, 98u, 0xffffu, 2u);
	d[105] = 0xffu;
	d[106] = 0xffu;
	d[108] = m->identify;
	put(d, 111u, 0xffffu, 2u);
	return 113u;
}

// IEEE 1722.1-2021 7.2.32; Milan v1.2 5.3.3.11
static size_t clock_domain(const struct pbaem *m, uint8_t *d)
{
	named(d, "Clock Reference Format", 0u, false, 0xffffu);
	put(d, 70u, m->clock_source, 2u);
	put(d, 72u, 76u, 2u);
	put(d, 74u, PBAEM_CLOCK_SOURCES, 2u);
	for (unsigned k = 0; k < PBAEM_CLOCK_SOURCES; ++k) {
		put(d, 76u + 2u * k, k, 2u);
	}
	return 88u;
}

// IEEE 1722.1-2021 7.2
size_t pbaem_descriptor(const struct pbaem *model, uint16_t type, uint16_t index,
			uint8_t *output, size_t capacity)
{
	if (index >= pbaem_count(type)) {
		return 0;
	}
	uint8_t d[PBAEM_DESCRIPTOR_BYTES];
	memset(d, 0, sizeof d);
	put(d, 0u, type, 2u);
	put(d, 2u, index, 2u);
	size_t length = 0;
	switch (type) {
	case ENTITY: length = entity(model, d); break;
	case CONFIGURATION: length = configuration(d); break;
	case AUDIO_UNIT: length = audio_unit(d); break;
	case STREAM_INPUT: length = stream(model, d, true, index); break;
	case STREAM_OUTPUT: length = stream(model, d, false, index); break;
	case AVB_INTERFACE: length = avb_interface(model, d); break;
	case CLOCK_SOURCE: length = clock_source(d, index); break;
	case LOCALE: length = locale(d); break;
	case STRINGS: length = strings(d); break;
	case STREAM_PORT_INPUT: length = stream_port(d, true, index); break;
	case STREAM_PORT_OUTPUT: length = stream_port(d, false, index); break;
	case AUDIO_CLUSTER: length = audio_cluster(d, index); break;
	case AUDIO_MAP: length = audio_map(d, index); break;
	case CONTROL: length = control(model, d); break;
	default: length = clock_domain(model, d); break;
	}
	if (capacity < length) {
		return 0;
	}
	memcpy(output, d, length);
	return length;
}
