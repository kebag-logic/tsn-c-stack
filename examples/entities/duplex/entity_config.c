// SPDX-License-Identifier: MIT
#include "entity_config.h"

_Static_assert(DUPLEX_ENTITY_SCHEMA_VERSION == 0x010000u, "entity schema version mismatch");
_Static_assert(ACMP_MAX_INTERFACES >= 2u, "entity capacity mismatch");
_Static_assert(ACMP_MAX_SINKS >= 2u, "entity capacity mismatch");
_Static_assert(ACMP_MAX_SOURCES >= 2u, "entity capacity mismatch");

const struct duplex_identity duplex_identity = {
    .name = "\105\170\141\155\160\154\145\040\144\165\160\154\145\170",
    .vendor_name = "\105\170\141\155\160\154\145\040\166\145\156\144\157\162",
    .serial_number = "\105\130\101\115\120\114\105\055\060\060\060\061",
    .group_name = "",
};

// IEEE 1722.1-2021 6.2.2; Milan v1.2 5.6.2
const struct adp_entity duplex_adp[2] = {
    {
        .entity_id = UINT64_C(0x020000fffe000001),
        .entity_model_id = UINT64_C(0x001bc50000000003),
        .mac = UINT64_C(0x0000020000000001),
        .entity_capabilities = 50568u,
        .talker_stream_sources = 2u,
        .talker_capabilities = 18433u,
        .listener_stream_sinks = 2u,
        .listener_capabilities = 18433u,
        .identify_control_index = 0u,
    },
    {
        .entity_id = UINT64_C(0x020000fffe000001),
        .entity_model_id = UINT64_C(0x001bc50000000003),
        .mac = UINT64_C(0x0000020000000002),
        .entity_capabilities = 50568u,
        .talker_stream_sources = 2u,
        .talker_capabilities = 18433u,
        .listener_stream_sinks = 2u,
        .listener_capabilities = 18433u,
        .identify_control_index = 0u,
    },
};

// Milan v1.2 5.5.3.5.1
const struct acmp_config duplex_acmp = {
    .entity_id = UINT64_C(0x020000fffe000001),
    .n_interfaces = 2u,
    .mac = {UINT64_C(0x020000000001), UINT64_C(0x020000000002)},
    .n_sinks = 2u,
    .sink_interface = {1u, 0u},
    .n_sources = 2u,
    .source_interface = {0u, 1u},
};

// IEEE 1722-2016 B.3.2; IEEE 1722-2016 B.4
const struct duplex_maap_config duplex_maap[2] = {
    {.interface = 0u, .mac = UINT64_C(0x020000000001), .count = 1u, .preferred = UINT64_C(0x91e0f0000010)},
    {.interface = 1u, .mac = UINT64_C(0x020000000002), .count = 1u, .preferred = UINT64_C(0x91e0f0000020)},
};
