// SPDX-License-Identifier: MIT
#include "entity_config.h"

_Static_assert(POCKETBEAGLE_ENTITY_SCHEMA_VERSION == 0x010000u, "entity schema version mismatch");
_Static_assert(ACMP_MAX_INTERFACES >= 1u, "entity capacity mismatch");
_Static_assert(ACMP_MAX_SINKS >= 5u, "entity capacity mismatch");
_Static_assert(ACMP_MAX_SOURCES >= 5u, "entity capacity mismatch");

const struct pocketbeagle_identity pocketbeagle_identity = {
    .name = "\120\157\143\153\145\164\102\145\141\147\154\145\040\062\040\142\162\151\144\147\145",
    .vendor_name = "\113\145\142\141\147\040\114\157\147\151\143",
    .serial_number = "",
    .group_name = "",
};

// IEEE 1722.1-2021 6.2.2; Milan v1.2 5.6.2
const struct adp_entity pocketbeagle_adp[1] = {
    {
        .entity_id = UINT64_C(0x020000fffe000001),
        .entity_model_id = UINT64_C(0x001bc5c52e47a158),
        .mac = UINT64_C(0x0000020000000001),
        .entity_capabilities = 50568u,
        .talker_stream_sources = 5u,
        .talker_capabilities = 18433u,
        .listener_stream_sinks = 5u,
        .listener_capabilities = 18433u,
        .identify_control_index = 0u,
    },
};

// Milan v1.2 5.5.3.5.1
const struct acmp_config pocketbeagle_acmp = {
    .entity_id = UINT64_C(0x020000fffe000001),
    .n_interfaces = 1u,
    .da_fresh_ms = 15000u,
    .mac = {UINT64_C(0x020000000001)},
    .n_sinks = 5u,
    .sink_interface = {0u, 0u, 0u, 0u, 0u},
    .n_sources = 5u,
    .source_interface = {0u, 0u, 0u, 0u, 0u},
};

// IEEE 1722-2016 B.3.2; IEEE 1722-2016 B.4
const struct pocketbeagle_maap_config pocketbeagle_maap[1] = {
    {.interface = 0u, .mac = UINT64_C(0x020000000001), .count = 5u, .preferred = UINT64_C(0x000000000000)},
};
