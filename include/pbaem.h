// SPDX-License-Identifier: MIT
#ifndef PBAEM_H
#define PBAEM_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

// REQ: AEM-01
enum {
    PBAEM_AAF_STREAMS = 4,
    PBAEM_STREAMS = 5,
    PBAEM_CLUSTERS = 48,
    PBAEM_CLOCK_SOURCES = 6,
    PBAEM_DESCRIPTORS = 84,
    PBAEM_DESCRIPTOR_BYTES = 452
};

struct pbaem_identity {
    uint64_t entity_id;
    uint64_t model_id;
    uint64_t mac;
    uint64_t clock_identity;
    char name[64];
    char firmware[64];
    char serial[64];
    char group[64];
};

struct pbaem {
    struct pbaem_identity identity;
    uint64_t input_formats[PBAEM_STREAMS];
    uint32_t available_index;
    uint16_t clock_source;
    uint8_t identify;
};

void pbaem_init(struct pbaem *model, const struct pbaem_identity *identity);
uint64_t pbaem_output_format(unsigned stream);
uint64_t pbaem_default_input_format(unsigned stream);
bool pbaem_input_format_supported(unsigned stream, uint64_t format);
bool pbaem_set_input_format(struct pbaem *model, unsigned stream, uint64_t format);
bool pbaem_set_clock_source(struct pbaem *model, unsigned source);
unsigned pbaem_count(uint16_t type);
size_t pbaem_descriptor(const struct pbaem *model, uint16_t type, uint16_t index,
                        uint8_t *output, size_t capacity);

#ifdef __cplusplus
}
#endif

#endif
