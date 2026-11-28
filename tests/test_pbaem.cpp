// SPDX-License-Identifier: MIT
#include <gtest/gtest.h>
#include <array>
#include <cstring>
#include "pbaem.h"
#include "wire.h"

namespace {
class Pbaem : public ::testing::Test {
protected:
    pbaem model{};
    std::array<uint8_t, 512> bytes{};
    void SetUp() override
    {
        pbaem_identity id{};
        id.entity_id = UINT64_C(0x0200aafffe000001);
        id.model_id = UINT64_C(0x001bc5c52e47a158);
        id.mac = UINT64_C(0x0200aa000001);
        id.clock_identity = UINT64_C(0x0200aafffe0000ee);
        std::memcpy(id.name, "Bridge under test", 17);
        std::memcpy(id.firmware, "9.8.7", 5);
        std::memcpy(id.serial, "SERIAL-7", 8);
        std::memcpy(id.group, "Group 3", 7);
        pbaem_init(&model, &id);
    }
    size_t read(uint16_t type, uint16_t index = 0)
    {
        bytes.fill(0xa5);
        return pbaem_descriptor(&model, type, index, bytes.data(), bytes.size());
    }
};

const uint16_t types[] = {0x0000, 0x0001, 0x0002, 0x0005, 0x0006, 0x0009, 0x000a, 0x000c,
                          0x000d, 0x000e, 0x000f, 0x0014, 0x0017, 0x001a, 0x0024};
const unsigned counts[] = {1, 1, 1, 5, 5, 1, 6, 1, 1, 4, 4, 48, 4, 1, 1};
}

// REQ: AEM-01
TEST_F(Pbaem, DescriptorBounds)
{
    for (unsigned t = 0; t < 15; ++t) {
        EXPECT_EQ(pbaem_count(types[t]), counts[t]) << "each descriptor type has its model count";
        for (unsigned i = 0; i < counts[t]; ++i) {
            const size_t n = read(types[t], static_cast<uint16_t>(i));
            ASSERT_GE(n, 4u) << "every counted descriptor is readable";
            EXPECT_LE(n, 452u) << "no descriptor exceeds the largest model descriptor";
            EXPECT_EQ(wire_be16(bytes.data()), types[t]) << "a descriptor carries its own type";
            EXPECT_EQ(wire_be16(bytes.data() + 2), i) << "a descriptor carries its own index";
            EXPECT_EQ(bytes[n], 0xa5) << "the writer stops at the descriptor length";
            const auto whole = bytes;
            for (size_t capacity : {size_t{0}, n - 1}) {
                bytes.fill(0xa5);
                EXPECT_EQ(pbaem_descriptor(&model, types[t], static_cast<uint16_t>(i), bytes.data(), capacity), 0u)
                    << "a short destination is refused";
                for (auto b : bytes) EXPECT_EQ(b, 0xa5) << "a refused read writes nothing";
            }
            ASSERT_EQ(pbaem_descriptor(&model, types[t], static_cast<uint16_t>(i), bytes.data(), n), n);
            EXPECT_EQ(bytes, whole) << "an exact destination receives the same descriptor";
        }
        EXPECT_EQ(read(types[t], static_cast<uint16_t>(counts[t])), 0u) << "the first index past a count is absent";
    }
    for (uint16_t absent : {0x0003, 0x0007, 0x0011, 0x001b, 0x0025, 0xffff}) {
        EXPECT_EQ(pbaem_count(absent), 0u) << "a descriptor type outside the model has no instance";
        EXPECT_EQ(read(absent), 0u) << "a descriptor type outside the model reads nothing";
    }
}

