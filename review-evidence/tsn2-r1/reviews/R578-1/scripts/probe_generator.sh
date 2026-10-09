#!/bin/sh
# SPDX-License-Identifier: MIT
# Usage: probe_generator.sh <tsn-c-stack checkout at the reviewed head> <scratch dir>
# Exercises generator refusals, determinism, drift detection, boundary output on the real cores.
set -u
REPO=$(cd "$1" && pwd); W=$2; rm -rf "$W"; mkdir -p "$W/tree" "$W/out"
git -C "$REPO" archive HEAD | tar -x -C "$W/tree"
T=$W/tree; G="python3 -I $T/scripts/entity_yaml.py"
step() { printf '\n## %s\n' "$1"; }
step "D1 determinism: generate every persona twice via CLI and compare with the tracked goldens"
for p in listener talker duplex ax7101; do
  $G $T/configs/$p.yaml --output $W/out/$p.1 --prefix $p; $G $T/configs/$p.yaml --output $W/out/$p.2 --prefix $p
  cmp -s $W/out/$p.1/entity_config.c $W/out/$p.2/entity_config.c && cmp -s $W/out/$p.1/entity_config.c $T/examples/entities/$p/entity_config.c && cmp -s $W/out/$p.1/entity_config.h $T/examples/entities/$p/entity_config.h && echo "$p: identical runs and identical to golden" || echo "$p: MISMATCH"
done
step "D2 drift: edit a config, then a golden, in the disposable copy; --examples --check must fail"
sed -i 's/interface: 1$/interface: 0/' $T/configs/duplex.yaml; (cd $T && python3 -I scripts/entity_yaml.py --examples --check); echo "config drift rc=$?"
git -C "$REPO" show HEAD:configs/duplex.yaml > $T/configs/duplex.yaml
sed -i 's/count = 2u/count = 3u/' $T/examples/entities/ax7101/entity_config.c; (cd $T && python3 -I scripts/entity_yaml.py --examples --check); echo "golden drift rc=$?"
git -C "$REPO" show HEAD:examples/entities/ax7101/entity_config.c > $T/examples/entities/ax7101/entity_config.c
(cd $T && python3 -I scripts/entity_yaml.py --examples --check); echo "restored copy rc=$?"
step "R refusal probes (each input is the duplex example with one change)"
probe() { label=$1; shift; python3 -I - "$T/configs/duplex.yaml" "$W/out/r.yaml" "$@" <<'PY'
import sys
src, dst, old, new = sys.argv[1:5]
text = open(src).read()
assert old in text, old
open(dst, 'w').write(text.replace(old, new, 1))
PY
  printf '%s: ' "$label"; $G $W/out/r.yaml --output $W/out/r --prefix r 2>&1; echo "rc=$?"; }
probe "R1 merge key" "capabilities:" "capabilities:
  <<: {entity: 50568}
  _x: 0
capabilities_unused:"
probe "R2 unquoted all-digit MAC (YAML 1.1 sexagesimal integer)" "- mac: 02:00:00:00:00:02" "- mac: 12:30:30:40:50:51"
probe "R3 sexagesimal integer accepted as identify index" "identify_control_index: 0" "identify_control_index: 1:00"
probe "R4 leading-zero octal integer for an interface" "  interface: 1
  kind: audio" "  interface: 01
  kind: audio"
probe "R5 65-byte name" "name: Example duplex" "name: $(printf 'x%.0s' $(seq 65))"
probe "R6 64-byte name" "name: Example duplex" "name: $(printf 'x%.0s' $(seq 64))"
probe "R7 schema_version as float" "schema_version: 1.0.0" "schema_version: 1.0"
probe "R8 entity_id hex string" "entity_id: mac-derived" "entity_id: '0x020000FFFE000001'"
probe "R9 unknown top-level field" "maap:" "extra: 1
maap:"
probe "R10 sink on missing interface" "  interface: 1
  kind: audio" "  interface: 2
  kind: audio"
