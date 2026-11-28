// SPDX-License-Identifier: MIT
#include <stdint.h>
#include <string.h>

void *memset(void *destination, int value, size_t length)
{
    unsigned char *out = destination;
    for (size_t i = 0; i < length; ++i) out[i] = (unsigned char)value;
    return destination;
}

void *memcpy(void *destination, const void *source, size_t length)
{
    unsigned char *out = destination;
    const unsigned char *in = source;
    for (size_t i = 0; i < length; ++i) out[i] = in[i];
    return destination;
}

_Noreturn void port_exit(unsigned code)
{
    *(volatile uint32_t *)UINT32_C(0x100000) = code ? (code << 16) | 0x3333u : 0x5555u;
    for (;;) { }
}

_Noreturn void port_assert_failed(void)
{
    port_exit(254);
}

void ctrl_reentry_assert(const char *module)
{
    (void)module;
    port_assert_failed();
}
