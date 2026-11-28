// SPDX-License-Identifier: MIT
#ifndef TALKER_ENTITY_CONFIG_V1_0_0_H
#define TALKER_ENTITY_CONFIG_V1_0_0_H

#include "adp.h"
#include "acmp.h"

#define TALKER_ENTITY_SCHEMA_VERSION 0x010000u

#ifdef __cplusplus
extern "C" {
#endif

struct talker_identity {
    char name[65];
    char vendor_name[65];
    char serial_number[65];
    char group_name[65];
};

// IEEE 1722-2016 B.3.2; IEEE 1722-2016 B.4
struct talker_maap_config {
    unsigned interface;
    uint64_t mac;
    uint16_t count;
    uint64_t preferred;
};

extern const struct talker_identity talker_identity;
extern const struct adp_entity talker_adp[1];
extern const struct acmp_config talker_acmp;
extern const struct talker_maap_config talker_maap[1];

#ifdef __cplusplus
}
#endif

#endif