// REQ: AEM-01
TEST_F(Pbaem, EntityFromIdentity)
{
    model.available_index = 0x01020304;
    ASSERT_EQ(read(0x0000), 312u);
    EXPECT_EQ(wire_be64(bytes.data() + 4), UINT64_C(0x0200aafffe000001)) << "ENTITY entity_id is the caller's";
    EXPECT_EQ(wire_be64(bytes.data() + 12), UINT64_C(0x001bc5c52e47a158)) << "ENTITY entity_model_id is the caller's";
    EXPECT_EQ(wire_be32(bytes.data() + 20), 0xc588u) << "ENTITY declares the Milan entity capabilities";
    EXPECT_EQ(wire_be64(bytes.data() + 24), UINT64_C(0x0005480100054801))
        << "five talker sources and five listener sinks, audio and media clock";
    EXPECT_EQ(wire_be32(bytes.data() + 36), 0x01020304u) << "available_index follows the model state";
    EXPECT_EQ(std::memcmp(bytes.data() + 48, "Bridge under test", 18), 0) << "entity_name is the caller's";
    EXPECT_EQ(wire_be32(bytes.data() + 112), 0x00020000u) << "vendor string 2 and model string 0";
    EXPECT_EQ(std::memcmp(bytes.data() + 116, "9.8.7", 6), 0) << "firmware_version is the caller's";
    EXPECT_EQ(std::memcmp(bytes.data() + 180, "Group 3", 8), 0) << "group_name is the caller's";
    EXPECT_EQ(std::memcmp(bytes.data() + 244, "SERIAL-7", 9), 0) << "serial_number is the caller's";
    EXPECT_EQ(wire_be32(bytes.data() + 308), 0x00010000u) << "one configuration, index zero current";
    ASSERT_EQ(read(0x0009), 102u);
    EXPECT_EQ(wire_be64(bytes.data() + 70) >> 16, UINT64_C(0x0200aa000001)) << "AVB_INTERFACE carries the caller MAC";
    EXPECT_EQ(wire_be16(bytes.data() + 76), 7u) << "gPTP, SRP and the gPTP grandmaster are supported";
    EXPECT_EQ(wire_be64(bytes.data() + 78), UINT64_C(0x0200aafffe0000ee))
        << "AVB_INTERFACE clock_identity is the caller's own";
    EXPECT_EQ(wire_be64(bytes.data() + 86), UINT64_C(0xf8f8fffffef800fd)) << "the gPTP dataset of the end station";
    EXPECT_EQ(wire_be16(bytes.data() + 96), 1u) << "the AVB interface is port one";
}

// REQ: AEM-01
TEST_F(Pbaem, ConfigurationAndAudioUnit)
{
    ASSERT_EQ(read(0x0001), 106u);
    const uint8_t table[] = {0, 2, 0, 1, 0, 5, 0, 5, 0, 6, 0, 5, 0, 9, 0, 1,
                             0, 0x24, 0, 1, 0, 10, 0, 6, 0, 0x1a, 0, 1, 0, 12, 0, 1};
    EXPECT_EQ(wire_be32(bytes.data() + 70), 0x0008004au) << "eight top level counts at offset seventy four";
    EXPECT_EQ(std::memcmp(bytes.data() + 74, table, sizeof table), 0) << "the configuration lists every top level count";
    ASSERT_EQ(read(0x0002), 148u);
    EXPECT_EQ(wire_be64(bytes.data() + 72), UINT64_C(0x0004000000040000)) << "four stream ports each way from zero";
    EXPECT_EQ(wire_be32(bytes.data() + 136), 48000u) << "the audio unit runs at 48 kHz";
    EXPECT_EQ(wire_be64(bytes.data() + 140), UINT64_C(0x009000010000bb80)) << "48 kHz is its one sampling rate";
    const unsigned clusters[] = {8, 8, 4, 4};
    const unsigned bases[] = {0, 8, 16, 20};
    for (unsigned k = 0; k < 4; ++k) {
        ASSERT_EQ(read(0x000e, static_cast<uint16_t>(k)), 20u);
        EXPECT_EQ(wire_be16(bytes.data() + 6), 1u) << "an input port is a clock sync source";
        EXPECT_EQ(wire_be16(bytes.data() + 12), clusters[k]) << "an input port has its stream's mono clusters";
        EXPECT_EQ(wire_be16(bytes.data() + 14), bases[k]) << "input clusters follow the USB capture channels";
        EXPECT_EQ(wire_be16(bytes.data() + 16), 0u) << "an input port has no static map (Milan v1.2 5.3.3.9)";
        ASSERT_EQ(read(0x000f, static_cast<uint16_t>(k)), 20u);
        EXPECT_EQ(wire_be16(bytes.data() + 12), clusters[k]) << "an output port has its stream's mono clusters";
        EXPECT_EQ(wire_be16(bytes.data() + 14), 24 + bases[k]) << "output clusters follow the USB playback channels";
        EXPECT_EQ(wire_be32(bytes.data() + 16), 0x00010000u + k) << "an output port has its own static map";
        const size_t n = read(0x0017, static_cast<uint16_t>(k));
        ASSERT_EQ(n, 8 + 8 * clusters[k]);
        EXPECT_EQ(wire_be32(bytes.data() + 4), (8u << 16) | clusters[k]) << "a map lists one row per channel";
        for (unsigned j = 0; j < clusters[k]; ++j) {
            EXPECT_EQ(wire_be64(bytes.data() + 8 + 8 * j), (uint64_t{k} << 48) | (uint64_t{j} << 32) | (j << 16))
                << "stream channel j goes to cluster offset j";
        }
    }
    for (unsigned k = 0; k < 48; ++k) {
        ASSERT_EQ(read(0x0014, static_cast<uint16_t>(k)), 90u);
        const char *prefix = k < 24 ? "USB Out " : "USB In ";
        const unsigned n = k < 24 ? k : k - 24;
        char name[16] = {0};
        std::snprintf(name, sizeof name, "%s%u", prefix, n);
        EXPECT_EQ(std::memcmp(bytes.data() + 4, name, std::strlen(name) + 1), 0) << "each cluster has its USB name";
        EXPECT_EQ(wire_be16(bytes.data() + 70), k < 24 ? 0xffffu : 2u) << "output clusters come from the audio unit";
        EXPECT_EQ(wire_be64(bytes.data() + 76), UINT64_C(0x000001f4000001f4)) << "half a microsecond of latency";
        EXPECT_EQ(wire_be32(bytes.data() + 84), 0x00014000u) << "one channel of multibit linear audio";
    }
}

