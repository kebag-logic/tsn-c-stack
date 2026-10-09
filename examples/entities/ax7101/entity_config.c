// SPDX-License-Identifier: MIT
#include "entity_config.h"

_Static_assert(AX7101_ENTITY_SCHEMA_VERSION == 0x010000u, "entity schema version mismatch");
_Static_assert(ACMP_MAX_INTERFACES >= 1u, "entity capacity mismatch");
_Static_assert(ACMP_MAX_SINKS >= 2u, "entity capacity mismatch");
_Static_assert(ACMP_MAX_SOURCES >= 2u, "entity capacity mismatch");

const struct ax7101_identity ax7101_identity = {
    .name = "\115\151\154\141\156\040\106\120\107\101\040\061\170\061\040\124\104\115\070",
    .vendor_name = "\113\145\142\141\147\040\114\157\147\151\143",
    .serial_number = "\101\130\067\061\060\061\055\060\060\060\061",
    .group_name = "",
};

// IEEE 1722.1-2021 6.2.2; Milan v1.2 5.6.2
const struct adp_entity ax7101_adp[1] = {
    {
        .entity_id = UINT64_C(0x020000fffe000001),
        .entity_model_id = UINT64_C(0x001bc5c1935893e1),
        .mac = UINT64_C(0x0000020000000001),
        .entity_capabilities = 50568u,
        .talker_stream_sources = 2u,
        .talker_capabilities = 18433u,
        .listener_stream_sinks = 2u,
        .listener_capabilities = 18433u,
        .identify_control_index = 0u,
    },
};

// Milan v1.2 5.5.3.5.1
const struct acmp_config ax7101_acmp = {
    .entity_id = UINT64_C(0x020000fffe000001),
    .n_interfaces = 1u,
    .mac = {UINT64_C(0x020000000001)},
    .n_sinks = 2u,
    .sink_interface = {0u, 0u},
    .n_sources = 2u,
    .source_interface = {0u, 0u},
};

// IEEE 1722-2016 B.3.2; IEEE 1722-2016 B.4
const struct ax7101_maap_config ax7101_maap[1] = {
    {.interface = 0u, .mac = UINT64_C(0x020000000001), .count = 2u, .preferred = UINT64_C(0x000000000000)},
};
