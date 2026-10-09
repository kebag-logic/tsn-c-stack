// SPDX-License-Identifier: MIT
// Reviewer probe: replays the five discovery_state() conditions of tests/test_adp.cpp
// and the RV32 smoke setup, printing the reached ADP state, timer and owed flags, then
// checks header-offset decoding against an independently built ADPDU.
#include <stdio.h>
#include <string.h>
#include "adp.h"
#include "wire.h"

struct fk { int room, link; unsigned sends, starts, stops; } fk;
static bool snd(void *c, unsigned i, const uint8_t *f, size_t n) { (void)c; (void)i; (void)f; (void)n; if (!fk.room) return false; fk.sends++; return true; }
static void st(void *c, unsigned i, uint32_t ms) { (void)c; (void)i; (void)ms; fk.starts++; }
static void sp(void *c, unsigned i) { (void)c; (void)i; fk.stops++; }
static void gp(void *c, unsigned i, uint64_t *gm, uint8_t *d) { (void)c; (void)i; *gm = 1; *d = 0; }
static bool lk(void *c, unsigned i) { (void)c; (void)i; return fk.link; }
static uint32_t sd(void *c) { (void)c; return 0x5EED; }
static const struct adp_ports ports = {NULL, snd, st, sp, gp, lk, sd};
static const struct adp_entity entity = {.entity_id = 0x0011223344556677ull};

static void setup(struct adp *a, unsigned s) {
    memset(&fk, 0, sizeof fk); fk.room = 1; fk.link = s != 1u;
    adp_init(a, &entity, &ports, 0, 2);
    if (s != 0u) adp_set_enable(a, true);
    if (s == 3u) fk.room = 0;
    if (s >= 3u) adp_timer_expired(a);
}

/* independent ADPDU: Ethernet(14) + AVTP control header(12) + 56 */
static void build(uint8_t *f, unsigned sv, unsigned ver, unsigned msg, unsigned vt, unsigned cdl, uint64_t eid) {
    memset(f, 0, 82);
    f[12] = 0x22; f[13] = 0xF0;
    f[14] = 0xFA;
    f[15] = (uint8_t)((sv << 7) | (ver << 4) | msg);
    f[16] = (uint8_t)((vt << 3) | (cdl >> 8)); f[17] = (uint8_t)cdl;
    for (int i = 0; i < 8; ++i) f[18 + i] = (uint8_t)(eid >> (56 - 8 * i));
}

static int outcome(unsigned s, const uint8_t *f, size_t n) {
    struct adp a; setup(&a, s);
    unsigned d = a.discarded; enum adp_state st0 = a.state;
    adp_rx(&a, f, n);
    if (a.discarded == d + 1u) return 'R';            /* refused and counted */
    if (a.state != st0) return 'A';                   /* acted: entered DELAY */
    return 'I';                                       /* ignored by state */
}

int main(void) {
    static const char *names[] = {"disabled", "DOWN(link down)", "DELAY", "blocked-output DELAY", "WAITING"};
    for (unsigned s = 0; s < 5; ++s) {
        struct adp a; setup(&a, s);
        printf("cond %u %-22s enabled=%d state=%d timer=%d available_owed=%d departing_owed=%u sends=%u\n",
               s, names[s], a.enabled, (int)a.state, (int)a.timer, (int)a.available_owed, (unsigned)a.departing_owed, fk.sends);
    }
    uint8_t f[82], g[82];
    struct adp a; setup(&a, 4);
    adp_build(&a, ADP_MSG_ENTITY_DISCOVER, 0, g);
    build(f, 0, 0, 2, 0, 56, 0);
    printf("adp_build discover header bytes 12..17 match independent layout: %s\n", memcmp(f + 12, g + 12, 6) == 0 ? "yes" : "no");
    printf("valid global      : %c\n", outcome(4, f, 82));
    build(f, 0, 0, 2, 0, 56, entity.entity_id); printf("valid own         : %c\n", outcome(4, f, 82));
    build(f, 0, 1, 2, 0, 56, 0); printf("version 1         : %c\n", outcome(4, f, 82));
    build(f, 0, 0, 2, 0, 56, 0); printf("len 81            : %c\n", outcome(4, f, 81));
    printf("len 26            : %c\n", outcome(4, f, 26));
    build(f, 0, 0, 2, 0, 0, 0); printf("cdl 0             : %c\n", outcome(4, f, 82));
    build(f, 0, 0, 2, 0, 56 + 2048 - 2048, 0); printf("cdl 56            : %c\n", outcome(4, f, 82));
    build(f, 0, 0, 2, 31, 56, 0); printf("valid_time 31 cdl 56 (upper 5 bits) : %c\n", outcome(4, f, 82));
    build(f, 1, 0, 2, 0, 56, 0); printf("sv=1 version 0    : %c\n", outcome(4, f, 82));
    build(f, 0, 0, 2, 0, 56, 0x99); printf("foreign target    : %c\n", outcome(4, f, 82));
    return 0;
}