// REQ: AEM-01
TEST_F(Pbaem, StreamFormats)
{
    const uint64_t eight = UINT64_C(0x0205022002006000), four = UINT64_C(0x0205022001006000);
    const uint64_t crf = UINT64_C(0x041060010000bb80), family = UINT64_C(0x0215022002006000);
    const uint64_t outputs[] = {eight, eight, four, four, crf};
    for (unsigned k = 0; k < 5; ++k) {
        EXPECT_EQ(pbaem_output_format(k), outputs[k]) << "outputs run eight, eight, four, four channels and CRF";
        EXPECT_EQ(pbaem_default_input_format(k), outputs[k]) << "inputs start in their output's format";
        ASSERT_EQ(read(0x0006, static_cast<uint16_t>(k)), 146u);
        EXPECT_EQ(wire_be16(bytes.data() + 72), k == 4 ? 3u : 2u) << "only the CRF output is a clock sync source";
        EXPECT_EQ(wire_be64(bytes.data() + 74), outputs[k]) << "an output's current format is its own";
        EXPECT_EQ(wire_be32(bytes.data() + 82), 0x008a0001u) << "an output lists one format";
        EXPECT_EQ(wire_be32(bytes.data() + 128), 0u) << "an output has no receive buffer";
        EXPECT_EQ(wire_be64(bytes.data() + 138), outputs[k]) << "an output's one listed format";
        const unsigned listed = k == 4 ? 1 : 2;
        ASSERT_EQ(read(0x0005, static_cast<uint16_t>(k)), 138 + 8 * listed);
        EXPECT_EQ(wire_be16(bytes.data() + 72), 3u) << "every input is a clock sync source";
        EXPECT_EQ(wire_be32(bytes.data() + 82), 0x008a0000u + listed) << "an AAF input lists its base and its family";
        EXPECT_EQ(wire_be32(bytes.data() + 128), 2126000u) << "an input buffers the presentation offset";
        EXPECT_EQ(wire_be16(bytes.data() + 132), 138 + 8 * listed) << "no redundant streams follow the formats";
        EXPECT_EQ(wire_be64(bytes.data() + 138), outputs[k]) << "an input lists its base format first";
        if (k < 4) {
            EXPECT_EQ(wire_be64(bytes.data() + 146), family) << "an AAF input lists 1 to 8 channels (Milan 6.4)";
        }
    }
    EXPECT_EQ(pbaem_output_format(5), 0u) << "there is no sixth output";
    EXPECT_EQ(pbaem_default_input_format(5), 0u) << "there is no sixth input";
    for (unsigned k = 0; k < 4; ++k) {
        EXPECT_FALSE(pbaem_input_format_supported(k, UINT64_C(0x0205022000006000))) << "zero channels are refused";
        for (unsigned ch = 1; ch <= 8; ++ch) {
            EXPECT_TRUE(pbaem_input_format_supported(k, UINT64_C(0x0205022000006000) | (uint64_t{ch} << 22)))
                << "an AAF input takes every base channel count up to eight";
        }
        EXPECT_FALSE(pbaem_input_format_supported(k, UINT64_C(0x0205022002406000))) << "nine channels are refused";
        EXPECT_FALSE(pbaem_input_format_supported(k, UINT64_C(0x0206022002006000))) << "44.1 kHz is refused";
        EXPECT_FALSE(pbaem_input_format_supported(k, UINT64_C(0x0205021802006000))) << "24-bit depth is refused";
        EXPECT_FALSE(pbaem_input_format_supported(k, family)) << "the family entry is not a stream format";
        EXPECT_FALSE(pbaem_input_format_supported(k, crf)) << "an AAF input refuses CRF";
    }
    EXPECT_TRUE(pbaem_input_format_supported(4, crf)) << "the CRF input takes CRF";
    EXPECT_FALSE(pbaem_input_format_supported(4, eight)) << "the CRF input refuses AAF";
    EXPECT_FALSE(pbaem_input_format_supported(4, crf + 1)) << "the CRF input refuses another CRF format";
    EXPECT_FALSE(pbaem_input_format_supported(5, crf)) << "an absent input supports nothing";
    const auto before = model;
    EXPECT_FALSE(pbaem_set_input_format(&model, 2, crf)) << "an unsupported format is refused";
    EXPECT_EQ(std::memcmp(&model, &before, sizeof model), 0) << "a refused format changes nothing";
    EXPECT_TRUE(pbaem_set_input_format(&model, 2, eight)) << "a four channel input takes eight channels";
    ASSERT_EQ(read(0x0005, 2), 154u);
    EXPECT_EQ(wire_be64(bytes.data() + 74), eight) << "STREAM_INPUT current_format follows the change";
    EXPECT_EQ(wire_be64(bytes.data() + 138), four) << "the listed base format is the model's";
}

