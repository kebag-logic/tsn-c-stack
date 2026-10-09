// SPDX-License-Identifier: MIT
#ifndef TSN_PORT_ASSERT_H
#define TSN_PORT_ASSERT_H
_Noreturn void port_assert_failed(void);
#ifdef NDEBUG
#define assert(expression) ((void)0)
#else
#define assert(expression) ((expression) ? (void)0 : port_assert_failed())
#endif
#endif
