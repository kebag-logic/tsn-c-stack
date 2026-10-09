// SPDX-License-Identifier: MIT
#ifndef DUPLEX_ENTITY_CONFIG_V1_0_0_H
#define DUPLEX_ENTITY_CONFIG_V1_0_0_H

#include "adp.h"
#include "acmp.h"

#define DUPLEX_ENTITY_SCHEMA_VERSION 0x010000u

#ifdef __cplusplus
extern "C" {
#endif

struct duplex_identity {
    char name[65];
    char vendor_name[65];
    char serial_number[65];
    char group_name[65];
};

// IEEE 1722-2016 B.3.2; IEEE 1722-2016 B.4
struct duplex_maap_config {
    unsigned interface;
    uint64_t mac;
    uint16_t count;
    uint64_t preferred;
};

extern const struct duplex_identity duplex_identity;
extern const struct adp_entity duplex_adp[2];
extern const struct acmp_config duplex_acmp;
extern const struct duplex_maap_config duplex_maap[2];

#ifdef __cplusplus
}
#endif

#endif
