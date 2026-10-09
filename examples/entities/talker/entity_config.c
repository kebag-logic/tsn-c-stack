// SPDX-License-Identifier: MIT
#include "entity_config.h"

_Static_assert(TALKER_ENTITY_SCHEMA_VERSION == 0x010000u, "entity schema version mismatch");
_Static_assert(ACMP_MAX_INTERFACES >= 1u, "entity capacity mismatch");
_Static_assert(ACMP_MAX_SINKS >= 0u, "entity capacity mismatch");
_Static_assert(ACMP_MAX_SOURCES >= 1u, "entity capacity mismatch");

const struct talker_identity talker_identity = {
    .name = "\105\170\141\155\160\154\145\040\164\141\154\153\145\162",
    .vendor_name = "\105\170\141\155\160\154\145\040\166\145\156\144\157\162",
    .serial_number = "\105\130\101\115\120\114\105\055\060\060\060\061",
    .group_name = "",
};

// IEEE 1722.1-2021 6.2.2; Milan v1.2 5.6.2
const struct adp_entity talker_adp[1] = {
    {
        .entity_id = UINT64_C(0x020000fffe000001),
        .entity_model_id = UINT64_C(0x001bc50000000002),
        .mac = UINT64_C(0x0000020000000001),
        .entity_capabilities = 50568u,
        .talker_stream_sources = 1u,
        .talker_capabilities = 16385u,
        .listener_stream_sinks = 0u,
        .listener_capabilities = 0u,
        .identify_control_index = 0u,
    },
};

// Milan v1.2 5.5.3.5.1
const struct acmp_config talker_acmp = {
    .entity_id = UINT64_C(0x020000fffe000001),
    .n_interfaces = 1u,
    .mac = {UINT64_C(0x020000000001)},
    .n_sinks = 0u,
    .sink_interface = {0u},
    .n_sources = 1u,
    .source_interface = {0u},
};

// IEEE 1722-2016 B.3.2; IEEE 1722-2016 B.4
const struct talker_maap_config talker_maap[1] = {
    {.interface = 0u, .mac = UINT64_C(0x020000000001), .count = 1u, .preferred = UINT64_C(0x91e0f0000010)},
};
