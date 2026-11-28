// SPDX-License-Identifier: MIT
#ifndef AX7101_ENTITY_CONFIG_V1_0_0_H
#define AX7101_ENTITY_CONFIG_V1_0_0_H

#include "adp.h"
#include "acmp.h"

#define AX7101_ENTITY_SCHEMA_VERSION 0x010000u

#ifdef __cplusplus
extern "C" {
#endif

struct ax7101_identity {
    char name[65];
    char vendor_name[65];
    char serial_number[65];
    char group_name[65];
};

// IEEE 1722-2016 B.3.2; IEEE 1722-2016 B.4
struct ax7101_maap_config {
    unsigned interface;
    uint64_t mac;
    uint16_t count;
    uint64_t preferred;
};

extern const struct ax7101_identity ax7101_identity;
extern const struct adp_entity ax7101_adp[1];
extern const struct acmp_config ax7101_acmp;
extern const struct ax7101_maap_config ax7101_maap[1];

#ifdef __cplusplus
}
#endif

#endif