probe "R11 tab-containing name" "name: Example duplex" "name: \"a\\tb\""
step "B boundary entity: 4 interfaces, 16/16 streams, max pool end; compile with the cores (C11 -Werror -pedantic) and C++20 header, then run init calls"
cat > $W/out/max.yaml <<'Y'
schema_version: 1.0.0
identity: {entity_id: mac-derived, model_id: 0xFFFFFFFFFFFFFFFE, name: '', vendor_name: '', serial_number: '', group_name: ''}
capabilities: {entity: 0x03F8CFFF, identify_control_index: 65535}
interfaces: [{mac: '02:00:00:00:00:01'}, {mac: '02:00:00:00:00:02'}, {mac: '02:00:00:00:00:03'}, {mac: 'fe:ff:ff:ff:ff:ff'}]
inputs: [{name: i, interface: 3, kind: clock}, {name: i, interface: 2, kind: audio}, {name: i, interface: 1, kind: audio}, {name: i, interface: 0, kind: audio}, {name: i, interface: 3, kind: audio}, {name: i, interface: 3, kind: audio}, {name: i, interface: 3, kind: audio}, {name: i, interface: 3, kind: audio}, {name: i, interface: 3, kind: audio}, {name: i, interface: 3, kind: audio}, {name: i, interface: 3, kind: audio}, {name: i, interface: 3, kind: audio}, {name: i, interface: 3, kind: audio}, {name: i, interface: 3, kind: audio}, {name: i, interface: 3, kind: audio}, {name: i, interface: 3, kind: audio}]
outputs: [{name: o, interface: 3, kind: audio}, {name: o, interface: 3, kind: audio}, {name: o, interface: 3, kind: audio}, {name: o, interface: 3, kind: audio}, {name: o, interface: 3, kind: audio}, {name: o, interface: 3, kind: audio}, {name: o, interface: 3, kind: audio}, {name: o, interface: 3, kind: audio}, {name: o, interface: 3, kind: audio}, {name: o, interface: 3, kind: audio}, {name: o, interface: 3, kind: audio}, {name: o, interface: 3, kind: audio}, {name: o, interface: 3, kind: audio}, {name: o, interface: 3, kind: audio}, {name: o, interface: 3, kind: clock}, {name: o, interface: 0, kind: audio}]
maap: [{interface: 3, preferred: 0x91E0F000FDF1}, {interface: 0, preferred: 0x91E0F000FDFF}]
Y
$G $W/out/max.yaml --output $W/out/max --prefix max; echo "generate rc=$?"
cat > $W/out/max/main.c <<'C'
#include "entity_config.h"
#include "maap.h"
#include <stdio.h>
static bool tx(void *c, unsigned i, const uint8_t *f, size_t l) { (void)c; (void)i; (void)f; (void)l; return true; }
static void st(void *c, unsigned i, uint32_t d) { (void)c; (void)i; (void)d; }
static void sp(void *c, unsigned i) { (void)c; (void)i; }
static void rg(void *c, unsigned i, uint64_t b, uint16_t n, bool v) { (void)c; (void)i; (void)b; (void)n; (void)v; }
static uint32_t ck(void *c) { (void)c; return 1; }
static void tm(void *c, unsigned i, bool a, uint32_t d) { (void)c; (void)i; (void)a; (void)d; }
static void gp(void *c, unsigned i, uint64_t *g, uint8_t *d) { (void)c; (void)i; *g = 1; *d = 0; }
static void ad(void *c, unsigned i, unsigned s, bool b, uint64_t t) { (void)c; (void)i; (void)s; (void)b; (void)t; }
static bool lk(void *c, uint64_t *o) { (void)c; *o = 0; return false; }
static void so(void *c, unsigned i, struct acmp_source_state *o) { (void)c; (void)i; (void)o; }
static void sr(void *c, unsigned s, const struct acmp_stream *x) { (void)c; (void)s; (void)x; }
static void nt(void *c, unsigned s) { (void)c; (void)s; }
int main(void)
{
    static struct acmp a; static struct maap m;
    const struct acmp_ports ap = {0, tx, ck, tm, gp, ck, ad};
    const struct acmp_env ae = {0, lk, so, sr, nt, nt};
    const struct maap_ports mp = {0, tx, st, sp, rg, ck};
    int bad = !acmp_init(&a, &max_acmp, &ap, &ae);
    unsigned owners = 0;
    for (unsigned i = 0; i < 4; ++i) {
        if (!max_maap[i].count) continue;
        ++owners;
        bad |= !maap_init(&m, &mp, max_maap[i].interface, max_maap[i].mac, max_maap[i].count);
        bad |= !maap_begin(&m, max_maap[i].preferred);
    }
    printf("acmp sinks=%u sources=%u if=%u; maap owners=%u counts=%u,%u; adp src=%u sink=%u tcaps=0x%04x lcaps=0x%04x eid=%016llx bad=%d\n",
           a.cfg.n_sinks, a.cfg.n_sources, a.cfg.n_interfaces, owners, max_maap[0].count, max_maap[3].count,
           max_adp[3].talker_stream_sources, max_adp[3].listener_stream_sinks, max_adp[3].talker_capabilities,
           max_adp[3].listener_capabilities, (unsigned long long)max_adp[0].entity_id, bad);
    return bad;
}
C
gcc -std=c11 -pedantic -Wall -Wextra -Werror -I$T/include -I$W/out/max $W/out/max/entity_config.c $W/out/max/main.c $T/src/adp.c $T/src/acmp.c $T/src/maap.c -o $W/out/max/run && $W/out/max/run; echo "boundary run rc=$?"
printf '#include "entity_config.h"\nint main() { return max_adp[0].identify_control_index == 65535u ? 0 : 1; }\n' > $W/out/max/cxx.cpp
g++ -std=c++20 -Wall -Wextra -Werror -I$T/include -I$W/out/max -c $W/out/max/cxx.cpp -o $W/out/max/cxx.o; echo "C++20 header rc=$?"
step "P prefixes that share core module names compile beside the cores"
for pre in adp acmp maap wire; do $G $T/configs/duplex.yaml --output $W/out/p_$pre --prefix $pre && printf '#include "entity_config.h"\n#include "maap.h"\n#include "wire.h"\nint main(void){return (int)%s_maap[0].count - 1;}\n' $pre > $W/out/p_$pre/m.c && gcc -std=c11 -Wall -Wextra -Werror -I$T/include -I$W/out/p_$pre $W/out/p_$pre/entity_config.c $W/out/p_$pre/m.c $T/src/adp.c $T/src/acmp.c $T/src/maap.c -o $W/out/p_$pre/m && $W/out/p_$pre/m; echo "prefix $pre rc=$?"; done