// REQ: AEM-01
TEST_F(Pbaem, ClockSourcesAndControl)
{
    const uint16_t locations[][2] = {{0x000a, 0}, {0x0005, 4}, {0x0005, 0}, {0x0005, 1}, {0x0005, 2}, {0x0005, 3}};
    const char *names[] = {"Internal", "CRF Clock", "Stream Clock 0", "Stream Clock 1", "Stream Clock 2",
                           "Stream Clock 3"};
    for (unsigned k = 0; k < 6; ++k) {
        ASSERT_EQ(read(0x000a, static_cast<uint16_t>(k)), 86u);
        EXPECT_EQ(std::memcmp(bytes.data() + 4, names[k], std::strlen(names[k]) + 1), 0) << "each source has its name";
        EXPECT_EQ(wire_be32(bytes.data() + 70), k == 0 ? 0x00020000u : 0x00020002u)
            << "the internal source and five input stream sources";
        EXPECT_EQ(wire_be16(bytes.data() + 82), locations[k][0]) << "a stream source is located on a STREAM_INPUT";
        EXPECT_EQ(wire_be16(bytes.data() + 84), locations[k][1]) << "CRF is STREAM_INPUT four, AAF k is k";
        EXPECT_TRUE(pbaem_set_clock_source(&model, k)) << "every listed source can be selected";
        ASSERT_EQ(read(0x0024), 88u);
        EXPECT_EQ(wire_be16(bytes.data() + 70), k) << "the clock domain reports the selected source";
        EXPECT_EQ(wire_be64(bytes.data() + 72) >> 32, UINT64_C(0x004c0006)) << "six sources listed at offset 76";
        EXPECT_EQ(wire_be16(bytes.data() + 76 + 2 * k), k) << "the domain lists source k at position k";
    }
    EXPECT_FALSE(pbaem_set_clock_source(&model, 6)) << "a seventh source is refused";
    EXPECT_EQ(model.clock_source, 5u) << "a refused source keeps the selection";
    model.identify = 0xff;
    ASSERT_EQ(read(0x001a), 113u);
    EXPECT_EQ(wire_be64(bytes.data() + 82), UINT64_C(0x90e0f00000000001)) << "the control is IDENTIFY";
    EXPECT_EQ(wire_be32(bytes.data() + 94), 0x00680001u) << "one value at offset one hundred four";
    const uint8_t value[] = {0x00, 0xff, 0xff, 0x00, 0xff, 0x00, 0x00, 0xff, 0xff};
    EXPECT_EQ(std::memcmp(bytes.data() + 104, value, sizeof value), 0) << "identify range, default and current value";
    ASSERT_EQ(read(0x000c), 72u);
    EXPECT_EQ(std::memcmp(bytes.data() + 4, "en-US", 6), 0) << "one English locale for the United States (7.2.11)";
    ASSERT_EQ(read(0x000d), 452u);
    EXPECT_EQ(std::memcmp(bytes.data() + 132, "Kebag Logic", 12), 0) << "string two is the vendor";
}
