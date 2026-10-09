// SPDX-License-Identifier: MIT
#define _GNU_SOURCE
#include "adp.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>

struct observer { unsigned calls, sends, starts, stops; bool room, link; };
static bool send_frame(void *v, unsigned i, const uint8_t *f, size_t n) {
    struct observer *p=v; (void)i; (void)f; (void)n;
    ++p->calls; ++p->sends; return p->room;
}
static void start(void *v, unsigned i, uint32_t ms) {
    struct observer *p=v; (void)i; (void)ms; ++p->calls; ++p->starts;
}
static void stop(void *v, unsigned i) {
    struct observer *p=v; (void)i; ++p->calls; ++p->stops;
}
static void gptp(void *v, unsigned i, uint64_t *gm, uint8_t *d) {
    (void)i; ++((struct observer *)v)->calls; *gm=1; *d=2;
}
static bool link_up(void *v, unsigned i) {
    (void)i; struct observer *p=v; ++p->calls; return p->link;
}
static uint32_t seed(void *v) { ++((struct observer *)v)->calls; return 12345; }
static void fail(const char *what, unsigned state, unsigned field) {
    fprintf(stderr, "FAIL %s state=%u field=%u\n", what, state, field); exit(1);
}
static void frame_make(uint8_t *f, uint64_t id, unsigned header) {
    memset(f,0,128); f[12]=0x22; f[13]=0xf0; f[14]=0xfa; f[15]=2;
    f[16]=(uint8_t)(header>>8); f[17]=(uint8_t)header;
    for (unsigned j=0;j<8;++j) f[18+j]=(uint8_t)(id>>(56-8*j));
}
static void check(const struct adp *base, struct observer *p, const uint8_t *f,
                  size_t len, bool refused, unsigned state, unsigned field) {
    struct adp a, expected; struct observer before;
    memcpy(&a,base,sizeof a); memcpy(&expected,base,sizeof expected);
    memcpy(&before,p,sizeof before);
    adp_rx(&a,f,len);
    if (refused) ++expected.discarded;
    if (refused || state!=4) {
        if (memcmp(&a,&expected,sizeof a)) fail("storage-or-discard",state,field);
        if (memcmp(p,&before,sizeof before)) fail("callback",state,field);
    } else {
        if (a.discarded!=base->discarded || a.state!=ADP_STATE_DELAY ||
            a.timer!=ADP_TIMER_DELAY || a.draws!=base->draws+1 ||
            p->calls!=before.calls+2 || p->starts!=before.starts+1 ||
            p->stops!=before.stops+1 || p->sends!=before.sends)
            fail("valid-control",state,field);
    }
    memcpy(p,&before,sizeof before);
}
int main(void) {
    unsigned long cases=0;
    const long page=sysconf(_SC_PAGESIZE);
    if (page<128) return 2;
    uint8_t *mem=mmap(NULL,(size_t)page*2,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANONYMOUS,-1,0);
    if (mem==MAP_FAILED || mprotect(mem+page,(size_t)page,PROT_NONE)) return 2;
    const struct adp_entity entity={.entity_id=UINT64_C(0x1122334455667788)};
    for (unsigned state=0;state<7;++state) {
        struct observer p={.room=true,.link=state!=1};
        const struct adp_ports ports={&p,send_frame,start,stop,gptp,link_up,seed};
        struct adp base; adp_init(&base,&entity,&ports,0,0);
        if(state) adp_set_enable(&base,true);
        if(state==3) p.room=false;
        if(state>=3) adp_timer_expired(&base);
        if(state>=5) { p.room=false; adp_set_enable(&base,false); }
        if(state==6) { adp_set_enable(&base,true); adp_timer_expired(&base); }
        const enum adp_state states[]={ADP_STATE_DOWN,ADP_STATE_DOWN,ADP_STATE_DELAY,
            ADP_STATE_DELAY,ADP_STATE_WAITING,ADP_STATE_DOWN,ADP_STATE_DELAY};
        if(base.state!=states[state] || (state==3 && !base.available_owed) ||
           (state>=5 && !base.departing_owed)) fail("setup",state,0);
        for(unsigned target=0;target<2;++target) {
            uint8_t bytes[129], *f=bytes+1;
            uint64_t id=target?entity.entity_id:0;
            for(unsigned word=0;word<65536;++word) {
                frame_make(f,id,word);
                check(&base,&p,f,82,(word&2047)!=56,state,word); ++cases;
            }
            for(unsigned version=1;version<8;++version) {
                frame_make(f,id,0xf838); f[15]=(uint8_t)(2|(version<<4));
                check(&base,&p,f,82,true,state,version); ++cases;
            }
            frame_make(f,id,56);
            for(unsigned len=0;len<82;++len) {
                uint8_t *short_f=mem+page-len;
                memcpy(short_f,f,len);
                check(&base,&p,short_f,len,true,state,len); ++cases;
            }
            for(unsigned len=82;len<=128;++len) {
                check(&base,&p,f,len,false,state,len); ++cases;
            }
            base.discarded=UINT32_MAX;
            f[15]=0x12;
            check(&base,&p,f,82,true,state,0); ++cases;
            base.discarded=0;
        }
    }
    if(munmap(mem,(size_t)page*2)) return 2;
    printf("PASS %lu cases; seven states; two targets; all 65536 control words; versions 1..7; guarded lengths 0..81; unaligned input; trailing lengths 82..128; discard wrap\n",cases);
    return 0;
}
